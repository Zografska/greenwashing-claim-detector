# Coop UCPD Golden Set v2 — 250 Products, Reclassified

## What changed and why
This is a claim-level redo of `golden_set_coop_ucpd_250_combined.json`, done the same
way the original set insists on being built — direct reading of every one of the 610
extracted claims, not pattern-matching. It grew out of a long back-and-forth working
through specific borderline claims one at a time ("tradizionale", "meno plastica",
"dermatologicamente testata", "fonte di fibre", endorsement claims, historical-recipe
claims, botanical health claims...). Six recurring problems turned up. This redo fixes
all six **across the full 250-product set**, not just the examples that came up in
conversation.

**Nothing here touches `golden_bucket` directly.** Bucket assignment is a holistic
call the original README explicitly says wasn't reduced to a formula, and redoing it
by formula would repeat the exact mistake ("regex bucket was wrong on 20% of products")
the original build already learned from. Instead, 19 products got a `bucket_review_flag`
— a pointer for a human to recheck, not an automatic override. See §5.

## 1. Puffery was getting flagged as if it were a real claim
**47 instances removed** from `extracted_claims` entirely. A claim-detection classifier's
own Part-A test — *is this a specific, checkable, attributable assertion, or just
subjective marketing language?* — was being applied inconsistently. Things like
*"è un autentico trionfo di pasticceria"*, *"Buona com'era"*, *"L'iconica lacca"*,
*"un'esperienza di gusto e benessere unica"* assert nothing a fact-checker could test.
They stayed in because they *sit next to* real claims (a date, a percentage, a named
institute) and pattern-matching can't tell the wrapper from the substance. Full list
with individual reasoning: `CHANGELOG.md` §1.

This is the single biggest source of over-flagging in the original set — bigger than
any miscategorization below.

## 2. Two new categories, because two real claim types had no home
| New category | Catches | Why it needed to exist |
|---|---|---|
| `misleading_composition_or_ingredient_claim` | "Senza grassi idrogenati", allergen/perfume/colorant-absence claims | These are optional, factual, checkable composition assertions the manufacturer chose to print. They were landing in `irrelevant_claim` ("legally mandated or trivially true") — but nobody is *required* to print them, which is the actual test for that bucket. Optional ≠ irrelevant, regardless of how mundane the claim sounds. |
| `nutrition_content_claim` | Bare "Fonte di fibre", "Ricca in calcio", "Fonte di proteine", "Naturalmente priva di caffeina" | These are real NHCR-Annex nutrient-content claims with fixed compositional thresholds (e.g. source-of-fibre requires ≥3g/100g or ≥1.5g/100kcal). Whether any given product actually clears that threshold isn't visible from ad copy — it depends on data this dataset doesn't have. Filing them as "irrelevant" quietly asserted they were compliant with no basis for that assertion. |

Claims using the **full authorized EFSA physiological-function wording** ("Il calcio
contribuisce alla normale funzione muscolare", melatonin, Italian mineral-water
Ministerial-Decree claims) were **left in `irrelevant_claim`** rather than moved —
moving well-substantiated claims into a category named `unsubstantiated_...` would
have been its own contradiction. Instead they got two additions: a `irrelevant_subreason:
"eu_authorized_optional_claim"` field, and a `compliance_unverified_from_text` modifier,
so "nothing to flag" no longer silently means "definitely compliant."

## 3. Ten miscategorized claims moved to where they actually belong
25 claim-level moves total; the ten most consequential:

| Claim | Was | Now |
|---|---|---|
| "Solo nocciole italiane" | `irrelevant_claim` | `misleading_authenticity_or_origin_claim` |
| "PANE ARABO-COTTO A LEGNA" | `irrelevant_claim` | `misleading_authenticity_or_origin_claim` |
| "1500 Controlli di qualità giornalieri" | `irrelevant_claim` | `misleading_superiority_or_absolute_claim` |
| "Brevetto internazionale" | `irrelevant_claim` | `misleading_superiority_or_absolute_claim` |
| "Fai la differenziata per il pianeta" | `environmental_unsubstantiated` | `irrelevant_claim` (generic recycling PSA, not a product-performance claim) |
| "0% di allergeni comuni..." | `environmental_unsubstantiated` | `misleading_composition_or_ingredient_claim` |
| "Dal 1820 la famiglia Grondona garantisce" | `misleading_endorsement_claim` | `misleading_authenticity_or_origin_claim` (nobody is endorsing this — it's the company's own heritage claim) |

Full list with reasoning: `CHANGELOG.md` §2.

## 4. Modifier tags — the cross-cutting distinctions that kept mattering
Every claim now carries a `modifiers` list. These aren't new categories; they're
properties that showed up *inside* nearly every existing category and were getting
lost:

