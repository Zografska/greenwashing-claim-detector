# Carrefour UCPD Golden Set — 300 Products

## What this is
300 hand-extracted, claim-labeled products drawn from 16 Carrefour category files
(12,407 products total), built the same way as the Coop set: every product read
directly — no regex-only labeling — using the full 10-category UCPD taxonomy plus the
`modifiers` / `irrelevant_subreason` refinements from the Coop redo.

## Composition
| Bucket | Count |
|---|---|
| hard_yes | 96 |
| in_between | 103 |
| hard_no | 101 |
| **Total** | **300** |

Balanced within a few products of an even three-way split, and spread across all 16
source categories (11–20 products each — `carne` sits lowest at 11 because real reading
found almost no marketing claims in that category at all, see below).

By source file: acqua-e-analcolici 19 · articoli-per-la-casa 20 · birra-vino-e-liquori 20 ·
carne 11 · condimenti-e-conserve 19 · cura-della-casa 19 · dolci-e-prima-colazione 20 ·
gastronomia 17 · gelati-e-surgelati 19 · pane-e-snack-salati 20 · pasta-riso-e-farina 20 ·
pesce 18 · prodotti-prima-infanzia 20 · salumi-e-formaggi 20 · salute-e-benessere 19 ·
uova-latte-e-latticini 19

## How this was built
1. **Heuristic pre-scan.** Adapted the Coop scoring engine to Carrefour's C4-schema
   fields (`C4_MarketingProduct`, `C4_MarketingBrand`, `C4_NutritionClaims`,
   `C4_LongDescription`, `C4_SalesDenomination`, `C4_Origin`, `C4_PreparationInfo`) and
   scored all 12,407 products for diversity sampling only — not for final labels.
2. **535 candidates pulled**, oversampled per category (hard_no candidates sorted
   shortest-text-first, since that pattern held up from the Coop set: less text means
   less room for a hidden claim).
3. **All 535 read directly, claim by claim**, in batches of ~20-30, using the taxonomy
   below. Puffery (subjective, non-checkable language — "un'esperienza di gusto
   assoluta", "buono dentro e fuori") was identified and excluded from
   `extracted_claims` from the start, per the lesson from the Coop redo, rather than
   extracted and cleaned up in a second pass.
4. **300 selected** from the 535 for category and bucket balance across all 16 files.

## Category taxonomy (same as the Coop REDO baseline)
`environmental_unsubstantiated` · `offset_based_neutrality` · `fake_or_unverified_label` ·
`unfair_comparison` · `unsubstantiated_health_or_efficacy_claim` ·
`unauthorized_or_borderline_medicinal_claim` · `misleading_authenticity_or_origin_claim` ·
`misleading_superiority_or_absolute_claim` · `misleading_endorsement_claim` ·
`misleading_composition_or_ingredient_claim` · `nutrition_content_claim` ·
`irrelevant_claim`

`unauthorized_or_borderline_medicinal_claim` again has **zero hits** — checked
specifically, found none. This retailer's copy doesn't cross that line either.

Category totals across all 685 extracted claims: `environmental_unsubstantiated` (175)
and `misleading_authenticity_or_origin_claim` (148) dominate, followed by
`misleading_superiority_or_absolute_claim` (106) and `unsubstantiated_health_or_efficacy_claim`
(69). Same pattern as Coop: heritage/tradition storytelling ("Dal 1902", "come una
volta", "ricetta tradizionale") and self-referential superiority claims turned out to be
just as common as environmental claims, sometimes more so, in categories like
pasta/rice, cured meats, and coffee — brands with long histories lean hard on it.

## What's different about this dataset vs. Coop
- **Real, well-substantiated claims showed up more often here.** Several brands cite
  specific, checkable sources: Carbon Trust certification (Santàl), the Grazing
  Foundation's independent audit (Leerdammer), ISCC Plus + WWF + University of Bologna
  (Mulino Bianco's "Carta del Mulino" — same pattern seen in the Coop set), Nielsen/IRI
  sales data with named methodology, DIN CERTCO / TÜV Austria certificate numbers. These
  are flagged as claims (they're still assertions a reviewer should be able to check)
  but rated LOW risk given the disclosure.
- **A live "Italian sounding" case appeared again**: two Plasmon baby-food products
  (idx-equivalent to the Coop case) headline "Prodotto in Italia" with a footnoted
  "*Ingredienti di origine UE e non UE" — same pattern flagged in the Coop set, not a
  one-off.
- **`carne` (meat) is almost entirely clean.** Of 270 products in that file, real
  reading found exactly one candidate with any marketing claim at all (and even that
  one didn't hold up under closer reading — see `bucket_correction` on that record).
  Plain cuts of meat just don't carry marketing copy the way branded packaged goods do.
- **Health/wellness (`salute-e-benessere`) surfaced a new claim shape**: Durex condoms
  repeat the same five or six claims (dermatologically tested, "World's No.1", "90
  years") across nearly every SKU in the range — useful for seeing how the same brand
  claim looks when it's boilerplate across a product line rather than one-off copy.
- **Compression stockings (Manon) produced the highest-risk single claim in the set**:
  "Ti aiuta a combattere gli inestetismi della cellulite e ne previene l'eventuale
  formazione migliorando il microcircolo" — rated HIGH given how specific and
  medical-sounding the cellulite-prevention mechanism claim is for a retail hosiery
  product.

## Known judgment calls (same caveats as Coop, still unresolved)
- Obvious hyperbole vs. actionable claims still isn't disentangled by any rule here —
  "il più buono dell'universo"-style puffery was excluded entirely, but claims that
  sit between clear puffery and a specific checkable assertion (e.g. "un salmone per
  chef... di carattere!") required a judgment call each time.
- `vague_or_unquantified` / `specific_quantified` modifiers are **not** applied in this
  dataset — the earlier reconstruction attempt on the Coop set showed this distinction
  needs a narrower rule than "contains a digit," and that rule was never fully
  recovered. Better to leave it out than guess wrong again.
- Single-pass extraction, same as always — no second independent reviewer.

## Fields per product
Same schema as the Carrefour source files (`C4_MarketingProduct`, `C4_SalesDenomination`,
etc.) plus: `origin_file`, `golden_bucket` (primary label), `heuristic_bucket` (original
regex label), `matched_signals` (regex hits, for comparison), `extracted_claims`
(`claim_text`, `category`, `risk_level`, optional `modifiers`), `bucket_correction`
(where the heuristic bucket was wrong), `extraction_note` (a handful of products where
the call needed a comment).

## Files
- `golden_set_carrefour_300.json` — all 300 products
