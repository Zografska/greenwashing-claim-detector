# ECGT claim detector: embedding retriever, implementation checklist

Replaces LLM Pass 1 with deterministic segmentation plus an embedding and lexical candidate
retriever. Pass 2 (triggers) and POST (triggers → label) stay as they are. Pass 2 also gets
retrieved anchors as dynamic few-shot examples.

```
record ─► PRE ─► segment ─► footnote join ─► candidate? (lexical OR margin > τ)
       ─► dedupe / source_field ─► PASS 2 (+ top-3 anchors as few-shot) ─► POST
```

**Core rule:** the retriever decides *whether* a span is an ECGT candidate, never *which label*
it gets. Labels come only from Pass 2 triggers and the POST code.

---

## Decisions log (settled, 2026-09-24)

- [x] Positive anchors are pooled for candidate retrieval; the IN_SCOPE/NV split lives only in Pass 2 and POST.
- [x] Scoring uses a margin, `max_sim(pos) − max_sim(neg)`, not a raw similarity threshold.
- [x] Geographic origin → negative (`origin`).
- [x] DOP/IGP/STG → negative (`quality_scheme`).
- [x] «Aroma/gusto naturale» → negative (`natural_flavour`).
- [x] Functional packaging (salvafreschezza, richiudibile, …) → negative (`functional_packaging`).
- [x] «Senza siliconi» → positive `pollutant_free` (NV).
- [x] Footnoted anchors are stored in joined form (`claim ... footnote body`).
- [x] Anchors are real first, with synthetic ones filling gaps, tagged `origin: synthetic`.
- [x] POST stays unchanged: `defined_term` cancels only `undefined_natural`.
- [x] Anchor set v1: `anchors.jsonl`, 123 anchors (74 pos / 49 neg), at least 3 per category.
- [x] Anchor set v2: `anchors_v2.jsonl`, 120 anchors (74 pos / 46 neg). Changes from v1:
  - dropped the 3 `mandatory_disclosure` anchors (PRE regex removes these texts deterministically)
  - made the tomato pair topic-neutral: «Raccolti a mano» (farming_practice), «Coltivati in Puglia» (origin)
