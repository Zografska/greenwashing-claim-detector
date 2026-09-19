"""JSON schemas for prompt suite v4.

The single most important change from v3 is FIELD ORDER. Generation is
autoregressive: a field emitted earlier conditions every field after it.

v3 emitted:  claim_text, category, risk_level, risk_rationale
             -> the model commits to a label, THEN writes a justification for
                a decision it has already made. The rationale can never
                influence the label.

v4 emits:    quote, why, category        (extract)
             claim_index, backing, severity   (severity)
             -> the evidence field is written first and conditions the label.

Ollama honours property order in `format` for grammar-constrained decoding,
so this is not cosmetic. Test it as its own ablation: v3 field order vs v4
field order, everything else held constant. It is a one-line change with a
plausibly large effect.
"""

CLAIM_CATEGORIES = [
    "unsubstantiated_health_or_efficacy_claim",
    "nutrition_content_claim",
    "misleading_composition_or_ingredient_claim",
    "misleading_authenticity_or_origin_claim",
    "misleading_superiority_or_absolute_claim",
    "unfair_comparison",
    "misleading_endorsement_claim",
    "fake_or_unverified_label",
    "environmental_unsubstantiated",
    "offset_based_neutrality",
    "irrelevant_claim",
]

# --- gate -----------------------------------------------------------------
GATE_SCHEMA = {
    "type": "object",
    "properties": {
        "trigger": {"type": "string"},
        "has_claims": {"type": "boolean"},
    },
    "required": ["trigger", "has_claims"],
}

# --- extract --------------------------------------------------------------
EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "quote": {"type": "string"},
                    "why": {"type": "string"},
                    "category": {"type": "string", "enum": CLAIM_CATEGORIES},
                },
                "required": ["quote", "why", "category"],
            },
        }
    },
    "required": ["claims"],
}

# --- verify (cascade) -----------------------------------------------------
VERIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "verdicts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "candidate_index": {"type": "integer"},
                    "in_source": {"type": "boolean"},
                    "verdict": {"type": "string", "enum": ["keep", "reject"]},
                    "category": {"type": "string", "enum": CLAIM_CATEGORIES},
                },
                "required": ["candidate_index", "in_source", "verdict", "category"],
            },
        }
    },
    "required": ["verdicts"],
}

# --- severity -------------------------------------------------------------
# `backing` before `severity` is the whole mechanism. A model that must write
# "none" in a required field before scoring cannot silently rationalise its
# way to a low score — the empty justification is on the page first, and it
# is auditable afterwards. This replaces two failed attempts (
# SYSTEM_PROMPT_REASONING, RISK_SYSTEM_PROMPT_REASONING) at *instructing* the
# model not to do it.
SEVERITY_SCHEMA = {
    "type": "object",
    "properties": {
        "assessments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_index": {"type": "integer"},
                    "backing": {"type": "string"},
                    "severity": {"type": "integer", "minimum": 0, "maximum": 100},
                },
                "required": ["claim_index", "backing", "severity"],
            },
        }
    },
    "required": ["assessments"],
}


def severity_schema(n: int) -> dict:
    """v3 forced minItems == maxItems == n on the detection call. That makes
    a dropped or duplicated index unrecoverable AND gives the model no way to
    signal 'I lost alignment' — it just fills. Prefer soft cardinality plus a
    code-side check on `claim_index` coverage, so a misalignment is a logged
    failure rather than silent corruption."""
    s = {**SEVERITY_SCHEMA}
    s["properties"] = {**SEVERITY_SCHEMA["properties"]}
    s["properties"]["assessments"] = {
        **SEVERITY_SCHEMA["properties"]["assessments"],
        "minItems": n,  # floor only, no maxItems
    }
    return s
