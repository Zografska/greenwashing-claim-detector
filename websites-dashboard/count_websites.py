#!/usr/bin/env python3
"""
Count websites in the `website_address` column and total documents in a folder.

Usage (from inside websites-dashboard):
    python count_websites.py            # scans the current folder
    python count_websites.py path/to/folder

Reads every .csv, .tsv, .txt, .xlsx and .xls file in the folder (recursively).
"""
import sys
from pathlib import Path

import pandas as pd

COLUMN = "website_address"
EXTENSIONS = {".csv", ".tsv", ".txt", ".xlsx", ".xls"}
MISSING = {"", "na", "n/a", "n.a.", "nan", "none", "null", "-"}


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path, dtype=str)
    # sep=None lets pandas detect comma / semicolon / tab automatically
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(path, sep=None, engine="python", dtype=str,
                               keep_default_na=False, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode {path}")


def normalize(url: str) -> str:
    u = url.strip().lower()
    for prefix in ("https://", "http://"):
        if u.startswith(prefix):
            u = u[len(prefix):]
    if u.startswith("www."):
        u = u[4:]
    return u.rstrip("/")


def main() -> None:
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    files = sorted(p for p in folder.rglob("*")
                   if p.is_file() and p.suffix.lower() in EXTENSIONS
                   and p.name != Path(__file__).name)

    total_files = len(files)
    total_records = 0
    total_with_site = 0
    unique_sites = set()

    print(f"Scanning: {folder.resolve()}\n")
    print(f"{'file':<45} {'records':>9} {'websites':>9}")
    print("-" * 65)

    for path in files:
        try:
            df = read_table(path)
        except Exception as e:
            print(f"{path.name:<45} skipped ({e})")
            continue

        df.columns = [str(c).strip().lower() for c in df.columns]
        n_records = len(df)
        total_records += n_records

        if COLUMN not in df.columns:
            print(f"{path.name:<45} {n_records:>9} {'no column':>9}")
            continue

        sites = df[COLUMN].fillna("").astype(str).str.strip()
        present = sites[~sites.str.lower().isin(MISSING)]
        total_with_site += len(present)
        unique_sites.update(normalize(s) for s in present)

        print(f"{path.name:<45} {n_records:>9} {len(present):>9}")

    print("-" * 65)
    print(f"Documents (files) found:        {total_files}")
    print(f"Total records (rows):           {total_records}")
    print(f"Records with a website:         {total_with_site}")
    print(f"Records without a website:      {total_records - total_with_site}")
    print(f"Unique websites (normalized):   {len(unique_sites)}")
    if total_records:
        print(f"Website coverage:               {total_with_site / total_records:.1%}")


if __name__ == "__main__":
    main()
