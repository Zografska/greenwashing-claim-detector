"""
Pulls claim spans out of product descriptions that may be unfair under the
EU Unfair Commercial Practices Directive (Directive 2005/29/EC, "UCPD").
Adapted from the notebook extraction pipeline.

Note: this version narrows focus to UCPD scope -- misleading actions (Art. 6),
misleading omissions (Art. 7), and blacklisted practices (Annex I) -- covering
nutrition/health, origin, composition, and value claims. This is broader than
the ECGT/greenwashing-only version this file used previously: environmental
claims are still in scope here (UCPD covers them too), but so is everything
else UCPD covers that ECGT doesn't (nutrition, health, origin, price/value).
"""

import json
import time
from pathlib import Path
import re

import httpx

from .data import load_descriptions, iter_records


OLLAMA_URL = "http://localhost:11434/api/generate"

# --- JSON Schema for Ollama's grammar-constrained decoding ---------------
# Categories below are UCPD's actual legal hooks, not ECGT's vocabulary --
# "offset_based_neutrality" and "fake_or_unverified_label" are ECGT-specific
# concepts (about *environmental* claim substantiation) that don't have a
# direct UCPD equivalent, so they're replaced rather than relabeled.
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_text": {"type": "string"},
                    "category": {
                        "type": "string",
                        "enum": [
                            "NUTRITION_HEALTH_CLAIM",
                            "ORIGIN_PROVENANCE_CLAIM",
                            "COMPOSITION_CLAIM",
                            "PRICE_VALUE_CLAIM",
                            "ENVIRONMENTAL_CLAIM",
                            "SAFETY_INSTRUCTION_CLAIM",
                        ],
                    },
                    "ucpd_category": {
                        "type": "string",
                        "enum": [
                            "misleading_action",
                            "misleading_omission",
                            "blacklisted_practice",
                            "aggressive_practice",
                            "none",
                        ],
                    },
                    "risk_level": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                    "risk_rationale": {"type": "string"},
                },
                "required": [
                    "claim_text",
                    "category",
                    "ucpd_category",
                    "risk_level",
                    "risk_rationale",
                ],
            },
        }
    },
    "required": ["claims"],
}

# Kept as a plain dict too, in case other code in this package imports SCHEMA
# directly for docs/tests. Not used in the prompt anymore.
SCHEMA = {
    "claims": [
        {
            "claim_text": "exact text as found in description",
            "category": "NUTRITION_HEALTH_CLAIM | ORIGIN_PROVENANCE_CLAIM | COMPOSITION_CLAIM | PRICE_VALUE_CLAIM | ENVIRONMENTAL_CLAIM | SAFETY_INSTRUCTION_CLAIM",
            "ucpd_category": "misleading_action | misleading_omission | blacklisted_practice | aggressive_practice | none",
            "risk_level": "HIGH | MEDIUM | LOW",
            "risk_rationale": "specific reason this risk level applies",
        }
    ]
}

