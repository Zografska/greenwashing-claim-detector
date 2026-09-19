"""
Prompt suite v4 -- gate -> extract -> [verify] -> severity pipeline.

Implements the redesign proposed in `.claude/reccomendations/` (extract.md,
gate_and_verify.md, severity.md, schemas.py), kept as a separate module
rather than modifying extraction.py in place -- same "keep the old pipeline
comparable" convention this repo already follows for
`src/dissected_extraction.py`. `src/extraction.py`'s v3 pipeline is
untouched and remains the current best-measured baseline
(model_comparison_report.md); this module is an unproven variant to A/B
against it (A3 onward in extract.md's ablation matrix), not a replacement.

Reuses extraction.py's prefilter/keyword machinery (`_prefilter_description`,
CLAIM_KEYWORDS) rather than re-deriving it -- Phase 0 (see
model_comparison_report.md §8) measured that machinery, not v3's prompt
wording, as the dominant source of missed claims, and none of that finding
is specific to the v3 prompt. Also reuses dissected_extraction.py's generic
`_ollama_json_call`/`_find_items_list` helpers rather than duplicating them.

Two axes changed from v3, deliberately kept independent:
  - detection/categorization: an ordered decision procedure (first-match-
    wins over 11 rules) instead of v3's 11 parallel definitions, calibrated
    to gold's real average (2.45 claims/product) instead of v3's "4-10"
    exhaustiveness framing, and `why` emitted before `category` (label
    follows reasoning, not vice versa).
  - severity: split into its own call (never conflated with detection),
    0-100 continuous score instead of HIGH/MEDIUM/LOW, with a REQUIRED
    `backing` field emitted before the score so a low score is only
    reachable by first naming specific evidence -- see SEVERITY_SYSTEM_PROMPT.
    The nutrition_content_claim -> LOW hard exception is gone entirely
    (matches Phase 0's B1 fix to v3, done independently here since this
    axis has no categorical LOW to except in the first place).

An optional gate call (cheap binary screen, no incentive to produce
content) and an optional deepseek-r1 verify cascade (candidate accept/
reject, not a generator) sit around detection -- both off by default via
CLI flags, since neither has been measured yet.

num_predict/num_ctx tiers below are INITIAL ESTIMATES sized by word/token
counting the prompts themselves, following extraction.py's own budgeting
convention (see the comments above `extract_claims` there) -- but unlike
that file's tiers, which were tuned against measured truncation failures,
these have NOT been run against a live model yet. Calibrate with
`--limit 2-3` before trusting them on a full file; override via
`--num-predict`/`--num-ctx`/`--*-num-predict`/`--*-num-ctx` if they're wrong.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .data import iter_records
from .extraction import CLAIM_CATEGORIES, USE_SCHEMA_GRAMMAR_DEFAULT, _prefilter_description
from .dissected_extraction import _ollama_json_call, _find_items_list

# --- shared category decision procedure (extract.md) -----------------------
# Used verbatim by both the extract prompt (as the primary categorization
# instruction) and the verify prompt (gate_and_verify.md's verify.md says
# to "insert the numbered decision procedure from extract.md, rules 1-11" --
# pulled into one constant rather than duplicated so the two can't drift).
_CATEGORY_DECISION_PROCEDURE = """Apply these in order. The first rule that matches wins.

1. Carbon-neutral or net-zero achieved by offsetting emissions
   -> `offset_based_neutrality`
2. Packaging, emissions, recyclability, or resource use
   -> `environmental_unsubstantiated`
3. What is or is not in the product (ingredients, additives, allergens)
   -> `misleading_composition_or_ingredient_claim`
   This rule beats rule 2 even when both appear in one sentence.
4. A named third-party body, institute, or professional group approving the
   product -> `misleading_endorsement_claim`
5. A trust-mark, or a social, charitable, or cause-marketing impact
   -> `fake_or_unverified_label`
6. A nutrient tied to a fixed legal compositional threshold (fibre, vitamin,
   mineral, calorie, fat content) -> `nutrition_content_claim`
7. A health, wellness, or efficacy benefit -> `unsubstantiated_health_or_efficacy_claim`
8. Geographic origin, heritage, tradition, founding date, or "made in"
   provenance -> `misleading_authenticity_or_origin_claim`
9. A comparison against another product or an unstated baseline
   -> `unfair_comparison`
