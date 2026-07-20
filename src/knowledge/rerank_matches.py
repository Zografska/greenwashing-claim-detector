#!/usr/bin/env python3
"""
LLM reranking over compare_e5.py's matches.json: for each ad, asks a local
Ollama model to actually read the ad's claim-relevant text next to its
top-k retrieved legal-passage candidates, and decide which one (if any)
genuinely applies.

Why this exists: embedding retrieval narrows the 56-passage legal corpus
down to a handful of candidates per ad, but evaluate_matches.py against
25.06/gold.json showed 0/8 top-1 accuracy even after fixing a chunking bug
-- several ECGT Art. 1 sub-definitions ("asserzione ambientale" / "asserzione
ambientale generica" / "marchio di sostenibilita") sit too close together in
embedding space for a short phrase like "Meno plastica" to separate. An LLM
reading the actual wording side-by-side can use lexical distinctions
embeddings miss. This is capped by what retrieval already surfaced, though:
if the right chunk isn't among an ad's top_matches, reranking can't recover
it -- rerun compare_e5.py with a larger --top-k first if that's the bottleneck.

The ad-side context given to the model is the FULL prefiltered text (all of
an ad's claim-adjacent sentences joined -- matches.json's query_sentences,
the same thing src/extraction.py's _prefilter_description produces), not
the single matched_sentence that won retrieval. A bare two-word fragment
like "Meno plastica" is too little context for an LLM to reason about too;
this is deliberately more context than embedding retrieval got (which
needs isolation to avoid hub dilution, see prepare_ads_chunks.py) and less
than the whole raw ad (nutrition tables etc. would distract the LLM the
same way they diluted the embeddings).

Requires a local Ollama server (see src/extraction.py's OLLAMA_URL).

Usage:
  python rerank_matches.py
  python rerank_matches.py --matches embeddings/matches.json --out embeddings/reranked.json --model llama3.2
"""

import argparse
import json
from pathlib import Path

import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
SCRIPT_DIR = Path(__file__).parent