- [x] Anchor set v4: `retriever/knowledge/anchors_v4.jsonl`, 121 anchors = v3 with the gold-overlapping Pampers anchor replaced by a reserve span (2026-10-03).
- [x] Anchor set v3: `retriever/knowledge/anchors_v3.jsonl`, 121 anchors (74 pos / 47 neg) = v2 + «Senza parabeni» (`free_from_non_pollutant`). «Latte Alto Adige» not added.
- [x] Retriever code, config and anchors live in `retriever/` (config: `retriever/ecgt_retriever.yaml`, the source of truth for the keyword list, model names and anchor path).
- [x] Anchors stay topic-neutral: no product nouns or brand names in new synthetic anchors.
- [x] Template-sharing negatives that slip through («Formula esclusiva», «Pack richiudibile», «Adatto alle pelli sensibili», «fonte di fibre») are accepted: they cost one Pass 2 call each.
- [x] Headings are never claims on their own; a heading over disposal instructions is dropped with them (2026-10-03).
- [x] Heading rule exempts brand eco-slogans («<Brand> per l'ambiente» stays a claim even above a disposal block) (2026-10-03).
- [x] Recycling calls-to-action: bare CTA → out_of_scope; CTA + environmental-benefit clause («per il pianeta») → generic_green (2026-10-03).
- [x] Gold claims may carry `needs_review: true`; evaluators skip them.
- [x] Retriever errors are asymmetric: a missed positive can be lost for good, a leaked negative costs one Pass 2 call. Gates measure positives kept; negatives rejected is a cost metric.

---

## Step 0: Housekeeping (before any code)

- [x] Decide on the two omissions:
  - [x] «Senza parabeni» added as `N-free_from_non_pollutant-06` → **anchor set v3** (`retriever/knowledge/anchors_v3.jsonl`, 121: 74 pos / 47 neg). LOO on v3: positives kept unchanged (e5 70/74, mpnet 65/74, same misses as v2); mpnet rejects «Senza parabeni» itself, e5 does not (margin +0.013, nn «Senza fosfati»).
  - [x] «Latte Alto Adige» skipped: `origin` already has 3 anchors incl. a region («Coltivati in Puglia»), and "Latte" is a product noun.
- [x] Anchors under version control in `retriever/knowledge/` (v1 = `anchors.jsonl`, v2, v3). Config `retriever/ecgt_retriever.yaml` points at v3.
- [x] Pass 2 `out_of_scope` line now lists all 11 negative anchor categories one-to-one, incl. natural flavour/taste and packaging function.
  - [x] Added `CLAIM: Aroma naturale` → `["out_of_scope"]` as a **5th** static few-shot (dynamic few-shot only retrieves positive anchors, so Pass 2 would otherwise see no negative example). `pass2.static_fewshot: 5`.
- [x] `ECGT_TWO_PASS_PROMPT.md`:
  - [x] Open questions 1–3 marked resolved (origin → out_of_scope, DOP/IGP → out_of_scope, «Senza microplastiche»/«Senza siliconi» → NV); Q4 marked superseded.
  - [x] PASS 1 section **kept** as the Step 7 baseline (A), with a pointer to the retriever at the top.
- [x] Keyword list: no `extraction.py` on this branch. The ECGT-only list lives in `lexical.include` in `retriever/ecgt_retriever.yaml` (word-bounded): the planned additions (vegan, agricoltor, tracciabil, mucche, allevat, approvat, rischio, compostabil, PFAS, fosfati, microplastic, siliconi, carbon, emissioni, origine animale, derivat… animal) plus `biologic`, `natura`, `verde`, `plastica`, `impatto`, `climatic`, `rinnovabil`, `certificat`, `fsc`, `fairtrade`, `ecolabel`.
- [x] `check_prefilter_coverage.py` replaced by `retriever/lexical_coverage.py`:
  - anchors v3: 67/74 positives hit, 3/47 negatives hit (the 3 natural_flavour anchors, via `\bnatural\w*`)
  - positives missed by both LOO embedding and lexical: **e5 0**, mpnet 1 («Raccolti a mano»)
  - Coop LLM-run claims (not gold): 15/16 IN_SCOPE/NV hit; 3/9 DISCARD hit

## Step 1: Choose the embedding model (leave-one-out)

- [x] `pip install sentence-transformers`
- [x] Run (current form):
  ```
  python3 retriever/loo_check.py --anchors retriever/knowledge/anchors_v4.jsonl \
    --csv retriever/loo_results_v4.csv \
    --models charngram intfloat/multilingual-e5-base \
             sentence-transformers/paraphrase-multilingual-mpnet-base-v2
  ```
- [x] v1 results (123 anchors), positives kept / negatives rejected / overall polarity:
  - charngram (baseline): 79.7% / 55.1% / 69.9%
  - **multilingual-e5-base: 91.9% / 59.2% / 78.9%**
  - paraphrase-multilingual-mpnet: 86.5% / 59.2% / 75.6%
  - bge-m3: 86.5% / 57.1% / 74.8%
- [x] Hard pairs reviewed: mandatory_disclosure dropped, tomato pair reworded, template-sharing negatives accepted, keyword gaps added in Step 0.
- [x] Models going forward: **e5 primary, mpnet runner-up**. bge-m3 dropped (largest model, scored last).
  - Note: e5 margins are compressed (mostly 0.00–0.07), so sweep τ in fine steps in Step 5.
- [x] Reran LOO on v2 (120 anchors). Positives kept / negatives rejected / overall polarity:
  - charngram (baseline): 79.7% / 56.5% / 70.8%
  - **multilingual-e5-base: 94.6% / 60.9% / 81.7%**, with lexical rule: 74/74 positives kept
  - **paraphrase-multilingual-mpnet: 87.8% / 65.2% / 79.2%**, with lexical rule: 72–73/74 (re-measured on v3 with the config keyword list: 73/74, only «Raccolti a mano» missed by both)
  - bge-m3: 87.8% / 60.9% / 77.5% (not carried forward)
- [x] Dropping `mandatory_disclosure` fixed «Vaschetta … PET riciclato» in all three models.
- [ ] Watch «Raccolti a mano» in Step 5: it is short and generic enough to act as a magnet. In e5 it passes with only a +0.003 margin (nearest neighbour «Etichetta in carta riciclata») and it pulls «Brevetto internazionale» and «Marchio registrato» over the line. In mpnet it still fails.
- [x] `ambiente` and `pianeta` are in `lexical.include`.
- [ ] Record the model name and version in config, not in code, so embeddings stay versioned. (Names are in `retriever/ecgt_retriever.yaml`; `revision` still null.)
- [x] **Gate:** positives kept ≥ 85% in LOO, and ≥ 95% when combined with the lexical rule. Negatives rejected is reported as a cost, with no gate. **Passed by e5 and mpnet on v2.**

## Step 2: Build the gold span set

- [x] 100 Carrefour records across 16 aisles (food 72, personal care/household 28), from `golden/clean/carrefour.json`: `golden/labeled/golden_set_ecgt_100.json` (+ README). Reserve of 174 more records labelled the same way: `golden_set_ecgt_reserve.json`.
  - [x] 28 records with **zero** ECGT claims (all carry DISCARDED decoys).
  - Single retailer, and `description` is the only text field, so multi-field dedupe / `source_field` isn't exercised here; Step 3 unit tests cover it.
- [x] Validated (2026-10-03): every claim and footnote is a verbatim substring of its description, `source_index` matches the EAN, labels follow the POST rule, all triggers are valid, no duplicates.
- [x] Reviewed the unannotated lines that hit keywords; 3 amendments + 2 conventions (headings, recycling calls-to-action), see the README's "Amendments" section and the decisions log. 1 claim is `needs_review` (skip in scoring).
- [x] Frozen as `eval/gold_spans_v1.jsonl`: 777 spans (288 IN_SCOPE/NV, 489 DISCARDED), sha256 `776085444c4668f927adf84e5c239f4405de8af30a2506eed7c2bf5bdede7ca5`. **Never add these spans to the anchors, never tune keywords on them.**
  - [x] Anchor `P-recycled_recyclable-02` («Qualità Pampers in cartoni 100% riciclati») was identical to a gold claim → replaced in **anchors v4** by a reserve span («Bottiglia, esclusi etichetta e tappo, realizzata con il 100% di plastica riciclata»). LOO on v4 unchanged: e5 70/74, mpnet 65/74.
- [x] The reserve set is the **dev set**: keywords/anchors get tuned there (`eval.dev_spans` in the config).
  - [x] Keyword list extended from reserve misses (+22 patterns, `ricicla`→`ricicl`, `allevat`→`alleva`). Reserve: 212 → **258/268** positives hit; DISCARDED hits 39 → 62/433 (cost).
  - Held-out gold, measured once: **258/288 (89.6%)** keywords alone; DISCARDED hits 53/488. Visible gold-only gaps (deliberately *not* added, to keep gold clean): `biodiversit`, «Ecofriendly», `glifosato`, «società benefit». Add them only if they turn up in the reserve set or new data.

## Step 3: Segmentation module

Done 2026-10-03: `retriever/segment.py` (settings in the config's `pre`/`segmentation`), tests in `tests/test_segment.py` (30 passing), coverage check `retriever/segment_coverage.py`.

- [x] **PRE:** only the config's `text_fields` are segmented (certifications, features, producer_info, description; name/denomination are not claims), so annotation/recycling fields are ignored by construction. Whole lines are dropped by **structural** patterns only (`pre.drop_lines`): disposal block (material codes, «Largamente riciclabile», «Raccolta <material>», «Verifica … tuo comune» instructions), retailer origin lines, labelled sections (Ingredienti/Ricetta/Modalità d'uso/Conservazione/…). Old `_MANDATORY_DISCLOSURE_PATTERNS` **not** reused: it dropped every «<Brand> per l'ambiente», which are positive anchors.
  - [x] Heading rule: a short line directly above a pattern-dropped disposal line is dropped only if it has heading vocabulary (ambiente/pianeta/natura/confezione/imballo) and no specific wording; brand eco-slogans («Fiorentini per l'ambiente») are exempt (decision 2026-10-03).
- [x] **Base units:** line break (also HTML `<br>`), bullet, sentence end; never a comma; abbreviations («Dott.», «A.I.Nut.», «S.p.A.») don't end a sentence.
- [x] **Windows:** 2 adjacent units within one paragraph — never across a blank line, a dropped line or a footnote body (no gold span crosses a blank line).
- [x] **Sub-clauses:** `Span.clauses` (comma split) for scoring only; the whole unit is emitted.
- [x] **Footnote join:** marker-carrying spans joined as `claim ... body` (several bodies joined by newlines, same field first, else any field); joined bodies are not scored alone; unused bodies stay as units (recall-first). «N°1», «12 °C» are not markers.
- [x] **Dedupe:** same normalized text kept once, `source_field` by `text_fields` order, other fields in `also_in`.
- [x] Unit tests: the *Bagnoschiuma* fixture, multiple markers, same text in two fields, plus comma/abbreviation/`<br>`/window/disposal/heading/origin cases.
- [x] **Coverage** (labelled claims reproduced as a span, exact or covered):
  - reserve (dev): IN_SCOPE/NV **267/267**; 16.0 spans/record
  - gold, measured once: **287/288 (99.7%)**; the miss was a too-broad `tuo comune` disposal pattern, fixed afterwards (now 288/288, but that figure is gold-informed). 26.8 spans/record (gold favours long records).
  - all 950 cleaned records segment without errors in < 1 s.
  - reserve relabel: «Rispettiamo l'ambiente» (cameo) → out_of_scope under the heading rule.

## Step 4: Candidate scoring

- [ ] Load anchors once and embed them into a normalized numpy matrix. No vector DB needed at this size.
- [ ] Score each span as `margin = max_sim(pos) − max_sim(neg)`. Also try the mean of the top-3 for each polarity.
- [ ] Score `Span.clauses` and the joined text; unit score = max.
- [ ] **Lexical hit:** `lexical.include` from `retriever/ecgt_retriever.yaml`, word-bounded (`\bbio\b`, not the substring).
  - [ ] Add exclusion patterns (`\baroma naturale\b`, `\bgusto naturale\b`) only if Step 5 shows leakage.
- [ ] Candidate rule: `lexical_hit OR margin > τ`.
- [ ] For each candidate, keep its top-3 nearest **positive** anchors (id, text, triggers) for Pass 2.
- [ ] Handle empty records and records with zero candidates without errors.

## Step 5: Calibrate τ on the gold set

- [ ] Sweep τ, and at each value report:
  - span recall (overall and per trigger)
  - candidates per record, which is the Pass 2 cost
  - how many recalled spans came from lexical only vs. embedding only
- [ ] Calibrate τ separately for e5 and mpnet (their margin scales differ), then pick the model with fewer candidates per record at equal recall.
- [ ] Choose the **smallest τ with span recall ≥ 95%**. A missed span is lost for good, while an extra candidate costs only one Pass 2 call.
- [ ] Check per-trigger recall. Add real anchors for any trigger below 90%.
- [ ] **Gate:** recall ≥ 95% with a candidate count you can afford to run.

## Step 6: Pass 2 with dynamic few-shot

- [ ] Keep the 5 static examples, and append the top-3 retrieved anchors as extra `CLAIM → triggers` examples.
  - [ ] Use each anchor's `triggers` field as its expected output.
- [ ] Watch the token budget: `num_ctx` ≈ 3k should still fit. Check this with `--limit 2-3`.
- [ ] POST is unchanged. Claims whose only trigger is `out_of_scope` are dropped, which is also how retriever false positives get discarded.

## Step 7: End-to-end evaluation

- [ ] On the gold set, compare:
  - A) original two-pass (LLM Pass 1 + Pass 2)
  - B) retriever + Pass 2 with static few-shot
  - C) retriever + Pass 2 with dynamic few-shot
- [ ] Metrics:
  - claim-level precision and recall
  - label accuracy (IN_SCOPE / NV)
  - trigger-set exact match
  - runtime per record
- [ ] **Decision:** keep the retriever if B or C matches A on recall and label accuracy while being faster or cheaper.

## Step 8: Later

- [ ] Replace synthetic anchors with real spans from production records as they turn up. Keep `origin` accurate.
- [ ] Once there are a few hundred labeled spans, train logistic regression or SetFit on the embeddings as the candidate classifier. Anchors then serve only as the few-shot pool.
- [ ] If outputs must be citable in Italy, add Codice del Consumo article mapping to the triggers (see `legal-framework-ecgt-ucpd.md`), e.g. the Art. 23 letters for the blacklist triggers.
- [ ] Re-embed the anchors and rerun Steps 1 and 5 whenever the model or the anchor set changes.
