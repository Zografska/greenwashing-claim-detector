# NaturaSì UCPD Golden Set — 200 Products

## Read this first — this dataset is structurally different from Coop and Carrefour
NaturaSì's scraped data has **no marketing prose field at all**. There's no
`C4_MarketingProduct`, no `description`, nothing resembling freeform ad copy — just
structured, regulatory fields: `certifications` (a tag array), `legal_name` (the
regulated product designation), `producer`/`production_facility` (addresses),
`quality_recipe` (ingredient list), `table_nutrition` (numbers), `storage`. I checked —
this isn't a scraping gap, it's how the retailer's site is built. NaturaSì is an organic
specialty chain; its whole premise is "certified clean," and the data reflects that: the
certification tags are overwhelmingly real, named, independently-audited schemes
(Demeter, NaTrue, Cosmos Organic/Natural, BDIH, Ecocert, CCPB, ICEA, AIC's official
gluten-free registry) rather than the brand-invented labels or heritage storytelling that
filled the Coop and Carrefour sets.

**Practical consequence: hard_yes is genuinely scarce here — 24 products out of 3,843
qualified, full stop.** I didn't under-sample it; I used every single one. This isn't a
gap in the methodology, it's an honest finding about the retailer: there's very little
room for unsubstantiated claims when there's no narrative field to put them in.

## Composition
| Bucket | Count |
|---|---|
| hard_yes | 24 |
| in_between | 90 |
| hard_no | 86 |
| **Total** | **200** |

By source file: prodotti-da-forno 25 · pasta-riso-e-farine 22 · colazione-e-merende 18 ·
bevande 17 · dispensa-e-condimenti 16 · gastronomia 15 · latte-formaggi-e-uova 15 ·
cereali-e-legumi 13 · bevande-vegetali 8 · carne-pesce-e-salumi 8 · proteine-vegetali 8 ·
casa-e-giardino 7 · cura-della-persona 6 · surgelati-e-gelati 6 · tisane-e-infusi 6 ·
vino-e-birra 5 · yogurt-e-kefir 5

All 24 hard_yes products cluster in exactly two places: **artisan bread/bakery**
(`prodotti-da-forno`, `colazione-e-merende`, `gastronomia` — stacking "con pasta madre"
+ "farina macinata a pietra" + "cereali antichi") and **rice/flour** (`pasta-riso-e-farine`
— stacking "Equosolidale" + "prodotto da nostra filiera"). Every other category in the
dataset — cosmetics (948 products!), wine/beer, yogurt, frozen foods — produced **zero**
hard_yes candidates on direct reading.

## How this was built
1. Since there's no prose to parse, the claim signal here is almost entirely the
   `certifications` tag array. I sorted every tag actually present in the data (78
   unique tags across all 3,843 products) into: real/legit certification schemes,
   regulated nutrition-content tags, regulated composition/dietary tags, and a small set
   of genuinely unverified marketing-adjacent tags.
2. **First pass over-triggered.** My initial heuristic treated *any* two low-risk
   regulated tags stacking together (e.g. "senza glutine" + "fonte di fibre") as enough
   to call a product `in_between`. That's wrong, and it's wrong for the same reason
   stacking legit EU-authorized nutrient claims didn't push Coop products to
   `in_between` — regulated, properly-used claim categories don't become suspicious
   just because there are several of them on one label. I caught this by actually
   reading through the first ~60 candidates and noticing almost all of them were
   genuinely clean, corrected the bucket logic to require a real unverified/unsubstantiated
   tag before a product counts as anything but `hard_no`, and rebuilt the candidate
   pool from there.
3. With that fixed, the classification became mechanical and reliable — this is a
   tag-based dataset, so once the tag→category mapping is right, applying it
   consistently across all 290 read candidates doesn't require the same
   claim-by-claim prose judgment the Coop/Carrefour sets needed. I did spot-check a
   broad sample by hand, checked every free-text field for the one thing tags can't
   catch (genuine "ricetta della tradizione" phrasing, as opposed to a producer's legal
   name happening to contain the word "Tradizionale"), and found it exactly once.
4. 290 candidates read, 200 selected — all 24 hard_yes taken, 90 in_between and 86
   hard_no diversity-sampled across all 17 categories.

## What counted as a claim here, and what didn't
**Treated as genuinely unverified (MEDIUM, pushes bucket):**
- `prodotto da nostra filiera` — "from our own supply chain," no independent verification
- `Equosolidale` — generic "fair trade," not tied to a named certifying body (contrast
  with the same products' `Demeter` tag, which *is* a real, audited scheme)
- `con pasta madre`, `cereali antichi`, `farina macinata a pietra`, `da latte crudo` —
  specific production-method claims (sourdough starter, ancient grain, stone-ground,
  raw milk) that are checkable in principle but self-declared, not independently audited

**Treated as legit/LOW (does not push bucket):** `Agricoltura biologica`, `NaTrue`,
`Demeter`, `Cosmos Natural/Organic`, `BDIH`, `Vegan Society`, `Kosher`, `Spiga barrata`,
the AIC gluten-free registry, and about a dozen more real cosmetics/detergent
certification schemes (Ecocert, CCPB, ICEA, BioAgriCert, Slow Cosmétique, Cosmebio) —
plus regulated nutrition-content tags (`fonte di fibre`, `ad alto contenuto di
proteine`) and dietary/composition tags (`senza glutine`, `ricetta vegana`). These are
still listed in `extracted_claims` for completeness (tagged LOW risk, with
`compliance_unverified_from_text` where relevant, since the actual compositional
threshold isn't verifiable from the tag alone) — they just don't make a product
`in_between` on their own, the same way a well-worded EU-authorized nutrient claim
didn't in the Coop set.

## Category totals (352 claims across 200 products)
`misleading_composition_or_ingredient_claim` (121) and `misleading_authenticity_or_origin_claim`
(72) dominate — composition/free-from tags are the single most common category simply
because they're the most common tag type in the data, and authenticity claims cluster
almost entirely in the bread/bakery hard_yes cases described above.
`fake_or_unverified_label` (69) is almost entirely `prodotto da nostra filiera` and
`Equosolidale`. `nutrition_content_claim` (60) is regulated content tags, all LOW risk.
Risk split: 212 LOW / 140 MEDIUM / **0 HIGH** — there's no offset-based neutrality claim,
no fake medical claim, nothing that rises to HIGH anywhere in this dataset.

## Known limitations
- **hard_no is dominated by one reason**: 82 of 86 are `legit_certification_only` — this
  retailer's clean products are clean because of real certifications, not because there
  was nothing to say.
- Unlike Coop/Carrefour, I did not do exhaustive prose-level puffery removal here — there
  wasn't prose to remove it from. The equivalent judgment call in this dataset was
  entirely about tag classification (legit cert vs. self-declared marketing tag), and
  that line is disclosed above in full, not buried in per-product notes.
- `cura-della-persona` (cosmetics, 948 products, the largest single category in the raw
  data) is under-represented in the final 200 (6 products) relative to its size, simply
  because almost every cosmetics product carries nothing but real, named certification
  schemes — there was very little genuine `in_between`/`hard_yes` material to sample
  from it.

## Fields per product
Original NaturaSì fields (`certifications`, `legal_name`, `producer`, `quality_recipe`,
`table_nutrition`, etc.) plus: `origin_file`, `golden_bucket`, `extracted_claims`
(`claim_text`, `category`, `risk_level`, optional `modifiers`), `hard_no_reason` (hard_no
items only).

## Files
- `golden_set_naturasi_200.json` — all 200 products
