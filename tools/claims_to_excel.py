"""Export claims from a product JSON file to an Excel sheet.

One row per claim: product_id, claim_text, label, confidence.
Only IN_SCOPE and NEEDS_VERIFICATION claims are kept.

Input: a JSON list of products (or a .jsonl file, one product per line),
each with `product_id` and `claims[]`.

Usage:
    python3 tools/claims_to_excel.py golden/labeled/golden_set_ecgt_100.json
    python3 tools/claims_to_excel.py golden/clean/coop_claims.json -o coop_claims.xlsx
"""
import argparse
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

KEEP_LABELS = {"IN_SCOPE", "NEEDS_VERIFICATION"}
COLUMNS = ["product_id", "claim_text", "label", "confidence"]


def load_products(path):
    text = Path(path).read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return json.loads(text)


def claim_rows(products):
    for product in products:
        for claim in product.get("claims") or []:
            if claim.get("label") in KEEP_LABELS:
                yield [product.get("product_id"), claim.get("claim_text"),
                       claim.get("label"), claim.get("confidence")]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input", type=Path)
    ap.add_argument("-o", "--output", type=Path,
                    help="output .xlsx (default: input path with .xlsx suffix)")
    args = ap.parse_args()
    output = args.output or args.input.with_suffix(".xlsx")

    wb = Workbook()
    ws = wb.active
    ws.title = "claims"
    ws.append(COLUMNS)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    n = 0
    for row in claim_rows(load_products(args.input)):
        ws.append(row)
        n += 1

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for col, width in zip("ABCD", (18, 90, 22, 12)):
        ws.column_dimensions[col].width = width

    wb.save(output)
    print(f"wrote {n} claims to {output}")


if __name__ == "__main__":
    main()