SYSTEM_PROMPT = """You are an EU consumer-law analyst reviewing Italian grocery
ads against Directive 2024/825 ("ECGT", greenwashing) and Directive
2005/29/EC ("UCPD", unfair commercial practices). An embedding-based
retrieval step has already narrowed the full legal corpus down to a short
list of CANDIDATE passages for one ad. A MATCH requires BOTH of the
following to hold -- getting either one wrong causes a different, opposite
mistake, so check them separately:

(A) Is the ad making a CLAIM at all, of the kind a legal definition could
    even apply to? A claim is a specific, assertive statement that
    attributes a property, benefit, status, or impact to the product --
    e.g. "senza conservanti", "100% italiano", "meno plastica", "biologico",
    "certificato". It is NOT: recipe/serving suggestions, taste
    description, brand slogans, storage/conservation instructions,
    allergen warnings, shipping/purchase logistics, or addresses -- those
    never match any candidate, no matter how the wording is stretched.
    (Getting this wrong -- treating ordinary product description as a
    claim -- is what causes false positives.)

(B) IF the ad makes such a claim, does it fall under THIS candidate's
    specific subject matter (environmental performance vs. nutrition vs.
    origin vs. price vs. certification, etc.) -- regardless of whether the
    claim seems true, substantiated, or independently verifiable? Do NOT
    reject a real claim just because it sounds like typical vague
    advertising or you can't verify it -- judging truthfulness/substantiation
    is a separate, later step in this pipeline, not yours here. (Getting
    this wrong -- ALSO requiring the claim be proven true -- is what causes
    false negatives.)

ENVIRONMENTAL CLAIMS SPECIFICALLY -- how to recognize one:
An "asserzione ambientale" asserts or implies impact on nature, the
environment, biodiversity, emissions, waste, or resource use -- not merely
where something is from or how it was made. Trigger vocabulary includes:
"biologico"/"agricoltura biologica", "sostenibile"/"sostenibilità",
"rispettoso della natura/dell'ambiente", "biodiversità", "impatto
ambientale", "a basso impatto", "meno plastica", "riciclato"/"riciclabile",
"a impatto zero"/"carbon neutral", "emissioni".

Do NOT mistake these for origin or quality claims just because they appear
alongside origin/quality language in the same sentence. A sentence can make
BOTH kinds of claim at once -- evaluate the environmental-claim candidate
purely on whether the trigger vocabulary is present, independent of whatever
origin/quality language surrounds it.

By contrast, these are origin/quality/certification claims, NOT environmental
claims, even though they can sound adjacent: "100% italiano", "filiera
controllata"/"selezione delle aziende fornitrici", "DOP"/"DOC"/"IGP" (an
official EU-mandated scheme, not a voluntary sustainability label),
"artigianale", "ricetta tradizionale", "controlli rigorosi".

Worked examples (from prior review of this exact task):
- "È un formaggio... prodotto con attenzione verso le materie prime e
  l'impiego di un ciclo di produzione, rispettoso della natura e della sua
  biodiversità" -> MATCH on asserzione ambientale. "Rispettoso della natura
  e della biodiversità" is environmental-impact language, even though the
  same ad also separately claims "100% latte italiano" (origin, no match on
  its own).
- "Preparata... da allevamenti italiani", "Italiana al 100%", "un'accurata
  selezione delle aziende fornitrici e... rigorosi controlli sulla filiera"
  -> NO_MATCH on any environmental candidate. These are origin/traceability
  claims with no environmental trigger vocabulary present.
- "Prodotta in Grecia e certificata con la DOP" -> NO_MATCH on
  "sistema di certificazione", even though it uses the word "certificata".
  DOP is an official, legally mandatory EU scheme, not the kind of
  voluntary private certification scheme ECGT Art. 1 lett. r) defines --
  do not match official/mandatory schemes to this candidate.
- "Conad per l'ambiente Incarto - 7 - Raccolta Plastica", "Film interno -
  C/PAP 81 - Raccolta Carta", "Vaschetta - PET 1 - Raccolta Plastica" ->
  NO_MATCH on any environmental candidate, even though they contain
  "ambiente" and disposal language. This is a MANDATORY EU
  packaging-labeling disclosure (which bin to put the packaging in),
  present on nearly every ad regardless of whether the product makes any
  real environmental claim -- it is not a voluntary assertion about the
  product's environmental impact, just like DOP above. Do not match
  container-name + "Raccolta <material>" bin-sorting instructions to any
  environmental-claim candidate on their own.

Special case -- definitional/structural articles: some candidates (e.g.
UCPD Art. 2) merely DEFINE general legal terms like "consumer", "trader",
"product", or "commercial practice". These describe the law's scope, not a
claim type. Almost no ad should ever match one of these, because nearly
every ad trivially "concerns a product" or "is a commercial practice" --
that is true of every ad and is therefore never a meaningful match. Only
match one of these if the ad's text is unusually and specifically ABOUT
that defined concept itself (rare).

Rules:
- Several candidates may be superficially similar (e.g. neighboring
  sub-definitions of the same article, like "environmental claim" vs.
  "generic environmental claim" vs. "sustainability label"). Pick the one
  whose specific wording actually fits the ad's claim's subject matter, not
  just the closest by vague theme.
- Cite only wording that is ACTUALLY PRESENT in the ad's claim text above as
  evidence for a match. Never treat a candidate definition's own wording as
  if it were something the ad said.
- legal_chunk_id must be exactly one of the candidate ids listed, or "NONE"
  when verdict is NO_MATCH.
- rationale: one short sentence (max 20 words) quoting the specific ad
  wording that is both (A) a real claim and (B) on this candidate's topic.
- is_environmental_claim: answer (B) directly as its own true/false, separate
  from rationale. True ONLY if the ad wording you quoted asserts or implies
  environmental/nature/emissions/resource-use impact per the trigger
  vocabulary above. A real, assertive claim about origin, ingredients,
  nutrition, price, or an official certification scheme (DOP/IGP/DOC) is
  still a real claim -- answer false here anyway, since it is not an
  environmental one. Do not let "it's a genuine claim" talk you into true;
  that only answers (A)."""


def _build_user_prompt(title: str, claim_text: str, candidates: list[dict]) -> str:
    candidate_block = "\n\n".join(
        f"[{c['legal_chunk_id']}] {c['legal_title']}\n{c['legal_text']}"
        for c in candidates
    )
    return f"""AD: {title}

AD CLAIM-RELEVANT TEXT:
{claim_text}

CANDIDATE LEGAL PASSAGES:
{candidate_block}

Which candidate (if any) does this ad's claim genuinely match?"""


def _response_schema(candidate_ids: list[str]) -> dict:
    # Field order matters under grammar-constrained decoding: the model fills
    # properties in the order they're declared here, so "rationale" MUST come
    # first -- otherwise it commits to verdict/legal_chunk_id before it's
    # worked through the reasoning that's supposed to justify them. Seen
    # directly: with verdict/legal_chunk_id first, a real run's rationale
    # text correctly identified an environmental claim ("L'asserzione
    # ambientale e presente nel testo dell'ad") while verdict still said
    # NO_MATCH -- the reasoning came too late to change an answer already
    # generated.
    #
    # is_environmental_claim is a second forcing function, added after
    # measuring reranked_v8_8b: free-text "rationale" alone lets the model
    # answer only criterion (A) ("senza conservanti attribuisce una
    # proprieta al prodotto" -- yes, it's A claim) and skip criterion (B)
    # (is it specifically an ENVIRONMENTAL claim) before jumping to
    # verdict=MATCH. Every false positive in that run's rationale stopped at
    # (A) and never mentioned the environmental angle at all. A dedicated
    # boolean between rationale and verdict makes (B) something the model
    # must commit to, not something free text can silently skip -- and
    # main() below backstops it deterministically in case the model still
    # answers false here but MATCH below anyway.
    return {
        "type": "object",
        "properties": {
            "rationale": {"type": "string"},
            "is_environmental_claim": {"type": "boolean"},
            "verdict": {"type": "string", "enum": ["MATCH", "NO_MATCH"]},
            "legal_chunk_id": {"type": "string", "enum": candidate_ids + ["NONE"]},
        },
        "required": ["rationale", "is_environmental_claim", "verdict", "legal_chunk_id"],
    }


