"""
Pulls claim spans out of product descriptions that may be unfair under the
EU Unfair Commercial Practices Directive (Directive 2005/29/EC, "UCPD").
Adapted from the notebook extraction pipeline.

Note: this version narrows focus to UCPD scope -- misleading actions (Art. 6),
misleading omissions (Art. 7), and blacklisted practices (Annex I) -- covering
nutrition/health, origin, composition, and value claims. This is broader than
the ECGT/greenwashing-only version this file used previously: environmental
claims are still in scope here (UCPD covers them too), but so is everything
else UCPD covers that ECGT doesn't (nutrition, health, origin, price/value).
"""

import json
import time
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple

import httpx

from .data import load_descriptions, iter_records


OLLAMA_URL = "http://localhost:4639/api/generate"

# --- JSON Schema for Ollama's grammar-constrained decoding ---------------
# `category` values are lifted verbatim from golden/canonical/<retailer>.json
# -- the same 11-way taxonomy the golden set's extracted_claims use -- so
# extraction output and gold labels are directly comparable without a
# relabeling step. This replaces an earlier hand-designed 6-way UCPD split
# (NUTRITION_HEALTH_CLAIM/ORIGIN_PROVENANCE_CLAIM/etc.) that didn't match
# the golden set at all.
#
# `ucpd_category` (the separate misleading_action/misleading_omission/
# blacklisted_practice/aggressive_practice/none legal-hook axis) is dropped
# entirely, not just relabeled: golden/canonical/*.json's own ucpd_category
# field is always null (that legal-hook mapping is done downstream by
# src/adapters/legal_mapping.py, not at extraction time), so asking a small
# model to hit two independent enums plus risk_level in one pass was pure
# added failure surface for a field nothing consumes.
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_text": {"type": "string"},
                    "category": {
                        "type": "string",
                        "enum": [
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
                        ],
                    },
                    "risk_level": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                    "risk_rationale": {"type": "string"},
                },
                "required": [
                    "claim_text",
                    "category",
                    "risk_level",
                    "risk_rationale",
                ],
            },
        }
    },
    "required": ["claims"],
}

# Kept as a plain dict too, in case other code in this package imports SCHEMA
# directly for docs/tests. Not used in the prompt anymore.
SCHEMA = {
    "claims": [
        {
            "claim_text": "exact text as found in description",
            "category": (
                "unsubstantiated_health_or_efficacy_claim | nutrition_content_claim | "
                "misleading_composition_or_ingredient_claim | misleading_authenticity_or_origin_claim | "
                "misleading_superiority_or_absolute_claim | unfair_comparison | misleading_endorsement_claim | "
                "fake_or_unverified_label | environmental_unsubstantiated | offset_based_neutrality | "
                "irrelevant_claim"
            ),
            "risk_level": "HIGH | MEDIUM | LOW",
            "risk_rationale": "specific reason this risk level applies",
        }
    ]
}