10. Absolute or superiority language with no comparator or metric stated
    -> `misleading_superiority_or_absolute_claim`
11. Checkable, but it is a mandatory legal disclosure, EU-authorized wording
    used correctly, or a trivial fact -> `irrelevant_claim`

Classify each span on its own subject matter, not on what sits beside it in
the same sentence."""

# --- gate (gate_and_verify.md's gate.md) ------------------------------------
GATE_SYSTEM_PROMPT = """You are screening Italian grocery product descriptions.

Answer one question: does this description contain at least one statement a
regulator could demand evidence for?

These do NOT count:
- taste, texture, or experience description
- brand slogans with no factual content
- recipes, serving suggestions, storage or usage instructions
- ingredient lists and nutrition tables presented as data
- dietary-lifestyle labels alone (vegan, gluten-free, lactose-free)
- mandatory packaging-disposal or labelling text

These DO count: any assertion about health, nutrition content, origin,
composition, environmental impact, endorsement, certification, superiority,
or comparison.

Emit, in this order:
- `trigger` -- the single strongest candidate span, quoted exactly, or "none"
- `has_claims` -- true or false

Many descriptions legitimately contain nothing. "false" is a common and
correct answer."""

GATE_SCHEMA = {
    "type": "object",
    "properties": {
        "trigger": {"type": "string"},
        "has_claims": {"type": "boolean"},
    },
    "required": ["trigger", "has_claims"],
}

# system(~150 words =~ 210 tok) + schema(~60) + user overhead(~60) +
# prefiltered description (same scale extraction.py budgets for, up to
# ~800 words Italian =~ 1120 tok) + num_predict(200) =~ 1650 -- rounded up
# generously since this is unmeasured.
GATE_NUM_CTX = 2500
GATE_NUM_PREDICT = 200

# --- extract v4 (extract.md) ------------------------------------------------
EXTRACT_V4_SYSTEM_PROMPT = f"""You are an EU consumer-law analyst applying the Unfair Commercial Practices
Directive (2005/29/EC) to Italian grocery marketing copy.

Read the PRODUCT DESCRIPTION. Find every span that makes a checkable
commercial assertion about the product. For each one, quote it exactly,
state briefly what is asserted, then assign one category.

## What counts as a claim

A span is a claim if a regulator could demand evidence for it. The test:
could this statement be shown true or false?

- Taste, feeling, brand mood, or slogan with nothing verifiable: not a claim.
  It does not appear in your output at all.
- Storage, preparation, or usage instructions: not a claim.
- An ingredient list or nutrition table reproduced as data: not a claim.
- A benefit asserted inside a usage sentence: this IS a claim. Extract the
  benefit, not the instruction.

Judge on checkability and authorization, not on whether the underlying
science is real. An ingredient genuinely having a chemical property still
produces a claim when that property is asserted outside EU-authorized
wording. The EU botanicals health-claims list has been on hold since 2010,
so the gap is authorization, not evidence. Do not use outside knowledge to
excuse a claim.

## Categories

{_CATEGORY_DECISION_PROCEDURE}

## How many claims

Most descriptions contain between 0 and 4 claims. Many contain none: a short
description, pure recipe or serving text, or dietary-lifestyle labels alone
(vegan, gluten-free, lactose-free) yield an empty list. An empty list is a
correct and common answer.

Extract what is present. Do not pad the list to reach a count. Read to the
end of the description before you finish -- a claim in the last sentence
counts as much as one in the first.

## Output

For each claim, emit these fields in this order:

- `quote` -- copied character-for-character from PRODUCT DESCRIPTION. Do not
  translate, shorten, correct spelling, or join separated sentences. If you
  cannot copy it exactly as it appears, do not emit the claim.
- `why` -- at most 12 words: what is asserted, and what is unverified. Your
  own words, not a restatement of a category definition.
- `category` -- one value from the list above.