# --- System prompt: UCPD scope -------------------------------------------
# Category/risk definitions spelled out for the model. Same verbatim-copy
# and scope rules as before, carried over since they fixed real bugs
# (mistranslation, multi-line concatenation) unrelated to which directive
# is being applied.
SYSTEM_PROMPT = """You are an EU consumer law analyst (UCPD, Dir. 2005/29/EC). Extract
unfair claims from this Italian product description.

ucpd_category:
- misleading_action: a false or unverifiable factual claim about composition,
  origin, or health/nutrition, stated as if proven (Art. 6).
- misleading_omission: hides info the consumer needs, or downplays/contradicts
  an official safety or storage instruction (Art. 7).
- blacklisted_practice: claims a certification, status, or health benefit the
  product does not actually have evidence for (Annex I).
- aggressive_practice: specifically recommends the product to, or targets,
  a vulnerable group (children, elderly, pregnant, immunocompromised) in a
  way connected to a real risk for that group -- not just any mention of them.
- none: not a legal claim at all (recipe tips, taste description, brand slogans).

category: NUTRITION_HEALTH_CLAIM | ORIGIN_PROVENANCE_CLAIM | COMPOSITION_CLAIM
| PRICE_VALUE_CLAIM | ENVIRONMENTAL_CLAIM | SAFETY_INSTRUCTION_CLAIM

risk_level: HIGH = directly contradicted by, or unverifiable against, the
product's own stated facts. MEDIUM = plausible but no evidence given either
way. LOW = factual, or backed by a real EU certification -- skip these,
do not output them at all.

EXAMPLE (for format only, not content to copy):
claim_text: "è tra i pochi formaggi magri"
category: NUTRITION_HEALTH_CLAIM | ucpd_category: misleading_action | risk_level: HIGH
risk_rationale: "Calls a high-fat cheese low-fat; contradicts its own nutrition values."

Rules:
- claim_text: copy exactly from the input. Never translate or paraphrase it.
- risk_rationale: your own short, specific reason for THIS claim (max 15
  words). Never repeat these category definitions or instructions back as
  the rationale.
- Only use aggressive_practice if the text actually connects the product to
  a vulnerable group's risk -- not for unrelated convenience claims like
  pre-sliced packaging.
- Skip recipes, serving suggestions, taste description, brand slogans.
- No claims found -> empty array. Never invent a claim not in the text."""

# --- Pre-filter: cut description down to claim-adjacent fragments before --
# it ever reaches the model. On local Ollama, prefill time scales with
# input tokens, so this is the main latency lever for long product
# descriptions that are mostly recipe filler. Falls back to the full
# description if no keyword hits, so it never silently zeroes out a record.
#
# Widened from the ECGT version, which only matched environmental terms
# (ambiente, riciclat, plastica...). Left as-is, that filter would have
# silently stripped out nutrition/origin/composition sentences -- exactly
# the claim types UCPD scope is now meant to catch -- before the model ever
# saw them. Now also matches nutrition/health, origin, composition, and
# price/value language.
CLAIM_KEYWORDS = re.compile(
    r"(ambiente|sostenib|riciclat|riciclabil|plastica|carta|imballaggi|imballagg|"
    r"biodegrad|compostabil|biologic|naturale|natura|co2|carbon|climate|neutral|"
    r"eco[- ]?friendly|green|impatto|filiera|certificat|km zero|territorio|"
    r"raccolta|verde|rispett|"
    # nutrition / health
    r"calori|grass|magr|light|leggero|proteic|vitamin|calcio|fosforo|"
    r"saziant|nutrit|dieta|sportiv|forma fisica|salute|benefici|ricc[ao] (?:di|in)|"
    r"fonte di|"
    # origin / provenance
    r"italian|origine|provenien|dop\b|igp\b|denominazione|allevat|pascol|"
    r"montagna|territorio|"
    # composition
    r"100%|ingredient|latte (?:crudo|fresco)|non pastorizzat|edibile|commestibil|"
    # price / value
    r"qualità.{0,15}prezzo|conveni|risparm|economic|"
    # safety/storage instructions worth flagging as trivialized
    r"consumare entro|conservare|superflu)",
    re.IGNORECASE,
)
# Old name kept as an alias in case other code in this package still imports
# GREEN_KEYWORDS directly.
GREEN_KEYWORDS = CLAIM_KEYWORDS

# Scrape artifact: packaging/disposal badges (e.g. "Vaschetta e Film - 7 -
# Raccolta Plastica") are separate UI elements on the source page with no
# delimiting punctuation from whatever text precedes them, so a short claim
# right before one (e.g. "Meno plastica") ends up fused into the same
# fragment as the badge instead of splitting into two. Matched by its
# container word (Vaschetta/Incarto/Film/Confezione/Flowpack) followed
# shortly by "Raccolta" -- inserting a split boundary right before it
# separates the badge from whatever precedes it without needing a
# general-purpose sentence segmenter.
_PACKAGING_BADGE_BOUNDARY = r"(?=\b(?:Vaschetta|Incarto|Film|Confezione|Flowpack)\b[^.\n]{0,30}?Raccolta\b)"

