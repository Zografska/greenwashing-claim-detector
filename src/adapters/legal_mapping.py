"""
Maps a golden-set claim (category + modifiers, already hand-labeled per
golden/CHANGELOG.md and the retailer READMEs) to a specific chunk id in the
56-chunk ECGT+UCPD legal corpus (src/knowledge/chunks/{ecgt,ucpd}.json),
so retrieval/rerank against that corpus can be scored the same way
src/knowledge/evaluate_matches.py already scores the 25.06 gold set.

Read the full corpus before changing this table. Most golden-set categories
do NOT correspond to one of the 31 UCPD Annex I blacklist points or 21 ECGT
definitions -- those are narrow, enumerated practices (fake trust marks,
pyramid schemes, false cure claims, false endorsement...). Authenticity/
origin, superiority, composition, and most nutrition-content claims are
assessed under the GENERAL UCPD Art. 6 (misleading actions) / Art. 7
(misleading omissions) test instead, and get mapped there rather than left
null -- legally accurate, but it means retrieval evaluation on that
(majority) slice is really "did it find the generic catch-all," not
fine-grained discrimination. There is also no Comparative Advertising
Directive (2006/114/EC) chunk in this corpus at all, so `unfair_comparison`
has no good fit -- a real corpus coverage gap, not patched over here.
"""

import re

# Sustainability/environmental vocabulary, used only to disambiguate
# fake_or_unverified_label (see _fake_label_chunk below). Deliberately a
# narrower list than src/extraction.py's CLAIM_KEYWORDS -- this only needs
# to catch "is this label environmental in flavor," not the full UCPD scope.
# Includes "vivi verde" (Coop's own eco-sub-brand wordmark) and standalone
# "green" -- but NOT bare "verde" alone, which is often just a food color
# ("fagiolini verdi") with nothing to do with sustainability.
_SUSTAINABILITY_WORDS = re.compile(
    r"sostenibil|ambiental|biodivers|filiera sostenibile|eco[- ]?friendly|"
    r"impatto ambientale|carbon|co2|emissioni|vivi verde|\bgreen\b",
    re.IGNORECASE,
)


def _fake_label_chunk(claim: dict) -> str:
    """fake_or_unverified_label spans both environmental sustainability marks
    (ECGT_AnnexI_2_bis: "esibire un marchio di sostenibilità... senza sistema
    di certificazione") and general non-environmental self-declared labels
    (UCPD_AnnexI_2: general trust/quality mark without authorization) -- e.g.
    NaturaSì's "Equosolidale"/"prodotto da nostra filiera" aren't
    environmental at all. Heuristic: sustainability vocabulary in the CLAIM'S
    OWN TEXT only. An earlier version also checked whether the same PRODUCT
    had an unrelated environmental sibling claim, but that swept claims in
    too eagerly -- e.g. a bare "PROTEIN +" label got mapped to the
    environmental chunk purely because the same product also had an
    unrelated FSC-packaging claim elsewhere on the listing."""
    if _SUSTAINABILITY_WORDS.search(claim.get("claim_text") or ""):
        return "ECGT_AnnexI_2_bis"
    return "UCPD_AnnexI_2"


def assign_legal_chunk_id(claim: dict) -> dict:
    """Returns {"chunk_id": str|None, "confidence": "high"|"medium"|"low",
    "note": str|None}."""
    category = claim.get("category")
    modifiers = claim.get("modifiers") or []

    if category == "environmental_unsubstantiated":
        if "vague_or_unquantified" in modifiers:
            return {
                "chunk_id": "ECGT_Art1_NuoveDefinizioni_p",
                "confidence": "high",
                "note": None,
            }
        return {"chunk_id": "ECGT_Art1_NuoveDefinizioni_o", "confidence": "high", "note": None}

    if category == "offset_based_neutrality":
        return {"chunk_id": "ECGT_AnnexI_4_quater", "confidence": "high", "note": None}

    if category == "unauthorized_or_borderline_medicinal_claim":
        return {"chunk_id": "UCPD_AnnexI_17", "confidence": "high", "note": None}

    if category == "unsubstantiated_health_or_efficacy_claim":
        if "borderline_medicinal_claim_candidate" in modifiers:
            return {"chunk_id": "UCPD_AnnexI_17", "confidence": "high", "note": None}
        return {
            "chunk_id": "UCPD_Art6",
            "confidence": "medium",
            "note": "no blacklist point for botanical/EFSA-mimicry wording; general misleading-action test",
        }

    if category == "misleading_endorsement_claim":
        return {"chunk_id": "UCPD_AnnexI_4", "confidence": "high", "note": None}

    if category == "fake_or_unverified_label":
        return {
            "chunk_id": _fake_label_chunk(claim),
            "confidence": "low",
            "note": "environmental vs. general trust-mark split is a heuristic, not a certain read",
        }

    if category == "misleading_authenticity_or_origin_claim":
        return {
            "chunk_id": "UCPD_Art6",
            "confidence": "medium",
            "note": "general misleading action; Art. 6(1)'s 'even if factually correct' clause "
            "covers two_part_verification_required heritage claims specifically",
        }

    if category == "misleading_superiority_or_absolute_claim":
        return {
            "chunk_id": "UCPD_Art6",
            "confidence": "medium",
            "note": "general misleading action, no dedicated blacklist point",
        }

    if category == "misleading_composition_or_ingredient_claim":
        return {"chunk_id": "UCPD_Art6", "confidence": "medium", "note": "general misleading action"}

    if category == "nutrition_content_claim":
        if "compliance_unverified_from_text" in modifiers:
            return {
                "chunk_id": "UCPD_Art7",
                "confidence": "medium",
                "note": "undisclosed threshold is an omission, not a false assertion",
            }
        return {"chunk_id": "UCPD_Art6", "confidence": "medium", "note": "general misleading action"}

    if category == "unfair_comparison":
        return {
            "chunk_id": "UCPD_Art6",
            "confidence": "low",
            "note": "no Comparative Advertising Directive (2006/114/EC) chunk exists in this "
            "corpus -- UCPD_Art6 is the best available fit, not a good one",
        }

    if category == "irrelevant_claim":
        return {"chunk_id": None, "confidence": "high", "note": "not a claim; true negative"}

    return {"chunk_id": None, "confidence": "low", "note": f"unrecognized category: {category!r}"}
