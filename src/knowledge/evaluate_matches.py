#!/usr/bin/env python3
"""
Score compare_e5.py's matches.json -- or rerank_matches.py's reranked
output -- against a hand-labeled gold set (one record per ad: gold_match,
gold_legal_chunk_id, evidence_sentence, notes).

This measures two different things, and they shouldn't be collapsed into
one number:

  - Retrieval/rerank accuracy on ads that DO have a real claim
    (gold_match=true): does the system's top pick match gold_legal_chunk_id?

  - Separability on ads that DON'T (gold_match=false): in raw-retrieval mode,
    what similarity score did the system's best (wrong) guess get?
    compare_e5.py's --min-similarity has had no default because there was
    no gold data to calibrate one against -- this is that calibration data.
    The floor's job is "is the top candidate confident enough to report at
    all", which is a question about the top-1 SIMILARITY SCORE, independent
    of whether that top-1 guess happens to be correct -- so calibration here
    uses each ad's top-1 similarity, not specifically the gold chunk's score.
    (In --rerank mode there's no similarity score to calibrate -- the model
    gives a MATCH/NO_MATCH verdict directly -- so this section is skipped.)

Two modes:
  --matches (default): scores raw embedding retrieval (each ad's top_matches).
    Run compare_e5.py WITHOUT --min-similarity first, so every ad has a real
    top-1 candidate to score (a floor already applied at prediction time
    would hide the exact signal this script calibrates).
  --rerank: scores an LLM rerank_matches.py output instead -- each ad's
    "rerank" verdict/legal_chunk_id -- and replaces --matches as the source
    file (a reranked file already contains everything matches.json had).

Usage:
  python evaluate_matches.py
  python evaluate_matches.py --matches embeddings/matches.json --gold 25.06/gold.json --k 3
  python evaluate_matches.py --rerank embeddings/reranked.json
"""

