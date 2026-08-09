"""Coop UCPD golden set -> canonical shapes. See golden/golden_set_coop_ucpd_250_README.md."""

from .common import build_canonical_gold_record, join_nonempty


def to_canonical_gold(record: dict) -> dict:
    return build_canonical_gold_record(record, retailer="coop")


def to_extraction_input(record: dict) -> dict:
    """Coop already has a `description` field, but it's null on some records
    (the marketing text lives in `features` instead -- see e.g. record 0 of
    golden_set_coop_ucpd_250.json, where `description` is null and the
    "100% Naturale" / antioxidant claims are in `features`).

    `producer_info` also has to be joined in, not just description+features:
    measured against the full 250-product golden set, 178/250 products
    (71%) have real marketing content in `producer_info` that appears
    NOWHERE else -- e.g. "Pasticcini lunette"'s heritage/superiority claims
    ("la tradizionale, autentica pastafrolla...", "dal 1820 la famiglia
    Grondona garantisce...") and "Infuso di zenzero e curcuma"'s
    environmental/digestive-health claims are entirely in producer_info.
    Missing it silently starved extraction of most of a product's real
    marketing text on the majority of records -- this was originally missed
    because the one documented justification example above ("100%
    Naturale") happened to already be in `features`, which masked the gap.

    Still NOT fully complete even with this fix: 159/562 gold claim_texts
    (28%) aren't found verbatim in description+features+producer_info at
    all. ~71 of those trace to `certifications`/`recycling_other` (trust-
    mark/eco-label names like "Coop per l'ambiente", "VIVI VERDE") -- left
    out of this join deliberately, since that field also carries exactly
    the mandatory-disclosure/packaging-badge boilerplate
    src/extraction.py's _MANDATORY_DISCLOSURE_PATTERNS exists to filter
    OUT, so blindly joining it risks reintroducing that noise rather than
    fixing a gap. ~88 more are unaccounted for in any field checked so far.
    Treat this as a known remaining gap, not something this fix resolves.
    """
    description = join_nonempty(
        record.get("description"), record.get("features"), record.get("producer_info")
    )
    return {**record, "description": description}
