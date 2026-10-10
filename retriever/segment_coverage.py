"""Step 3 gate: can segmentation reproduce the labelled claims?

For each labelled record (golden_set_ecgt_*.json format) the source record is segmented and
every claim is matched against the spans:
  exact    normalized text equal (case, whitespace and trailing .;!? ignored)
  covered  not exact, but one span contains the claim (span at most 2.5x longer), the claim
           contains a span covering at least half of it (e.g. a 3-line gold span vs. 2-unit windows),
           or the claim part before " ... " is equal (the span joined a different footnote set)
  missed   neither; the PRE drop reason of the claim's first line is shown when there is one
IN_SCOPE/NV claims are what matter (recall); DISCARDED claims are reported for reference.
Claims with `needs_review: true` are skipped. Tune on the reserve set, measure gold once.

Usage:
  python3 retriever/segment_coverage.py golden/labeled/golden_set_ecgt_reserve.json
"""
import argparse
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from segment import Segmenter, _norm, load_config  # noqa: E402

ROOT = HERE.parent


def match(claim, spans):
    c = _norm(claim)
    texts = [_norm(s.text) for s in spans]
    if c in texts:
        return "exact"
    head = c.split(" ... ")[0]
    for t in texts:
        if (c in t and len(t) <= 2.5 * len(c)) or (t in c and len(t) >= 0.5 * len(c)):
            return "covered"
        if " ... " in c and t.split(" ... ")[0] == head:    # same claim, different footnote set
            return "covered"
    return "missed"


def drop_reason(seg, text, claim):
    first = claim.split(" ... ")[0].split("\n")[0].strip()
    for ln in seg._pre(seg._lines(text)):
        if first and first in ln.text:
            return ln.drop
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("labelled", nargs="+")
    ap.add_argument("--show", type=int, default=40, help="max misses to print")
    args = ap.parse_args()
    seg = Segmenter(load_config())

    for path in args.labelled:
        products = json.load(open(path, encoding="utf-8"))
        sources = {}
        res = collections.Counter()
        by_trigger = collections.defaultdict(collections.Counter)
        misses, n_spans, kinds = [], 0, collections.Counter()
        for p in products:
            src_file = ROOT / "golden" / p["source_file"]
            if src_file not in sources:
                sources[src_file] = json.load(open(src_file, encoding="utf-8"))
            rec = sources[src_file][p["source_index"]]
            spans = seg.segment(rec)
            n_spans += len(spans)
            kinds.update(s.kind for s in spans)
            for c in p["claims"]:
                if c.get("needs_review"):
                    continue
                pos = c["label"] != "DISCARDED"
                m = match(c["claim_text"], spans)
                res[(pos, m)] += 1
                if pos:
                    for t in c["triggers"]:
                        if t != "out_of_scope":
                            by_trigger[t][m] += 1
                    if m == "missed":
                        why = drop_reason(seg, rec.get(c["source_field"]) or "", c["claim_text"])
                        misses.append((p["product_id"], c["triggers"], c["claim_text"], why))

        n_pos = sum(v for (pos, _), v in res.items() if pos)
        n_neg = sum(v for (pos, _), v in res.items() if not pos)
        print(f"\n=== {path} ===")
        print(f"records {len(products)} · spans {n_spans} ({n_spans / len(products):.1f}/record) · {dict(kinds)}")
        for pos, n in ((True, n_pos), (False, n_neg)):
            name = "IN_SCOPE/NV" if pos else "DISCARDED  "
            e, cv, ms = (res[(pos, k)] for k in ("exact", "covered", "missed"))
            print(f"{name}: exact {e}/{n}  covered {cv}  missed {ms}  → recall {(e + cv) / max(n, 1):.1%}")
        print("per trigger (exact+covered / total):")
        for t, cnt in sorted(by_trigger.items(), key=lambda kv: (kv[1]["exact"] + kv[1]["covered"]) / sum(kv[1].values())):
            tot = sum(cnt.values())
            print(f"  {(cnt['exact'] + cnt['covered']) / tot:5.0%}  {t} ({tot})")
        if misses:
            print(f"missed IN_SCOPE/NV claims ({len(misses)}):")
            for pid, tr, text, why in misses[:args.show]:
                print(f"  [{pid}] {[t for t in tr if t != 'out_of_scope']} drop={why} {text[:110]!r}")


if __name__ == "__main__":
    main()
