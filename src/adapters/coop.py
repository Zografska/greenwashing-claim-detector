"""Coop UCPD golden set -> canonical shapes. See golden/golden_set_coop_ucpd_250_README.md."""

from .common import build_canonical_gold_record, join_nonempty


def to_canonical_gold(record: dict) -> dict:
    return build_canonical_gold_record(record, retailer="coop")


def to_extraction_input(record: dict) -> dict:
    """Coop already has a `description` field, but it's null on some records
    (the marketing text lives in `features` instead -- see e.g. record 0 of
    golden_set_coop_ucpd_250.json, where `description` is null and the
    "100% Naturale" / antioxidant claims are in `features`). Join both rather
    than trust `description` alone."""
    description = join_nonempty(record.get("description"), record.get("features"))
    return {**record, "description": description}
