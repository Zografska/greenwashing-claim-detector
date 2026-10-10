"""Step 5: sweep τ for each embedding model × aggregation on a labelled set.

For every labelled IN_SCOPE/NV claim (needs_review skipped) we keep the spans that reproduce it
(segment_coverage.match: exact or covered). A claim is recalled at τ if any of those spans is a
candidate, i.e. `lexical_hit OR margin > τ`. Per τ we report:
  recall              combined rule, overall
  emb_recall          margin alone (no keywords): robustness if the keyword list misses a phrasing
  lex_only / emb_only claims recalled only through keywords / only through the margin
  cand_per_rec        candidates per record (= Pass 2 calls), and the share of all spans
  discarded_cand      share of labelled DISCARDED claims that still become candidates
Selection (run on the dev/reserve set only): the largest τ (fewest candidates) whose recall is
≥ --target. Per-trigger recall is printed at the selected τ.

Usage:
  python3 retriever/calibrate.py golden/labeled/golden_set_ecgt_reserve.json --target 0.99 \\
      --csv retriever/calibration_reserve.csv
  python3 retriever/calibrate.py eval/... --fixed e5:max:0.02      # measure one setting, no selection
"""
import argparse
import collections
import csv
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from score import Retriever  # noqa: E402
from segment import load_config  # noqa: E402
from segment_coverage import match  # noqa: E402


def collect(retriever, products):
    """Per record: span (margin, lexical) list; per claim: label, triggers, matching span indices."""
    sources, recs = {}, []
    for p in products:
        src = ROOT / "golden" / p["source_file"]
        if src not in sources:
            sources[src] = json.load(open(src, encoding="utf-8"))
        scored = retriever.score_record(sources[src][p["source_index"]])
        claims = []
        for c in p["claims"]:
            if c.get("needs_review"):
                continue
            idx = [i for i, s in enumerate(scored) if match(c["claim_text"], [s.span]) != "missed"]
            claims.append(dict(pos=c["label"] != "DISCARDED", triggers=c["triggers"], spans=idx))
        recs.append(dict(margin=np.array([s.margin for s in scored]),
                         lex=np.array([bool(s.lexical) for s in scored]), claims=claims))
    return recs


def evaluate(recs, tau):
    """Metrics at one τ (None = keywords only)."""
    out = collections.Counter()
    trig = collections.defaultdict(lambda: [0, 0])
    n_spans = n_cand = 0
    for r in recs:
        emb = r["margin"] > tau if tau is not None else np.zeros(len(r["margin"]), bool)
        cand = r["lex"] | emb
        n_spans += len(cand)
        n_cand += int(cand.sum())
        for c in r["claims"]:
            idx = c["spans"]
            hit, by_lex, by_emb = bool(cand[idx].any()), bool(r["lex"][idx].any()), bool(emb[idx].any())
            if not c["pos"]:
                out["neg"] += 1
                out["neg_cand"] += hit
                continue
            out["pos"] += 1
            out["hit"] += hit
            out["emb_hit"] += by_emb
            out["lex_only"] += by_lex and not by_emb
            out["emb_only"] += by_emb and not by_lex
            for t in c["triggers"]:
                if t != "out_of_scope":
                    trig[t][0] += hit
                    trig[t][1] += 1
    n_rec = len(recs)
    return dict(tau=tau, recall=out["hit"] / out["pos"], hit=out["hit"], pos=out["pos"],
                emb_recall=out["emb_hit"] / out["pos"], lex_only=out["lex_only"], emb_only=out["emb_only"],
                cand_per_rec=n_cand / n_rec, cand_share=n_cand / max(n_spans, 1),
                discarded_cand=out["neg_cand"] / max(out["neg"], 1), triggers=dict(trig))


def fmt(m):
    t = "lex only" if m["tau"] is None else f"{m['tau']:+.4f}"
    return (f"  τ={t:>9}  recall {m['hit']}/{m['pos']} = {m['recall']:6.1%}  emb-alone {m['emb_recall']:6.1%}  "
            f"lex-only {m['lex_only']:3d}  emb-only {m['emb_only']:3d}  cand/rec {m['cand_per_rec']:5.1f} "
            f"({m['cand_share']:4.0%} of spans)  DISCARDED→cand {m['discarded_cand']:4.0%}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("labelled")
    ap.add_argument("--models", nargs="+", default=["e5", "mpnet"])
    ap.add_argument("--aggregations", nargs="+", default=["max", "top3_mean"])
    ap.add_argument("--target", type=float, help="recall target (default: eval.target_recall)")
    ap.add_argument("--fixed", help="model:aggregation:tau — measure only this setting")
    ap.add_argument("--csv", help="write the full sweep here")
    args = ap.parse_args()
    cfg = load_config()
    target = args.target or cfg["eval"]["target_recall"]
    sw = cfg["eval"]["tau_sweep"]
    grid = [None] + list(np.round(np.arange(sw["stop"], sw["start"] - 1e-9, -sw["step"]), 4))
    products = json.load(open(args.labelled, encoding="utf-8"))

    if args.fixed:
        model, agg, tau = args.fixed.split(":")
        settings, grid = [(model, agg)], [None if tau == "none" else float(tau)]
    else:
        settings = [(m, a) for m in args.models for a in args.aggregations]

    rows = []
    for model in dict.fromkeys(m for m, _ in settings):
        r = Retriever(cfg, model=model)
        for agg in [a for m, a in settings if m == model]:
            r.aggregation = agg
            recs = collect(r, products)
            sweep = [evaluate(recs, t) for t in grid]
            for m in sweep:
                rows.append(dict(model=model, aggregation=agg, **{k: v for k, v in m.items() if k != "triggers"}))
            print(f"\n=== {model} / {agg} on {args.labelled} ({len(products)} records) ===")
            if args.fixed:
                chosen = sweep[0]
            else:
                ok = [m for m in sweep if m["recall"] >= target]
                chosen = min(ok, key=lambda m: m["cand_per_rec"]) if ok else max(sweep, key=lambda m: m["recall"])
                for m in sweep:
                    if m is sweep[0] or m is chosen or (m["tau"] is not None and abs(m["tau"] * 400 % 4) < 1e-6):
                        print(("→" if m is chosen else " ") + fmt(m)[1:])
                print(f"selected for recall ≥ {target:.0%}: τ = {chosen['tau']}")
            if args.fixed:
                print(fmt(chosen))
            print("per-trigger recall at that τ (weakest first):")
            for t, (h, n) in sorted(chosen["triggers"].items(), key=lambda kv: kv[1][0] / kv[1][1]):
                print(f"    {h / n:5.0%}  {t} ({h}/{n})")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"\nwrote {len(rows)} rows to {args.csv}")


if __name__ == "__main__":
    main()
