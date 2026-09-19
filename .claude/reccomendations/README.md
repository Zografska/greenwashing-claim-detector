# Prompt suite v4 — analysis and test plan

## Structural bugs found in v3 (fix before any prompt A/B)

These are not wording problems. Each one caps a metric no matter what the
prompt says, and each is verifiable with a script, not a GPU run.

### B1 — `nutrition_content_claim` is structurally unreachable

`SYSTEM_PROMPT` (extraction.py:184-187) and `RISK_SYSTEM_PROMPT`
(dissected:262-264) both instruct: nutrition_content_claim stays LOW even
when unverified. `_validate_claims` (extraction.py:836) then drops every LOW
claim.

Net effect: 1 of your 11 categories can never appear in output. If your gold
set contains nutrition claims — and Italian grocery copy is full of them —
that is pure unrecoverable recall loss, and it is charged to whichever model
happened to be running.

**Check:** `grep` the category counts in your gold set. If nutrition claims
are >10% of the 49, this alone is worth several points of recall.

### B2 — the keyword prefilter can drop gold claims before the model runs

`_prefilter_description` (extraction.py:425) keeps only fragments matching
`CLAIM_KEYWORDS`. Gold was labelled on the *full* description. Any gold claim
whose sentence lacks a keyword is unreachable — a recall ceiling below 1.0
that no model or prompt can lift.

The fallback ("return full description if nothing matches") does not save
you: it only fires when *zero* fragments match. On a product where 3
fragments match and a 4th gold claim's sentence doesn't, that claim is
silently deleted.

Related: `_MANDATORY_DISCLOSURE_PATTERNS` (extraction.py:384) is hardcoded to
**Conad** strings ("Conad per l'ambiente"). Your gold set is **Coop**. Those
patterns are either dead code on your eval set, or — worse — the Coop
equivalents are passing through unfiltered while you believe they're handled.

**Check (5 minutes, no GPU):** for each gold claim, test whether its text
survives `_prefilter_description(full_description)`. Report the survival
rate. That number is your true recall ceiling. I'd expect it to be the
single most surprising number in this whole project.

### B3 — field order defeats the rationale field

Every schema emits the label before the justification:
`risk_level` then `risk_rationale`; `category` then nothing. The model
commits to a decision, then writes prose defending a decision already made.
The rationale cannot inform the label.

This is also, mechanically, the deepseek story. You asked it not to
rationalise its way to LOW — but the schema *requires* it to pick LOW first
and rationalise second. It was never able to do what you asked.

**Fix:** swap the order (see `schemas.py`). One-line change, testable alone.

---

## Prompt-level weaknesses

| # | Issue | Location | Effect |
|---|---|---|---|
| W1 | "most real products have MULTIPLE distinct claims, often 4-10" | extraction.py:234-236 | Gold averages **2.45** claims/product. The prompt instructs the model to produce 2-4x gold. This is a direct, sufficient explanation for 4-5 hard_no FPs out of 6 — the model is doing what it was told. |
| W2 | Contradictory objectives | :169-170 vs :240-242 | "Do not invent a claim" and "missing a real claim is worse than including one you're unsure of" cannot both be followed. Under grammar-forced choice the second wins. |
| W3 | Worked example with 4 claims, risk MEDIUM/LOW/MEDIUM/HIGH | :201-212 | Few-shot examples anchor *distribution*, not just shape. The grammar already enforces shape, so this block buys nothing and costs an anchor plus ~15 lines of leak-defence text that itself names the failure mode. Delete it. |
| W4 | ~8 exclusionary rules vs 1 exhaustiveness bullet | throughout | Your own §5 hypothesis, and I think it's right — but the fix is fewer rules, not a counterweight paragraph. v4 converts parallel definitions into an ordered decision procedure. |
| W5 | 11 parallel definitions, no precedence | :109-139 | Overlapping categories with no tie-break is a plausible driver of 0.65 category accuracy. v4 gives explicit first-match-wins ordering. |
| W6 | Category + severity in one pass | schema | Two unrelated judgments share one autoregressive budget. Split. |
| W7 | "Output ONLY this JSON object — no reasoning, commentary, or text before or after it" | dissected:347-348 | Sent to `deepseek-r1`, which *must* emit `<think>`. You are instructing a reasoning model to suppress the thing it structurally does. Unknown effect, plausibly bad. Remove for reasoning models. |
| W8 | Verbatim check removed | :803-816 | The comment says it "false-rejected valid claims over cosmetic differences" — which means the model **is** paraphrasing, at an unmeasured rate. Every paraphrased span costs you a span match. Reinstate as a *logged metric*, not a filter. |
| W9 | `irrelevant_claim` vs `not_a_claim` | dissected:158-172 | A subtle distinction stated twice in prose. Likely a large slice of the confusion matrix. Check before optimising anything else. |
| W10 | English prompt, Italian source, English category names | all | Untested axis. Cheap to try. |

---

## Ablation matrix

Run in this order. Each row is one variable. Stop when the CI on the
delta excludes zero, or when you've established the axis is null.

| # | Ablation | Cost | Prediction |
|---|---|---|---|
| A0 | Prefilter ON vs OFF (v3 prompt, unchanged) | 1 run | **Largest single effect in the table.** Do this first. |
| A1 | Drop-LOW ON vs OFF | free, from cache | Recovers deepseek recall without touching the prompt |
| A2 | v3 field order vs v4 field order, v3 prompt otherwise | 1 run | Tests B3 in isolation |
| A3 | v3 vs v4 extract prompt (severity held at v3) | 1 run | Tests W1/W3/W4/W5 as a bundle |
| A4 | HIGH/MEDIUM/LOW vs 0-100 + tuned threshold | 1 run + sweep | Tests the calibration reframe |
| A5 | `backing`-before-`severity` vs severity alone | 1 run | Tests the forced-evidence mechanism |
| A6 | gate ON vs OFF | 1 short run | Should move hard_no FP specifically |
| A7 | 3b extract -> deepseek verify, vs 70b alone | 1 run | The cascade |
| A8 | English vs Italian prompt | 1 run | Unexplored axis |
| A9 | grammar-constrained vs `format: json` + parser | 1 run | W7-adjacent; suspected in under-extraction |

A0, A1 and A2 are the ones I'd want to see before anything else. Two of them
cost no GPU time at all.

---

## Note on the "4-10 claims" line

I want to flag this one specifically because it reframes your §5.

Your report treats deepseek's low output as a defect. But if gold is 2.45
claims/product, then deepseek's 19-37 total claims across 20 products
(0.95-1.85/product) is *closer to gold* than llama3.3:70b's 52 (2.6/product,
with 4 of 6 clean products contaminated). Deepseek may not be
under-extracting. It may be the only model not obeying an instruction that
was wrong.

That is worth testing before spending more effort making deepseek less
conservative.
