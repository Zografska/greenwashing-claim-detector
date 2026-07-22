#!/usr/bin/env python3
"""
Scores compare_e5.py's matches.json -- or rerank_matches.py's reranked
output -- against the CLAIM-level gold built by src/adapters/build.py
(golden/canonical/<retailer>.json), using the gold_legal_chunk_id each claim
was assigned by src/adapters/legal_mapping.py.

This is a sibling to evaluate_matches.py, not a replacement: that script
scores the 25.06 gold set, which is one row per AD with a single
gold_legal_chunk_id. These 4 retailer golden sets commonly have MULTIPLE
claims per product, in different categories, that should match DIFFERENT
legal chunks -- a shape evaluate_matches.py's gold format can't express.

Two real asymmetries carried over/adapted from evaluate_matches.py and
src/evaluate.py, not papered over:

- Only claims with risk_level != "LOW" and a non-null gold_legal_chunk_id
  are scored (see src/adapters/legal_mapping.py -- irrelevant_claim always
  maps to None, i.e. "not a claim at all"). Reported as excluded_claims.

- legal_mapping_confidence == "low" claims (fake_or_unverified_label's
  environmental-vs-general split, unfair_comparison's no-good-fit case) are
  reported SEPARATELY from the main accuracy number, since their own ground
  truth is a heuristic, not a certain read -- see legal_mapping.py.

Retrieval mode scores at the CLAIM level directly: compare_e5.py already
returns multiple top_matches per ad (pools per sentence, keeps each
passage's best-scoring sentence -- see its own docstring), so each of an
ad's claims can independently be checked against that same shared
top_matches list.

Rerank mode can't do the same, because rerank_matches.py still returns only
ONE verdict + legal_chunk_id per ad (restructuring it to go per-claim is a
separate, deferred piece of work). So rerank is scored at the AD level:
is the single predicted legal_chunk_id a member of the SET of that ad's
gold chunk ids (best-case credit)? Ads with 2+ distinct gold chunk ids are
reported separately as "ceiling cases" -- today's per-ad rerank structurally
cannot get these fully right no matter how good the model is, so they're
surfaced rather than silently averaged into one pass/fail number.

Usage:
  python evaluate_claim_matches.py --matches embeddings/matches.json \\
      --gold ../../golden/canonical/coop.json
  python evaluate_claim_matches.py --rerank embeddings/reranked.json \\
      --gold ../../golden/canonical/coop.json ../../golden/canonical/carrefour.json
"""