# --- System prompt: UCPD scope, golden-set-aligned category taxonomy ----
SYSTEM_PROMPT = """You are an EU consumer law analyst (UCPD, Dir. 2005/29/EC). Extract
unfair claims from this Italian product description.

category (pick exactly one per claim). Descriptions below are deliberately
abstract, with NO quoted Italian example phrases -- any concrete phrase
written here would just be copied into your output verbatim on a thin
product, which has happened before. Apply the definition to what THIS
product's own text actually says, never to a phrase that merely resembles
a definition:
- unsubstantiated_health_or_efficacy_claim: a health, wellness, or efficacy
  benefit claim about the product, not stated in EU-authorized regulatory
  wording.
- nutrition_content_claim: a nutrient-content claim tied to a fixed legal
  compositional threshold (fibre, vitamin, mineral, calorie content, etc.)
  -- whether the product actually clears that threshold isn't visible from
  ad text alone.
- misleading_composition_or_ingredient_claim: an OPTIONAL (not legally
  required) factual statement about what is or isn't among the product's
  ingredients or additives. Optional and checkable, not mandatory labeling.
- misleading_authenticity_or_origin_claim: a claim about geographic origin,
  heritage, tradition, a founding date, or "made in" provenance.
- misleading_superiority_or_absolute_claim: absolute or superiority language
  about the product with no stated comparator or metric.
- unfair_comparison: a comparison against another product or an unstated,
  vague baseline.
- misleading_endorsement_claim: a named third-party body, institute, or
  professional group endorsing or approving the product.
- fake_or_unverified_label: a trust-mark, cause-marketing, or social/
  charitable-impact claim whose backing can't be confirmed from the text.
- environmental_unsubstantiated: a general or vague environmental-benefit
  claim about packaging, emissions, recyclability, or resource use that is
  NOT an offset-based carbon-neutrality claim (see next).
- offset_based_neutrality: specifically a carbon-neutral or net-zero claim
  based on offsetting emissions. Always HIGH risk -- this is blacklisted per
  se (Annex I, via Dir. 2024/825) regardless of whether the underlying
  offset is real.
- irrelevant_claim: a real, specific, checkable statement that turns out to
  be a mandatory legal disclosure, EU-authorized wording used correctly, or
  a trivial non-actionable fact. This is NOT the same as "not a claim" --
  see the puffery rule below for that case.

Disambiguation rule -- classify each clause on ITS OWN subject matter, never
by what it sits next to in the same sentence. A statement about what IS or
ISN'T in the product (ingredients, additives, allergens) is always
misleading_composition_or_ingredient_claim, even beside an environmental
claim in the same sentence. environmental_unsubstantiated is ONLY for
packaging, emissions, recyclability, or resource-use language -- never for
what's in the product itself.

Chemistry rule -- judge health/efficacy claims on checkability and
authorization, never on whether you believe the underlying chemistry is
real. An ingredient genuinely having a real chemical property is still
unsubstantiated_health_or_efficacy_claim if that property isn't asserted in
EU-authorized wording: the EU botanicals health-claims list has been on hold
since 2010, so the gap is authorization, not evidence. Do not use outside
scientific knowledge to excuse a claim.

Puffery rule -- subjective marketing language with nothing checkable (vague
taste/experience description, a brand slogan with no factual content) is
not a claim at all: do not add a claims entry for it, even though it may
sit right next to a real claim in the same sentence. Only use irrelevant_claim
for a real, specific, checkable statement that happens to be mandatory/
authorized/trivial -- never as a bucket for vague sentiment.

Sparse-input rule -- claim_text must be a sentence that literally appears in
the PRODUCT DESCRIPTION text below, never the PRODUCT NAME or MARKETING
BADGE line (those are metadata, not marketing copy). A description that is
short, or contains only recipe/usage instructions, dietary-lifestyle labels
(vegan, gluten-free, lactose-free), or nothing else -- has NO claims. A
product with zero claims is a normal, common, correct result. Do not invent
a claim to avoid returning an empty array.

risk_level: HIGH = directly contradicted by, or blacklisted regardless of,
the product's own stated facts. MEDIUM = a real, checkable benefit is
asserted but the ad gives no specific data, mechanism, or certification for
THAT exact claim. LOW = trivially true, or backed by a real, specifically-
named certification/EU-authorized wording for THAT exact claim.

Certification scope rule -- a certification only lowers risk for the SPECIFIC
claim it names (e.g. a named packaging-certification body backs only the
packaging claim it certifies). A certification mentioned anywhere in the ad
never justifies LOW for a *different*, unrelated claim in the same product
just because a certification exists somewhere in the text.

MEDIUM-by-default rule -- applies to EVERY category except nutrition_content_claim
(that one has fixed NHCR legal thresholds to fall back on, so it stays LOW
even unverified -- the category itself is legally bounded and low-severity;
no other category gets this exception). For every other category:
"I can't find a contradiction" is NEVER sufficient grounds for LOW. An
asserted-but-unbacked benefit, heritage claim, superiority claim, or
efficacy claim defaults to MEDIUM regardless of how plausible or
uncontroversial it sounds -- this includes authenticity/origin claims,
absolute-superiority claims, and unbacked environmental or health
assertions, not just the categories shown in the example below. Reserve
LOW only for a claim you can point to REAL backing
for: an EU-authorized phrase used correctly, or that exact claim's own
named certification. Being unable to disprove a claim is not backing.

Emit every claim you find at every risk_level, including LOW -- do not
silently drop LOW-risk claims; filtering happens downstream, not here.

EXAMPLE (JSON STRUCTURE ONLY. Every claim_text/risk_rationale below is a
PLACEHOLDER in angle brackets, not real content -- there is no real product
behind this example. NEVER copy any text from this example into a real
answer: your claim_text must always be a verbatim sentence you can point to
in THIS product's own PRODUCT DESCRIPTION, never text that merely resembles
this example's shape):
{"claims": [
  {"claim_text": "<verbatim sentence from the product asserting an unbacked health/efficacy benefit>", "category": "unsubstantiated_health_or_efficacy_claim", "risk_level": "MEDIUM", "risk_rationale": "<specific reason: what's asserted, why it's unbacked>"},
  {"claim_text": "<verbatim sentence from the product using a fixed-threshold nutrient wording>", "category": "nutrition_content_claim", "risk_level": "LOW", "risk_rationale": "<specific reason: legally bounded category, threshold unverified from text>"},
  {"claim_text": "<verbatim sentence from the product about heritage, tradition, or origin>", "category": "misleading_authenticity_or_origin_claim", "risk_level": "MEDIUM", "risk_rationale": "<specific reason: unbacked heritage/origin assertion>"},
  {"claim_text": "<verbatim sentence from the product about a carbon-offset or net-zero claim>", "category": "offset_based_neutrality", "risk_level": "HIGH", "risk_rationale": "<specific reason: blacklisted per se regardless of truth>"}
]}

Rules:
- claim_text: copy exactly from the PRODUCT DESCRIPTION section only.
  NEVER from the CANDIDATE LEGAL CONTEXT section, even partially. That
  section is statute text (Annex I / Art. 6 / Art. 7 wording) fed to you as
  background reference -- it is never something the product itself said.
  If a sentence you're about to use as claim_text sounds like a legal
  definition or statute (formal, third-person, describing a general
  practice rather than this specific product) rather than marketing copy,
  you have the wrong source -- go back and find the actual product sentence,
  or drop the claim if there isn't one. Never translate or paraphrase
  claim_text either.
- risk_rationale: your own short, specific reason for THIS claim (max 15
  words). Never repeat these category definitions or instructions back as
  the rationale.
- Skip recipes, serving suggestions, and pure taste/sentiment description --
  see the puffery rule above. A sentence giving USAGE instructions (how/where
  to use the product) is not a health or efficacy claim, even if it mentions
  a benefit in passing -- if the sentence is telling the consumer what to DO
  with the product rather than asserting something the product itself
  possesses, it is not a claim.
- Be EXHAUSTIVE, not just correct: most real products with any marketing
  copy at all have MULTIPLE distinct claims, often 4-10, each about a
  different subject (origin, composition, health, environment...). Read
  every sentence in PRODUCT DESCRIPTION on its own. Finding one clear claim
  and stopping there is wrong if other sentences also assert something
  checkable -- go through the ENTIRE description, not just the first or
  most obvious claim. Missing a real claim is a worse error than including
  one you're only moderately confident about (that's what risk_level is
  for -- MEDIUM exists precisely for claims you're not fully certain of).
- No claims found -> empty array. Never invent a claim not in the text. But
  do not default to a single claim either -- verify you checked every
  sentence before deciding you're done.
- If a CANDIDATE LEGAL CONTEXT section is present: it was retrieved by
  embedding similarity, not verified -- treat it as reference material that
  may help sharpen a risk_rationale, never as confirmation that a claim
  exists, which category/risk_level it gets, or (see above) as a source for
  claim_text itself. Some or all listed passages may be irrelevant to this
  specific product; do not force a claim to match one just because it was
  retrieved."""

