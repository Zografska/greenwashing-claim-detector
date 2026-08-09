"""
Measures how many gold claims survive src/extraction.py's keyword prefilter
(_prefilter_description) before a description ever reaches the model. Any
gold claim that doesn't survive is structurally unreachable regardless of
model or prompt -- this is a repeatable check for CLAIM_KEYWORDS gaps,
meant to be re-run every time CLAIM_KEYWORDS changes.

Usage:
    python3 -m src.check_prefilter_coverage \\
        --gold golden/samples/canonical/sample_coop.json \\
        --extraction-input data/raw/sample_coop_extraction_input.json
"""

import argparse
import json
import re
from typing import Set

from .extraction import _prefilter_description

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _tokens(text: str) -> Set[str]:
    return set(_TOKEN_RE.findall((text or "").lower()))


def survives(claim_text: str, prefiltered: str, threshold: float = 0.6) -> bool:
    """A claim survives if most of its own tokens are still present in the
    prefiltered (kept) text -- lenient token-overlap, not exact substring,
    since the prefilter joins fragments with whitespace that may not match
    the claim's original spacing/punctuation exactly."""
    claim_tokens = _tokens(claim_text)
    if not claim_tokens:
        return True
    kept_tokens = _tokens(prefiltered)
    overlap = len(claim_tokens & kept_tokens) / len(claim_tokens)
    return overlap >= threshold


def check(gold_path: str, extraction_input_path: str, threshold: float = 0.6):
    with open(gold_path, encoding="utf-8") as f:
        gold = json.load(f)
    with open(extraction_input_path, encoding="utf-8") as f:
        ext = json.load(f)
    ext_by_ean = {r.get("ean"): r for r in ext if r.get("ean")}

    total = 0
    survived = 0
    misses = []

    for record in gold:
        claims = record.get("extracted_claims") or []
        if not claims:
            continue
        ext_record = ext_by_ean.get(record.get("ean"))
        description = (ext_record or {}).get("description", "")
        prefiltered = _prefilter_description(description)

        for claim in claims:
            text = claim.get("claim_text", "")
            total += 1
            if survives(text, prefiltered, threshold):
                survived += 1
            else:
                # Distinguish a real prefilter bug (claim is in the raw
                # description but CLAIM_KEYWORDS/_split_claim_sentences
                # drops it) from a pre-existing data gap (claim's source
                # field was never joined into `description` at all, e.g.
                # recycling_other -- see CLAUDE.md's adapters notes).
                cause = "prefilter" if survives(text, description, threshold) else "data-gap"
                misses.append(
                    {
                        "product": record.get("name"),
                        "ean": record.get("ean"),
                        "claim_text": text,
                        "category": claim.get("category"),
                        "cause": cause,
                    }
                )

    return total, survived, misses


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True)
    parser.add_argument("--extraction-input", required=True)
    parser.add_argument("--threshold", type=float, default=0.6)
    args = parser.parse_args()

    total, survived, misses = check(args.gold, args.extraction_input, args.threshold)
    rate = survived / total if total else 0.0
    prefilter_caused = [m for m in misses if m["cause"] == "prefilter"]
    data_gap = [m for m in misses if m["cause"] == "data-gap"]
    print(f"Survival rate: {survived}/{total} ({rate:.1%})")
    print(
        f"\n{len(misses)} non-surviving claims "
        f"({len(prefilter_caused)} prefilter-caused, {len(data_gap)} pre-existing data gap):"
    )
    for m in misses:
        print(f"- [{m['cause']}][{m['category']}] {m['product']} ({m['ean']}): {m['claim_text']!r}")
