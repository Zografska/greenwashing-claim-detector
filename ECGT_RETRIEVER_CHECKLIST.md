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
- [x] Anchor set v3: `retriever/knowledge/anchors_v3.jsonl`, 121 anchors (74 pos / 47 neg) = v2 + «Senza parabeni» (`free_from_non_pollutant`). «Latte Alto Adige» not added.
- [x] Retriever code, config and anchors live in `retriever/` (config: `retriever/ecgt_retriever.yaml`, the source of truth for the keyword list, model names and anchor path).
- [x] Anchors stay topic-neutral: no product nouns or brand names in new synthetic anchors.
- [x] Template-sharing negatives that slip through («Formula esclusiva», «Pack richiudibile», «Adatto alle pelli sensibili», «fonte di fibre») are accepted: they cost one Pass 2 call each.
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
  python3 retriever/loo_check.py --anchors retriever/knowledge/anchors_v3.jsonl \
    --csv retriever/loo_results_v3.csv \
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

- [ ] Sample 50–100 real records across categories (food, personal care, household).
  - [ ] Include about 10 records with **zero** ECGT claims.
- [ ] Run the original LLM Pass 1 on them to get silver spans.
- [ ] Hand-correct them. Record for each span: `record_id`, `claim_text` (verbatim, joined form if footnoted), `source_field`, expected `triggers`, expected `label`.
- [ ] Freeze the set as `eval/gold_spans_v1.jsonl`. **Never add these spans to the anchors.**

## Step 3: Segmentation module

- [ ] **PRE:** strip annotation fields, drop the `recycling` field, drop mandatory disclosures (reuse `_MANDATORY_DISCLOSURE_PATTERNS`), drop ingredient lists and cooking/storage text.
- [ ] **Base units:** split on line break, bullet and sentence end. Never split at a comma.
- [ ] **Windows:** also build merged spans of 2 adjacent units. This covers «Emissioni zero / …» and «Viva la Natura! / …».
- [ ] **Sub-clauses:** split each unit on commas for *scoring only*. The unit's score is the max over its clauses, but the whole unit is emitted.
- [ ] **Footnote join (before embedding):**
  - [ ] Find marker-carrying spans (`*`, `**`, `^`, `°`) and join each with its body line as `claim ... body`.
  - [ ] Remove the standalone body lines so they are never scored on their own.
- [ ] Unit tests:
  - [ ] Use the *Bagnoschiuma idratante* few-shot record as a fixture (footnote, mixed fields, negatives).
  - [ ] A record with multiple footnote markers.
  - [ ] A record where one text appears in two fields; the dedupe must keep the most specific `source_field`.

## Step 4: Candidate scoring

- [ ] Load anchors once and embed them into a normalized numpy matrix. No vector DB needed at this size.
- [ ] Score each span as `margin = max_sim(pos) − max_sim(neg)`. Also try the mean of the top-3 for each polarity.
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
