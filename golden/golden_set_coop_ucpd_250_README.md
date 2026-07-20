# Coop UCPD Golden Set — 250 Products

## What this is
A hand-labeled reference set of 250 Coop-schema Italian grocery/health/beauty retail
products, built for tuning and evaluating a claim-detection classifier under the **full
Unfair Commercial Practices Directive (2005/29/EC, as amended)** — not just environmental
("greenwashing") claims, but misleading health/efficacy claims, fake authenticity claims,
unsubstantiated superiority claims, unverified endorsements, and fake or private-label
certifications too.

Every product's `golden_bucket` and `extracted_claims` reflect **direct manual reading**,
not regex or keyword matching. That distinction matters — see "How this was built" below,
because the regex version of this same exercise got the bucket wrong on 1 in 5 products.

## Final composition
| Bucket | Count |
|---|---|
| hard_yes | 77 |
| in_between | 96 |
| **hard_no** | **77** |
| **Total** | **250** |

hard_no sub-reasons: `no_claim_content` (61 — plain factual copy, nothing to flag),
`dietary_lifestyle_only` (9 — vegan/kosher/halal/gluten-free tags, not environmental or
health claims), `legit_certification_only` (7 — real, named, checkable certifications
like DOP/BIOLOGICO/FSC with no embellishment on top).

By source category:
cura-persona 43 · colazione-dolci-e-snack-salati 42 · gastronomia-salumi-e-formaggi 35 ·
pane-pasta-riso-e-farine 27 · acqua-e-bevande 26 · latte-yogurt-e-uova 24 ·
parafarmacia 19 · prima-infanzia 18 · condimenti-conserve-e-scatolame 16

(Source files: the 9 Coop-schema files still available at build time — 2 of the
original 11 category files were overwritten by a later Carrefour upload under the same
filenames, `carne.json` and `frutta-e-verdura.json`, and 2 more, `pesce.json` and
`surgelati-e-gelati.json`, are no longer present at all. Meat, fish, and frozen-food Coop
categories are therefore not represented here. Re-upload those four if you want full
coverage — everything else in this set is unaffected.)

