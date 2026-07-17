#!/usr/bin/env python3
"""
Converts data/raw/<file>.json product records ({"ean", "url", "description"})
into the chunk schema embed_e5.py expects ({"id", "title", "source", "text"}),
so product descriptions can be embedded in --mode query and compared against
the ecgt/ucpd legal passages with compare_e5.py.

Records with an empty description are skipped, same as src/data.py's
iter_records.

Usage:
  python prepare_ads_chunks.py --file 06.25.json --out ads_chunks.json
  python embed_e5.py --input ads_chunks.json --output-dir ./embeddings --mode query
"""

import argparse
import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"


def _title_from_url(url: str, ean: str) -> str:
    """Best-effort human-readable title from the listing URL slug, e.g.
    ".../p/crescenza-200-g-conad--400012" -> "Crescenza 200 g conad".
    Falls back to the ean if the url is missing or has no usable slug."""
    slug = (url or "").rstrip("/").rsplit("/", 1)[-1]
    slug = slug.split("--")[0]
    name = re.sub(r"[-_]+", " ", slug).strip()
    return name.capitalize() if name else ean


def build_chunks(filename: str) -> list[dict]:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"No file found at {path}")

    with open(path, encoding="utf-8") as f:
        records = json.load(f)

    chunks = []
    for record in records:
        description = record.get("description")
        if not description or not description.strip():
            continue
        ean = record.get("ean") or ""
        url = record.get("url") or ""
        chunks.append({
            "id": ean,
            "title": _title_from_url(url, ean),
            "source": url,
            "text": description,
        })
    return chunks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", required=True, help="filename in data/raw/, e.g. 06.25.json")
    parser.add_argument("--out", required=True, type=Path, help="path to write the chunk-schema JSON")
    args = parser.parse_args()

    chunks = build_chunks(args.file)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(chunks, ensure_ascii=False, indent=2))
    print(f"Wrote {len(chunks)} chunks -> {args.out}")
