"""
Sweeps severity.md's drop threshold against a dev gold set, without any new
model calls -- src/extraction_v4.py's `to_v3_shape` applies the keep/drop
cutoff entirely from a cached results file (severity is already computed
once per claim; only the threshold changes per sweep step). This is the A4
ablation ("0-100 + tuned threshold") from
.claude/reccomendations/extract.md's ablation matrix.

Usage:
    python3 -m src.sweep_severity_threshold \\
        --predictions results/phase1/v4_predictions.json \\
        --gold golden/samples/canonical/sample_coop.json \\
        --thresholds 0 10 20 30 40 50 60 70 80 90
"""

import argparse
import json

from .evaluate import category_accuracy, extraction_prf
from .extraction_v4 import to_v3_shape


def sweep(results, gold, thresholds):
    rows = []
    for t in thresholds:
        shaped = to_v3_shape(results, threshold=t)
        prf = extraction_prf(shaped, gold)
        cat = category_accuracy(shaped, gold)
        rows.append({
            "threshold": t,
            "precision": prf["precision"],
            "recall": prf["recall"],
            "f1": prf["f1"],
            "category_accuracy": cat["accuracy"],
            "category_considered": cat["considered"],
        })
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--predictions", required=True,
        help="src/extraction_v4.py results file (unthresholded -- every claim with its raw severity attached)",
    )
    parser.add_argument("--gold", required=True)
    parser.add_argument("--thresholds", type=int, nargs="+", default=list(range(0, 101, 10)))
    args = parser.parse_args()

    with open(args.predictions, encoding="utf-8") as f:
        results = json.load(f)
    with open(args.gold, encoding="utf-8") as f:
        gold = json.load(f)

    rows = sweep(results, gold, args.thresholds)
    best = max(rows, key=lambda r: r["f1"])
    for r in rows:
        marker = "  <-- best F1" if r["threshold"] == best["threshold"] else ""
        print(
            f"threshold={r['threshold']:>3}  P={r['precision']:.4f}  R={r['recall']:.4f}  F1={r['f1']:.4f}  "
            f"cat_acc={r['category_accuracy']:.4f} ({r['category_considered']}){marker}"
        )