def rerank_ad(title: str, claim_text: str, candidates: list[dict], model: str) -> dict:
    candidate_ids = [c["legal_chunk_id"] for c in candidates]
    response = httpx.post(
        OLLAMA_URL,
        json={
            "model": model,
            "system": SYSTEM_PROMPT,
            "prompt": _build_user_prompt(title, claim_text, candidates),
            "stream": False,
            "format": _response_schema(candidate_ids),
            "options": {
                "temperature": 0,   # greedy -- same reasoning as extraction.py: this is a
                                    # judgment call, not free text, run-to-run drift is noise
                "num_predict": 600,  # was 250 -- fine when verdict/legal_chunk_id came first,
                                     # but the schema now generates "rationale" FIRST (see
                                     # _response_schema), and a verbose rationale (seen: a
                                     # real 4-sentence, multi-paragraph response) can burn
                                     # through a small budget before the model ever reaches
                                     # the verdict/legal_chunk_id fields, truncating the JSON
                                     # entirely. 600 leaves real headroom above that.
                "num_ctx": 12000,    # was 4096 for a top-3 candidate set. Widened to give
                                     # the reranker the FULL legal corpus as candidates
                                     # (--top-k 56 on compare_e5.py), since retrieval was
                                     # never surfacing the gold chunk in top-3/top-15 for
                                     # any of the 8 known positives -- measured worst case:
                                     # 56 candidates ~7900 tok + a verbose ad's claim text
                                     # ~750 tok + system prompt ~500 tok + response 250 tok
                                     # = ~9400 tok; 12000 leaves real margin above that.
            },
        },
        timeout=600,  # same rationale as extraction.py: local Ollama on CPU/small-GPU
                      # hardware, better to wait than to lose a completed result
    )
    response.raise_for_status()
    return json.loads(response.json()["response"])


def _apply_environmental_backstop(verdict: dict) -> dict:
    """Deterministic backstop for is_environmental_claim=false + verdict=MATCH,
    the exact combination reranked_v8_8b showed the model reaching for on
    "senza conservanti"/origin-only ad text: it answers criterion (A) --
    yes this is a real claim -- and lets that alone carry it to MATCH
    without the environmental angle ever being true. Same "soft prompt
    instruction still needs a hard backstop" pattern as src/extraction.py's
    _validate_claims dropping risk_level=LOW rows."""
    if verdict.get("verdict") == "MATCH" and verdict.get("is_environmental_claim") is False:
        return {
            **verdict,
            "verdict": "NO_MATCH",
            "legal_chunk_id": "NONE",
            "rationale": f"[backstop: is_environmental_claim=false overrode MATCH] {verdict.get('rationale', '')}",
        }
    return verdict


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--matches", type=Path, default=SCRIPT_DIR / "embeddings" / "matches.json")
    parser.add_argument("--out", type=Path, default=SCRIPT_DIR / "embeddings" / "reranked.json")
    parser.add_argument("--model", default="llama3.2")
    args = parser.parse_args()

    with open(args.matches, "r", encoding="utf-8") as f:
        matches = json.load(f)

    def _save(results):
        # Overwrite --out after every ad, not just at the end, so a kill/crash
        # mid-run (this has happened twice: an orphaned concurrent run, and
        # Ollama itself crashing under an 8B + wide-context load) still leaves
        # everything processed so far on disk instead of losing the whole batch.
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    results = []
    for i, ad in enumerate(matches, 1):
        candidates = ad.get("top_matches") or []
        title = ad["query_title"]
        claim_text = " ".join(ad.get("query_sentences") or [])

        if not candidates or not claim_text.strip():
            results.append({
                **ad,
                "rerank": {"verdict": "NO_MATCH", "legal_chunk_id": "NONE", "rationale": "no retrieval candidates"},
            })
            print(f"[{i}/{len(matches)}] {title}: skipped (no candidates)")
            _save(results)
            continue

        try:
            verdict = rerank_ad(title, claim_text, candidates, args.model)
            verdict = _apply_environmental_backstop(verdict)
        except Exception as e:
            print(f"[{i}/{len(matches)}] {title}: FAILED ({e})")
            results.append({**ad, "rerank": {"verdict": "ERROR", "legal_chunk_id": None, "rationale": str(e)}})
            _save(results)
            continue

        results.append({**ad, "rerank": verdict})
        print(f"[{i}/{len(matches)}] {title}: {verdict['verdict']} -> {verdict['legal_chunk_id']}")
        _save(results)

    print(f"\nSaved {len(results)} reranked results -> {args.out}")


if __name__ == "__main__":
    main()
