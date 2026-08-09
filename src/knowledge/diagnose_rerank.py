#!/usr/bin/env python3
"""
Splits a compare_retrieval_vs_rerank.py run's ad-level accuracy into the
numbers that single aggregate hides.

score_rerank (evaluate_claim_matches.py) credits an ad as "correct" whenever
rerank says NO_MATCH and the ad truly has no gold claim -- so on a golden set
that's ~30-40% true negatives, an aggregate ad-level accuracy can look
respectable even if the model never once finds the right article for an ad
that actually has a claim. This script reports that split directly:

  - true-positive ads: ad has a real gold claim -- did rerank pick the
    right legal_chunk_id?
  - true-negative ads: ad has no gold claim -- did rerank correctly say
    NO_MATCH?

It also splits true-positive ads by whether their gold chunk is ECGT
(environmental) vs. UCPD (everything else), because rerank_matches.py's
SYSTEM_PROMPT is currently scoped to ECGT environmental claims only, and
_apply_environmental_backstop deterministically forces NO_MATCH whenever the
model decides a claim isn't environmental -- regardless of whether the
correct chunk was in the candidate pool. On a full-UCPD-scope golden set,
a near-zero true-positive rate is expected to be a prompt-scope artifact,
not necessarily a model-capability one; this split is how to tell the two
apart before concluding a bigger model would help.

Usage:
  python diagnose_rerank.py --retailer coop
  python diagnose_rerank.py --retailer coop \\
      --gold ../../golden/canonical/coop.json \\
      --rerank-jsonl embeddings/coop_rerank_progress.jsonl
"""

import argparse
import json
from pathlib import Path
from typing import Set

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent


def _gold_chunk_ids_by_ean(gold_path: Path) -> dict:
    with open(gold_path, encoding="utf-8") as f:
        gold_records = json.load(f)
    gold_by_ean = {}
    for rec in gold_records:
        ids: Set[str] = set()
        for claim in rec.get("extracted_claims", []):
            chunk_id = claim.get("gold_legal_chunk_id")
            if claim.get("risk_level") != "LOW" and chunk_id is not None:
                ids.add(chunk_id)
        gold_by_ean[rec.get("ean")] = ids
    return gold_by_ean


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--retailer", required=True)
    parser.add_argument("--gold", type=Path, default=None, help="default: golden/canonical/<retailer>.json")
    parser.add_argument(
        "--rerank-jsonl", type=Path, default=None,
        help="default: ./embeddings/<retailer>_rerank_progress.jsonl (compare_retrieval_vs_rerank.py's --rerank-out)",
    )
    args = parser.parse_args()

    gold_path = args.gold or (PROJECT_ROOT / "golden" / "canonical" / f"{args.retailer}.json")
    rerank_path = args.rerank_jsonl or (SCRIPT_DIR / "embeddings" / f"{args.retailer}_rerank_progress.jsonl")

    gold_by_ean = _gold_chunk_ids_by_ean(gold_path)

    pos_total = pos_correct = 0
    neg_total = neg_correct = 0
    env_total = env_correct = 0
    other_total = other_correct = 0

    with open(rerank_path, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            gold_ids = gold_by_ean.get(rec["query_ad_id"], set())
            rerank = rec["rerank"]
            hit = rerank.get("verdict") == "MATCH" and rerank.get("legal_chunk_id") in gold_ids

            if gold_ids:
                pos_total += 1
                pos_correct += hit
                if any(chunk_id.startswith("ECGT") for chunk_id in gold_ids):
                    env_total += 1
                    env_correct += hit
                else:
                    other_total += 1
                    other_correct += hit
            else:
                neg_total += 1
                neg_correct += rerank.get("verdict") == "NO_MATCH"

    def pct(numer: int, denom: int) -> str:
        return f"{numer}/{denom} = {numer / denom:.1%}" if denom else f"{numer}/{denom} = n/a"

    print(f"true-positive ads (real claim exists): {pct(pos_correct, pos_total)}")
    print(f"true-negative ads (no claim in gold):   {pct(neg_correct, neg_total)}")
    print()
    print(f"  of which environmental (in-scope):     {pct(env_correct, env_total)}")
    print(f"  of which non-environmental (out-of-scope): {pct(other_correct, other_total)}")


if __name__ == "__main__":
    main()
