# AUDIT_00 — Inventory of `golden_set_coop_ucpd_250.json`

Phase 0. **Read-only. Nothing in the golden file was modified.**

Date: 2026-09-19 · Source: `golden/golden_set_coop_ucpd_250.json` (475,212 bytes, mtime 2025-07-21)

---

## 1. Record count and container shape

| Metric | Value |
|---|---|
| Top-level container | JSON array |
| Product records | **250** |
| Claim records (`extracted_claims[]`) | **562** |
| Distinct `claim_text` values | 481 (so 81 are repeats across products) |
| Products with zero claims | 74 |

## 2. Current schema — product level

Fill rate = present **and** not null / "" / [] / {}.

| Field | Present | Filled | Fill % | Types observed |
|---|---|---|---|---|
| `origin_file` | 250 | 250 | 100.0% | str×250 |
| `golden_bucket` | 250 | 250 | 100.0% | str×250 |
| `ean` | 250 | 250 | 100.0% | str×250 |
| `product_id` | 250 | 250 | 100.0% | str×250 |
| `name` | 250 | 250 | 100.0% | str×250 |
| `brand` | 250 | 225 | 90.0% | str×224, null×25, dict×1 |
| `url` | 250 | 250 | 100.0% | str×250 |
| `denomination` | 250 | 160 | 64.0% | str×160, null×90 |
| `description` | 250 | 55 | 22.0% | null×195, str×54, list×1 |
| `features` | 250 | 182 | 72.8% | str×182, null×68 |
| `producer_info` | 250 | 179 | 71.6% | str×179, null×71 |
| `certifications` | 250 | 94 | 37.6% | null×156, list×94 |
| `life_style` | 250 | 51 | 20.4% | null×199, str×43, list×8 |
| `recycling` | 250 | 141 | 56.4% | list×115, null×109, str×25, dict×1 |
| `recycling_other` | 250 | 158 | 63.2% | str×158, null×92 |
| `matched_signals` | 250 | 138 | 55.2% | list×250 |
| `legit_or_disclosed_basis_detected` | 250 | 44 | 17.6% | list×250 |
| `heuristic_bucket` | 250 | 250 | 100.0% | str×250 |
| `extracted_claims` | 250 | 176 | 70.4% | list×250 |
| `redo_schema_version` | 250 | 250 | 100.0% | int×250 |
| `bucket_review_flag` | 19 | 19 | 7.6% | str×19 |
| `bucket_review_detail` | 19 | 19 | 7.6% | str×19 |
| `hard_no_reason` | 112 | 112 | 44.8% | str×112 |
| `bucket_correction` | 40 | 40 | 16.0% | str×40 |
| `extraction_note` | 11 | 11 | 4.4% | str×11 |

### Schema irregularities worth knowing before migration

- `brand` — 224 str, **1 dict**, 25 null.
- `description` — 54 str, **1 list**, 195 null.
- `recycling` — 115 list, **25 str**, **1 dict**, 109 null. Not a stable type.
- `life_style` — 43 str, **8 list**, 199 null.
- Five fields are **sparse and undeclared** (present on only some records): `hard_no_reason` (112), `bucket_correction` (40), `bucket_review_flag` (19), `bucket_review_detail` (19), `extraction_note` (11). These are annotation-process residue, not on your §4 removal list — flagged for a decision at Phase 3.

## 3. Current schema — claim level

| Field | Count | Fill % of 562 |
|---|---|---|
| `claim_text` | 562 | 100.0% |
| `category` | 562 | 100.0% |
| `risk_level` | 562 | 100.0% |
| `modifiers` | 562 | 100.0% |
| `irrelevant_subreason` | 41 | 7.3% |

> **There is no claim-level `label` field.** See §7.

## 4. Current label distribution

### 4a. `golden_bucket` — the adjudicated product-level label

| Bucket | Products | % |
|---|---|---|
| `in_between` | 96 | 38.4% |
| `hard_yes` | 77 | 30.8% |
| `hard_no` | 77 | 30.8% |

