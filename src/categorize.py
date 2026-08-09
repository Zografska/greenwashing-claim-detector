"""
Assigns a greenwashing category to each extracted claim, optionally grounded
by retrieved directive passages (RAG conditions) or by a fine-tuned model
(distilled conditions).

Categories below are a starting point derived from the ECGT blacklist
practices. Still open: single-label vs multi-label, since vague claims and
unsubstantiated claims overlap a lot in practice. Decide before you build
the gold annotation set, it changes the annotation schema.
"""

from typing import List, Optional

CATEGORIES = [
    "generic_unsubstantiated",   # "eco-friendly", "green" with no certified backing
    "offset_based_neutrality",   # "climate neutral" / "CO2 neutral" via offsetting
    "fake_or_unverified_label",  # self-created sustainability seals/symbols
    "unfair_comparison",         # comparative claim without disclosed basis
    "irrelevant_claim",          # true but legally required anyway / not a differentiator
    "none",                      # not a greenwashing-relevant claim
]


def categorize_claim(
    claim_text: str,
    retrieved_context: Optional[List] = None,
    model: str = "llama3.2",
) -> str:
    """
    Return one (or more, if multi-label) label from CATEGORIES for the claim.

    TODO:
    - prompt template that takes claim_text + retrieved_context (if any)
      and returns a structured label + short reasoning
    - swap `model` for the fine-tuned checkpoint in distilled conditions
    """
    raise NotImplementedError