# --- Pre-filter: cut description down to claim-adjacent fragments before --
# it ever reaches the model. On local Ollama, prefill time scales with
# input tokens, so this is the main latency lever for long product
# descriptions that are mostly recipe filler. Falls back to the full
# description if no keyword hits, so it never silently zeroes out a record.
#
# Widened from the ECGT version, which only matched environmental terms
# (ambiente, riciclat, plastica...). Left as-is, that filter would have
# silently stripped out nutrition/origin/composition sentences -- exactly
# the claim types UCPD scope is now meant to catch -- before the model ever
# saw them. Now also matches nutrition/health, origin, composition, and
# price/value language.
CLAIM_KEYWORDS = re.compile(
    r"(ambiente|sostenib|riciclat|riciclabil|plastica|carta|imballaggi|imballagg|"
    r"biodegrad|compostabil|biologic|naturale|natura|co2|carbon|climate|neutral|"
    r"eco[- ]?friendly|green|impatto|filiera|certificat|km zero|territorio|"
    r"raccolta|verde|rispett|"
    # nutrition / health
    r"calori|grass|magr|light|leggero|proteic|vitamin|calcio|fosforo|"
    r"saziant|nutrit|dieta|sportiv|forma fisica|salute|benefici|ricc[ao] (?:di|in)|"
    r"fonte di|"
    # origin / provenance
    r"italian|origine|provenien|dop\b|igp\b|denominazione|allevat|pascol|"
    r"montagna|territorio|"
    # composition
    r"100%|ingredient|latte (?:crudo|fresco)|non pastorizzat|edibile|commestibil|"
    # price / value
    r"qualità.{0,15}prezzo|conveni|risparm|economic|"
    # safety/storage instructions worth flagging as trivialized
    r"consumare entro|conservare|superflu)",
    re.IGNORECASE,
)
# Old name kept as an alias in case other code in this package still imports
# GREEN_KEYWORDS directly.
GREEN_KEYWORDS = CLAIM_KEYWORDS