`quote` comes only from PRODUCT DESCRIPTION. Not from PRODUCT NAME, not from
MARKETING BADGE, and not from CANDIDATE LEGAL CONTEXT if that section is
present. Statute text is background reference: formal, third-person, and
about practices in general rather than this product. If a span reads that
way, it came from the wrong section."""

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

# system(~600 words english =~ 800 tok) + schema(~200) + user overhead(~100)
# + prefiltered description (up to ~800 words Italian =~ 1120 tok) +
# num_predict(800, sized for ~4 claims at ~45 words/claim per the v4
# calibration above, generous margin over that) =~ 3020 -- rounded up.
EXTRACT_V4_NUM_CTX = 4000
EXTRACT_V4_NUM_PREDICT = 800

# --- verify cascade (gate_and_verify.md's verify.md) ------------------------
VERIFY_SYSTEM_PROMPT = f"""You are an EU consumer-law analyst applying the Unfair Commercial Practices
Directive (2005/29/EC).

A first-pass system has proposed candidate claims from an Italian product
description. Some are real; some are marketing puffery, usage instructions,
or mandatory labelling text that the first pass mistook for claims.

You are given the full description and the candidates. For each candidate:

1. `in_source` -- is `quote` present verbatim in the description? true/false.
2. `verdict` -- `keep` or `reject`.
   Reject when the span is puffery, a usage or storage instruction, an
   ingredient or nutrition table entry, mandatory labelling text, or not
   present in the source.
   Keep when the span asserts something checkable about the product.
3. `category` -- if you keep it, assign the correct category from the list
   below. Correct the first pass where it was wrong; you are not bound by
   its label.

{_CATEGORY_DECISION_PROCEDURE}

You are not extracting. Do not propose claims the candidate list does not
contain. Judge only what you are given."""

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

# system(verify.md prose ~150 words + embedded decision procedure ~250 words
# =~ 400 words =~ 550 tok) + schema(~250) + user overhead(~100) + FULL
# (unfiltered -- verify judges in_source against the true text, not the
# prefiltered fragments) description, up to ~1200 words Italian =~ 1680 tok
# + up to 10 candidates at ~40 words each =~ 560 tok + num_predict(700, ~10
# candidates * ~45 tok/verdict) =~ 3840 -- rounded up.
VERIFY_NUM_CTX = 5000
VERIFY_NUM_PREDICT = 700

# --- severity v4 (severity.md) ----------------------------------------------
SEVERITY_SYSTEM_PROMPT = """You are an EU consumer-law analyst applying the Unfair Commercial Practices
Directive (2005/29/EC). You will be given claims already extracted from an
Italian product description, each with a category assigned.

For each claim, decide how much regulatory exposure it carries.

## Procedure

For each claim, in this order:

1. Write `backing`: the specific thing in the product's own text that
   supports this exact claim. A named certification body. An EU-authorized
   phrase used correctly. A stated product fact that makes the claim
   self-evident. Quote or name it.

   If nothing in the text does this, write `backing: "none"`.

2. Write `severity`: an integer from 0 to 100.

## Severity scale

- **0-19** -- `backing` names a real certification, authorization, or
  mandatory disclosure covering this exact claim.
- **20-39** -- `backing` names a product fact that makes the claim
  self-evidently true.
- **40-69** -- `backing` is "none". A real, checkable assertion with nothing
  in the text supporting it. **This is the default and most claims land
  here.**
- **70-89** -- `backing` is "none" and the claim is either undercut by the
  product's own stated facts, or falls in a per-se restricted area with no
  authorization present.
- **90-100** -- Directly contradicted by the product's own stated facts, or
  blacklisted per se. An offsetting-based carbon-neutral or net-zero claim
  is always 90+ regardless of whether the offset is genuine.

## The rule that governs scores below 40

A score below 40 requires `backing` to name something specific. These do not
count as backing and must not produce a score below 40:

- "nothing in the text contradicts it"
- "this is plausible"
- "this is common for products of this type"
- a certification that exists somewhere in the product text but covers a
  *different* claim

Being unable to disprove a claim is not backing. If you find yourself
constructing a reason the claim is probably fine, that reasoning belongs in
the 40-69 band, not below it.

A certification lowers severity only for the specific claim it names.

## Output

