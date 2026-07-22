"""
Turns one retailer's golden set into the two canonical outputs evaluate.py
and extraction.py need:

  - --gold-out: canonical gold (one JSON array, same shape across retailers)
  - --extraction-out: same records + a `description` field, written into
    data/raw/ so the existing `python -m src.extraction --file <name>` CLI
    can run against it unmodified (src/data.py's iter_records requires a
    `description` key and only looks inside data/raw/).

Usage:
  python -m src.adapters.build --retailer coop \\
      --in golden/golden_set_coop_ucpd_250.json \\
      --gold-out golden/canonical/coop.json \\
      --extraction-out data/raw/coop_extraction_input.json
"""

import argparse
import json
from pathlib import Path

from . import carrefour, coop, eurospin, naturasi

ADAPTERS = {
    "coop": coop,
    "carrefour": carrefour,
    "eurospin": eurospin,
    "naturasi": naturasi,
}


def build(retailer: str, in_path: Path, gold_out: Path, extraction_out: Path) -> dict:
    adapter = ADAPTERS[retailer]
    records = json.loads(in_path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError(f"Expected a JSON array in {in_path}, got {type(records).__name__}")

    gold = [adapter.to_canonical_gold(r) for r in records]
    extraction_input = [adapter.to_extraction_input(r) for r in records]

    gold_out.parent.mkdir(parents=True, exist_ok=True)
    gold_out.write_text(json.dumps(gold, indent=2, ensure_ascii=False), encoding="utf-8")

    extraction_out.parent.mkdir(parents=True, exist_ok=True)
    extraction_out.write_text(
        json.dumps(extraction_input, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    empty_descriptions = sum(1 for r in extraction_input if not r.get("description", "").strip())
    all_claims = [c for g in gold for c in g["extracted_claims"]]
    low_confidence = [c for c in all_claims if c["legal_mapping_confidence"] == "low"]
    return {
        "total_records": len(records),
        "empty_descriptions": empty_descriptions,
        "total_claims": len(all_claims),
        "low_confidence_legal_mappings": len(low_confidence),
        "low_confidence_by_category": {
            cat: sum(1 for c in low_confidence if c["category"] == cat)
            for cat in sorted({c["category"] for c in low_confidence})
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--retailer", required=True, choices=sorted(ADAPTERS))
    parser.add_argument("--in", dest="in_path", required=True, help="path to the golden_set_*.json file")
    parser.add_argument("--gold-out", required=True, help="output path for canonical gold JSON")
    parser.add_argument(
        "--extraction-out", required=True,
        help="output path for the extraction-input JSON (put this in data/raw/ so "
        "`python -m src.extraction --file <basename>` can find it)",
    )
    args = parser.parse_args()

    stats = build(args.retailer, Path(args.in_path), Path(args.gold_out), Path(args.extraction_out))
    print(f"{args.retailer}: wrote {stats['total_records']} records to {args.gold_out} and {args.extraction_out}")
    if stats["empty_descriptions"]:
        print(
            f"WARNING: {stats['empty_descriptions']}/{stats['total_records']} records have an empty "
            f"synthesized description -- src/data.py's iter_records will skip these (they'll never "
            f"reach the model, and won't count as extraction misses since there was nothing to extract from)."
        )
    if stats["low_confidence_legal_mappings"]:
        print(
            f"NOTE: {stats['low_confidence_legal_mappings']}/{stats['total_claims']} claims got a "
            f"low-confidence gold_legal_chunk_id mapping (see src/adapters/legal_mapping.py) -- "
            f"by category: {stats['low_confidence_by_category']}"
        )