### 4b. `heuristic_bucket` — the pre-adjudication machine guess

| Bucket | Products |
|---|---|
| `hard_no` | 112 |
| `in_between` | 71 |
| `hard_yes` | 67 |

### 4c. Confusion: heuristic → golden

| heuristic ↓ / golden → | hard_no | in_between | hard_yes |
|---|---|---|---|
| **hard_no** | 77 | 30 | 5 |
| **in_between** | 0 | 66 | 5 |
| **hard_yes** | 0 | 0 | 67 |

Human adjudication moved **40** of 250 products off the heuristic's bucket — all of them upward in severity except none downward. `bucket_correction` records the reason on 40 records.

### 4d. Claim-level `category` — the nearest thing to a claim label

| Category | Claims | % of 562 |
|---|---|---|
| `unsubstantiated_health_or_efficacy_claim` | 132 | 23.5% |
| `environmental_unsubstantiated` | 130 | 23.1% |
| `misleading_authenticity_or_origin_claim` | 68 | 12.1% |
| `misleading_superiority_or_absolute_claim` | 65 | 11.6% |
| `irrelevant_claim` | 54 | 9.6% |
| `fake_or_unverified_label` | 44 | 7.8% |
| `unfair_comparison` | 24 | 4.3% |
| `misleading_endorsement_claim` | 15 | 2.7% |
| `nutrition_content_claim` | 13 | 2.3% |
| `misleading_composition_or_ingredient_claim` | 11 | 2.0% |
| `offset_based_neutrality` | 6 | 1.1% |

### 4e. Claim-level `risk_level`

| Risk | Claims |
|---|---|
| `MEDIUM` | 330 |
| `LOW` | 223 |
| `HIGH` | 9 |

### 4f. `modifiers` (claim-level, multi-valued)

| Modifier | Claims |
|---|---|
| `specific_quantified` | 40 |
| `compliance_unverified_from_text` | 33 |
| `eu_authorized_wording` | 20 |
| `vague_or_unquantified` | 18 |
| `botanical_or_generic_antioxidant_not_on_eu_register` | 14 |
| `annex_i_blacklist_candidate` | 12 |
| `two_part_verification_required` | 10 |
| `annex_i_blacklist_per_se` | 5 |
| `checkable_binary_fact` | 4 |
| `borderline_medicinal_claim_candidate` | 2 |
| `weak_evidence_self_report` | 2 |
| `retailer_level_claim_not_product_claim` | 2 |
| `authorized_style_mimicry` | 2 |
| `vague_unnamed_endorser` | 1 |
| `undisclosed_test_result` | 1 |
| `medical_device_context_different_regulation` | 1 |
| `checkable_historical_claim_well_hedged` | 1 |

Claims with an empty `modifiers` list: 419.

### 4g. `irrelevant_subreason` (present on 41 claims)

| Value | Claims |
|---|---|
| `eu_authorized_optional_claim` | 20 |
| `mandatory_disclosure` | 17 |
| `trivial_non_actionable` | 4 |

All 54 `irrelevant_claim` claims: 20 EU-authorised, 17 mandatory disclosure, 4 trivial, 13 with no subreason.

## 5. Claims per product

| Claims | Products | Cumulative claims |
|---|---|---|
| 0 | 74 | 0 |
| 1 | 28 | 28 |
| 2 | 52 | 132 |
| 3 | 33 | 231 |
| 4 | 24 | 327 |
| 5 | 18 | 417 |
| 6 | 11 | 483 |
| 7 | 6 | 525 |
| 9 | 3 | 552 |
| 10 | 1 | 562 |

Mean **2.25** · median **2** · max **10** · zero-claim products **74** (30%).

By adjudicated bucket:

| golden_bucket | Products | Claims | Mean claims/product | Zero-claim products |
|---|---|---|---|---|
| `hard_yes` | 77 | 328 | 4.26 | 0 |
| `in_between` | 96 | 226 | 2.35 | 2 |
| `hard_no` | 77 | 8 | 0.10 | 72 |