import argparse
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def load(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _flaggable_claims(gold_records: list[dict]) -> list[dict]:
    """Every scoreable (product, claim) pair, flattened, tagged with its
    product's ean/name for reporting. Excludes LOW-risk and no-chunk claims
    (irrelevant_claim, or an unrecognized category -- see legal_mapping.py)."""
    out = []
    for rec in gold_records:
        for claim in rec.get("extracted_claims", []):
            if claim.get("risk_level") == "LOW" or claim.get("gold_legal_chunk_id") is None:
                continue
            out.append({**claim, "ean": rec.get("ean"), "product_name": rec.get("name")})
    return out


def score_claims(matches_by_ad: dict, claims: list[dict], ks: list[int]) -> dict:
    """Hit@k for every k in `ks`, computed from each claim's ad's existing
    top_matches list (already ranked) -- no need to rerun retrieval per k.
    Returns {"n": int, "no_prediction": int, "hits": {k: int, ...}}, so
    callers can print it (see evaluate_retrieval) or consume it directly
    (see tune_retrieval.py, which needs several k values per config)."""
    hits = {k: 0 for k in ks}
    no_prediction = 0
    for c in claims:
        pred = matches_by_ad.get(c["ean"])
        if pred is None or not pred["top_matches"]:
            no_prediction += 1
            continue
        ids = [m["legal_chunk_id"] for m in pred["top_matches"]]
        for k in ks:
            hits[k] += c["gold_legal_chunk_id"] in ids[:k]
    return {"n": len(claims), "no_prediction": no_prediction, "hits": hits}


def evaluate_retrieval(matches_by_ad: dict, claims: list[dict], k: int) -> dict:
    high_conf = [c for c in claims if c["legal_mapping_confidence"] != "low"]
    low_conf = [c for c in claims if c["legal_mapping_confidence"] == "low"]

    def score_and_print(subset: list[dict], label: str) -> dict:
        result = score_claims(matches_by_ad, subset, [1, k])
        n = result["n"]
        print(f"\n=== {label}: {n} claims ===")
        if n:
            print(f"  Top-1 accuracy: {result['hits'][1]}/{n} = {result['hits'][1] / n:.1%}")
            print(f"  Hit@{k}:        {result['hits'][k]}/{n} = {result['hits'][k] / n:.1%}")
            if result["no_prediction"]:
                print(f"  No prediction (ad not in matches file / empty top_matches): {result['no_prediction']}")
        return result

    high_conf_result = score_and_print(high_conf, "high/medium-confidence gold claims")
    low_conf_result = score_and_print(low_conf, "low-confidence gold claims (heuristic mapping -- read, don't trust blindly)") if low_conf else None
    return {"high_confidence": high_conf_result, "low_confidence": low_conf_result}


def score_rerank(matches_by_ad: dict, gold_records: list[dict]) -> dict:
    """Ad-level rerank scoring: is the single predicted legal_chunk_id a member
    of the SET of that ad's gold chunk ids (best-case credit, since
    rerank_matches.py returns only one verdict per ad)? Returns
    {"correct": int, "total": int, "ceiling_cases": int} -- callers print
    (see evaluate_rerank) or consume directly (see compare_retrieval_vs_rerank.py)."""
    correct = total = ceiling_cases = 0
    for rec in gold_records:
        ean = rec.get("ean")
        gold_chunk_ids = {
            c["gold_legal_chunk_id"]
            for c in rec.get("extracted_claims", [])
            if c.get("risk_level") != "LOW" and c.get("gold_legal_chunk_id") is not None
        }
        pred = matches_by_ad.get(ean)
        rerank = pred.get("rerank") if pred else None
        if rerank is None:
            continue
        total += 1
        if len(gold_chunk_ids) > 1:
            ceiling_cases += 1
        verdict = rerank.get("verdict")
        if verdict == "NO_MATCH":
            correct += len(gold_chunk_ids) == 0
        elif verdict == "MATCH":
            correct += rerank.get("legal_chunk_id") in gold_chunk_ids
        # ERROR verdicts excluded from both correct and total-considered below
        else:
            total -= 1
    return {"correct": correct, "total": total, "ceiling_cases": ceiling_cases}


def evaluate_rerank(matches_by_ad: dict, gold_records: list[dict]) -> dict:
    result = score_rerank(matches_by_ad, gold_records)
    correct, total, ceiling_cases = result["correct"], result["total"], result["ceiling_cases"]

    print(f"\n=== Ad-level rerank accuracy: {correct}/{total} = {correct / total:.1%} ===" if total else "\nNo scoreable ads.")
    if ceiling_cases:
        print(
            f"NOTE: {ceiling_cases}/{total} ads have 2+ distinct gold legal_chunk_ids -- "
            f"rerank_matches.py returns only ONE verdict per ad today, so these ads have a real "
            f"ceiling on this metric regardless of model quality (per-claim reranking is deferred, "
            f"separate follow-up work)."
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--matches", type=Path, default=SCRIPT_DIR / "embeddings" / "matches.json")
    parser.add_argument(
        "--rerank", type=Path, default=None,
        help="Path to a rerank_matches.py output. When given, scores the LLM's rerank "
             "verdict/legal_chunk_id at the ad level instead of raw top-1 retrieval, and "
             "replaces --matches as the source file.",
    )
    parser.add_argument(
        "--gold", type=Path, nargs="+", required=True,
        help="one or more golden/canonical/<retailer>.json files (from src/adapters/build.py)",
    )
    parser.add_argument("--k", type=int, default=3, help="hit@k (retrieval mode only)")
    args = parser.parse_args()

    source_path = args.rerank if args.rerank is not None else args.matches
    matches = load(source_path)
    matches_by_ad = {m["query_ad_id"]: m for m in matches}

    gold_records = [rec for path in args.gold for rec in load(path)]

    if args.rerank is not None:
        evaluate_rerank(matches_by_ad, gold_records)
    else:
        claims = _flaggable_claims(gold_records)
        missing = {c["ean"] for c in claims} - set(matches_by_ad)
        if missing:
            print(f"WARNING: {len(missing)} gold ean(s) not found in {source_path.name}\n")
        evaluate_retrieval(matches_by_ad, claims, args.k)


if __name__ == "__main__":
    main()