# Same scrape-artifact problem on the OTHER side of a packaging badge: the
# structured product-spec sheet that follows it (Denominazione di vendita /
# Marchio / Conservazione / Paese di origine / Produttori / Ingredienti e
# valori nutrizionali / Allergeni / Tracciabilita) has no punctuation
# separating its own fields either, so without a closing boundary the badge
# fuses into one giant fragment with the entire rest of the spec sheet --
# e.g. "Vaschetta - Plastica - Raccolta Plastica  Segui sempre le regole del
# tuo comune ... Denominazione di vendita ... Ingredienti e valori
# nutrizionali ... Allergeni ...". That fragment matches CLAIM_KEYWORDS on
# "raccolta"/"plastica" and gets handed to the environmental-claim reranker
# as if it were one claim, when in reality it's a disposal badge glued to
# ~200 words of unrelated mandatory label text -- this was the single
# biggest driver of the false-positive rate measured in reranked_v6_8b_top20
# (Crescenza/Stracchino/Asiago/Emmental/Maasdam ads all failed this way).
# Inserting a boundary before each of these field labels isolates them same
# as the badge boundary above, so nutrition-table numbers (needed elsewhere,
# e.g. to catch "e tra i pochi formaggi magri" contradicting a high-fat
# value) stay intact as their own fragment instead of diluting a "claim".
_LABEL_BOUNDARY = (
    r"(?=\b(?:Denominazione di vendita|Marchio|Conservazione:|Paese di origine|"
    r"Produttori\b|Confezionato per|Prodotto per|Ingredienti e valori nutrizionali|"
    r"Valori nutrizionali|Allergeni|Additivi|Tracciabilità|"
    r"Segui sempre|Verifica (?:le|sempre))\b)"
)

# Mandatory disclosures that superficially match CLAIM_KEYWORDS (they contain
# words like "ambiente"/"raccolta"/"plastica") but are never a voluntary claim
# about the product -- they're required-by-law labeling text present on
# nearly every ad regardless of what the product actually asserts. Dropped
# outright rather than left for the LLM to reject each time: rerank_matches.py's
# own system prompt already carries worked counter-examples for exactly these
# (packaging bin-sorting codes, DOP/IGP as an official scheme) and the smaller
# local models still matched on them whenever they leaked into candidate text.
_MANDATORY_DISCLOSURE_PATTERNS = [
    re.compile(r"^Conad per l'ambiente\s*$", re.IGNORECASE),
    re.compile(
        r"^(?:Vaschetta|Incarto|Film|Confezione|Flowpack)\b[^.\n]{0,40}?Raccolta\s+\w+\s*$",
        re.IGNORECASE,
    ),
    re.compile(r"^(?:Segui|Verifica)\b.{0,80}?(?:regole del tuo comune|disposizioni del tuo comune)", re.IGNORECASE),
]


def _is_mandatory_disclosure(fragment: str) -> bool:
    return any(p.search(fragment) for p in _MANDATORY_DISCLOSURE_PATTERNS)


def _split_claim_sentences(description: str) -> list[str]:
    """Split into sentence-ish fragments and keep only the ones mentioning
    claim-adjacent terms (nutrition, origin, composition, price/value,
    environmental, safety instructions -- the full UCPD scope, not just
    environmental claims). Building block behind _prefilter_description;
    exposed separately for callers that want the individual sentences
    rather than one joined string (e.g. src/knowledge/prepare_ads_chunks.py,
    which embeds each claim-adjacent sentence as its own chunk instead of
    concatenating them -- concatenation dilutes a short embedding vector
    with whatever unrelated sentences also happened to match a keyword).

    Fragments that are purely a mandatory disclosure (packaging bin-sorting
    badge, the "Conad per l'ambiente" section header, the boilerplate
    "verifica le regole del tuo comune" sentence) are dropped even though
    they match CLAIM_KEYWORDS -- see _MANDATORY_DISCLOSURE_PATTERNS."""
    if not description:
        return []
    fragments = re.split(
        r"(?<=[.!?])\s+|\n+|" + _PACKAGING_BADGE_BOUNDARY + "|" + _LABEL_BOUNDARY, description
    )
    return [
        f.strip()
        for f in fragments
        if f.strip() and CLAIM_KEYWORDS.search(f) and not _is_mandatory_disclosure(f.strip())
    ]