> Multi-claim products dominate: the 40 products with 5+ claims carry 253 of 562 claims (45%). Any per-claim score is disproportionately set by them.
---

## 6. The six fields on the §4 removal list — value distributions

Required before anything is deleted. One correction first:

> **`redo_scchema_version` does not exist.** The file has **`redo_schema_version`** (one spelling, `int`, present on all 250, value `2` on all 250). There is no second misspelled variant. Nothing to remove twice.


### 6.1 `recycling` — 141/250 filled (56.4%)

Type-unstable: 115 list, 25 str, 1 dict, 109 null. 11 distinct values in the list form.

| Value | Occurrences |
|---|---|
| `Plastica - Largamente riciclabile` | 161 |
| `Carta - Largamente riciclabile` | 90 |
| `Metallo - Largamente riciclabile` | 26 |
| `(str) Plastica - Largamente riciclabile…` | 11 |
| `Non riciclabile` | 11 |
| `Vetro - Largamente riciclabile` | 9 |
| `(str) Carta - Largamente riciclabile…` | 6 |
| `Riciclabile` | 5 |
| `(str) Metallo - Largamente riciclabile…` | 2 |
| `Degradabile e compostabile - Largamente riciclabile` | 2 |
| `(dict) {'Vaso': 'Vetro - Largamente riciclabile'}` | 1 |
| `(str) Non riciclabile…` | 1 |

Distinct values: 17. Content is CONAI-style packaging-material disposal coding — 'Plastica – Largamente riciclabile' and friends. **Mandatory disclosure, not a marketing claim.**

### 6.2 `recycling_other` — 158/250 filled (63.2%), 151 distinct

Free text. Mostly material codes and municipal-sorting instructions (`PAP 21 - Carta`, `Verifica le disposizioni del tuo Comune`). **But not only that** — see §7.1, this field is load-bearing.

```
Raccolta differenziata
Astuccio - PAP 21 - Carta
Bustina - PAP 22 - Carta
Verifica le disposizioni del tuo Comune
```
```
Raccolta differenziata
Astuccio - Carta
```
```
Rigoni di Asiago per l'ambiente
Capsula - C/FE 91 - Acciaio
Vasetto - GL 70 - Vetro
Raccolta differenziata
Verifica le disposizioni del tuo Comune
Etichetta in carta riciclata
```

### 6.3 `matched_signals` — 138/250 records non-empty (55.2%)

250 signal objects, all with exactly `{matched_text, category, risk_level}`. 137 distinct `matched_text`.

| Signals on record | Records |
|---|---|
| 0 | 112 |
| 1 | 69 |
| 2 | 45 |
| 3 | 12 |
| 4 | 7 |
| 5 | 3 |
| 6 | 2 |

**Signal `category`:**

| Category | Signals |
|---|---|
| `environmental_unsubstantiated` | 110 |
| `misleading_authenticity_or_origin_claim` | 46 |
| `unfair_comparison` | 24 |
| `unsubstantiated_health_or_efficacy_claim` | 23 |
| `fake_or_unverified_label` | 15 |
| `misleading_superiority_or_absolute_claim` | 11 |
| `misleading_endorsement_claim` | 11 |
| `offset_based_neutrality` | 7 |
| `irrelevant_claim` | 3 |

**Signal `risk_level`:** HIGH 7 · MEDIUM 240 · LOW 3.

**Top 20 `matched_text` — this is the keyword trigger list, read as one:**

| Trigger text | Hits |
|---|---|
| `VIVI VERDE` | 11 |
| `tradizionale` | 11 |
| `Coop per l'ambiente` | 10 |
| `tradizionali` | 9 |
| `sostenibile` | 8 |
| `biodegradabile` | 6 |
| `Dermatologicamente testato` | 6 |
| `N°1 in Italia` | 5 |
| `Clinicamente testato` | 5 |
| `100% naturale` | 5 |
| `pianeta` | 5 |
| `autentico` | 4 |
| `Sostenibile` | 4 |
| `100% Naturale` | 3 |
| `fonti rinnovabili` | 3 |
| `green` | 3 |
| `dermatologicamente testata` | 3 |
| `artigianali` | 3 |
| `tradizionalmente` | 3 |
| `edulcorante ⏎ Per l'ambiente` | 3 |

