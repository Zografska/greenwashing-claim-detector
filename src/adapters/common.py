"""
Shared helpers for the per-retailer adapters in this package. Each retailer's
golden set carries its own raw schema (see coop.py/carrefour.py/eurospin.py/
naturasi.py) but needs to end up in one of two canonical shapes:

  - canonical gold record: for src/evaluate.py, so it doesn't have to know
    about retailer-specific fields (modifiers presence, hard_no_reason vs.
    bucket_review_flag, etc.)
  - extraction-input record: the *same* original record plus a `description`
    field, so the existing, unmodified `python -m src.extraction --file ...`
    CLI (via src/data.py's `iter_records`, which hard-requires `description`)
    can run against it without any changes to src/data.py or src/extraction.py.
"""


def _as_text(part) -> str:
    """Most fields are a plain string, but at least one Coop record (product
    671255) has `description` as a list of bullet strings instead -- join
    those into one string rather than crash or silently drop the content."""
    if isinstance(part, list):
        return "\n".join(str(p) for p in part if p)
    return str(part) if part is not None else ""


def join_nonempty(*parts, sep: str = "\n\n") -> str:
    """Join whichever of these text fields are actually present and non-blank.
    Retailers leave most of their optional fields null/missing per-record
    (e.g. Carrefour's C4_MarketingProduct is present on only 169/300 records),
    so this has to tolerate holes rather than assume every field is there."""
    texts = (_as_text(p).strip() for p in parts)
    return sep.join(t for t in texts if t)


def normalize_claim(claim: dict) -> dict:
    """One gold claim -> canonical shape. `modifiers` and `irrelevant_subreason`
    are only present on some retailers/claims (see field-presence counts in
    the plan) -- default them rather than let evaluate.py branch per-retailer."""
    return {
        "claim_text": claim.get("claim_text", ""),
        "category": claim.get("category"),
        "risk_level": claim.get("risk_level"),
        "modifiers": claim.get("modifiers") or [],
        "irrelevant_subreason": claim.get("irrelevant_subreason"),
    }


def build_canonical_gold_record(
    record: dict, *, retailer: str, product_id_field: str = "product_id"
) -> dict:
    """Common shape for the canonical gold record. Retailer-specific extras
    (bucket_review_flag, hard_no_reason, bucket_correction, extraction_note,
    ...) are carried through verbatim under `extras` instead of being forced
    into the canonical shape or silently dropped."""
    known = {
        "origin_file",
        "golden_bucket",
        "product_id",
        "ean",
        "name",
        "extracted_claims",
    }
    extras = {k: v for k, v in record.items() if k not in known and k != product_id_field}
    return {
        "origin_retailer": retailer,
        "origin_file": record.get("origin_file"),
        "product_id": str(record.get(product_id_field) or record.get("ean") or ""),
        "ean": record.get("ean"),
        "name": record.get("name"),
        "golden_bucket": record.get("golden_bucket"),
        "extracted_claims": [normalize_claim(c) for c in record.get("extracted_claims", [])],
        "extras": extras,
    }