def _prefilter_description(description: str) -> str:
    """Keep only sentence-ish fragments mentioning claim-adjacent terms.
    Returns the full original description if nothing matches, so a gap in
    the keyword list degrades to "no speedup" rather than "missed claim"."""
    hits = _split_claim_sentences(description)
    return " ".join(hits) if hits else (description or "")


def _build_user_prompt(product: dict, description: str) -> str:
    filtered = _prefilter_description(description)
    return f"""Analyze the following Italian food product and extract all claims that
may be unfair under the EU Unfair Commercial Practices Directive (UCPD).

PRODUCT NAME: {product.get("name", "N/A")}
MARKETING BADGE: {product.get("marketing_badge", "none")}

PRODUCT DESCRIPTION (pre-filtered for claim-relevant content):
{filtered or "No description available"}

Extract claims across all in-scope categories: nutrition/health, origin,
composition, price/value, environmental, and safety-instruction claims."""


def _repair_misplaced_commas(raw: str) -> str:
    """Fix a specific grammar-decoding glitch seen with Ollama's JSON-Schema
    constrained output: a comma sometimes lands on its own line *before* the
    next key instead of right after the previous value, e.g.:

        "risk_level": "HIGH"
        ,
        "risk_rationale": "..."

    instead of the valid:

        "risk_level": "HIGH",
        "risk_rationale": "..."

    This is a mechanical, low-risk fix: it only moves a comma that's already
    present to the position immediately after the preceding value, it never
    inserts or removes content. Left for json.loads to validate afterward --
    if the result still doesn't parse, the repair didn't apply cleanly and
    the caller falls through to the original error as before.
    """
    # comma alone on a line (with only whitespace) -> move it to glue onto
    # the end of the previous non-whitespace character
    return re.sub(r'(["\d\}\]])\s*\n\s*,\s*\n', r'\1,\n', raw)


USE_SCHEMA_GRAMMAR = True  # flip to False to A/B test speed: grammar-
                           # constrained decoding (the JSON Schema passed to
                           # `format`) is what fixed the enum-leak bug from
                           # earlier (model echoing "A | B | C" back as a
                           # literal value), but constrained decoding has a
                           # real, well-documented generation-speed cost --
                           # often 2-5x slower per token, scaling with how
                           # branchy the grammar is. A 6-way x 5-way x 3-way
                           # nested enum schema is non-trivial as grammars go.
                           # Given the 94.7s/~1000-token result (~10 tok/s,
                           # slow for a 3B model on 100% GPU), this is the
                           # most likely cause of the slowdown, more so than
                           # prompt length at this point. Set this to False
                           # to fall back to loose "format": "json" mode and
                           # see if speed recovers -- if it does, you're
                           # trading the enum-leak protection for speed, and
                           # that's a real decision to make deliberately
                           # rather than something to default silently.


