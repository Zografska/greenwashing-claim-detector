#!/usr/bin/env python3
"""
extract_fields.py

Generic extractor: pulls a chosen set of fields out of every JSON file in a
folder (each file expected to contain a list of product records, or a single
record dict) and writes them out as one CSV or JSON file, sorted by a chosen
field.

Usage:
    python3 extract_fields.py <input_dir> [options]

Examples:
    # Default fields (C4_MarketingBrand, name, url, C4_ManufacturesAddress),
    # skips run_summary.json, sorts by "name", writes extracted.csv
    python3 extract_fields.py ./19.07_10

    # Custom fields, custom output path, custom sort field
    python3 extract_fields.py ./19.07_10 \\
        --fields C4_MarketingBrand,name,url,C4_ManufacturesAddress \\
        --output brands.csv \\
        --sort-by name

    # JSON output instead of CSV
    python3 extract_fields.py ./19.07_10 --format json --output brands.json

    # Exclude extra files besides the default run_summary.json
    python3 extract_fields.py ./19.07_10 --exclude run_summary.json,run_failures.json
"""

import argparse
import csv
import json
import sys
from pathlib import Path


DEFAULT_FIELDS = ["C4_MarketingBrand", "name", "url", "C4_ManufacturesAddress"]
DEFAULT_EXCLUDE = ["run_summary.json"]


def parse_args():
    p = argparse.ArgumentParser(
        description="Extract a fixed set of fields from every JSON file in a folder."
    )
    p.add_argument("input_dir", type=Path, help="Folder containing the .json files")
    p.add_argument(
        "--fields",
        default=",".join(DEFAULT_FIELDS),
        help=f"Comma-separated list of fields to extract (default: {','.join(DEFAULT_FIELDS)})",
    )
    p.add_argument(
        "--exclude",
        default=",".join(DEFAULT_EXCLUDE),
        help=f"Comma-separated list of filenames (in input_dir) to skip (default: {','.join(DEFAULT_EXCLUDE)})",
    )
    p.add_argument(
        "--sort-by",
        default="name",
        help="Field to sort the output rows by, case-insensitively (default: name). "
        "Pass an empty string to skip sorting.",
    )
    p.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="Output format (default: csv)",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file path (default: extracted.<format> inside input_dir)",
    )
    p.add_argument(
        "--recursive",
        action="store_true",
        help="Also look for .json files in subfolders of input_dir",
    )
    return p.parse_args()


def load_records(json_path: Path):
    """Load one JSON file and normalize it to a list of dicts."""
    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"  ! skipping {json_path.name}: could not read/parse ({e})", file=sys.stderr)
        return []

    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def main():
    args = parse_args()

    input_dir: Path = args.input_dir
    if not input_dir.is_dir():
        sys.exit(f"Error: {input_dir} is not a folder")

    fields = [f.strip() for f in args.fields.split(",") if f.strip()]
    exclude = {f.strip() for f in args.exclude.split(",") if f.strip()}
    sort_by = args.sort_by.strip()

    pattern = "**/*.json" if args.recursive else "*.json"
    json_files = sorted(
        f for f in input_dir.glob(pattern) if f.name not in exclude
    )

    if not json_files:
        sys.exit(f"No .json files found in {input_dir} (after excluding {sorted(exclude)})")

    rows = []
    for jf in json_files:
        records = load_records(jf)
        for rec in records:
            row = {field: rec.get(field, "") for field in fields}
            rows.append(row)
        print(f"  {jf.name}: {len(records)} record(s)")

    if sort_by:
        if sort_by not in fields:
            print(
                f"  ! warning: sort field '{sort_by}' is not one of the extracted "
                f"fields {fields}; sorting anyway",
                file=sys.stderr,
            )
        rows.sort(key=lambda r: str(r.get(sort_by, "") or "").casefold())

    output = args.output
    if output is None:
        output = input_dir / f"extracted.{args.format}"

    if args.format == "csv":
        with output.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    else:
        with output.open("w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"\nWrote {len(rows)} row(s) to {output}")


if __name__ == "__main__":
    main()