For each claim emit, in this order: `claim_index`, `backing`, `severity`.
Every claim you receive gets exactly one object. Do not skip any."""

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
    """Floor-only cardinality (minItems, no maxItems) -- schemas.py's own
    rationale, kept here verbatim: forcing minItems == maxItems == n (as
    dissected_extraction.py's detection call does) makes a dropped or
    duplicated index unrecoverable AND gives the model no way to signal
    "I lost alignment" -- it just fills. A soft floor plus the code-side
    claim_index coverage check in `assess_severity` below means a
    misalignment is a logged gap, not silent corruption."""
    s = {**SEVERITY_SCHEMA}
    s["properties"] = {**SEVERITY_SCHEMA["properties"]}
    s["properties"]["assessments"] = {
        **SEVERITY_SCHEMA["properties"]["assessments"],
        "minItems": n,
    }
    return s


# system(severity.md prose + scale + rule-below-40 section, ~400 words =~
# 550 tok) + schema(~200) + user overhead(~100) + numbered claims (up to
# ~10 claims * ~25 words =~ 350 tok) + num_predict(700, ~10 claims * ~45
# tok/assessment) =~ 1900 -- rounded up generously.
SEVERITY_NUM_CTX = 2500
SEVERITY_NUM_PREDICT = 700


# --- stage calls -------------------------------------------------------------

def _build_gate_prompt(product: dict, description: str) -> str:
    filtered = _prefilter_description(description)
    return f"""PRODUCT NAME: {product.get("name", "N/A")}

PRODUCT DESCRIPTION (pre-filtered for claim-relevant content):
{filtered or "No description available"}

Does this description contain at least one statement a regulator could
demand evidence for?"""


def gate_check(
    product: dict, description: str, model: str = "llama3.2", temperature: float = 0,
    use_schema_grammar: bool = USE_SCHEMA_GRAMMAR_DEFAULT,
    num_predict_override: Optional[int] = None, num_ctx_override: Optional[int] = None,
) -> dict:
    """Cheap binary pre-screen (gate.md) -- run before extract_claims_v4 to
    skip extraction outright on a "false" verdict. Has no incentive to
    produce content (unlike extraction, which is graded on exhaustiveness),
    so it's the intended lever against the hard_no false-positive rate --
    see gate_and_verify.md. Returns {"trigger": str, "has_claims": bool}."""
    prompt = _build_gate_prompt(product, description)
    return _ollama_json_call(
        GATE_SYSTEM_PROMPT, prompt, GATE_SCHEMA, model, temperature,
        num_predict_override or GATE_NUM_PREDICT, num_ctx_override or GATE_NUM_CTX, use_schema_grammar,
    )


def _build_extract_v4_prompt(product: dict, description: str) -> str:
    filtered = _prefilter_description(description)
    return f"""PRODUCT NAME: {product.get("name", "N/A")}
MARKETING BADGE: {product.get("marketing_badge", "none")}

PRODUCT DESCRIPTION (pre-filtered for claim-relevant content):
{filtered or "No description available"}

Extract every claim covered by the category list in the system prompt."""


def extract_claims_v4(
    product: dict, description: str, model: str = "llama3.2", temperature: float = 0,
    use_schema_grammar: bool = USE_SCHEMA_GRAMMAR_DEFAULT,
    num_predict_override: Optional[int] = None, num_ctx_override: Optional[int] = None,
) -> dict:
    """extract.md's detection+categorization call -- quote/why/category
    only, no severity (see module docstring for why that's a separate
    call). Returns {"claims": [{"quote", "why", "category"}, ...]}."""
    prompt = _build_extract_v4_prompt(product, description)
    return _ollama_json_call(
        EXTRACT_V4_SYSTEM_PROMPT, prompt, EXTRACT_SCHEMA, model, temperature,
        num_predict_override or EXTRACT_V4_NUM_PREDICT, num_ctx_override or EXTRACT_V4_NUM_CTX, use_schema_grammar,
    )


def _build_verify_prompt(description: str, candidates: List[dict]) -> str:
    numbered = "\n".join(
        f'{i + 1}. [{c.get("category")}] "{c.get("quote")}" -- {c.get("why", "")}'
        for i, c in enumerate(candidates)
    )
    return f"""FULL PRODUCT DESCRIPTION (unfiltered):
{description or "No description available"}

CANDIDATE CLAIMS ({len(candidates)}):
{numbered}

Judge each candidate. Return exactly {len(candidates)} verdicts,
candidate_index 1 through {len(candidates)}."""


def verify_claims(
    description: str, candidates: List[dict], model: str = "deepseek-r1:70b", temperature: float = 0,
    use_schema_grammar: bool = USE_SCHEMA_GRAMMAR_DEFAULT,
    num_predict_override: Optional[int] = None, num_ctx_override: Optional[int] = None,
) -> dict:
    """verify.md's cascade verifier -- judges extract_claims_v4's candidates
    against the FULL unfiltered description (not the prefiltered fragments
    extraction saw), using deepseek-r1's measured strength as a
    discriminator (best category accuracy 0.60-0.71, 0-1 false positives,
    model_comparison_report.md §5) rather than as a generator, where the
    same model measured badly (recall collapsed on every deepseek-involving
    generation run tried there). Returns {"verdicts": []} immediately if
    there are no candidates -- nothing to verify, and an empty-array call
    to the model would just waste a request."""
    if not candidates:
        return {"verdicts": []}
    prompt = _build_verify_prompt(description, candidates)
    return _ollama_json_call(
        VERIFY_SYSTEM_PROMPT, prompt, VERIFY_SCHEMA, model, temperature,
        num_predict_override or VERIFY_NUM_PREDICT, num_ctx_override or VERIFY_NUM_CTX, use_schema_grammar,
    )


def _build_severity_prompt(claims: List[dict]) -> str:
    numbered = "\n".join(
        f'{i + 1}. [{c.get("category")}] "{c.get("quote")}"'
        for i, c in enumerate(claims)
    )
    return f"""Assign backing + severity to each of these {len(claims)} claims.
Return exactly {len(claims)} assessments, claim_index 1 through {len(claims)}.

CLAIMS:
{numbered}"""


def assess_severity(
    claims: List[dict], model: str = "llama3.2", temperature: float = 0,
    use_schema_grammar: bool = USE_SCHEMA_GRAMMAR_DEFAULT,
    num_predict_override: Optional[int] = None, num_ctx_override: Optional[int] = None,
) -> Tuple[dict, List[int]]:
    """severity.md's severity call -- backing emitted before severity, both
    in schema property order and required-field order, the structural
    replacement for two failed prompt-only attempts at stopping a model
    from rationalizing its way to a low score (model_comparison_report.md
    §5's deepseek-r1 calibration dead end). Returns (parsed_response,
    missing_indices) -- missing_indices is schemas.py's own suggested
    code-side check on claim_index coverage (soft cardinality, not a hard
    raise -- see severity_schema's docstring)."""
    if not claims:
        return {"assessments": []}, []
    prompt = _build_severity_prompt(claims)
    schema = severity_schema(len(claims)) if use_schema_grammar else SEVERITY_SCHEMA
    result = _ollama_json_call(
        SEVERITY_SYSTEM_PROMPT, prompt, schema, model, temperature,
        num_predict_override or SEVERITY_NUM_PREDICT, num_ctx_override or SEVERITY_NUM_CTX, use_schema_grammar,
    )
    assessments = _find_items_list(result, "assessments", "claim_index")
    seen = {a.get("claim_index") for a in assessments}
    missing = [i for i in range(1, len(claims) + 1) if i not in seen]
    return result, missing


# --- orchestration -----------------------------------------------------------

def run_pipeline_v4(
    product: dict, description: str,
    model: str = "llama3.2", severity_model: Optional[str] = None, verify_model: Optional[str] = None,
    gate_enabled: bool = True, gate_model: Optional[str] = None,
    temperature: float = 0, use_schema_grammar: bool = USE_SCHEMA_GRAMMAR_DEFAULT,
) -> dict:
    """One product through gate(optional) -> extract-v4 -> verify(optional)
    -> severity.

    Deliberately returns ALL claims with raw severity/backing attached, no
    threshold-based drop applied here -- same "generate once, filter
    downstream" pattern as v3's `dropped_claims` (extraction.py's
    `_validate_claims` docstring). See `to_v3_shape` below for the
    threshold step, which re-runs cheaply against this cached output
    instead of re-calling the model for every candidate threshold --
    that's what makes the A4 "0-100 + tuned threshold" ablation affordable
    (sweep thresholds once, not once per model call).

    severity_model/gate_model default to `model` if unset. verify_model has
    NO default -- the cascade is off unless a model is explicitly given
    (per gate_and_verify.md, verify is a variant to A/B, not a default
    stage; deepseek-r1:70b is the model it was designed against).
    """
    severity_model = severity_model or model
    gate_model = gate_model or model

    gate_result = None
    if gate_enabled:
        gate_result = gate_check(
            product, description, model=gate_model, temperature=temperature, use_schema_grammar=use_schema_grammar,
        )
        if not gate_result.get("has_claims", True):
            return {
                "gate": gate_result, "candidates": [], "verify": None,
                "claims": [], "missing_severity_indices": [],
            }

    extract_result = extract_claims_v4(
        product, description, model=model, temperature=temperature, use_schema_grammar=use_schema_grammar,
    )
    candidates = extract_result.get("claims", [])

    verify_result = None
    working_claims = candidates
    if verify_model and candidates:
        verify_result = verify_claims(
            description, candidates, model=verify_model, temperature=temperature, use_schema_grammar=use_schema_grammar,
        )
        verdicts = _find_items_list(verify_result, "verdicts", "candidate_index")
        by_candidate_index = {v.get("candidate_index"): v for v in verdicts}
        working_claims = []
        for i, c in enumerate(candidates, 1):
            v = by_candidate_index.get(i)
            if v is None or v.get("verdict") != "keep":
                continue
            # verify.md: "Correct the first pass where it was wrong; you are
            # not bound by its label" -- take verify's category, not extract's.
            working_claims.append({**c, "category": v.get("category", c.get("category"))})

    severity_result, missing = assess_severity(
        working_claims, model=severity_model, temperature=temperature, use_schema_grammar=use_schema_grammar,
    )
    assessments = _find_items_list(severity_result, "assessments", "claim_index")
    by_claim_index = {a.get("claim_index"): a for a in assessments}
    final_claims = []
    for i, c in enumerate(working_claims, 1):
        a = by_claim_index.get(i, {})
        final_claims.append({**c, "backing": a.get("backing", "none"), "severity": a.get("severity")})

    return {
        "gate": gate_result, "candidates": candidates, "verify": verify_result,
        "claims": final_claims, "missing_severity_indices": missing,
    }


def pipeline_v4_from_file(
    filename: str, model: str = "llama3.2", severity_model: Optional[str] = None,
    verify_model: Optional[str] = None, gate_enabled: bool = True, gate_model: Optional[str] = None,
    temperature: float = 0, use_schema_grammar: bool = USE_SCHEMA_GRAMMAR_DEFAULT,
    limit: Optional[int] = None,
) -> Tuple[List[dict], List[dict]]:
    records = list(iter_records(filename))
    if limit is not None:
        records = records[:limit]
    total = len(records)
    results: List[dict] = []
    failed: List[dict] = []
    run_start = time.monotonic()

    for i, (idx, record) in enumerate(records, 1):
        name = record.get("name", f"record {idx}")
        print(f"[{i}/{total}] {name}", end=" ... ", flush=True)
        call_start = time.monotonic()
        try:
            description = record["description"]
            out = run_pipeline_v4(
                product=record, description=description, model=model,
                severity_model=severity_model, verify_model=verify_model,
                gate_enabled=gate_enabled, gate_model=gate_model,
                temperature=temperature, use_schema_grammar=use_schema_grammar,
            )
            elapsed = time.monotonic() - call_start
            results.append({
                "index": idx,
                "ean": record.get("ean"),
                "name": record.get("name"),
                "gate": out["gate"],
                "claims": out["claims"],
                "missing_severity_indices": out["missing_severity_indices"],
                "elapsed_seconds": round(elapsed, 2),
            })
            suffix = f" ({len(out['missing_severity_indices'])} missing severity)" if out["missing_severity_indices"] else ""
            print(f"{len(out['claims'])} claims found{suffix} [{elapsed:.1f}s]")
        except Exception as e:
            elapsed = time.monotonic() - call_start
            print(f"FAILED after {elapsed:.1f}s: {e}")
            failed.append({"index": idx, "ean": record.get("ean"), "name": name, "error": str(e)})
            time.sleep(2)
            continue

    total_elapsed = time.monotonic() - run_start
    avg_per_record = total_elapsed / total if total else 0
    print(f"\nDone: {len(results)} ok, {len(failed)} failed")
    print(f"Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min), avg {avg_per_record:.1f}s/record")
    if failed:
        print("Failed records:")
        for f in failed:
            print(f"  [{f['index']}] {f['name']} — {f['error']}")

    return results, failed


# --- v3-shape conversion (for src.evaluate, which stays unmodified) --------

def _severity_to_risk_level(severity: Optional[int]) -> str:
    """Derived bucketing for src.evaluate's risk_level_agreement bonus
    metric ONLY -- severity.md's own bands don't require this, it exists
    purely so a metric built for a categorical v3 output has something to
    compare a continuous v4 score against. extraction_prf/category_accuracy
    don't use risk_level on predictions at all, only claim_text/category,
    so this mapping can't affect either of those two scores.

    Boundaries follow severity.md's own band descriptions: 70+ ("undercut
    by the product's own facts" or worse) -> HIGH; 40-69 ("the default,
    most claims land here") -> MEDIUM; below 40 (named backing required)
    -> LOW. A claim below the drop threshold never reaches this function
    in practice (see to_v3_shape), so LOW here is display-only."""
    if severity is None:
        return "MEDIUM"
    if severity >= 70:
        return "HIGH"
    if severity >= 40:
        return "MEDIUM"
    return "LOW"


def to_v3_shape(results: List[dict], threshold: int = 40) -> List[dict]:
    """Convert run_pipeline_v4/pipeline_v4_from_file output into the exact
    shape src/evaluate.py already scores (claim_text/category/risk_level/
    risk_rationale + dropped_claims per record) -- so evaluate.py needs NO
    changes to score v4 output.

    `threshold` is severity.md's "drop threshold, tuned per severity-model
    on dev, not baked into the label space" -- applied HERE, downstream of
    generation, not inside run_pipeline_v4, so the same cached run can be
    re-scored at many candidate thresholds without a new model call. This
    is what makes src/sweep_severity_threshold.py (the A4 ablation) cheap.

    A claim with severity=None (missing from the model's severity response
    -- see assess_severity's missing_severity_indices) is always dropped,
    never kept by default: we have no basis to say it clears any threshold."""
    converted = []
    for r in results:
        kept, dropped = [], []
        for c in r.get("claims", []):
            severity = c.get("severity")
            shaped = {
                "claim_text": c.get("quote", ""),
                "category": c.get("category"),
                "risk_level": _severity_to_risk_level(severity),
                "risk_rationale": c.get("backing", "none"),
                "severity": severity,
            }
            if severity is not None and severity >= threshold:
                kept.append(shaped)
            else:
                dropped.append({**shaped, "_dropped_reason": f"severity={severity} < threshold={threshold}"})
        converted.append({
            "index": r.get("index"),
            "ean": r.get("ean"),
            "name": r.get("name"),
            "claims": kept,
            "dropped_claims": dropped,
            "elapsed_seconds": r.get("elapsed_seconds"),
        })
    return converted


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="filename in data/raw/, e.g. sample_coop_extraction_input.json")
    parser.add_argument("--model", default="llama3.2", help="model for the extract-v4 call")
    parser.add_argument("--severity-model", default=None, help="defaults to --model if unset")
    parser.add_argument(
        "--verify-model", default=None,
        help="enables the verify cascade with this model (e.g. deepseek-r1:70b) -- off (no cascade) if unset, "
        "per gate_and_verify.md's verify.md.",
    )
    parser.add_argument("--gate-model", default=None, help="defaults to --model if unset")
    parser.add_argument(
        "--no-gate", dest="gate_enabled", action="store_false",
        help="skip the gate.md pre-screen and always run extract-v4 -- gate is ON by default.",
    )
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument(
        "--no-schema-grammar", dest="use_schema_grammar", action="store_false",
        help="disable grammar-constrained decoding (falls back to loose 'format': 'json') -- the A9 ablation.",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    results, failed = pipeline_v4_from_file(
        args.file, model=args.model, severity_model=args.severity_model, verify_model=args.verify_model,
        gate_enabled=args.gate_enabled, gate_model=args.gate_model, temperature=args.temperature,
        use_schema_grammar=args.use_schema_grammar, limit=args.limit,
    )

    print(f"\nProcessed {len(results)} products")
    total_claims = sum(len(r["claims"]) for r in results)
    print(f"Total claims extracted: {total_claims}")
    print(f"Failed records: {len(failed)}")

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
        print(f"Saved to {args.out}")
        if failed:
            fail_path = out_path.parent / "failed.json"
            fail_path.write_text(json.dumps(failed, indent=2, ensure_ascii=False))
            print(f"Failed records saved to {fail_path}")
    else:
        print(json.dumps(results[:2], indent=2, ensure_ascii=False))