# Scrape artifact: packaging/disposal badges (e.g. "Vaschetta e Film - 7 -
# Raccolta Plastica") are separate UI elements on the source page with no
# delimiting punctuation from whatever text precedes them, so a short claim
# right before one (e.g. "Meno plastica") ends up fused into the same
# fragment as the badge instead of splitting into two. Matched by its
# container word (Vaschetta/Incarto/Film/Confezione/Flowpack) followed
# shortly by "Raccolta" -- inserting a split boundary right before it
# separates the badge from whatever precedes it without needing a
# general-purpose sentence segmenter.
_PACKAGING_BADGE_BOUNDARY = r"(?=\b(?:Vaschetta|Incarto|Film|Confezione|Flowpack)\b[^.\n]{0,30}?Raccolta\b)"

# Same scrape-artifact problem on the OTHER side of a packaging badge: the
# structured product-spec sheet that follows it (Denominazione di vendita /
# Marchio / Conservazione / Paese di origine / Produttori / Ingredienti e
# valori nutrizionali / Allergeni / Tracciabilita) has no punctuation
# separating its own fields either, so without a closing boundary the badge
# fuses into one giant fragment with the entire rest of the spec sheet --
# e.g. "Vaschetta - Plastica - Raccolta Plastica  Segui sempre le regole del
# tuo comune ... Denominazione di vendita ... Ingredienti e valori
# nutrizionali ... Allergeni ...". That fragment matches CLAIM_KEYWORDS on
# "raccolta"/"plastica" and gets handed to the environmental-claim reranker
# as if it were one claim, when in reality it's a disposal badge glued to
# ~200 words of unrelated mandatory label text -- this was the single
# biggest driver of the false-positive rate measured in reranked_v6_8b_top20
# (Crescenza/Stracchino/Asiago/Emmental/Maasdam ads all failed this way).
# Inserting a boundary before each of these field labels isolates them same
# as the badge boundary above, so nutrition-table numbers (needed elsewhere,
# e.g. to catch "e tra i pochi formaggi magri" contradicting a high-fat
# value) stay intact as their own fragment instead of diluting a "claim".
_LABEL_BOUNDARY = (
    r"(?=\b(?:Denominazione di vendita|Marchio|Conservazione:|Paese di origine|"
    r"Produttori\b|Confezionato per|Prodotto per|Ingredienti e valori nutrizionali|"
    r"Valori nutrizionali|Allergeni|Additivi|Tracciabilità|"
    r"Segui sempre|Verifica (?:le|sempre))\b)"
)

# Mandatory disclosures that superficially match CLAIM_KEYWORDS (they contain
# words like "ambiente"/"raccolta"/"plastica") but are never a voluntary claim
# about the product -- they're required-by-law labeling text present on
# nearly every ad regardless of what the product actually asserts. Dropped
# outright rather than left for the LLM to reject each time: rerank_matches.py's
# own system prompt already carries worked counter-examples for exactly these
# (packaging bin-sorting codes, DOP/IGP as an official scheme) and the smaller
# local models still matched on them whenever they leaked into candidate text.
_MANDATORY_DISCLOSURE_PATTERNS = [
    re.compile(r"^Conad per l'ambiente\s*$", re.IGNORECASE),
    re.compile(
        r"^(?:Vaschetta|Incarto|Film|Confezione|Flowpack)\b[^.\n]{0,40}?Raccolta\s+\w+\s*$",
        re.IGNORECASE,
    ),
    re.compile(r"^(?:Segui|Verifica)\b.{0,80}?(?:regole del tuo comune|disposizioni del tuo comune)", re.IGNORECASE),
]


def _is_mandatory_disclosure(fragment: str) -> bool:
    return any(p.search(fragment) for p in _MANDATORY_DISCLOSURE_PATTERNS)


