"""
Scores src/extraction.py's predictions against the canonical golden sets
produced by src/adapters/build.py (golden/canonical/<retailer>.json).

Two separate scores, don't blend them:
1. extraction quality: did we find the right claim spans (relaxed overlap,
   not exact string match, wording will vary from gold)
2. category accuracy: of the claims we got right, did we label them right

A third, bonus score (risk-level agreement) is reported separately again --
see RISK LEVEL below.

Important asymmetries this scorer has to account for, not paper over:

- src/extraction.py's `_validate_claims` deterministically drops every
  risk_level=LOW claim by policy, regardless of what the model decided.
  Gold sets are full of LOW-risk claims (all `irrelevant_claim` entries,
  plus most composition/nutrition-content claims) that will therefore
  NEVER appear in predictions -- that's expected behavior, not a miss.
  extraction_prf only scores gold claims with risk_level != "LOW"
  ("flaggable" claims) and reports the excluded count so it isn't silently
  baked into a lower recall number.

- src/extraction.py's output taxonomy (6 broad categories) is coarser than
  the golden sets' taxonomy (11 categories actually observed across all 4
  retailers -- see GOLD_TO_COARSE below). Some gold categories
  (misleading_superiority_or_absolute_claim, misleading_endorsement_claim,
  unfair_comparison, irrelevant_claim) have NO corresponding extraction.py
  category at all -- there's no honest way to score "did the model pick the
  right category" for a claim type the schema can't express. These are
  UNMAPPED: excluded from category_accuracy's denominator, with the excluded
  count reported rather than hidden. Symmetrically, extraction.py's
  PRICE_VALUE_CLAIM and SAFETY_INSTRUCTION_CLAIM have no gold category
  feeding into them at all in these 4 sets -- predictions in those two
  buckets can't be validated against this gold data either way.

Run with (see src/adapters/build.py to produce the --gold file first):
    python -m src.evaluate --predictions results/coop/predictions.json \\
        --gold golden/canonical/coop.json

Multiple retailers in one call (pooled score + per-retailer breakdown):
    python -m src.evaluate \\
        --predictions results/coop/predictions.json results/carrefour/predictions.json \\
        --gold golden/canonical/coop.json golden/canonical/carrefour.json
"""

import argparse
import json
import re
from typing import List, Set, Tuple

# --- category taxonomy mapping --------------------------------------------
# Gold's 11 observed categories (a 12th, unauthorized_or_borderline_medicinal_claim,
# has zero hits across all 4 golden sets per their READMEs, included here for
# completeness) -> extraction.py's 6-category RESPONSE_SCHEMA enum.
# None means "no honest mapping exists" -- see module docstring.
GOLD_TO_COARSE = {
    "environmental_unsubstantiated": "ENVIRONMENTAL_CLAIM",
    "offset_based_neutrality": "ENVIRONMENTAL_CLAIM",
    "unsubstantiated_health_or_efficacy_claim": "NUTRITION_HEALTH_CLAIM",
    "unauthorized_or_borderline_medicinal_claim": "NUTRITION_HEALTH_CLAIM",
    "nutrition_content_claim": "NUTRITION_HEALTH_CLAIM",
    "misleading_composition_or_ingredient_claim": "COMPOSITION_CLAIM",
    "misleading_authenticity_or_origin_claim": "ORIGIN_PROVENANCE_CLAIM",
    # Closest available bucket: fake_or_unverified_label is about whether a
    # claimed certification/label/scheme is real -- an authenticity question,
    # same shape as misleading_authenticity_or_origin_claim. An editorial
    # call, not an obvious 1:1 fit -- revisit if it doesn't hold up in practice.
    "fake_or_unverified_label": "ORIGIN_PROVENANCE_CLAIM",
    # No honest match in extraction.py's 6-category schema:
    "misleading_superiority_or_absolute_claim": None,
    "misleading_endorsement_claim": None,
    "unfair_comparison": None,
    "irrelevant_claim": None,
}


