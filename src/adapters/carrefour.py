"""Carrefour UCPD golden set -> canonical shapes. See golden/golden_set_carrefour_300_README.md.

Carrefour's raw schema is C4_*-prefixed spec-sheet fields, not a single
`description` string -- most are present on well under 100% of the 300
records (e.g. C4_MarketingProduct on 169/300, C4_LongDescription on 56/300),
so join_nonempty has to tolerate holes.
"""

from .common import build_canonical_gold_record, join_nonempty

# Same fields the golden set's own heuristic pre-scan used (see the README's
# "How this was built" step 1), plus C4_RecyclingInfo/C4_RecyclingMoreText
# since packaging/recycling claims (e.g. "plastica riciclata") show up there
# too, not just in C4_MarketingProduct.
_MARKETING_FIELDS = (
    "C4_MarketingProduct",
    "C4_MarketingBrand",
    "C4_NutritionClaims",
    "C4_LongDescription",
    "C4_SalesDenomination",
    "C4_Origin",
    "C4_PreparationInfo",
    "C4_RecyclingInfo",
    "C4_RecyclingMoreText",
)


def to_canonical_gold(record: dict) -> dict:
    return build_canonical_gold_record(record, retailer="carrefour")


def to_extraction_input(record: dict) -> dict:
    description = join_nonempty(*(record.get(f) for f in _MARKETING_FIELDS))
    return {**record, "description": description}
