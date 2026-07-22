# Eurospin UCPD Golden Set — 200 Products

## What this is
200 hand-extracted, claim-labeled products from 12 Eurospin category files (3,389
products total), built the same way as Coop, Carrefour, and NaturaSì: every product read
directly, no regex-only labeling, using the full UCPD taxonomy plus the `modifiers`
refinements from the Coop redo. Unlike NaturaSì, this dataset has real marketing prose
(`marketing_text`, `other_claim`, `further_description`, `sales_description`) — closer in
character to Coop/Carrefour than to NaturaSì's pure structured data.

## Composition
| Bucket | Count |
|---|---|
| hard_yes | 32 |
| in_between | 48 |
| hard_no | 120 |
| **Total** | **200** |

This one skews hard_no more than Coop/Carrefour did. That's a genuine finding, not
under-sampling: of 291 candidates read (all available hard_yes and in_between taken in
full), the underlying pool only had 32 hard_yes and 48 in_between against 211 hard_no.
Eurospin is a discount/private-label retailer — a lot of its catalog is plain factual
descriptions ("SALAME MILANO", "PATATE 1,5kg") with no room for a claim at all.

By source file: igiene-e-cura-personale 35 · dispensa 27 · bevande 25 · frutta-e-verdura
23 · mondo-bimbi 19 · gastronomia-salumi-e-formaggi 14 · carne-e-pesce 12 ·
latticini-e-uova 12 · mondo-animali 12 · pane-e-pasticceria 10 · surgelati-e-gelati 10 ·
tecnologia-e-elettrodomestici 1 (this file produced almost nothing — see below)

## Where the claims actually are
Three clusters account for most of the hard_yes/in_between products:
1. **The "Amo essere Bio" product line** (organic own-brand, spans bevande, dispensa,
   frutta-e-verdura, latticini-e-uova) — every product in this line carries an identical
   boilerplate paragraph about sustainability and biodiversity. It's real but vague
   enough to count as one `environmental_unsubstantiated` MEDIUM claim per product —
   almost never enough on its own to reach hard_yes, which is why so many of these
   products landed in `in_between` rather than `hard_yes`.
2. **Feminine hygiene and baby diapers** ("Fior di Magnolia", "Hello Baby") — these
   consistently stack 2-4 MEDIUM claims per product (self-referential superiority like
   "una morbidezza mai provata", vague efficacy claims about superabsorbent polymers,
   bare "Dermatologicamente testato"), making this category the single richest source of
   `hard_yes` in the set.
3. **Small-producer wine, beer, and liquor** — heritage/tradition language ("Ricetta
   tradizionale", "Antica ricetta 1952", superiority framing like "il sovrano degli
   amari") clusters here, contrasted sharply with larger wine producers who cite real,
   named sustainability certifications (Equalitas, VIVA, SQNPI) instead — see below.

## A recurring, important distinction: named certifications vs. bare claims
This dataset made the "is there a real body behind this" test unusually visible because
both versions show up side by side in the same category:
- **Real, named, checkable schemes were treated as LOW/legit and pushed products toward
  hard_no**: Equalitas and VIVA (wine sustainability, government-recognized), SQNPI
  (Italian national integrated-production standard), MSC and Friend of the Sea
  (sustainable fishing), UTZ and RSPO (cocoa/palm oil), ICEA and Bio Eco Cosmesi AIAB
  (cosmetics). A wine citing "Cantina sostenibile Equalitas" with nothing else is
  hard_no; a wine or spirit with only "Sostenibilità ecologica, etica, economica" and no
  named scheme is a real MEDIUM claim.
- **The same sustainability language without a named body stayed MEDIUM and could push a
  product to hard_yes**: "Consorzio vini di Romagna - Cantina sostenibile" (no
  independent certification named), "Da filiera controllata nel rispetto della natura"
  (self-declared, no scheme).
- This distinction drove a lot of correction activity during manual reading — my initial
  heuristic scorer treated "sostenibil-" as one undifferentiated signal, and about a
  third of the candidates needed a bucket correction once I actually checked whether a
  specific certifying body was named.

## Category totals (229 claims across 200 products)
`unsubstantiated_health_or_efficacy_claim` (66) is the largest category — dominated by
the repeated "Dermatologicamente testato" pattern across cosmetics, hygiene, and baby
products, plus the specific efficacy language layered on top in the richer cases (BB
cream, arnica gel, scrub, doposole). `environmental_unsubstantiated` (56) is mostly the
"Amo essere Bio" boilerplate plus the bare (unnamed-scheme) sustainability language
described above. `misleading_superiority_or_absolute_claim` (35) clusters in feminine
hygiene ("una morbidezza mai provata"), craft beer ("il meglio dell'arte birraia"), and
one notably absolute sugar claim ("L'unico zucchero 100% italiano... l'unica VERA filiera
corta"). Risk split: 137 MEDIUM / 92 LOW / **0 HIGH** — no offset-based neutrality claim,
no borderline medicinal claim anywhere in this dataset either.

## What almost produced nothing
`tecnologia-e-elettrodomestici` (128 products, small appliances) returned a single
hard_no candidate and nothing else — heuristic scoring found zero hard_yes and zero
in_between across the whole file on the first pass, and manual spot-checking confirmed
it: this category is pure spec-sheet copy (wattage, dimensions, warranty terms), no
claim-bearing language at all. `pane-e-pasticceria` was similarly thin, though not quite
empty.

## Known limitations
- Same puffery-exclusion approach as Coop/Carrefour: hyperbolic language with no
  checkable content ("un'esplosione di sapori che conquisterà") was excluded from
  `extracted_claims` rather than counted.
- `vague_or_unquantified` / `specific_quantified` modifiers are not applied here either,
  for the same reason noted in the Coop redo — the actual rule behind that distinction
  was never fully recovered, and guessing wrong once was enough.
- Single-pass extraction. No second independent reviewer.

## Fields per product
Original Eurospin fields (`sales_description`, `marketing_text`, `other_claim`,
`further_description`, etc.) plus: `origin_file`, `golden_bucket`, `extracted_claims`
(`claim_text`, `category`, `risk_level`, optional `modifiers`), `bucket_correction`
(where the heuristic first-pass bucket was wrong).

## Files
- `golden_set_eurospin_200.json` — all 200 products
