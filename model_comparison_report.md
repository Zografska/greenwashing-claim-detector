# UCPD Claim Extraction — Model/Pipeline Comparison Report

Prepared for cross-model brainstorming. Written to be self-contained — no
prior conversation context assumed.

## 1. What this system does

Extracts consumer-law-relevant claims from Italian grocery product
descriptions (scraped e-commerce listings) and classifies each claim into
one of 11 categories under the EU Unfair Commercial Practices Directive
(UCPD, Dir. 2005/29/EC): `unsubstantiated_health_or_efficacy_claim`,
`nutrition_content_claim`, `misleading_composition_or_ingredient_claim`,
`misleading_authenticity_or_origin_claim`,
`misleading_superiority_or_absolute_claim`, `unfair_comparison`,
`misleading_endorsement_claim`, `fake_or_unverified_label`,
`environmental_unsubstantiated`, `offset_based_neutrality`,
`irrelevant_claim`. Each claim also gets a `risk_level` (HIGH/MEDIUM/LOW).

All models run locally via Ollama (no API-based LLMs used). Models
available: `llama3.2:1b/3b`, `llama3.1:70b`, `llama3.3:70b`,
`deepseek-r1:70b` (a reasoning model — emits a `<think>...</think>` trace
before its answer).

## 2. Evaluation methodology