**Linkage to claims — the decisive number for the migrate-or-drop call:**

| Relationship of claim to this record's signals | Claims |
|---|---|
| `claim_text` **is** a `matched_text` verbatim | 55 |
| a `matched_text` is a **substring** of `claim_text` | 145 |
| **no signal on the record matches the claim at all** | 362 |

So only **200 of 562 claims (36%)** can be traced back to a keyword trigger. The provenance record is real but **partial** — 64% of claims were extracted by something other than these signals.

### 6.4 `legit_or_disclosed_basis_detected` — 44/250 records non-empty (17.6%)

List of strings. 39 records with 1 entry, 5 with 2. 22 distinct values, 49 occurrences.

| Value | Occurrences | What it actually is |
|---|---|---|
| `DOP` | 10 | certification scheme |
| `IGP` | 3 | certification scheme |
| `Fonte IRI` | 3 | disclosed data source |
| `rispetto alla formula precedente` | 3 | disclosed comparator |
| `STG` | 3 | certification scheme |
| `agricoltura biologica` | 3 | certification scheme |
| `da agricoltura biologica` | 3 | certification scheme |
| `certificati FSC` | 2 | certification scheme |
| `carta certificata FSC` | 2 | certification scheme |
| `dati Nielsen` | 2 | disclosed data source |
| `certificato FSC` | 2 | certification scheme |
| `Dati IRI` | 2 | disclosed data source |
| `rispetto alla confezione precedente` | 2 | disclosed comparator |
| `fonte IRI` | 1 | disclosed data source |
| `Fairtrade` | 1 | certification scheme |
| `Equosolidale` | 1 | certification scheme |
| `Rainforest Alliance` | 1 | certification scheme |
| `Commercio equo e solidale` | 1 | certification scheme |
| `commercio equo e solidale` | 1 | certification scheme |
| `FOREST STEWARDSHIP COUNCIL` | 1 | certification scheme |
| `Fonte: Nielsen` | 1 | disclosed data source |
| `Dati Nielsen` | 1 | disclosed data source |

By kind: **certification scheme 34**, **disclosed data source 10**, **disclosed comparator 5**.

### 6.5 `heuristic_bucket` — 250/250

`hard_no` 112 · `in_between` 71 · `hard_yes` 67. Superseded by `golden_bucket` on all 250; disagrees with it on 61. Pure pre-adjudication residue.

### 6.6 `redo_schema_version` — 250/250

`int`, value `2` on every record. Single-valued: zero information content.
---

## 7. Findings you need before Phase 1 — three of them block part of §4

### 7.1 BLOCKER — `recycling_other` is the only source text for 45 claims

Deleting `recycling` and `recycling_other` would strand **45 of 562 claims** (8%): their `claim_text` appears nowhere else in the record. A later annotator re-deriving claims from source text would not be able to find them, and the discard log's audit value drops with them.

Several are **your own §3 seed examples**:

- `Coop per l'ambiente` (IN_SCOPE seed) — 10 occurrences, **all** of them sourced only from `recycling_other`
- `Fai la differenziata per il pianeta` (IN_SCOPE seed) — product 701225
- `Etichetta in carta riciclata` (NEEDS_VERIFICATION seed) — products 663509, 603892
- `Rigoni di Asiago per l'ambiente` (IN_SCOPE seed) — products 663509, 603892

The pattern is that Italian producers print their environmental slogan **inside the packaging-disposal panel**, so the mandatory-disclosure field carries voluntary marketing text alongside the material codes.

<details><summary>All 45 claims sourced only from recycling / recycling_other</summary>

