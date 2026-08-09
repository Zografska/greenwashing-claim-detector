#!/usr/bin/env python3
"""
Head-to-head comparison: tuned embedding-only retrieval alone vs. that SAME
top-k candidate pool + an LLM rerank pass on top of it -- on a small sample,
to get concrete evidence for whether rerank_matches.py's resource cost
(requires a local Ollama server; ~2-3 min/ad at its original --top-k 56
sizing) is worth it once retrieval is already tuned.

Fairness matters here: both arms see the IDENTICAL top-k candidates from one
compare() call (tuned config: center=True, csls=True, csls_k=15 -- see
tune_retrieval.py). Comparing tuned top-7 retrieval against
rerank_matches.py's original convention (reranking over the full 56-chunk
corpus) would confound "does rerank help" with "does rerank see more
candidates" -- this script holds the candidate pool constant so only the
LLM-reasoning-vs-no-LLM-reasoning variable moves.

Three numbers are reported per ad, since "does rerank beat retrieval" only
means something if you compare it to the RIGHT baseline:
  - embedding top-1 (ad-level): the naive "just trust the #1 embedding
    match, no LLM at all" baseline -- this is what rerank actually needs to
    beat to be worth its cost.
  - embedding top-k (ad-level, oracle ceiling): was the correct chunk
    anywhere in the k candidates handed to rerank? Rerank's accuracy is
    capped by this number no matter how good the model is.
  - +rerank (ad-level): the LLM's chosen verdict/chunk, scored against the
    ad's gold chunk-id set (same "member of gold set" logic
    evaluate_claim_matches.py's score_rerank already uses).

Also reports claim-level Hit@6/7/10 for the embedding-only arm (via
evaluate_claim_matches.score_claims), since that's the metric
tune_retrieval.py already established as the tuning target.

Requires a local Ollama server for the rerank arm (see src/extraction.py's
OLLAMA_URL) -- the embedding arm needs no LLM at all.

Usage:
  python compare_retrieval_vs_rerank.py --retailer coop --model llama3.2:3b
  python compare_retrieval_vs_rerank.py --retailer coop --model llama3.3:70b --top-k 7
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from compare_e5 import compare, load_passage_set, load_query_set  # noqa: E402
from evaluate_claim_matches import _flaggable_claims, load, score_claims, score_rerank  # noqa: E402
from rerank_matches import _apply_environmental_backstop, rerank_ad  # noqa: E402

GOLD_DIR = PROJECT_ROOT / "golden" / "canonical"

# Tuned config from tune_retrieval.py -- see that script for the grid search
# this came from (pooled Hit@7 winner across all 4 retailers).
TUNED_CONFIG = {"center": True, "csls": True, "csls_k": 15}


def run_rerank_pass(
    results: List[dict], model: str, out_path: Optional[Path] = None
) -> Tuple[List[dict], dict]:
    """Reranks each ad's candidates (already top-k from compare()) with the
    given model. Returns (reranked_results, timing) -- timing has
    total_seconds/n_ads/avg_seconds_per_ad so the resource-cost side of the
    comparison is a real, printed number, not an afterthought.

    If out_path is given, each ad's record is appended as one JSON line and
    flushed to disk immediately after that ad's call returns -- so a killed
    session (broken pipe, SSH drop) only loses the in-flight ad, not every
    result computed so far."""
    reranked = []
    call_seconds = []
    out_f = None
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_f = open(out_path, "w", encoding="utf-8")
        print(f"  (streaming per-ad results to {out_path})")

    def _emit(record: dict) -> None:
        reranked.append(record)
        if out_f is not None:
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            out_f.flush()

    try:
        for i, ad in enumerate(results, 1):
            candidates = ad.get("top_matches") or []
            title = ad["query_title"]
            claim_text = " ".join(ad.get("query_sentences") or [])

            if not candidates or not claim_text.strip():
                _emit({
                    **ad,
                    "rerank": {"verdict": "NO_MATCH", "legal_chunk_id": "NONE", "rationale": "no retrieval candidates"},
                })
                print(f"  [{i}/{len(results)}] {title}: skipped (no candidates)")
                continue

            start = time.monotonic()
            try:
                verdict = rerank_ad(title, claim_text, candidates, model)
                verdict = _apply_environmental_backstop(verdict)
            except Exception as e:
                elapsed = time.monotonic() - start
                print(f"  [{i}/{len(results)}] {title}: FAILED after {elapsed:.1f}s ({e})")
                _emit({**ad, "rerank": {"verdict": "ERROR", "legal_chunk_id": None, "rationale": str(e)}})
                continue
            elapsed = time.monotonic() - start
            call_seconds.append(elapsed)
            _emit({**ad, "rerank": verdict})
            print(f"  [{i}/{len(results)}] {title}: {verdict['verdict']} -> {verdict['legal_chunk_id']} [{elapsed:.1f}s]")
    finally:
        if out_f is not None:
            out_f.close()

    timing = {
        "total_seconds": sum(call_seconds),
        "n_ads": len(call_seconds),
        "avg_seconds_per_ad": (sum(call_seconds) / len(call_seconds)) if call_seconds else 0.0,
    }
    return reranked, timing


def embedding_ad_level_scores(matches_by_ad: dict, gold_records: List[dict]) -> dict:
    """Two ad-level baselines for the embedding-only arm, computed the same
    "member of gold set" way score_rerank scores the LLM's single verdict --
    so all three numbers in the final table are directly comparable:
      - top1: naive "just trust the #1 embedding match" baseline
      - topk: oracle ceiling -- was the right chunk anywhere in the k
        candidates handed to rerank at all?
    """
    top1_correct = topk_correct = total = 0
    for rec in gold_records:
        ean = rec.get("ean")
        gold_chunk_ids = {
            c["gold_legal_chunk_id"]
            for c in rec.get("extracted_claims", [])
            if c.get("risk_level") != "LOW" and c.get("gold_legal_chunk_id") is not None
        }
        pred = matches_by_ad.get(ean)
        if pred is None:
            continue
        total += 1
        ids = [m["legal_chunk_id"] for m in pred["top_matches"]]
        if not ids:
            top1_correct += len(gold_chunk_ids) == 0
            topk_correct += len(gold_chunk_ids) == 0
            continue
        top1_correct += (ids[0] in gold_chunk_ids) if gold_chunk_ids else False
        topk_correct += bool(set(ids) & gold_chunk_ids) if gold_chunk_ids else False
    return {"top1_correct": top1_correct, "topk_correct": topk_correct, "total": total}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--retailer", required=True)
    parser.add_argument("--model", default="llama3.2:3b", help="Ollama model for the rerank arm")
    parser.add_argument("--queries", default=None, help="query embedding set name under ./embeddings/ (default: sample_<retailer>)")
    parser.add_argument("--gold", type=Path, default=None, help="canonical gold path (default: golden/canonical/<retailer>.json)")
    parser.add_argument("--top-k", type=int, default=7, help="candidates per ad -- fed identically to both arms")
    parser.add_argument(
        "--rerank-out", type=Path, default=None,
        help="stream each ad's rerank result here as JSONL, flushed after every call "
        "(default: ./embeddings/<queries_name>_rerank_progress.jsonl; pass 'none' to disable)",
    )
    args = parser.parse_args()

    queries_name = args.queries or f"sample_{args.retailer}"
    if args.rerank_out is not None and str(args.rerank_out).lower() == "none":
        rerank_out = None
    else:
        rerank_out = args.rerank_out or (SCRIPT_DIR / "embeddings" / f"{queries_name}_rerank_progress.jsonl")
    if args.gold:
        gold_path = args.gold
    elif queries_name.startswith("sample_"):
        # Default queries are the small sample set -- gold must match, or the
        # Hit@k denominator silently comes from the FULL retailer's claims
        # while only the sample's ads have predictions (massively deflates
        # the hit rate via unreported no_prediction misses). Caught by
        # actually running this before handing it off.
        gold_path = PROJECT_ROOT / "golden" / "samples" / "canonical" / f"sample_{args.retailer}.json"
    else:
        gold_path = GOLD_DIR / f"{args.retailer}.json"

    ecgt_emb, ecgt_meta = load_passage_set("ecgt")
    ucpd_emb, ucpd_meta = load_passage_set("ucpd")
    query_emb, query_meta = load_query_set(queries_name)
    gold_records = load(gold_path)

    print(f"Retrieving top-{args.top_k} candidates ({queries_name}, tuned config {TUNED_CONFIG}) ...")
    results = compare(
        query_emb, query_meta, ecgt_emb, ecgt_meta, ucpd_emb, ucpd_meta,
        top_k=args.top_k, **TUNED_CONFIG,
    )
    matches_by_ad = {r["query_ad_id"]: r for r in results}

    claims = _flaggable_claims(gold_records)
    high_conf = [c for c in claims if c["legal_mapping_confidence"] != "low"]
    embedding_claim_scores = score_claims(matches_by_ad, high_conf, [6, 7, min(10, args.top_k)])
    embedding_ad_scores = embedding_ad_level_scores(matches_by_ad, gold_records)

    print(f"\nReranking {len(results)} ads with model={args.model} (this needs your Ollama server) ...")
    reranked, timing = run_rerank_pass(results, args.model, out_path=rerank_out)
    reranked_by_ad = {r["query_ad_id"]: r for r in reranked}
    rerank_scores = score_rerank(reranked_by_ad, gold_records)

    n = embedding_claim_scores["n"]
    print(f"\n=== {args.retailer}: embedding-only claim-level Hit@k ({n} high/medium-confidence claims) ===")
    for k, hits in embedding_claim_scores["hits"].items():
        print(f"  Hit@{k}: {hits}/{n} = {hits / n:.1%}" if n else f"  Hit@{k}: n/a")
    if embedding_claim_scores["no_prediction"]:
        print(
            f"  ({embedding_claim_scores['no_prediction']}/{n} claims' ad had no prediction at all -- "
            f"check --queries/--gold are the same sample, not a full-retailer/sample mismatch)"
        )

    ad_n = embedding_ad_scores["total"]
    print(f"\n=== {args.retailer}: ad-level comparison ({ad_n} ads) ===")
    print(f"  embedding top-1 (naive, no LLM):     {embedding_ad_scores['top1_correct']}/{ad_n} = {embedding_ad_scores['top1_correct'] / ad_n:.1%}" if ad_n else "  n/a")
    print(f"  embedding top-{args.top_k} (oracle ceiling): {embedding_ad_scores['topk_correct']}/{ad_n} = {embedding_ad_scores['topk_correct'] / ad_n:.1%}" if ad_n else "  n/a")
    print(f"  +rerank ({args.model}):" + " " * max(1, 24 - len(args.model)) + f"{rerank_scores['correct']}/{rerank_scores['total']} = {rerank_scores['correct'] / rerank_scores['total']:.1%}" if rerank_scores["total"] else "  +rerank: n/a")
    if rerank_scores["ceiling_cases"]:
        print(
            f"  NOTE: {rerank_scores['ceiling_cases']}/{rerank_scores['total']} ads have 2+ distinct gold "
            f"chunk ids -- rerank returns one verdict per ad, so these have a real ceiling regardless of model quality"
        )

    print(f"\n=== rerank resource cost ({args.model}) ===")
    print(f"  {timing['n_ads']} successful calls, total {timing['total_seconds']:.1f}s, avg {timing['avg_seconds_per_ad']:.1f}s/ad")


if __name__ == "__main__":
    main()
