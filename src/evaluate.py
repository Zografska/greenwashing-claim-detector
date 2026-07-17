"""
Two separate scores, don't blend them:
1. extraction quality: did we find the right claim spans (relaxed overlap,
   not exact string match, wording will vary from gold)
2. category accuracy: of the claims we got right, did we label them right

Run with:
    python -m src.evaluate --predictions results/rag_only/predictions.jsonl --gold data/annotations/test.jsonl
"""

import argparse
import json


def load_jsonl(path: str) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def extraction_prf(predictions: list[dict], gold: list[dict], overlap_threshold: float = 0.5):
    """
    TODO: relaxed span-overlap matching (e.g. token-level Jaccard >= threshold
    counts as a match) per source document, then aggregate precision/recall/F1.
    """
    raise NotImplementedError


def category_accuracy(predictions: list[dict], gold: list[dict]):
    """
    TODO: accuracy (or per-category F1 if you end up multi-label) restricted
    to claims that were correctly extracted, per extraction_prf's matching.
    """
    raise NotImplementedError


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--gold", required=True)
    args = parser.parse_args()

    preds = load_jsonl(args.predictions)
    gold = load_jsonl(args.gold)

    print("extraction:", extraction_prf(preds, gold))
    print("category accuracy:", category_accuracy(preds, gold))