| product_id | name | claim_text | current category |
|---|---|---|---|
| 63854 | Preparato per crema al cioccolato | `Aiutiamo l'ambiente` | environmental_unsubstantiated |
| 621126 | Cioccolatini gianduiotto nero | `Aiutiamo l'ambiente` | environmental_unsubstantiated |
| 642705 | Biscotti con tavoletta cioccolato  | `Bahlsen per l'ambiente` | environmental_unsubstantiated |
| 578874 | Latte al cacao x3 | `Cannuccia e incarto cannuccia plastica compostabile` | environmental_unsubstantiated |
| 594304 | Aceto bianco di alcol | `Casaceto per l'ambiente` | environmental_unsubstantiated |
| 702976 | Coppa taglio fresco | `Citterio per l'ambiente` | environmental_unsubstantiated |
| 716821 | Prosciutto toscano dop taglio fres | `Citterio per l'ambiente` | environmental_unsubstantiated |
| 43145 | Tavoletta cioccolato extra fondent | `Coop per l'ambiente` | environmental_unsubstantiated |
| 41888 | Miele di castagno | `Coop per l'ambiente` | environmental_unsubstantiated |
| 44300 | Tavoletta cioccolato extra fondent | `Coop per l'ambiente` | environmental_unsubstantiated |
| 43616 | Wafer con crema alla nocciola | `Coop per l'ambiente` | environmental_unsubstantiated |
| 46529 | Asiago fresco DOP | `Coop per l'ambiente` | environmental_unsubstantiated |
| 46840 | Parmigiano reggiano DOP 20 mesi | `Coop per l'ambiente` | environmental_unsubstantiated |
| 552334 | Burrata burratina senza lattosio | `Coop per l'ambiente` | environmental_unsubstantiated |
| 41908 | Panetti pane di kamut stirati a ma | `Coop per l'ambiente` | environmental_unsubstantiated |
| 43907 | Pastina gemmine | `Coop per l'ambiente` | environmental_unsubstantiated |
| 40954 | Fagioli borlotti | `Coop per l'ambiente` | environmental_unsubstantiated |
| 39538 | Cialde caffè espresso bar | `Etichetta Ambientale` | irrelevant_claim |
| 594623 | Confettura di ciliegia di vignola  | `Etichetta Ambientale` | irrelevant_claim |
| 612478 | Shampoo per capelli spenti delicat | `Etichetta Ambientale` | irrelevant_claim |
| 608641 | Sapone liquido idratante ricarica | `Etichetta Ambientale` | irrelevant_claim |
| 602008 | Olio detergente struccante per pel | `Etichetta Ambientale` | irrelevant_claim |
| 646175 | Salviettine pelli sensibili base a | `Etichetta Ambientale` | irrelevant_claim |
| 612460 | Dentifricio con microgranuli | `Etichetta Ambientale` | irrelevant_claim |
| 45171 | Seitan alla piastra | `Etichetta Ambientale` | irrelevant_claim |
| 429528 | Feta DOP | `Etichetta Ambientale` | irrelevant_claim |
| 665410 | Gorgonzola DOP dolce al cucchiaio | `Etichetta Ambientale` | irrelevant_claim |
| 612212 | Albume d'uovo | `Etichetta Ambientale` | irrelevant_claim |
| 668756 | Gallette di grano saraceno | `Etichetta Ambientale` | irrelevant_claim |
| 43792 | Zuppa campagnola | `Etichetta Ambientale` | irrelevant_claim |
| 554704 | Succo nettare alla pesca | `Etichetta Ambientale` | irrelevant_claim |
| 43335 | Grissini integrali | `Etichetta ambientale` | irrelevant_claim |
| 663509 | Confettura di pesche gialle natù n | `Etichetta in carta riciclata` | environmental_unsubstantiated |
| 603892 | Confettura all'albicocca naturale  | `Etichetta in carta riciclata` | environmental_unsubstantiated |
| 701225 | Alternativa vegetale allo yogurt s | `Fai la differenziata per il pianeta` | irrelevant_claim |
| 42428 | Salviettine igieniche baby fresh x | `Fare una corretta raccolta differenziata fa bene all'ambiente` | irrelevant_claim |
| 418104 | Patatine la non patatina | `Fiorentini per l'ambiente` | environmental_unsubstantiated |
| 41950 | Farina per pane nero | `Il sacchetto di carta rispetta l'ambiente` | environmental_unsubstantiated |
| 418104 | Patatine la non patatina | `Incarto riciclabile 100% plastica` | environmental_unsubstantiated |
| 68928 | Patatine 1936 multipack | `L'ambiente è vita. Tienilo pulito` | irrelevant_claim |
| 571225 | Latte uht intero | `Latteria Soresina per l'ambiente` | environmental_unsubstantiated |
| 663509 | Confettura di pesche gialle natù n | `Rigoni di Asiago per l'ambiente` | environmental_unsubstantiated |
| 603892 | Confettura all'albicocca naturale  | `Rigoni di Asiago per l'ambiente` | environmental_unsubstantiated |
| 144400 | Proteggislip normali pure sensitiv | `Rispetta l'ambiente` | environmental_unsubstantiated |
| 164990 | Lievito vanigliato x10 | `Rispettiamo l'ambiente` | environmental_unsubstantiated |

