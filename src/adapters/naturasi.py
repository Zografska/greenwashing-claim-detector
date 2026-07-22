"""NaturaSì UCPD golden set -> canonical shapes. See golden/golden_set_naturasi_200_README.md.

NaturaSì has NO prose field at all -- no `description`, no `C4_MarketingProduct`
equivalent, just structured regulatory fields (`certifications` tag array,
`legal_name`, `quality_recipe`, `table_nutrition`, ...). The gold set's own
claim signal here is almost entirely the `certifications` array (see the
README's "How this was built"), so `to_extraction_input` synthesizes a
pseudo-description by labeling and joining certifications/legal_name/
quality_recipe -- there's no way to avoid this without changing what
src/extraction.py's prompt expects as input.

This is flagged as an open question in the plan, not a settled design:
src/extraction.py's CLAIM_KEYWORDS prefilter and prompt were built for
sentence-shaped prose, not a label:value tag list, and have never been
tested against this shape of input. Treat extraction results on this
retailer as an experiment to evaluate, not an assumption that it'll work.
"""

from .common import build_canonical_gold_record, join_nonempty


def to_canonical_gold(record: dict) -> dict:
    return build_canonical_gold_record(record, retailer="naturasi")


def to_extraction_input(record: dict) -> dict:
    certifications = record.get("certifications") or []
    parts = [
        f"Certificazioni: {', '.join(certifications)}" if certifications else None,
        f"Denominazione legale: {record['legal_name']}" if record.get("legal_name") else None,
        f"Ricetta: {record['quality_recipe']}" if record.get("quality_recipe") else None,
    ]
    description = join_nonempty(*parts)
    return {**record, "description": description}