`src/evaluate.py` is now a real, implemented eval harness (this line used
to say it was a stub, and it wasn't stale by accident: it's what's checked
in as of this commit, it just wasn't reflected in this doc). Numbers in §4
below still predate it and come from the one-off ad hoc script this section
used to describe. See §8 for the Phase 0 pass that fixed a real bug in it
(the category-accuracy computation was silently comparing two disjoint
taxonomies and reporting near-zero accuracy no matter what) and for fresh
numbers computed with the fixed harness.

Original description of the ad hoc script's methodology, kept for
historical context on how the §4 numbers below were produced:

- **Gold set**: a 20-product stratified sample (`golden/samples/canonical/
  sample_coop.json`) drawn from a 250-product hand-labeled Coop golden set,
  6 products with no real claims (`hard_no`), 8 ambiguous (`in_between`), 6
  clear-cut (`hard_yes`). Gold has 49 total labeled claims across the 20
  products.
- **Matching**: relaxed span-overlap, not exact string match. A predicted
  claim matches a gold claim if their word-sets overlap ≥50% of the
  smaller set's size (word-containment style Jaccard variant), matched
  greedily one-to-one per product, ranked by overlap score. Threshold was
  varied 0.3–0.7 and rankings were stable across that range.
- **Metrics reported**: precision/recall/F1 on the span match itself;
  category accuracy computed ONLY on spans that matched (i.e. "given we
  found the right claim, did we also get the category right"); a separate
  "hard_no false positive" count = how many of the 6 zero-claim products a
  run incorrectly generated ≥1 claim for; average wall-clock seconds/product.

## 3. Architecture / pipelines tried

**(a) `src/extraction.py` — single-pass extraction.** One Ollama call per
product: a system prompt with the 11 category definitions + several
disambiguation rules (see §5) + a JSON-Schema-constrained response asking
the model to emit an open-ended array of `{claim_text, category,
risk_level, risk_rationale}` objects. Supports:
  - `--matches <file>`: inject a per-product top-7 embedding-retrieved
    legal-passage shortlist as unlabeled "candidate context" (retrieval via
    a separate E5-embedding pipeline in `src/knowledge/`).
  - `--full-grounding`: instead of top-7 retrieval, attach the ENTIRE legal
    corpus (56 chunks / ~4500 formatted words / ~6300 tokens, ECGT+UCPD
    combined) every time.
  - `--reasoning-model`: swaps in a rebalanced system prompt
    (`SYSTEM_PROMPT_REASONING`) for reasoning models — see §5.
  - `--num-predict`/`--num-ctx`/`--limit`: raw overrides for models whose
    token cost isn't covered by the existing tiers (7000/9000/14000-15000
    depending on grounding mode).

**(b) `src/dissected_extraction.py` — per-clause pipeline.** Built to test
whether an earlier hypothesis ("large models collapse to ~1-2 claims per
product regardless of ground truth") was a framing artifact of the
open-ended array in (a). Three steps per product:
  1. Segment description into clauses in pure Python (regex-based sentence
     + comma/conjunction splitting).
  2. One Ollama call classifies EVERY clause into one of the 11 categories
     or `not_a_claim` — response schema has `minItems == maxItems ==
     clause count`, so the model structurally cannot return fewer
     classifications than clauses given.
  3. A second, separate Ollama call assigns `risk_level` +
     `risk_rationale`, only over clauses flagged as real claims in step 2.
  4. A hard-coded backstop drops every claim assigned `risk_level=LOW`
     before final output (same policy as pipeline (a)).

  Now supports independent models per step: `--model` for
  detection/categorization, `--risk-model` for the severity call (defaults
  to `--model` if unset) — plus independent `--risk-*` overrides for
  schema-grammar/num-predict/num-ctx/prompt-variant on that second call.

**(c) Model-pairing experiment.** Given (b)'s two-call structure, tried
using a different model for detection vs. risk-assessment, motivated by
each model's distinct measured strength (see §4).

## 4. Full results (relaxed span-match against the 20-product gold set)

| Run | Total claims | Precision | Recall | F1 | Category acc (on matched) | Hard_no FP (of 6) | Avg sec/product |
|---|---|---|---|---|---|---|---|
| llama3.2:3b (plain, pipeline a) | 50 | 0.22 | 0.22 | 0.22 | 0.18 | 5 | 2.5s |
| **llama3.3:70b (plain, pipeline a)** | 52 | 0.39 | **0.41** | **0.40** | 0.65 | 4 | 14.2s |
| dissected_3b (pipeline b, 3b both steps) | 66 | 0.27 | 0.37 | 0.31 | 0.33 | 2 | 6.1s |
| dissected_70b (pipeline b, 70b both steps) | 62 | 0.29 | 0.37 | 0.32 | 0.56 | 3 | 162.1s |
| full_grounding_3b (pipeline a, `--full-grounding`) | 21 | 0.24 | 0.10 | 0.14 | **0.00** | 0 | 3.4s |
| full_grounding_70b (pipeline a, `--full-grounding`) | 41 | 0.42 | 0.35 | 0.38 | 0.41 | 5 | 36.7s |
| full_grounding_deepseek_70b (pipeline a) | 19 | 0.37 | 0.14 | 0.21 | **0.71** | **0** | 29.6s |
| ungrounded_deepseek_70b (pipeline a, no grounding) | 37 | 0.41 | 0.31 | 0.35 | 0.60 | **1** | 13.2s |
| ungrounded_deepseek_70b + `--reasoning-model` | 36 | 0.39 | 0.29 | 0.33 | 0.57 | 1 | 9.7s |
| dissected: 3b detect + deepseek risk (uncalibrated) | 36 | 0.36 | 0.30 | 0.33 | 0.46 | 1 | 9.2s |
| dissected: 3b detect + deepseek risk (calibrated prompt) | 39 | 0.31 | 0.25 | 0.27 | 0.50 | 1 | — |

(Some rows computed on a 19/20-product basis due to one transient failure
mid-session, since fixed — treat as directionally reliable, not
decimal-precise across every row. `deepseek-r1:70b` and `llama3.1:70b`
were not tried in every combination; `llama3.2:1b` was not tried at all.)

**Bottom line: plain, ungrounded llama3.3:70b (pipeline a, single-pass,
no grounding, no dissection) remains the best overall option by F1.**
Ungrounded `deepseek-r1:70b` (same pipeline, no grounding) is the best
option specifically when minimizing false positives matters more than
raw recall. Every other variant tried — full-grounding (either model
size), the dissected per-clause pipeline (either model), and every
cross-model hybrid — underperforms one or both of those two on F1.

## 5. The dead end — deepseek-r1:70b's risk-severity calibration

This is the part most worth fresh eyes on.

**The finding.** `src/dissected_extraction.py`'s two-call structure let us
isolate detection from risk-assessment cleanly: run detection with
llama3.2:3b once, then run the SAME flagged clauses through the risk call
twice — once with 3b, once with deepseek-r1:70b. Same exact input clauses
both times. Risk-level distributions:

| Risk model (same input clauses) | HIGH | MEDIUM | LOW |
|---|---|---|---|
| llama3.2:3b | 29% | 50% | 21% |
| deepseek-r1:70b | 9% | 44% | **47%** |

Both models received the IDENTICAL system prompt instruction (a
"MEDIUM-by-default" rule: *"'nothing contradicts this' is NEVER sufficient
grounds for LOW... reserve LOW only for a claim you can point to real
backing for"*). deepseek assigns `LOW` more than 2x as often as 3b, and
`HIGH` a third as often, on the exact same claims.

**Why this matters.** Both pipelines have a hard-coded downstream rule:
drop every `risk_level=LOW` claim before final output (a deliberate design
choice — LOW-risk claims are treated as noise/non-actionable). Since
deepseek calls LOW far more often, this single calibration gap is the
mechanism behind EVERY deepseek-involving pipeline's low recall measured
this session:
  - Full-grounding + deepseek: recall 0.14 (worst of any variant except
    full-grounding+3b)
  - Ungrounded + deepseek: recall 0.31 (still below plain 70b's 0.41)
  - Dissected hybrid (3b detect + deepseek risk): recall 0.30

It is NOT a detection/extraction problem — deepseek's actual claim-finding
and categorization (when it does commit) is good; its category accuracy
on matched claims (0.60–0.71) is the best of anything tried. The problem
is specifically that it's reluctant to call things HIGH/MEDIUM severity.

**Two independent fix attempts, both null results:**

1. `SYSTEM_PROMPT_REASONING` (pipeline a): a rebalanced main extraction
   prompt adding an explicit "REASONING-MODEL NOTE" telling the model to
   default to inclusion under uncertainty rather than exclusion, plus a
   note that legal-context severity shouldn't raise the bar for what
   counts as a claim. Applied to the FULL single-pass extraction task (not
   the isolated risk call). Result: recall/F1/category-accuracy all
   *slightly worse*, not better (F1 0.35→0.33). No measured benefit.

2. `RISK_SYSTEM_PROMPT_REASONING` (pipeline b): a targeted rebalance of
   JUST the risk-assessment prompt, explicitly telling the model: *"If
   your rationale for LOW amounts to 'this seems plausible' or 'nothing
   here contradicts it,' that is MEDIUM, not LOW... do not let careful
   reasoning talk you into a lower severity than a less deliberate
   judgment would reach."* Applied on the SAME isolated-risk-call
   experiment as the table above. Result: LOW rate went from 47%→49% (no
   improvement, arguably worse), and pipeline F1 dropped further
   (0.33→0.27).

**Working hypothesis (unconfirmed):** deepseek-r1's conservatism here is
an intrinsic property of its own alignment/reasoning process on
legal-severity judgments — the model's `<think>` trace seems to generate
its own mitigating justifications for lower severity regardless of
explicit prompt instruction not to. Two independent, differently-worded
correction attempts both failed to move the number at all, which argues
against "just word the prompt better" as a viable path forward.

**What HASN'T been tried, for brainstorming:**
- Few-shot calibration examples showing exactly what should be HIGH/MEDIUM
  vs LOW (both fixes so far were abstract instructions, not examples —
  though note the rest of this codebase deliberately avoids concrete
  example text in prompts due to a measured leak-bug class on smaller
  models; would need to verify that risk doesn't reappear for a reasoning
  model specifically).
  - Sampling-based correction: multiple risk-call samples at
    temperature>0 + majority vote, instead of a single greedy call — no
    temperature/sampling variation has been tried on the risk call
    specifically (only on the full extraction task, where temperature 0
    vs 0.2 was measured byte-identical for a non-reasoning 70B model —
    unclear if that generalizes to deepseek's risk call).
  - Disabling the `<think>` phase entirely for the risk call, if Ollama's
    API/this deepseek build supports a non-reasoning mode or a `think:
    false` parameter (untested — current setup treats `<think>` output as
    inseparable from "response" text).
  - Not dropping LOW-risk claims when the risk model is deepseek
    specifically — i.e. treating deepseek's "LOW" as calibrated
    differently from 3b/70b's "LOW" (a threshold/policy fix rather than a
    prompt fix). Never tried; would need separate validation that
    deepseek's LOW-labeled claims are actually still real claims worth
    keeping, not noise.
  - Using deepseek only as a downstream accept/reject gate on already-
    generated HIGH/MEDIUM output from another model, rather than as the
    primary risk-assigner — different role entirely, unexplored.
  - `llama3.1:70b` and `deepseek-r1:70b`'s larger-context variants
    (`_80k`/`_128k` tags mentioned as available on the server) haven't
    been tried in this comparison at all.
  - No fine-tuning/distillation has been attempted — everything above is
    zero-shot prompting against off-the-shelf model weights.

## 6. Known, separately-confirmed findings (not dead ends, just context)

- An earlier hypothesis that "llama3.3:70b/llama3.1:70b collapse to ~1-2
  claims/product regardless of gold's real count" was DEBUNKED after
  fixing an unrelated data pipeline bug (a retailer adapter was silently
  dropping 71% of products' real marketing text before it ever reached the
  model). Once fixed, plain 70b's claim count was already in line with
  gold. The dissected per-clause pipeline (b) was originally built to fix
  this now-debunked collapse hypothesis — it still exists and is usable,
  but its original motivating problem turned out not to be real.
- Full-corpus legal grounding (`--full-grounding`) was tested as an
  alternative to weak top-7 embedding retrieval (measured Hit@7 ~37%/16%
  against a separate gold set). Verdict: net negative on every model size
  tried — it dilutes rather than sharpens category judgment, and is
  meaningfully slower. Also triggered a genuine degenerate-repetition loop
  on llama3.2:3b (fixed with `repeat_penalty=1.3`/`repeat_last_n=512`,
  unrelated to the calibration issue above).

## 7. Environment constraints worth knowing before brainstorming

- Local Ollama only (no hosted API models) — all experimentation must run
  within realistic latency/VRAM budgets on a shared GPU server.
- 70B-class models: ~14-37s/product single-call, ~160s/product for the
  2-call dissected pipeline. A 20-product test run costs low-single-digit
  minutes to ~1 hour depending on variant; a 247-product full run scales
  accordingly.
- deepseek-r1:70b's `<think>` trace has an unmeasured, variable token
  cost — currently handled with generous manual `--num-predict`/`--num-ctx`
  overrides (8000-12000 / 12000-24000 depending on call), not a principled
  budget.
- No test suite, no CI. `src/evaluate.py` is now a real, committed,
  reusable eval harness (see §2, §8) — the line this used to say ("no
  formal eval harness yet") was stale, not current, as of this report's
  original writing.

## 8. Phase 0 (this pass): bug fixes + cheap ablations

Triggered by an external "prompt suite v4" review
(`.claude/reccomendations/`) that flagged three structural bugs in the
extraction pipeline (its own B1/B2/B3 naming, kept here for cross-reference)
and proposed a bigger rewrite (a pre-extraction gate, a deepseek-r1 verify
cascade, a rewritten 0-100 severity call) that's deliberately deferred to a
follow-up pass. This section covers only the bug fixes + the cheap/free
ablation rows (A0/A1/A2) from that review's matrix.

**Real bug found that predates the external review: `src/evaluate.py`'s
category accuracy was silently broken.** It mapped gold's 11 categories
through a `GOLD_TO_COARSE` dict down to an old 6-category scheme
(`ENVIRONMENTAL_CLAIM`, `NUTRITION_HEALTH_CLAIM`, ...) that `extraction.py`
stopped emitting once it was broadened to output gold's exact 11 category
strings directly. Predicted and gold categories were being compared across
two disjoint string spaces. Measured effect on the exact predictions file
behind this report's §4 "llama3.3:70b (plain, pipeline a)" row
(`results/dissect vs full/70b_predictions.json`… now that file's own numbers
have moved, see below): **old (buggy) category_accuracy = 0.0 (0/6
correct)**, **fixed category_accuracy = 0.75 (6/8 correct)**. Fixed by
deleting `GOLD_TO_COARSE` and comparing category strings directly.

**B2 (keyword prefilter) confirmed as the dominant recall ceiling.**
Measured with a new reusable script, `src/check_prefilter_coverage.py`:
before any fix, only 24/49 (49%) of gold claims on the 20-product sample
survived `_prefilter_description`, and 22 of the 25 misses (45% of all gold
claims) were lost purely by `CLAIM_KEYWORDS` coverage gaps, not a data
issue — concrete gap categories included dermatological/clinical
proof-language, tradition/authenticity phrasing, endorsement/testimonial
language, superiority-ranking phrases, and personal-care/cosmetic
vocabulary (all 6 claims on one dental-adhesive product had zero keyword
coverage). After expanding `CLAIM_KEYWORDS`: 20-sample survival rose to
46/49 (93.9%), **0 remaining prefilter-caused misses** (the 3 residual
misses are a pre-existing, out-of-scope data gap — claims sourced from
`recycling_other`, which `src/adapters/coop.py` deliberately doesn't join
into the extraction input). Re-checked against the full 250-product set to
confirm generalization: went from 352/562 (62.6%) to 434/562 (77.2%)
survival, prefilter-caused misses down from 143 to 61 — the residual gap on
the full set is real (heavily personal-care/cosmetics vocabulary) but hit
diminishing returns for a "cheap fixes" pass; left for a follow-up if that
category becomes the binding constraint. `_MANDATORY_DISCLOSURE_PATTERNS`'
Conad-only "per l'ambiente" pattern was also generalized to any brand
prefix — confirmed via the Coop data that the exact analogous boilerplate
exists (`Coop per l'ambiente` ×10 in `recycling_other`, plus several other
brands) but this fix is currently inert for Coop specifically, since that
field isn't joined into the extraction input today.

**B1 (`nutrition_content_claim` forced to LOW) fixed, but measured to have
zero effect on any current score.** 100% of gold's `nutrition_content_claim`
claims (13/13 full set, 2/2 sample) are themselves labeled LOW in gold, and
`extraction_prf`/`category_accuracy` already exclude every gold LOW claim
from scoring by design — so this bug was real (a genuinely risky nutrition
claim would've been forced to LOW and silently dropped) but invisible to
every metric in this report. Fixed anyway, no dedicated ablation run.

**B3 (field order: label emitted before rationale)** — real per
`RESPONSE_SCHEMA` (`claim_text → category → risk_level → risk_rationale`).
Added as an opt-in `--rationale-first` flag (both schema property order and
the prompt's worked example get reordered together) rather than a default
change, so the A2 ablation stays possible. Same pattern fixed directly
(no flag) in `src/dissected_extraction.py`'s risk call, since that
pipeline isn't the one being benchmarked here.

**A1 (drop-LOW policy on/off) — free from cache**, since `dropped_claims`
was already retained in every prior run's output. Measured on the same
70b/20-sample predictions file used above:

| drop-LOW | precision | recall | F1 | category acc | risk agreement |
|---|---|---|---|---|---|
| ON (current default) | 0.1538 | 0.2581 | 0.1928 | 0.75 (6/8) | 1.0 (8/8) |
| OFF | 0.1587 | 0.3226 | 0.2128 | 0.70 (7/10) | 0.8 (8/10) |

Keeping LOW-risk model output modestly helps span recall/F1, at a small
cost to category accuracy and risk-level agreement (the 2 additional true
positives are claims gold scored as MEDIUM/HIGH that the model itself
called LOW).

**A0 (prefilter on/off) and A2 (v3 vs v4 field order) are prepared but not
yet run** — both need a fresh model call against the project's Ollama
endpoint (`demmgpu1`, see reference memory), which wasn't reachable from
the environment this pass ran in. Commands to run once connectivity is
back (llama3.2:3b, 20-product sample — cheap, ~1 min/run):

```bash
# baseline: prefilter ON, v3 field order -- reused as both A0's "on" arm
# and A2's "v3" arm, so only 3 model calls are needed total
python3 -m src.extraction --file sample_coop_extraction_input.json \
    --model llama3.2:3b --out results/phase0/baseline_3b.json

# A0: prefilter OFF
python3 -m src.extraction --file sample_coop_extraction_input.json \
    --model llama3.2:3b --no-prefilter --out results/phase0/a0_no_prefilter_3b.json

# A2: rationale-first (v4 field order)
python3 -m src.extraction --file sample_coop_extraction_input.json \
    --model llama3.2:3b --rationale-first --out results/phase0/a2_rationale_first_3b.json

# score all three against the fixed evaluate.py
python3 -m src.evaluate --predictions results/phase0/baseline_3b.json \
    --gold golden/samples/canonical/sample_coop.json
python3 -m src.evaluate --predictions results/phase0/a0_no_prefilter_3b.json \
    --gold golden/samples/canonical/sample_coop.json
python3 -m src.evaluate --predictions results/phase0/a2_rationale_first_3b.json \
    --gold golden/samples/canonical/sample_coop.json
```

The full gate → extract-v4 → verify → severity-v4 rewrite and the rest of
the ablation matrix (A3-A9) from `.claude/reccomendations/` remain deferred
to a follow-up pass, per this pass's explicit scope decision.