</details>

**Recommendation:** drop `recycling` (pure material coding, 11 distinct values, no claim depends on it) but **keep `recycling_other`**, or — if you want it gone from the record — copy it into a new `source_text` field first. I need your call; I am not deleting it either way until you give one.

### 7.2 `legit_or_disclosed_basis_detected` does not map to `verification.on_pack_qualifier`

Your §4 hypothesis was that it encodes on-pack qualifiers. It does not. Its 49 entries split three ways:

| Kind | Entries | Correct destination in the v2 shape |
|---|---|---|
| Certification scheme name (`DOP`, `IGP`, `STG`, `certificati FSC`, `Fairtrade`, `Rainforest Alliance`, `agricoltura biologica`, …) | 32 | `verification.scheme` |
| Disclosed data source (`Fonte IRI`, `dati Nielsen`, `Fonte: Nielsen`, `Dati IRI`) | 10 | `verification.on_pack_qualifier` |
| Disclosed comparator (`rispetto alla formula precedente`, `rispetto alla confezione precedente`) | 7 | `verification.on_pack_qualifier` |

Two further problems with migrating it as-is:

1. **It is product-level, not claim-level.** 44 records carry it; those records hold 141 claims between them. Nothing says which claim the basis belongs to. Migrating it mechanically would attach `DOP` to every claim on a DOP product, including its health claims.
2. **It is not where the real qualifiers live.** The footnote bodies your Appendix A example shows (`* water and naturally sourced ingredients with limited processing`) are already inside `claim_text` itself — 65 claims carry a `*`/`**`/`^` marker and 67 use the ` ... ` join to append the footnote body. That is the genuine `on_pack_qualifier` source, and it survives regardless of what happens to this field.

**Recommendation:** migrate, but **claim-scoped and by hand during Phase 2 adjudication**, not mechanically. The 22 distinct values are few enough to route individually. Its 32 scheme entries are genuinely useful — they are a shortlist of the products where a NEEDS_VERIFICATION `scheme` value is already known.

### 7.3 `matched_signals` — keep, but as a side file, not in the record

It is the only record of keyword provenance and it does show systematic over-detection: `tradizionale`/`tradizionali`/`tradizionalmente` fire 23 times and `Dermatologicamente testato`/`Clinicamente testato` 14 — exactly the two categories §2 sends to DISCARD. That makes it the evidence for *why* a whole category leaves the set, which is what your discard log is for.

But it covers only 36% of claims, it is product-scoped, and its `category`/`risk_level` duplicate fields that are already claim-level. **Recommendation:** write it out to `golden/matched_signals_v1.json` keyed by `product_id` at Phase 3 and drop it from the record, rather than either deleting it or carrying it forward.