def _split_claim_sentences(description: str) -> List[str]:
    """Split into sentence-ish fragments and keep only the ones mentioning
    claim-adjacent terms (nutrition, origin, composition, price/value,
    environmental, safety instructions -- the full UCPD scope, not just
    environmental claims). Building block behind _prefilter_description;
    exposed separately for callers that want the individual sentences
    rather than one joined string (e.g. src/knowledge/prepare_ads_chunks.py,
    which embeds each claim-adjacent sentence as its own chunk instead of
    concatenating them -- concatenation dilutes a short embedding vector
    with whatever unrelated sentences also happened to match a keyword).

    Fragments that are purely a mandatory disclosure (packaging bin-sorting
    badge, the "Conad per l'ambiente" section header, the boilerplate
    "verifica le regole del tuo comune" sentence) are dropped even though
    they match CLAIM_KEYWORDS -- see _MANDATORY_DISCLOSURE_PATTERNS."""
    if not description:
        return []
    fragments = re.split(
        r"(?<=[.!?])\s+|\n+|" + _PACKAGING_BADGE_BOUNDARY + "|" + _LABEL_BOUNDARY, description
    )
    return [
        f.strip()
        for f in fragments
        if f.strip() and CLAIM_KEYWORDS.search(f) and not _is_mandatory_disclosure(f.strip())
    ]


def _prefilter_description(description: str) -> str:
    """Keep only sentence-ish fragments mentioning claim-adjacent terms.
    Returns the full original description if nothing matches, so a gap in
    the keyword list degrades to "no speedup" rather than "missed claim"."""
    hits = _split_claim_sentences(description)
    return " ".join(hits) if hits else (description or "")


# Legal grounding is embedding-retrieval-only (src/knowledge/compare_e5.py,
# tuned config center=True/csls=True/csls_k=15 -- see tune_retrieval.py),
# not LLM-reranked: rerank_matches.py's per-ad LLM verdict is too slow/costly
# (~2-3 min/ad) for what this needs, which is just candidate context, not a
# confirmed verdict. Measured Hit@7 against golden/canonical/*.json: ~37%
# for claims with a real specific legal chunk (environmental, endorsement,
# medicinal-cure, offset-neutrality), ~16% for the generic UCPD_Art6/Art7
# catch-all that most other categories map to -- i.e. retrieval is often
# wrong. Chunks are therefore injected as UNLABELED candidate context ("may
# or may not be relevant"), never as an asserted fact the model should defer
# to -- see the "Rules" note in SYSTEM_PROMPT and the low hit rate above.
#
# Capped by total word count, not just chunk count: a real top-7 grounding
# set ranges from ~200 to ~2000 words (measured across 889 products across
# all 4 retailers), median ~789. Truncating the lowest-ranked (least
# similar) chunks first when a pathological long-chunk case would otherwise
# blow the token budget below keeps the most relevant chunks intact.
MAX_GROUNDING_WORDS = 1400  # covers ~90th percentile of observed real top-7
                            # grounding sets without sizing num_ctx to the
                            # rare ~2000-word worst case.


def _format_grounding(chunks: List[dict]) -> str:
    """chunks: compare_e5.py top_matches shape (each with legal_chunk_id,
    legal_title, legal_text), already ranked best-first. Truncates from the
    end (lowest-ranked first) if the combined word count exceeds
    MAX_GROUNDING_WORDS."""
    kept = []
    total_words = 0
    for chunk in chunks:
        words = len((chunk.get("legal_text") or "").split())
        if kept and total_words + words > MAX_GROUNDING_WORDS:
            break
        kept.append(chunk)
        total_words += words

    entries = "\n\n".join(
        f"[{c['legal_chunk_id']}] {c['legal_title']}\n{c['legal_text']}" for c in kept
    )
    return f"""CANDIDATE LEGAL CONTEXT (retrieved by embedding similarity, NOT verified --
some or all of these may be irrelevant to this specific product; use your own
judgment about which, if any, actually apply):
{entries}"""


def _build_user_prompt(product: dict, description: str, grounding_chunks: Optional[List[dict]] = None) -> str:
    filtered = _prefilter_description(description)
    # Only inserted when grounding_chunks is given, so the no-grounding
    # prompt is byte-identical to every prior run (no stray blank line).
    grounding_section = f"\n\n{_format_grounding(grounding_chunks)}\n" if grounding_chunks else ""
    return f"""Analyze the following Italian food product and extract all claims that
may be unfair under the EU Unfair Commercial Practices Directive (UCPD).

PRODUCT NAME: {product.get("name", "N/A")}
MARKETING BADGE: {product.get("marketing_badge", "none")}

PRODUCT DESCRIPTION (pre-filtered for claim-relevant content):
{filtered or "No description available"}{grounding_section}

Extract every claim covered by the category list in the system prompt."""


