#!/usr/bin/env python3
"""
Grid-searches compare_e5.py's ranking knobs (centering, CSLS, CSLS
neighborhood size) against the claim-level gold_legal_chunk_id ground truth
in golden/canonical/<retailer>.json, to find a config good enough to skip
rerank_matches.py's LLM reranking step entirely -- i.e. embedding retrieval
alone supplies the top-6/7 legal chunks fed to src/extraction.py as grounding.

Deliberately NOT in scope here (see the plan): tuning --min-similarity. That
floor is about "is there a real claim here at all" (calibrated against
true-negative/hard_no products), a separate question from "given there IS a
claim, does retrieval surface its correct legal chunk in the top-k" (what
this script tunes). Conflating the two would blur which number moved for
which reason.

Requires each retailer's query embeddings to already exist under
./embeddings/<retailer>/ (see the README/plan for the
prepare_ads_chunks.py -> embed_e5.py --mode query steps) and canonical gold
under golden/canonical/<retailer>.json (src/adapters/build.py).

Usage:
  python tune_retrieval.py
  python tune_retrieval.py --retailers coop carrefour --ks 6 7 10
"""

import argparse
import sys
from itertools import product
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from compare_e5 import compare, load_passage_set, load_query_set  # noqa: E402
from evaluate_claim_matches import _flaggable_claims, load, score_claims  # noqa: E402

GOLD_DIR = PROJECT_ROOT / "golden" / "canonical"
ALL_RETAILERS = ["coop", "carrefour", "eurospin", "naturasi"]

# Grid: centering on/off x CSLS on/off x CSLS neighborhood size (only
# meaningful when CSLS is on -- one entry with csls_k=None covers "CSLS off").
CENTER_OPTIONS = [True, False]
CSLS_OPTIONS = [(False, None), (True, 5), (True, 10), (True, 15)]


def build_configs():
    configs = []
    for center, (csls, csls_k) in product(CENTER_OPTIONS, CSLS_OPTIONS):
        configs.append({"center": center, "csls": csls, "csls_k": csls_k or 10})
    return configs


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--retailers", nargs="+", default=ALL_RETAILERS)
    parser.add_argument("--ks", type=int, nargs="+", default=[6, 7, 10], help="Hit@k values to report")
    parser.add_argument("--top-k", type=int, default=15, help="retrieval depth per config (must cover the largest --ks value)")
    args = parser.parse_args()

    if args.top_k < max(args.ks):
        sys.exit(f"--top-k ({args.top_k}) must be >= the largest --ks value ({max(args.ks)})")

    ecgt_emb, ecgt_meta = load_passage_set("ecgt")
    ucpd_emb, ucpd_meta = load_passage_set("ucpd")

    per_retailer_data = {}
    for retailer in args.retailers:
        query_emb, query_meta = load_query_set(retailer)
        gold_records = load(GOLD_DIR / f"{retailer}.json")
        claims = _flaggable_claims(gold_records)
        high_conf = [c for c in claims if c["legal_mapping_confidence"] != "low"]
        per_retailer_data[retailer] = (query_emb, query_meta, high_conf)
        print(f"{retailer}: {len(high_conf)} high/medium-confidence flaggable claims (of {len(claims)} total)")

    configs = build_configs()
    rows = []
    for cfg in configs:
        label = (
            f"center={cfg['center']} csls={cfg['csls']}"
            + (f"(k={cfg['csls_k']})" if cfg["csls"] else "")
        )
        pooled_hits = {k: 0 for k in args.ks}
        pooled_n = 0
        per_retailer_hits = {}

        for retailer, (query_emb, query_meta, high_conf) in per_retailer_data.items():
            results = compare(
                query_emb, query_meta, ecgt_emb, ecgt_meta, ucpd_emb, ucpd_meta,
                top_k=args.top_k, center=cfg["center"], csls=cfg["csls"], csls_k=cfg["csls_k"],
                verbose=False,
            )
            matches_by_ad = {r["query_ad_id"]: r for r in results}
            scored = score_claims(matches_by_ad, high_conf, args.ks)
            per_retailer_hits[retailer] = scored
            pooled_n += scored["n"]
            for k in args.ks:
                pooled_hits[k] += scored["hits"][k]

        rows.append({"label": label, "cfg": cfg, "pooled_hits": pooled_hits, "pooled_n": pooled_n, "per_retailer": per_retailer_hits})

    primary_k = max(args.ks) if len(args.ks) == 1 else sorted(args.ks)[len(args.ks) // 2]
    rows.sort(key=lambda r: r["pooled_hits"][primary_k], reverse=True)

    print(f"\n=== Ranked by pooled Hit@{primary_k} ({pooled_n} claims across {len(args.retailers)} retailers) ===\n")
    header = "config".ljust(28) + "".join(f"Hit@{k}".rjust(10) for k in args.ks)
    print(header)
    for row in rows:
        line = row["label"].ljust(28)
        for k in args.ks:
            hits, n = row["pooled_hits"][k], row["pooled_n"]
            line += f"{hits}/{n}={hits / n:.1%}".rjust(10)
        print(line)

    winner = rows[0]
    print(f"\nWinner: {winner['label']}")
    print("Per-retailer breakdown for the winner:")
    for retailer, scored in winner["per_retailer"].items():
        n = scored["n"]
        parts = ", ".join(f"Hit@{k}={scored['hits'][k]}/{n}={scored['hits'][k] / n:.1%}" if n else f"Hit@{k}=n/a" for k in args.ks)
        print(f"  {retailer}: {parts} (no_prediction={scored['no_prediction']})")


if __name__ == "__main__":
    main()
