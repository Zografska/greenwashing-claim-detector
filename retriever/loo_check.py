"""Leave-one-out sanity check for the ECGT anchor set.

Each anchor is used as a query against all other anchors. It reports:
  - polarity accuracy: does margin = max_sim(pos) - max_sim(neg) have the right sign?
  - category accuracy: is the nearest neighbour in the same category?
    (a proxy for how useful retrieved anchors will be as Pass 2 few-shot)
  - the closest cross-polarity pairs: the boundaries the model finds hardest

Usage:
  python loo_check.py --anchors anchors.jsonl --models charngram
  python loo_check.py --anchors anchors.jsonl \
      --models intfloat/multilingual-e5-base BAAI/bge-m3 \
               sentence-transformers/paraphrase-multilingual-mpnet-base-v2
  add --csv loo_results.csv to save per-anchor rows.

Caveat: anchors from the same template (e.g. three «X per l'ambiente») make
LOO optimistic. Real accuracy comes from the gold span set, not from this.
"""
import argparse
import csv
import json
import zlib

import numpy as np

# Prefixes some models expect. e5 uses "query: " on both sides for symmetric tasks.
PREFIXES = {"multilingual-e5": "query: "}


def load_anchors(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def charngram_encode(texts, dim=2 ** 16, n_range=(3, 5)):
    """Offline baseline: hashed character n-grams, L2-normalized."""
    X = np.zeros((len(texts), dim), dtype=np.float32)
    for i, t in enumerate(texts):
        s = f" {t.lower()} "
        for n in range(n_range[0], n_range[1] + 1):
            for j in range(len(s) - n + 1):
                X[i, zlib.crc32(s[j:j + n].encode()) % dim] += 1.0
    X /= np.linalg.norm(X, axis=1, keepdims=True) + 1e-9
    return X


def encode(texts, model_name):
    if model_name == "charngram":
        return charngram_encode(texts)
    from sentence_transformers import SentenceTransformer
    prefix = next((p for k, p in PREFIXES.items() if k in model_name), "")
    model = SentenceTransformer(model_name)
    return model.encode([prefix + t for t in texts], normalize_embeddings=True,
                        batch_size=32, show_progress_bar=False)


def run(anchors, model_name, n_hard=15):
    E = encode([a["text"] for a in anchors], model_name)
    S = E @ E.T
    np.fill_diagonal(S, -np.inf)                    # exclude self
    is_pos = np.array([a["polarity"] == "pos" for a in anchors])
    cats = np.array([a["category"] for a in anchors])

    rows, pol_ok, cat_ok = [], 0, 0
    for i, a in enumerate(anchors):
        best_pos, best_neg = S[i, is_pos].max(), S[i, ~is_pos].max()
        margin = float(best_pos - best_neg)
        p_ok = (margin > 0) == is_pos[i]
        nn = int(np.argmax(S[i]))
        c_ok = cats[nn] == cats[i]
        pol_ok += p_ok
        cat_ok += c_ok
        rows.append(dict(model=model_name, id=a["id"], polarity=a["polarity"],
                         category=a["category"], margin=round(margin, 4),
                         polarity_ok=bool(p_ok), nn_id=anchors[nn]["id"],
                         nn_text=anchors[nn]["text"], category_ok=bool(c_ok)))

    n = len(anchors)
    n_pos, n_neg = int(is_pos.sum()), int((~is_pos).sum())
    pos_kept = sum(r["polarity_ok"] for r in rows if r["polarity"] == "pos")
    neg_rej = sum(r["polarity_ok"] for r in rows if r["polarity"] == "neg")
    print(f"\n=== {model_name} ===")
    print(f"positives kept:    {pos_kept}/{n_pos} = {pos_kept / n_pos:.1%}   (gate: >= 85%)")
    print(f"negatives rejected: {neg_rej}/{n_neg} = {neg_rej / n_neg:.1%}   (cost metric, no gate)")
    print(f"polarity accuracy: {pol_ok}/{n} = {pol_ok / n:.1%}")
    print(f"category accuracy: {cat_ok}/{n} = {cat_ok / n:.1%}")

    fails = [r for r in rows if not r["polarity_ok"]]
    if fails:
        print(f"\npolarity failures ({len(fails)}):")
        for r in sorted(fails, key=lambda r: -abs(r["margin"])):
            print(f"  [{r['polarity']}:{r['category']}] {anchors[[a['id'] for a in anchors].index(r['id'])]['text']!r}")
            print(f"      margin={r['margin']:+.3f}  nn=[{r['nn_id']}] {r['nn_text']!r}")

    # closest cross-polarity pairs
    cross = S.copy()
    cross[np.equal.outer(is_pos, is_pos)] = -np.inf
    iu = np.triu_indices(n, k=1)
    order = np.argsort(-cross[iu])[:n_hard]
    print(f"\nclosest pos/neg pairs (top {n_hard}):")
    for k in order:
        i, j = iu[0][k], iu[1][k]
        print(f"  {cross[i, j]:.3f}  {anchors[i]['text']!r}  <->  {anchors[j]['text']!r}")

    # per-category polarity accuracy, weakest first
    print("\nper-category polarity accuracy (weakest first):")
    per = {}
    for r in rows:
        per.setdefault((r["polarity"], r["category"]), []).append(r["polarity_ok"])
    for (p, c), v in sorted(per.items(), key=lambda kv: np.mean(kv[1])):
        print(f"  {np.mean(v):5.0%}  {p}:{c}  (n={len(v)})")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchors", default="anchors.jsonl")
    ap.add_argument("--models", nargs="+", default=["charngram"])
    ap.add_argument("--csv", help="write per-anchor results here")
    args = ap.parse_args()

    anchors = load_anchors(args.anchors)
    all_rows = []
    for m in args.models:
        all_rows += run(anchors, m)
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(all_rows[0]))
            w.writeheader()
            w.writerows(all_rows)
        print(f"\nwrote {len(all_rows)} rows to {args.csv}")


if __name__ == "__main__":
    main()