def _repair_misplaced_commas(raw: str) -> str:
    """Fix a specific grammar-decoding glitch seen with Ollama's JSON-Schema
    constrained output: a comma sometimes lands on its own line *before* the
    next key instead of right after the previous value, e.g.:

        "risk_level": "HIGH"
        ,
        "risk_rationale": "..."

    instead of the valid:

        "risk_level": "HIGH",
        "risk_rationale": "..."

    This is a mechanical, low-risk fix: it only moves a comma that's already
    present to the position immediately after the preceding value, it never
    inserts or removes content. Left for json.loads to validate afterward --
    if the result still doesn't parse, the repair didn't apply cleanly and
    the caller falls through to the original error as before.
    """
    # comma alone on a line (with only whitespace) -> move it to glue onto
    # the end of the previous non-whitespace character
    return re.sub(r'(["\d\}\]])\s*\n\s*,\s*\n', r'\1,\n', raw)


USE_SCHEMA_GRAMMAR = True  # flip to False to A/B test speed: grammar-
                           # constrained decoding (the JSON Schema passed to
                           # `format`) is what fixed the enum-leak bug from
                           # earlier (model echoing "A | B | C" back as a
                           # literal value), but constrained decoding has a
                           # real, well-documented generation-speed cost --
                           # often 2-5x slower per token, scaling with how
                           # branchy the grammar is. A 6-way x 5-way x 3-way
                           # nested enum schema is non-trivial as grammars go.
                           # Given the 94.7s/~1000-token result (~10 tok/s,
                           # slow for a 3B model on 100% GPU), this is the
                           # most likely cause of the slowdown, more so than
                           # prompt length at this point. Set this to False
                           # to fall back to loose "format": "json" mode and
                           # see if speed recovers -- if it does, you're
                           # trading the enum-leak protection for speed, and
                           # that's a real decision to make deliberately
                           # rather than something to default silently.