def extract_claims(product: dict, description: str, model: str = "llama3.2") -> dict:
    """
    Extract greenwashing-relevant claims from a product description.

    Args:
        product: full product record (for name, brand, badge fields)
        description: the description string to analyze
        model: ollama model name

    Returns:
        dict with a "claims" list, each entry matching SCHEMA
    """
    response = httpx.post(
        OLLAMA_URL,
        json={
            "model": model,
            "system": SYSTEM_PROMPT,
            "prompt": _build_user_prompt(product, description),
            "stream": False,
            "format": RESPONSE_SCHEMA if USE_SCHEMA_GRAMMAR else "json",
            "options": {
                "temperature": 0,     # was 0.1 — fully greedy to remove the
                                       # run-to-run claim-count drift seen
                                       # earlier (4 vs 5, 2 vs 4 claims etc.)
                "num_predict": 1750,   # was 1100, which truncated on a 3.1:8b
                                       # run at the SAME record/claim as the
                                       # 3.2:3b model did -- a strong signal
                                       # this was a config ceiling, not a
                                       # model-capability problem (a 3x larger
                                       # model hit the identical wall). Root
                                       # cause: 1100 was sized using a SHORT
                                       # worked-example claim_text (~67
                                       # tok/claim), but this dataset's actual
                                       # marketing copy runs long, run-on
                                       # sentences -- e.g. record 1's claim_text
                                       # alone is 179 chars. Measured against
                                       # a real long claim_text + a full
                                       # 15-word rationale: ~120 tok/claim.
                                       # Record 0 already produced 10 claims
                                       # successfully; sizing to 14 claims at
                                       # the worst-case per-claim cost
                                       # (14 * 120 + 30 wrapper overhead =
                                       # ~1700) gives real margin above the
                                       # observed max, not just matching it.
                "num_ctx": 3200,        # was 2560. Must cover system prompt
                                        # (~600 tok) + schema (~200) + user
                                        # overhead (~60) + num_predict (1750)
                                        # = ~2610, leaving ~590 tokens for the
                                        # pre-filtered description text itself
                                        # -- verified headroom, not a guess.
            },
        },
        timeout=600,  # was 200. The real problem causing timeouts was call
                      # cost (prompt size + num_ctx + per-claim rationale
                      # length), now cut above. This is raised as a safety
                      # margin so a still-slow call on llama3.2 (a small,
                      # CPU-friendly but not fast model) completes and gets
                      # recorded as a real result instead of being killed by
                      # the client and lost. If runs are still timing out at
                      # 600s after the cuts above, that's a sign llama3.2
                      # itself is too slow for this workload on your hardware,
                      # not a config problem -- worth trying a smaller/faster
                      # model name or quant at that point.
    )
    response.raise_for_status()
    raw = response.json()["response"]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try repairing the misplaced-comma glitch before giving up on the raw text.
    try:
        return json.loads(_repair_misplaced_commas(raw))
    except json.JSONDecodeError:
        pass

    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            try:
                return json.loads(_repair_misplaced_commas(match.group()))
            except json.JSONDecodeError:
                pass

    # If we get here, the JSON is genuinely broken (the comma-repair attempt
    # above handles one specific cosmetic glitch, but most real-world
    # failures at this point are length-related): num_predict ran out before
    # the model finished the object, leaving a dangling string or no closing
    # brace at all.
    looks_truncated = not raw.rstrip().endswith("}")
    hint = (
        " (output does not end with a closing brace — truncated by "
        "num_predict; raise it further, e.g. to 2000-2500, especially for "
        "records likely to produce many claims)"
        if looks_truncated else
        " (has a closing brace but still won't parse — inspect the Raw text "
        "below for the actual syntax break, since this isn't the truncation "
        "case)"
    )
    raise ValueError(f"Model returned invalid JSON{hint}\n\nRaw: {raw[:500]}")