- **`vague_or_unquantified`** (15 hits) — "meno plastica"-shaped claims: real content,
  no baseline/comparator/metric. Distinct from a false claim; the defect is genericness
  itself (Annex I's generic-environmental-claims test), independent of truth.
- **`specific_quantified`** (44 hits) — the opposite: "95% plastica riciclata"-shaped.
  Checkable in principle even if not verified from ad text alone. Conflating this with
  the vague cluster under one "unsubstantiated" umbrella was hiding a real difference
  in what it takes to close each one out.
- **`compliance_unverified_from_text`** (33 hits) — nutrition/health claims using
  correct legal wording, where the open question is a threshold or dosage figure this
  dataset doesn't contain (the "fonte di fibre" / 2.4g-per-100g problem, generalized).
- **`botanical_or_generic_antioxidant_not_on_eu_register`** (14 hits) — curcuma,
  mirtillo-as-antioxidant, valeriana, passiflora, propoli, reishi, echinacea, ginseng,
  melissa, escolzia/tiglio, miglio/bambù. True chemistry doesn't rescue these; the EU
  botanicals health-claims list has been on hold since 2010, so authorization is the
  gap, not evidence. **Within this group**, claims that mimic the authorized EFSA
  "contribuisce/contribuiscono" phrasing *without* a "tradizionalmente noto" hedge
  (Reishi, Echinacea, Escolzia/tiglio, bare Passiflora) got bumped from MEDIUM to HIGH
  (`authorized_style_mimicry`) — they read as compliant, pre-approved claims, which is a
  materially worse pattern than an honestly-hedged traditional-use statement.
- **`annex_i_blacklist_candidate`** (12 hits) — named-body endorsement claims
  (A.I.Nut., ANDI, Skin Health Alliance, Aideco/AIDECO, "testato dai pediatri").
  These fall under UCPD **Annex I, point 4** — per se unfair if the endorsement is
  false or the terms weren't met, no "average consumer" materiality test required.
  Resolution is binary (does the body exist and did it approve this?), not
  probabilistic, unlike most of this dataset.
- **`annex_i_blacklist_per_se`** (5 hits) — the offset-based carbon-neutrality claims.
  Directive 2024/825 added offset-based neutrality claims to Annex I outright; these
  don't need substantiation analysis, they're prohibited regardless of truth.
- **`two_part_verification_required`** (10 hits) — dated heritage claims ("inizio
  Ottocento", "XVI secolo", "80 anni di tradizione", "dal 1907"). UCPD Art. 6(1)'s
  chapeau makes a practice misleading "even if the information is factually correct" —
  so the historical fact being true doesn't resolve these. Two separate things need
  checking: did the history happen, *and* is the product still made that way today.
- **`checkable_binary_fact`** (4 hits) — "Etichetta in carta riciclata"-shaped claims:
  no comparator problem (unlike "meno plastica"), just a plain fact that's either true
  or false.
- **`retailer_level_claim_not_product_claim`** (2 hits) — claims about the seller
  ("Farmaciauno") rather than the product, flagged as possibly out of scope for a
  product-claim taxonomy rather than force-categorized.
- **`borderline_medicinal_claim_candidate`** (2 hits) — "sconfiggere il gonfiore
  addominale e tutti i disturbi che colpiscono la digestione" and its companion
  sentence. The original README states `unauthorized_or_borderline_medicinal_claim`
  has **zero hits** across all 250 products, checked specifically for
  disease/disorder-linked cure/treat/prevent language. These two claims — treating
  "disturbi" (disorders) of digestion — sit close enough to that line that the zero-hit
  finding is worth a second look. Not recategorized outright; flagged for a human call.
- **`weak_evidence_self_report`** / **`undisclosed_test_result`** (2 + 1 hits, 2 risk
  bumps LOW→MEDIUM) — "Test di autovalutazione" (self-assessment, not instrumental)
  and "tested" with no disclosed pass/fail result are both weaker than a bare LOW label
  implies; downgraded to MEDIUM.
- **`medical_device_context_different_regulation`** (1 hit) — "Abbatte rapidamente il
  dolore" comes from a registered medical device, governed by the MDR rather than
  NHCR/cosmetics rules — a different compliance regime, flagged rather than assessed
  under the wrong framework.

## 5. Bucket-review flags (informational only — `golden_bucket` unchanged)
19 products got a `bucket_review_flag` + `bucket_review_detail`:

| Flag | Count | Meaning |
|---|---|---|
| `recheck_hard_yes_basis` | 13 | A puffery removal dropped this product's actionable-claim count; reverify it still clears the hard_yes bar (≥1 HIGH or ≥2 distinct real claims) rather than resting on a claim that's now gone. |
| `candidate_downgrade_to_hard_no` | 5 | Every previously-actionable claim on this product was either puffery (now removed) or is EU-authorized wording now correctly tagged as such — nothing flaggable remains under this taxonomy. |
| `candidate_upgrade_to_hard_yes` | 1 | An `in_between` product (immunity supplement drink) now carries 2 HIGH-risk claims after the botanical-mimicry risk bump (Reishi + Echinacea, both using unhedged "contribuisce" phrasing) — worth a look at moving it to hard_yes. |

## Fields added per claim
`modifiers` (list, always present, may be empty) · `irrelevant_subreason` (only on
`irrelevant_claim` entries: `mandatory_disclosure` / `eu_authorized_optional_claim` /
`trivial_non_actionable`)

## Fields added per product
`redo_schema_version: 2` · `bucket_review_flag` / `bucket_review_detail` (only on the
19 flagged products)

## What this redo did *not* do
- Did not verify any external fact (whether A.I.Nut. actually exists and approved a
  given product, whether a 1907-founding date is real, whether a nutrition panel
  actually clears the fibre/protein/calcium thresholds these claims assert). Every
  `compliance_unverified_from_text`, `two_part_verification_required`, and
  `annex_i_blacklist_candidate` tag marks something that needs an external check, not
  something resolved.
- Did not re-run the manual claim-*extraction* pass — this redo works claim-by-claim on
  the extraction the original build already did. If the original extraction missed a
  claim entirely (rather than miscategorizing one it caught), that gap carries forward
  unchanged.
- Did not touch `hard_no_reason`, `heuristic_bucket`, or any of the original v1
  provenance fields — those are left intact for comparison.

## Files
- `golden_set_coop_ucpd_250_combined_REDO.json` — all 250 products, corrected
  `extracted_claims` + new fields, use this one going forward
- `CHANGELOG.md` — every individual change (all 47 removals, 25 recategorizations,
  4 risk adjustments) with its specific reasoning
- `README_v2.md` — this file