def extract_claims(
    product: dict, description: str, model: str = "llama3.2", grounding_chunks: Optional[List[dict]] = None,
    temperature: float = 0,
) -> dict:
    """
    Extract greenwashing-relevant claims from a product description.

    Args:
        product: full product record (for name, brand, badge fields)
        description: the description string to analyze
        model: ollama model name
        grounding_chunks: optional retrieved legal chunks (compare_e5.py
            top_matches shape) to inject as unlabeled candidate context --
            see the comment above _format_grounding for why this is
            embedding-only, not LLM-reranked, and why it's capped by word
            count. None (the default) preserves the exact prompt/token
            budget of every prior run.
        temperature: 0 (default) is fully greedy -- picked to kill llama3.2's
            run-to-run claim-count drift. Measured on a larger model
            (llama3.3:70b) to have a DIFFERENT failure mode at temperature=0:
            it converges on ~1-2 claims per product almost regardless of how
            many real claims exist, which prose instructions telling it to
            "be exhaustive" did not change -- consistent with greedy decoding
            always taking the single highest-probability continuation
            (closing the array early) rather than exploring further options.
            Exposed as a parameter, not hardcoded, so this can be A/B tested
            per model rather than guessed at.

    Returns:
        dict with a "claims" list, each entry matching SCHEMA
    """
    # num_ctx must grow when grounding is attached -- a real top-7 grounding
    # block runs ~200-2000 words (median ~789), capped at MAX_GROUNDING_WORDS
    # (~1400 words =~ 1960 tokens at ~1.4 tok/word for Italian legal text).
    # SYSTEM_PROMPT itself was re-measured after the golden-set category
    # rewrite (11-way taxonomy + disambiguation/chemistry/MEDIUM-default
    # rules + an 8-claim worked example): ~1150 words / ~8800 chars, ~2000
    # tokens -- roughly 3x the ~600 tok the PREVIOUS num_ctx sizing assumed.
    # That gap, not num_predict, was the real cause of truncation reappearing
    # on multi-claim records (e.g. "Integratore alimentare al mirtillo"):
    # system(~2000) + schema(~190, measured from RESPONSE_SCHEMA's compact
    # JSON) + user overhead(~60) + num_predict(3500) + grounding(~1960) +
    # description headroom(~590) =~ 8300, already past the old 6000 ceiling
    # -- Ollama truncates generation when num_ctx runs out, which looks
    # identical to a num_predict truncation but isn't fixed by raising
    # num_predict alone. Baseline (ungrounded) budget: same system+schema+
    # overhead+num_predict+description =~ 6340, rounded up to 7000. Grounded:
    # +1960 for the capped grounding block =~ 8300, rounded up to 9000 --
    # real margin above the measured max, not just matching it.
    num_ctx = 9000 if grounding_chunks else 7000

    response = httpx.post(
        OLLAMA_URL,
        json={
            "model": model,
            "system": SYSTEM_PROMPT,
            "prompt": _build_user_prompt(product, description, grounding_chunks),
            "stream": False,
            "format": RESPONSE_SCHEMA if USE_SCHEMA_GRAMMAR else "json",
            "options": {
                "temperature": temperature,  # see the temperature arg's
                                       # docstring above -- 0 (the default)
                                       # was chosen to remove llama3.2's
                                       # run-to-run claim-count drift (4 vs 5,
                                       # 2 vs 4 claims etc.), but is suspected
                                       # to cause a DIFFERENT under-extraction
                                       # problem on larger models.
                "num_predict": 3500,   # was 2500, which still truncated on
                                       # "Integratore alimentare al mirtillo"
                                       # (a supplement -- many per-ingredient
                                       # efficacy claims, ~18-20 pre-filter is
                                       # plausible for this product type).
                                       # Sizing to 20 claims at ~170 tok/claim
                                       # + 30 wrapper overhead =~ 3430 -- real
                                       # margin above the observed max. NOTE:
                                       # the num_ctx bump below is the more
                                       # important fix this round -- see that
                                       # comment for why num_predict alone
                                       # wasn't the actual bottleneck here.
                "num_ctx": num_ctx,     # was 4000/6000 -- too small even for
                                        # num_predict=2500 once SYSTEM_PROMPT's
                                        # real size is counted; see the
                                        # comment above this function.
            },
        },
        timeout=600,  # was 200. The real problem causing timeouts was call
                      # cost (prompt size + num_ctx + per-claim rationale
                      # length), now cut above. This is raised as a safety
                      # margin so a still-slow call on llama3.2 (a small,
                      # CPU-friendly but not fast model) completes and gets
                      # recorded as a real result instead of being killed by
                      # the client and lost. If runs are still timing out at
                      # 600s after the cuts above, that's a sign llama3.2
                      # itself is too slow for this workload on your hardware,
                      # not a config problem -- worth trying a smaller/faster
                      # model name or quant at that point.
    )
    response.raise_for_status()
    raw = response.json()["response"]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try repairing the misplaced-comma glitch before giving up on the raw text.
    try:
        return json.loads(_repair_misplaced_commas(raw))
    except json.JSONDecodeError:
        pass

    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            try:
                return json.loads(_repair_misplaced_commas(match.group()))
            except json.JSONDecodeError:
                pass

    # If we get here, the JSON is genuinely broken (the comma-repair attempt
    # above handles one specific cosmetic glitch, but most real-world
    # failures at this point are length-related): num_predict ran out before
    # the model finished the object, leaving a dangling string or no closing
    # brace at all.
    looks_truncated = not raw.rstrip().endswith("}")
    hint = (
        " (output does not end with a closing brace — truncated by "
        "num_predict; raise it further, e.g. to 2000-2500, especially for "
        "records likely to produce many claims)"
        if looks_truncated else
        " (has a closing brace but still won't parse — inspect the Raw text "
        "below for the actual syntax break, since this isn't the truncation "
        "case)"
    )
    raise ValueError(f"Model returned invalid JSON{hint}\n\nRaw: {raw[:500]}")


def _validate_claims(claims: List[dict]) -> Tuple[List[dict], List[dict]]:
    """Drop rows with an empty claim_text (seen in a prior run: a placeholder
    row with "" and no real content), and drop LOW-risk claims.

    Deliberately NOT checking claim_text against the source description
    anymore. An earlier version did, which caught real model corruption
    (e.g. "Meno plastica" mangled into "Menoplasica"/"Menore plastica", or
    the model inserting a word that wasn't in the source) -- but it also
    false-rejected a larger number of valid claims over cosmetic
    whitespace/capitalization differences, even after normalizing for those.
    Trade-off accepted: corrupted claim_text will now pass through into
    `claims` unflagged. If that starts showing up in practice, the fix is
    to reintroduce a verbatim check (see git history / _normalize_for_match)
    rather than trying to patch around it here.

    The LOW-risk drop is deliberately a CODE filter, not a prompt instruction:
    SYSTEM_PROMPT tells the model to emit every claim it finds, including
    LOW-risk ones, and never to silently omit one -- otherwise a wrong "this
    is LOW, skip it" judgment call vanishes with nothing to audit later (the
    same reason golden/canonical/*.json tracks LOW-risk/irrelevant_claim rows
    explicitly instead of dropping them at labeling time). Filtering happens
    only here, downstream of generation, so every LOW-risk call the model
    made is still visible in `dropped_claims` for review.

    Returns (valid, dropped) so both kinds of drops are still visible in the
    output instead of silently vanishing.
    """
    valid, dropped = [], []
    for c in claims:
        text = (c.get("claim_text") or "").strip()
        if not text:
            dropped.append({**c, "_dropped_reason": "empty claim_text"})
            continue
        if (c.get("risk_level") or "").upper() == "LOW":
            dropped.append({**c, "_dropped_reason": "risk_level=LOW (filtered by policy)"})
            continue
        valid.append(c)
    return valid, dropped


