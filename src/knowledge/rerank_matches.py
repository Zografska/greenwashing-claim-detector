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
list of CANDIDATE passages for one ad. Your job: read the ad's claim text
and the candidates' actual wording, then judge which ONE candidate (if any)
the ad's claim genuinely matches.

Rules:
- Several candidates may be superficially similar (e.g. neighboring
  sub-definitions of the same article, like "environmental claim" vs.
  "generic environmental claim" vs. "sustainability label"). Pick the one
  whose specific wording actually fits the ad's claim, not just the closest
  by vague theme.
- If the ad's claim-relevant text doesn't genuinely match any candidate --
  including cases where it's only DOP/IGP certification, taste/recipe
  description, or plain nutrition facts with no unsubstantiated claim --
  answer NO_MATCH.
- legal_chunk_id must be exactly one of the candidate ids listed, or "NONE"
  when verdict is NO_MATCH.
- rationale: one short sentence (max 20 words) citing the specific wording
  that justifies your answer."""


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
    return {
        "type": "object",
        "properties": {
            "verdict": {"type": "string", "enum": ["MATCH", "NO_MATCH"]},
            "legal_chunk_id": {"type": "string", "enum": candidate_ids + ["NONE"]},
            "rationale": {"type": "string"},
        },
        "required": ["verdict", "legal_chunk_id", "rationale"],
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
                "num_predict": 250,  # response is 3 short fields (enum + enum + one
                                     # sentence rationale); 250 leaves comfortable margin
                "num_ctx": 4096,     # candidates can include a long article (e.g. UCPD_Art7,
                                     # ~700 tok) plus a verbose ad's full prefiltered text
                                     # (~750 tok observed) plus the system prompt (~300 tok)
                                     # -- 4096 covers the worst case seen with real data.
            },
        },
        timeout=600,  # same rationale as extraction.py: local Ollama on CPU/small-GPU
                      # hardware, better to wait than to lose a completed result
    )
    response.raise_for_status()
    return json.loads(response.json()["response"])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--matches", type=Path, default=SCRIPT_DIR / "embeddings" / "matches.json")
    parser.add_argument("--out", type=Path, default=SCRIPT_DIR / "embeddings" / "reranked.json")
    parser.add_argument("--model", default="llama3.2")
    args = parser.parse_args()

    with open(args.matches, "r", encoding="utf-8") as f:
        matches = json.load(f)

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
            continue

        try:
            verdict = rerank_ad(title, claim_text, candidates, args.model)
        except Exception as e:
            print(f"[{i}/{len(matches)}] {title}: FAILED ({e})")
            results.append({**ad, "rerank": {"verdict": "ERROR", "legal_chunk_id": None, "rationale": str(e)}})
            continue

        results.append({**ad, "rerank": verdict})
        print(f"[{i}/{len(matches)}] {title}: {verdict['verdict']} -> {verdict['legal_chunk_id']}")

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(results)} reranked results -> {args.out}")


if __name__ == "__main__":
    main()
