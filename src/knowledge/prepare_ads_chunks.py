#!/usr/bin/env python3
"""
Converts data/raw/<file>.json product records ({"ean", "url", "description"})
into the chunk schema embed_e5.py expects ({"id", "title", "source", "text"}),
so product descriptions can be embedded in --mode query and compared against
the ecgt/ucpd legal passages with compare_e5.py.

Each ad becomes MULTIPLE chunks, one per claim-adjacent sentence (split via
src/extraction.py's _split_claim_sentences -- reused rather than duplicated,
so "claim-adjacent" means the same thing here as in the extraction pipeline),
not one chunk for the whole description. A whole ad description is mostly
nutrition tables, allergen warnings and storage instructions that are nearly
identical across unrelated products; concatenating all of that into one
embedding vector drowns out the one or two sentences that actually make a
claim, which is what was pushing every ad's embedding toward the same
generic, boilerplate-heavy region of embedding space regardless of what the
ad actually said (see compare_e5.py's docstring on hubness). Splitting
instead of concatenating sidesteps needing a precise claim-vs-boilerplate
classifier: a boilerplate sentence that happens to match a keyword just
becomes its own low-relevance chunk, rather than polluting the one vector
that represents the whole ad.

Each sentence chunk carries the ad's ean as "ad_id" (in addition to its own
per-sentence "id") so compare_e5.py can group sentence-level retrieval
results back up to the ad they came from. If NO sentence in a description
matches a keyword, the whole description is kept as a single fallback
chunk -- same "never silently drop a record" rule iter_records/
_prefilter_description already follow.

Records with an empty description are skipped, same as src/data.py's
iter_records.

Usage:
  python prepare_ads_chunks.py --file 06.25.json --out ads_chunks.json
  python embed_e5.py --input ads_chunks.json --output-dir ./embeddings --mode query
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.extraction import _split_claim_sentences  # noqa: E402

DATA_DIR = PROJECT_ROOT / "data" / "raw"


def _title_from_url(url: str, ean: str) -> str:
    """Best-effort human-readable title from the listing URL slug, e.g.
    ".../p/crescenza-200-g-conad--400012" -> "Crescenza 200 g conad".
    Falls back to the ean if the url is missing or has no usable slug."""
    slug = (url or "").rstrip("/").rsplit("/", 1)[-1]
    slug = slug.split("--")[0]
    name = re.sub(r"[-_]+", " ", slug).strip()
    return name.capitalize() if name else ean


def build_chunks(filename: str) -> List[dict]:
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
        title = _title_from_url(url, ean)
        sentences = _split_claim_sentences(description) or [description]
        for idx, sentence in enumerate(sentences):
            chunks.append({
                "id": f"{ean}_{idx}",
                "ad_id": ean,
                "title": title,
                "source": url,
                "text": sentence,
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