### 7.4 There is no `schema_version` field to bump

§6 Phase 3 says to bump `schema_version` to 2. The file has no such field. It has `redo_schema_version: 2`, which is on your removal list. So 'bump to 2' has nothing to act on and the removal would take the only version marker with it.

**Recommendation:** add a real top-level `schema_version: 2` as a new field in the v2 shape, remove `redo_schema_version`, and note in the changelog that the two are unrelated counters. Confirm at Phase 3.

### 7.5 The set has no claim-level label at all

Appendix A assumes `claim.label`. The file labels **products** (`golden_bucket`: 77 `hard_yes` / 96 `in_between` / 77 `hard_no`) and annotates claims with `category` + `risk_level` + `modifiers`.

This is the schema expression of the problem your brief opens with: *'it collapses this is a violation together with someone has to check a certificate into a single positive class.'* It is worse than that — the positive class is **a product-level bucket**, so per-claim precision is not merely unmeasurable, it was never represented.

Consequence for Phase 2: the audit has no per-claim prior to disagree with. 'positive → DISCARD' has to be reconstructed. The honest mapping is:

| v1 signal | Read as v1 'positive' for the disagreement report |
|---|---|
| claim `category` ≠ `irrelevant_claim` | positive (508 claims) |
| claim `category` = `irrelevant_claim` | negative (54 claims) |

I will use exactly that mapping in AUDIT_02 and label it as a reconstruction, not a stored v1 label. Say so if you want a different one.

### 7.6 Smaller things

- **Separator is ASCII, not an ellipsis.** Composite claims join the claim and its footnote with `' ... '` (space, three full stops, space) — 67 claims — plus 1 with a bare `...`. Your Appendix A example shows `' … '` (U+2026). Migration must not silently convert; the §8 no-normalisation rule covers this and I will assert byte-equality on every retained `claim_text`.
- **81 claim texts are duplicates** across products (562 total, 481 distinct). `Etichetta Ambientale` ×14, `VIVI VERDE` ×13, `Coop per l'ambiente` ×10. A relabel decision on one of these is a decision on all its copies — the disagreement report will group them so you adjudicate once.
- **88 claim texts are not verbatim substrings of any source field** — they are annotator compositions joining a headline to a footnote across fields (`3x Denti più bianchi subito* ... Clinicamente provato su 58 soggetti`). They are the most information-rich claims in the set and the ones where `on_pack_qualifier` is recoverable. They are not errors; noting so nobody 'fixes' them later.
- **Five undeclared sparse fields** (`hard_no_reason` 112, `bucket_correction` 40, `bucket_review_flag` 19, `bucket_review_detail` 19, `extraction_note` 11) are annotation-process residue tied to the product-bucket scheme that v2 replaces. They are not on your §4 list. They will become meaningless after relabelling. Flagging now; decide at Phase 3.
- **74 products (30%) already carry zero claims.** Your rule 'a product whose every claim is discarded keeps its record' therefore has precedent in the file and costs nothing structurally.

---

## 8. Phase 0 gate — what I need from you

1. `recycling_other`: delete, keep, or copy to `source_text` before deleting? (45 claims depend on it — §7.1)
2. `legit_or_disclosed_basis_detected`: agree it is migrated by hand, claim-scoped, during Phase 2 — split between `verification.scheme` and `verification.on_pack_qualifier`? (§7.2)
3. `matched_signals`: agree it goes to `golden/matched_signals_v1.json` rather than being deleted or carried? (§7.3)
4. `schema_version`: add as a new field, given it does not exist? (§7.4)
5. The v1-positive reconstruction in §7.5 — is `category != irrelevant_claim` the right reading of 'positive'? (§7.5)

`recycling`, `heuristic_bucket` and `redo_schema_version` I am satisfied carry no signal the v2 schema needs, and will drop them once you sign off.

**Nothing has been modified.** The only files written are this report and its two source fragments.
