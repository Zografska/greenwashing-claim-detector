"""Eurospin UCPD golden set -> canonical shapes. See golden/golden_set_eurospin_200_README.md.

Unlike NaturaSì, Eurospin has real marketing prose -- just spread across
several optional fields instead of one `description` (e.g. `marketing_text`
present on only 82/200 records, `other_claim` on 91/200)."""

from .common import build_canonical_gold_record, join_nonempty

_MARKETING_FIELDS = ("sales_description", "marketing_text", "other_claim", "further_description")


def to_canonical_gold(record: dict) -> dict:
    return build_canonical_gold_record(record, retailer="eurospin")


def to_extraction_input(record: dict) -> dict:
    description = join_nonempty(*(record.get(f) for f in _MARKETING_FIELDS))
    return {**record, "description": description}