def _validate_claims(claims: list[dict]) -> tuple[list[dict], list[dict]]:
    """Drop rows with an empty claim_text (seen in a prior run: a placeholder
    row with "" and no real content), and drop LOW-risk claims.

    Deliberately NOT checking claim_text against the source description
    anymore. An earlier version did, which caught real model corruption
    (e.g. "Meno plastica" mangled into "Menoplasica"/"Menore plastica", or
    the model inserting a word that wasn't in the source) -- but it also
    false-rejected a larger number of valid claims over cosmetic
    whitespace/capitalization differences, even after normalizing for those.
    Trade-off accepted: corrupted claim_text will now pass through into
    `claims` unflagged. If that starts showing up in practice, the fix is
    to reintroduce a verbatim check (see git history / _normalize_for_match)
    rather than trying to patch around it here.

    The LOW-risk drop is a deterministic backstop for the "OUTPUT FILTER"
    instruction in SYSTEM_PROMPT, which tells the model not to emit LOW-risk
    claims at all. That instruction should cut most of the generation cost
    (fewer claims -> fewer tokens -> faster runs), but it's a soft constraint:
    the schema still allows risk_level="LOW" as a valid enum value, and local
    models are inconsistent about honoring negative instructions like "don't
    output X" under grammar-constrained decoding. This filter guarantees no
    LOW-risk claim reaches `claims` regardless of whether the model actually
    skipped generating it or generated it anyway.

    Returns (valid, dropped) so both kinds of drops are still visible in the
    output instead of silently vanishing.
    """
    valid, dropped = [], []
    for c in claims:
        text = (c.get("claim_text") or "").strip()
        if not text:
            dropped.append({**c, "_dropped_reason": "empty claim_text"})
            continue
        if (c.get("risk_level") or "").upper() == "LOW":
            dropped.append({**c, "_dropped_reason": "risk_level=LOW (filtered by policy)"})
            continue
        valid.append(c)
    return valid, dropped


def extract_from_file(filename: str, model: str = "llama3.2") -> tuple[list[dict], list[dict]]:
    records = list(iter_records(filename))
    total = len(records)
    results = []
    failed = []
    total_dropped = 0
    run_start = time.monotonic()

    for i, (idx, record) in enumerate(records, 1):
        name = record.get("name", f"record {idx}")
        print(f"[{i}/{total}] {name}", end=" ... ", flush=True)

        call_start = time.monotonic()
        try:
            description = record["description"]
            result = extract_claims(
                product=record,
                description=description,
                model=model,
            )
            elapsed = time.monotonic() - call_start

            claims, dropped = _validate_claims(result.get("claims", []))
            total_dropped += len(dropped)
            results.append({
                "index": idx,
                "ean": record.get("ean"),
                "name": record.get("name"),
                "claims": claims,
                "dropped_claims": dropped,  # empty list in the common case;
                                            # kept on every record (not just
                                            # ones with drops) so the schema
                                            # is consistent across the file
                "elapsed_seconds": round(elapsed, 2),  # wall-clock time for
                                                        # the model call only
                                                        # (excludes validation,
                                                        # which is negligible)
            })
            suffix = f" ({len(dropped)} dropped)" if dropped else ""
            print(f"{len(claims)} claims found{suffix} [{elapsed:.1f}s]")

        except Exception as e:
            elapsed = time.monotonic() - call_start
            print(f"FAILED after {elapsed:.1f}s: {e}")
            failed.append({"index": idx, "ean": record.get("ean"), "name": name, "error": str(e)})
            time.sleep(2)
            continue

    total_elapsed = time.monotonic() - run_start
    avg_per_record = total_elapsed / total if total else 0
    print(
        f"\nDone: {len(results)} ok, {len(failed)} failed, {total_dropped} claims "
        f"dropped by validation"
    )
    print(
        f"Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min), "
        f"avg {avg_per_record:.1f}s/record"
    )
    if failed:
        print("Failed records:")
        for f in failed:
            print(f"  [{f['index']}] {f['name']} — {f['error']}")

    return results, failed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="filename in data/raw/, e.g. 06.25.json")
    parser.add_argument("--model", default="llama3.2")
    parser.add_argument("--out", default=None, help="optional output path for results json")
    args = parser.parse_args()

    results, failed = extract_from_file(args.file, model=args.model)

    print(f"\nProcessed {len(results)} products")
    total_claims = sum(len(r["claims"]) for r in results)
    print(f"Total claims extracted: {total_claims}")
    print(f"Failed records: {len(failed)}")

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
        print(f"Saved to {args.out}")

        if failed:
            fail_path = out_path.parent / "failed.json"
            fail_path.parent.mkdir(parents=True, exist_ok=True)
            fail_path.write_text(json.dumps(failed, indent=2, ensure_ascii=False))
            print(f"Failed records saved to {fail_path}")
    else:
        print(json.dumps(results[:2], indent=2, ensure_ascii=False))