## Category taxonomy
| Category | What it catches | Typical risk |
|---|---|---|
| `environmental_unsubstantiated` | vague green/sustainability language, no backing | MEDIUM |
| `offset_based_neutrality` | CO2/climate "neutral" claims resting on offsetting | HIGH |
| `fake_or_unverified_label` | self-created seals (Coop's "VIVI VERDE," "FIOR FIORE," "BENE SI'," "CRESCENDO," brand-invented "green" sub-labels) standing in for a real accreditation | MEDIUM |
| `unfair_comparison` | comparative/quantified claims (environmental or general) without a disclosed baseline | MEDIUM |
| `unsubstantiated_health_or_efficacy_claim` | "dermatologicamente testato," "clinicamente testato," "rinforza," "supporta il sistema immunitario" — plausible, but the retail text shows no study, sample size, or institution | MEDIUM |
| `unauthorized_or_borderline_medicinal_claim` | food/cosmetics claiming to treat, cure, or prevent a named disease — categorically restricted under Reg. 1924/2006 Art. 2(2) regardless of truth | HIGH |
| `misleading_authenticity_or_origin_claim` | "artigianale," "tradizionale," "come fatto in casa," "ricetta della nonna" for what may be industrial-scale production; "Prodotto in Italia" headlines with "ingredienti UE e non UE" fine print | MEDIUM |
| `misleading_superiority_or_absolute_claim` | "il migliore," "N°1 in Italia," "leader," "nessun altro" — including self-referential comparisons that only compare a product to the brand's own earlier products | MEDIUM (LOW if a basis is disclosed, e.g. "*Fonte: dati Nielsen") |
| `misleading_endorsement_claim` | "consigliato da," "approvato da," "testato dai pediatri" without a clearly named, checkable, independent source | MEDIUM |
| `irrelevant_claim` | legally mandated or trivially-true statements (tethered-cap directive citations, the infant-formula breastfeeding disclaimer, plain traceability mentions, properly-worded EU-authorized nutrient claims) | LOW |

`unauthorized_or_borderline_medicinal_claim` has **zero** hits across all 250 products —
checked specifically for disease-name-linked cure/treat/prevent language and found none.
Worth knowing on its own: this retailer's copy doesn't cross that particular line, at
least in the fields scraped.

## Bucket definitions
- **hard_yes**: at least one HIGH-confidence signal, or two-plus distinct claims from any
  category (not just environmental).
- **hard_no**: no claims worth flagging on direct reading — either genuinely no marketing
  copy, or copy that's dietary-tag-only, or claims that are real but properly
  substantiated (e.g. exact EU-authorized nutrient wording, a named international
  standard, a disclosed independent data source).
- **in_between**: real ambiguity — a single claim, a claim with partial disclosure, or a
  mix of well-substantiated and unsubstantiated language in the same product.

## How this was built (three stages)
1. **Regex/heuristic pass.** Scored ~15,700 candidate products against a 10-category
   pattern-matching ruleset, sampled 200 for category and bucket diversity.
2. **Manual re-extraction (all 200).** Every product's text read directly, claim by
   claim, no pattern-matching. This is what `extracted_claims` reflects. Result: the
   regex bucket was wrong on **40 of 200 products (20%)** — almost all `hard_no → in_between`
   misses, because the regex had few or no patterns for health/efficacy and
   authenticity/heritage language, which turned out to be as common as environmental
   claims once someone actually read the text. `heuristic_bucket` preserves the original
   regex label so you can see exactly what changed.
3. **50 additional hard_no, added for balance.** After stage 2, confirmed hard_no had
   dropped to 27/200 — too thin to be a useful negative class. Pulled ~200 fresh
   candidates from the same 9 source files (regex-flagged hard_no, shortest text first,
   deduplicated, excluding all 200 EANs already used), then read every one of those by
   hand too rather than trusting the regex a second time. 13 looked clean at a glance but
   weren't — a deodorant's bare "48H" claim, an aftershave's "sollievo immediato," a
   fragrance's "developed with athletes," a yogurt carrying Coop's "BENE SI'" label,
   five parafarmacia supplements with botanical claims (astragalus, echinacea, propolis,
   valerian, ginseng) not on the EU-authorized health-claims register, and three baby
   products with real efficacy language. Those were excluded; the 50 that made it through
   are genuinely quiet — plain product names, factual free-from/composition statements,
   or supplements using only exact EU-authorized nutrient wording.

## Judgment calls worth knowing about (not resolved, just documented)
- **Obvious hyperbole vs. actionable claims is unresolved.** "Il più buono dell'universo"
  and "N°1 in Italia per vendite (Fonte: Nielsen)" get the same category tag — a human
  reviewer will read these very differently, and nothing here automates that distinction.
- **Well-disclosed claims are scored LOW even when the claim type would otherwise be
  MEDIUM.** A superiority or comparison claim backed by a named, independent data source
  (Nielsen, IRI, a cited standard like EN 13432 or SRP, a specific SCCS opinion number) is
  treated as meaningfully different from the same claim bare.
- **Properly-worded EU-authorized nutrient claims are not treated as violations.** Several
  parafarmacia supplements are marked hard_no *and* explicitly noted as correctly so —
  real claims present, legally backed, not a miss.
- **Botanical claims in "authorized-style" phrasing but not actually on the EU register**
  (reishi, echinacea, valerian, astragalus, propolis, ginseng "vitalità") are consistently
  flagged MEDIUM or excluded from hard_no, even when hedged conservatively — this is
  applied the same way throughout both extraction passes.
- **This is single-pass human-equivalent review, not multi-reviewer verified ground
  truth.** No second independent read was done to check the extraction itself.

## Fields per product
`origin_file` · `golden_bucket` (primary label) · `heuristic_bucket` (original regex
label, for comparison) · `ean` · `product_id` · `name` · `brand` · `url` · `denomination` ·
`description` · `features` · `producer_info` · `certifications` · `life_style` ·
`recycling` · `recycling_other` · `matched_signals` (original regex hits) ·
`extracted_claims` (real extraction: `claim_text`, `category`, `risk_level` per claim) ·
`legit_or_disclosed_basis_detected` · `hard_no_reason` (hard_no items only) ·
`bucket_correction` (present only where stage 2 changed the label) · `extraction_note`
(present on a handful of products where the call itself needed a comment)

## Files
- `golden_set_coop_ucpd_250_combined.json` — all 250 products, this is the one to use
- `golden_set_coop_ucpd_50_additional_hard_no.json` — just the 50 newest additions, if
  you want them separate