def _load_grounding_by_ean(matches_path: str) -> Dict[str, List[dict]]:
    """matches_path: a compare_e5.py output (matches.json shape), keyed by
    query_ad_id -- which src/knowledge/prepare_ads_chunks.py sets to the
    product's ean, same join key extract_from_file uses below."""
    with open(matches_path, encoding="utf-8") as f:
        matches = json.load(f)
    return {m["query_ad_id"]: m["top_matches"] for m in matches}


def extract_from_file(
    filename: str, model: str = "llama3.2", matches_file: Optional[str] = None, temperature: float = 0
) -> Tuple[List[dict], List[dict]]:
    records = list(iter_records(filename))
    total = len(records)
    results = []
    failed = []
    total_dropped = 0
    run_start = time.monotonic()

    grounding_by_ean = _load_grounding_by_ean(matches_file) if matches_file else {}

    for i, (idx, record) in enumerate(records, 1):
        name = record.get("name", f"record {idx}")
        print(f"[{i}/{total}] {name}", end=" ... ", flush=True)

        call_start = time.monotonic()
        try:
            description = record["description"]
            grounding_chunks = grounding_by_ean.get(record.get("ean")) if matches_file else None
            result = extract_claims(
                product=record,
                description=description,
                model=model,
                grounding_chunks=grounding_chunks,
                temperature=temperature,
            )
            elapsed = time.monotonic() - call_start

            claims, dropped = _validate_claims(result.get("claims", []))
            total_dropped += len(dropped)
            results.append({
                "index": idx,
                "ean": record.get("ean"),
                "name": record.get("name"),
                "claims": claims,
                "dropped_claims": dropped,  # empty list in the common case;
                                            # kept on every record (not just
                                            # ones with drops) so the schema
                                            # is consistent across the file
                "elapsed_seconds": round(elapsed, 2),  # wall-clock time for
                                                        # the model call only
                                                        # (excludes validation,
                                                        # which is negligible)
            })
            suffix = f" ({len(dropped)} dropped)" if dropped else ""
            print(f"{len(claims)} claims found{suffix} [{elapsed:.1f}s]")

        except Exception as e:
            elapsed = time.monotonic() - call_start
            print(f"FAILED after {elapsed:.1f}s: {e}")
            failed.append({"index": idx, "ean": record.get("ean"), "name": name, "error": str(e)})
            time.sleep(2)
            continue

    total_elapsed = time.monotonic() - run_start
    avg_per_record = total_elapsed / total if total else 0
    print(
        f"\nDone: {len(results)} ok, {len(failed)} failed, {total_dropped} claims "
        f"dropped by validation"
    )
    print(
        f"Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min), "
        f"avg {avg_per_record:.1f}s/record"
    )
    if failed:
        print("Failed records:")
        for f in failed:
            print(f"  [{f['index']}] {f['name']} — {f['error']}")

    return results, failed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="filename in data/raw/, e.g. 06.25.json")
    parser.add_argument("--model", default="llama3.2")
    parser.add_argument("--out", default=None, help="optional output path for results json")
    parser.add_argument(
        "--matches", default=None,
        help="optional compare_e5.py output (matches.json shape) to inject as unlabeled legal "
        "grounding context, joined by ean -- see src/knowledge/tune_retrieval.py for the tuned "
        "retrieval config this was measured against",
    )
    parser.add_argument(
        "--temperature", type=float, default=0,
        help="0 (default) is fully greedy -- fixes llama3.2's run-to-run claim-count drift, but "
        "measured to cause a larger model (llama3.3:70b) to converge on ~1-2 claims per product "
        "almost regardless of ground truth. Try a small positive value (e.g. 0.2) on a larger "
        "model if it's under-extracting at temperature=0.",
    )
    args = parser.parse_args()

    results, failed = extract_from_file(
        args.file, model=args.model, matches_file=args.matches, temperature=args.temperature
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
            fail_path.parent.mkdir(parents=True, exist_ok=True)
            fail_path.write_text(json.dumps(failed, indent=2, ensure_ascii=False))
            print(f"Failed records saved to {fail_path}")
    else:
        print(json.dumps(results[:2], indent=2, ensure_ascii=False))