import argparse
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def load(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def best_separating_threshold(pos_scores: list[float], neg_scores: list[float]):
    """Threshold t (predict "real match" iff score >= t) that maximizes
    correctly-classified count over these two labeled score sets."""
    candidates = sorted(set(pos_scores + neg_scores))
    best_t, best_correct = None, -1
    for t in candidates:
        correct = sum(1 for s in pos_scores if s >= t) + sum(1 for s in neg_scores if s < t)
        if correct > best_correct:
            best_correct, best_t = correct, t
    return best_t, best_correct


def evaluate_retrieval(matches_by_ad: dict, positives: list, negatives: list, k: int):
    """Raw embedding-retrieval mode: score each ad's top_matches list."""
    print(f"=== Positives: {len(positives)} ads with a real gold claim ===")
    top1_hits, topk_hits = 0, 0
    pos_top1_scores = []
    for g in positives:
        pred = matches_by_ad.get(g["query_ad_id"])
        if pred is None or not pred["top_matches"]:
            print(f"  MISS   {g['query_title']:60s} no prediction (below_similarity_threshold or missing)")
            continue
        ids = [m["legal_chunk_id"] for m in pred["top_matches"]]
        top1_sim = pred["top_matches"][0]["similarity"]
        pos_top1_scores.append(top1_sim)

        top1_hit = ids[0] == g["gold_legal_chunk_id"]
        topk_hit = g["gold_legal_chunk_id"] in ids[:k]
        top1_hits += top1_hit
        topk_hits += topk_hit

        rank = ids.index(g["gold_legal_chunk_id"]) + 1 if g["gold_legal_chunk_id"] in ids else None
        mark = "OK  " if top1_hit else ("HIT " if topk_hit else "MISS")
        rank_str = f"rank={rank}" if rank else "not in top-k"
        print(
            f"  {mark}   {g['query_title']:60s} gold={g['gold_legal_chunk_id']:30s} "
            f"top1={ids[0]:30s} ({rank_str}, top1_sim={top1_sim:.3f})"
        )

    if positives:
        print(f"\nTop-1 accuracy: {top1_hits}/{len(positives)} = {top1_hits / len(positives):.1%}")
        print(f"Hit@{k}:       {topk_hits}/{len(positives)} = {topk_hits / len(positives):.1%}")

    print(f"\n=== Negatives: {len(negatives)} ads with no real claim ===")
    neg_top1_scores = []
    neg_rows = []
    for g in negatives:
        pred = matches_by_ad.get(g["query_ad_id"])
        if pred is None or not pred["top_matches"]:
            neg_rows.append((g, None, None))
            continue
        top1 = pred["top_matches"][0]
        neg_top1_scores.append(top1["similarity"])
        neg_rows.append((g, top1["similarity"], top1["legal_chunk_id"]))

    for g, sim, chunk_id in sorted(neg_rows, key=lambda r: (r[1] is None, -(r[1] or 0))):
        sim_str = f"{sim:.3f}" if sim is not None else "N/A"
        print(f"  top1_sim={sim_str:>6}  {g['query_title']:60s} -> {chunk_id or '(none)'}")

    if neg_top1_scores:
        print(
            f"\nNegative top-1 similarity: min={min(neg_top1_scores):.3f} "
            f"max={max(neg_top1_scores):.3f} mean={sum(neg_top1_scores) / len(neg_top1_scores):.3f}"
        )

    if pos_top1_scores and neg_top1_scores:
        best_t, best_correct = best_separating_threshold(pos_top1_scores, neg_top1_scores)
        total = len(pos_top1_scores) + len(neg_top1_scores)
        print(
            f"\nSuggested --min-similarity ~ {best_t:.3f} "
            f"(correctly separates {best_correct}/{total} = {best_correct / total:.1%} of labeled ads "
            f"by top-1 similarity alone)"
        )
        overlap = max(min(neg_top1_scores), min(pos_top1_scores)) <= min(max(neg_top1_scores), max(pos_top1_scores))
        if overlap:
            print(
                "Note: positive and negative top-1 similarity ranges overlap -- no single floor "
                "perfectly separates them on this sample; see the per-ad rows above for the actual cost."
            )
    else:
        print("\nNot enough labeled positives/negatives with predictions to suggest a threshold.")


def evaluate_rerank(matches_by_ad: dict, positives: list, negatives: list):
    """LLM-rerank mode: score each ad's rerank.verdict / rerank.legal_chunk_id.
    No similarity score exists here, so there's no threshold section --
    the model's MATCH/NO_MATCH verdict IS the decision, not a score to floor."""
    print(f"=== Positives: {len(positives)} ads with a real gold claim ===")
    verdict_hits, chunk_hits = 0, 0
    for g in positives:
        pred = matches_by_ad.get(g["query_ad_id"])
        rerank = pred.get("rerank") if pred else None
        if rerank is None:
            print(f"  MISS   {g['query_title']:60s} no rerank result")
            continue
        is_match = rerank.get("verdict") == "MATCH"
        chunk_id = rerank.get("legal_chunk_id")
        chunk_hit = is_match and chunk_id == g["gold_legal_chunk_id"]
        verdict_hits += is_match
        chunk_hits += chunk_hit
        mark = "OK  " if chunk_hit else ("HIT " if is_match else "MISS")
        print(
            f"  {mark}   {g['query_title']:60s} gold={g['gold_legal_chunk_id']:30s} "
            f"verdict={rerank.get('verdict'):9s} -> {chunk_id}"
        )

    if positives:
        print(f"\nVerdict=MATCH correct: {verdict_hits}/{len(positives)} = {verdict_hits / len(positives):.1%}")
        print(f"Exact chunk id correct: {chunk_hits}/{len(positives)} = {chunk_hits / len(positives):.1%}")

    print(f"\n=== Negatives: {len(negatives)} ads with no real claim ===")
    correct_no_match = 0
    false_positives = []
    errors = []
    for g in negatives:
        pred = matches_by_ad.get(g["query_ad_id"])
        rerank = pred.get("rerank") if pred else None
        if rerank is None:
            print(f"  MISS   {g['query_title']:60s} no rerank result")
            continue
        verdict = rerank.get("verdict")
        if verdict == "NO_MATCH":
            correct_no_match += 1
            print(f"  OK      {g['query_title']:60s} NO_MATCH")
        elif verdict == "ERROR":
            errors.append((g, rerank))
            print(f"  ERROR   {g['query_title']:60s} {rerank.get('rationale')}")
        else:
            false_positives.append((g, rerank))
            print(f"  WRONG   {g['query_title']:60s} MATCH -> {rerank.get('legal_chunk_id')} | {rerank.get('rationale')}")

    if negatives:
        print(f"\nCorrectly said NO_MATCH: {correct_no_match}/{len(negatives)} = {correct_no_match / len(negatives):.1%}")
        if errors:
            print(f"Errored (excluded from accuracy, not scored either way): {len(errors)}/{len(negatives)}")

    total = len(positives) + len(negatives) - len(errors)
    binary_correct = verdict_hits + correct_no_match
    if total:
        print(f"\nOverall binary (MATCH vs NO_MATCH) accuracy, excluding errors: {binary_correct}/{total} = {binary_correct / total:.1%}")

    if false_positives:
        print(f"\n--- False positives ({len(false_positives)}) ---")
        for g, rerank in false_positives:
            print(f"  {g['query_title']}: -> {rerank.get('legal_chunk_id')} | {rerank.get('rationale')}")

    if errors:
        print(f"\n--- Errors ({len(errors)}) -- not counted as correct or incorrect ---")
        for g, rerank in errors:
            print(f"  {g['query_title']}: {rerank.get('rationale')}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--matches", type=Path, default=SCRIPT_DIR / "embeddings" / "matches.json")
    parser.add_argument(
        "--rerank", type=Path, default=None,
        help="Path to a rerank_matches.py output. When given, scores the LLM's rerank "
             "verdict/legal_chunk_id instead of raw top-1 retrieval, and replaces --matches "
             "as the source file (a reranked file already contains everything matches.json had).",
    )
    parser.add_argument("--gold", type=Path, default=SCRIPT_DIR / "25.06" / "gold.json")
    parser.add_argument("--k", type=int, default=3, help="hit@k (retrieval mode only) -- how many of each ad's top_matches to check gold_legal_chunk_id against")
    args = parser.parse_args()

    source_path = args.rerank if args.rerank is not None else args.matches
    matches = load(source_path)
    gold = load(args.gold)

    matches_by_ad = {m["query_ad_id"]: m for m in matches}
    missing = [g["query_ad_id"] for g in gold if g["query_ad_id"] not in matches_by_ad]
    if missing:
        print(f"WARNING: {len(missing)} gold ad_id(s) not found in {source_path.name}: {missing}\n")

    positives = [g for g in gold if g["gold_match"]]
    negatives = [g for g in gold if not g["gold_match"]]

    if args.rerank is not None:
        evaluate_rerank(matches_by_ad, positives, negatives)
    else:
        evaluate_retrieval(matches_by_ad, positives, negatives, args.k)


if __name__ == "__main__":
    main()