def load_json(path: str) -> List[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _tokens(text: str) -> Set[str]:
    return set(_TOKEN_RE.findall((text or "").lower()))


def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _match_claims(pred_claims: List[dict], gold_claims: List[dict], overlap_threshold: float):
    """Greedy one-to-one matching between a single record's predicted and
    gold claims by token-level Jaccard overlap on claim_text. Returns
    (matches, unmatched_gold, unmatched_pred), where matches is a list of
    (gold_claim, pred_claim) pairs."""
    pred_tokens = [_tokens(p.get("claim_text", "")) for p in pred_claims]
    gold_tokens = [_tokens(g.get("claim_text", "")) for g in gold_claims]

    scored = []
    for gi, gt in enumerate(gold_tokens):
        for pi, pt in enumerate(pred_tokens):
            score = _jaccard(gt, pt)
            if score >= overlap_threshold:
                scored.append((score, gi, pi))
    scored.sort(reverse=True)

    used_gold, used_pred = set(), set()
    matches = []
    for score, gi, pi in scored:
        if gi in used_gold or pi in used_pred:
            continue
        used_gold.add(gi)
        used_pred.add(pi)
        matches.append((gold_claims[gi], pred_claims[pi]))

    unmatched_gold = [g for gi, g in enumerate(gold_claims) if gi not in used_gold]
    unmatched_pred = [p for pi, p in enumerate(pred_claims) if pi not in used_pred]
    return matches, unmatched_gold, unmatched_pred


def _pair_records(predictions: List[dict], gold: List[dict]) -> List[Tuple[dict, dict]]:
    """Pair by ean (both canonical gold and extraction.py's predictions carry
    it), falling back to product_id/index. Gold records with no matching
    prediction (e.g. skipped by src/data.py for an empty description) are
    paired with an empty claims list rather than dropped, so they still
    count as recall misses instead of silently vanishing from the score."""
    pred_by_ean = {p.get("ean"): p for p in predictions if p.get("ean")}
    pairs = []
    for g in gold:
        p = pred_by_ean.get(g.get("ean")) or {"claims": []}
        pairs.append((p, g))
    return pairs


def extraction_prf(predictions: List[dict], gold: List[dict], overlap_threshold: float = 0.5) -> dict:
    """Relaxed span-overlap P/R/F1, restricted to gold claims with
    risk_level != "LOW" (see module docstring for why)."""
    tp = fp = fn = 0
    excluded_low = 0

    for pred_record, gold_record in _pair_records(predictions, gold):
        pred_claims = pred_record.get("claims", [])
        flaggable = [c for c in gold_record.get("extracted_claims", []) if c.get("risk_level") != "LOW"]
        excluded_low += len(gold_record.get("extracted_claims", [])) - len(flaggable)

        matches, unmatched_gold, unmatched_pred = _match_claims(pred_claims, flaggable, overlap_threshold)
        tp += len(matches)
        fn += len(unmatched_gold)
        fp += len(unmatched_pred)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "excluded_low_risk_gold_claims": excluded_low,
    }


def category_accuracy(predictions: List[dict], gold: List[dict], overlap_threshold: float = 0.5) -> dict:
    """Restricted to claims extraction_prf already matched (a wrong span
    can't have a "right" category), and further restricted to matched pairs
    whose gold category has an entry in GOLD_TO_COARSE that isn't None --
    see module docstring."""
    correct = 0
    considered = 0
    excluded_unmapped = 0

    for pred_record, gold_record in _pair_records(predictions, gold):
        pred_claims = pred_record.get("claims", [])
        flaggable = [c for c in gold_record.get("extracted_claims", []) if c.get("risk_level") != "LOW"]
        matches, _, _ = _match_claims(pred_claims, flaggable, overlap_threshold)

        for gold_claim, pred_claim in matches:
            coarse = GOLD_TO_COARSE.get(gold_claim.get("category"))
            if coarse is None:
                excluded_unmapped += 1
                continue
            considered += 1
            if pred_claim.get("category") == coarse:
                correct += 1

    accuracy = correct / considered if considered else 0.0
    return {
        "accuracy": round(accuracy, 4),
        "correct": correct,
        "considered": considered,
        "excluded_unmapped_gold_category": excluded_unmapped,
    }


def risk_level_agreement(predictions: List[dict], gold: List[dict], overlap_threshold: float = 0.5) -> dict:
    """Bonus metric, kept separate from the two above: of the matched claims,
    did predicted risk_level (HIGH/MEDIUM) agree with gold's? Both sides
    exclude LOW by construction (extraction.py never emits it; gold LOW
    claims are excluded from matching), so this is effectively HIGH-vs-MEDIUM
    agreement, not a 3-way comparison."""
    agree = total = 0
    for pred_record, gold_record in _pair_records(predictions, gold):
        pred_claims = pred_record.get("claims", [])
        flaggable = [c for c in gold_record.get("extracted_claims", []) if c.get("risk_level") != "LOW"]
        matches, _, _ = _match_claims(pred_claims, flaggable, overlap_threshold)
        for gold_claim, pred_claim in matches:
            total += 1
            if pred_claim.get("risk_level") == gold_claim.get("risk_level"):
                agree += 1
    return {
        "agreement": round(agree / total, 4) if total else 0.0,
        "agreed": agree,
        "considered": total,
    }


def evaluate(predictions: List[dict], gold: List[dict], overlap_threshold: float = 0.5) -> dict:
    return {
        "n_gold_records": len(gold),
        "n_prediction_records": len(predictions),
        "extraction_prf": extraction_prf(predictions, gold, overlap_threshold),
        "category_accuracy": category_accuracy(predictions, gold, overlap_threshold),
        "risk_level_agreement": risk_level_agreement(predictions, gold, overlap_threshold),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True, nargs="+", help="one or more results/<retailer>/predictions.json files")
    parser.add_argument("--gold", required=True, nargs="+", help="one or more golden/canonical/<retailer>.json files, same order as --predictions")
    parser.add_argument("--overlap-threshold", type=float, default=0.5)
    args = parser.parse_args()

    if len(args.predictions) != len(args.gold):
        raise SystemExit("--predictions and --gold must have the same number of files, paired by position")

    all_preds, all_gold = [], []
    for pred_path, gold_path in zip(args.predictions, args.gold):
        preds = load_json(pred_path)
        golds = load_json(gold_path)
        all_preds.extend(preds)
        all_gold.extend(golds)

        retailer = golds[0].get("origin_retailer", gold_path) if golds else gold_path
        print(f"=== {retailer} ({gold_path}) ===")
        print(json.dumps(evaluate(preds, golds, args.overlap_threshold), indent=2))
        print()

    if len(args.gold) > 1:
        print("=== pooled across all retailers ===")
        print(json.dumps(evaluate(all_preds, all_gold, args.overlap_threshold), indent=2))
