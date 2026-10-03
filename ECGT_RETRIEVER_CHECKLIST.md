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
- [x] Record the model name and version in config, not in code, so embeddings stay versioned (revisions pinned 2026-10-03).
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

Done 2026-10-03: `retriever/score.py` (`Retriever(cfg, model=None)`, `score_record`, `candidates`), tests in `tests/test_score.py` (offline char-n-gram encoder, no download).

- [x] Anchors embedded once into a normalized numpy matrix, cached under `.cache/anchor_embeddings/` keyed by model name + revision + prefix + anchors sha256. If `anchors.sha256` is set in the config, a mismatch is refused.
- [x] `margin = agg(sim pos) − agg(sim neg)`, `scoring.aggregation: max | top3_mean`.
- [x] Scored texts per span: the full text (with joined footnote) and each comma clause; span margin = max, `best_text` records which.
- [x] Lexical hit: `lexical.include` / `exclude` on the full span text.
- [x] Candidate rule: `lexical_hit OR margin > τ`; while `scoring.tau.<model>` is null, lexical only (margins still computed for Step 5).
- [x] Each span keeps its top-`fewshot_k` positive anchors (id, text, triggers, sim) to the full text.
- [x] Empty records and zero-candidate records return `[]`.
- [x] Reserve sanity run (e5, max): 268 ms/record on CPU/MPS incl. embedding; preview for Step 5:

  | τ | reserve recall (IN_SCOPE/NV) | candidates / spans | per record |
  |---|---|---|---|
  | none (lexical only) | 259/267 | 27% | 4.4 |
  | 0.03 | 261/267 | 30% | 4.9 |
  | 0.02 | 264/267 | 38% | 6.1 |
  | 0.01 | 266/267 | 54% | 8.6 |
  | 0.00 | 266/267 | 74% | 11.9 |

  Lexical is tuned on the reserve, so its share is optimistic; the 8 lexical misses are mostly named endorsements / supply-chain prose with margins +0.01…+0.04. Embedding margin alone separates weakly (95.5% recall needs τ = 0, i.e. 72% of all spans).

## Step 5: Calibrate τ (on the reserve/dev set; measure gold once)

Done 2026-10-03: `retriever/calibrate.py`; sweeps in `retriever/calibration_reserve.csv` (selection) and `retriever/calibration_gold_report_only.csv` (reporting only, never used to choose).

- [x] Swept τ (−0.05…+0.10, step 0.0025) for e5/mpnet × max/top3_mean, reporting recall (combined, per trigger, embedding alone), lexical-only vs embedding-only recalls, candidates per record, DISCARDED claims that still become candidates.
- [x] **Selection rule changed:** the original "smallest τ with recall ≥ 95%" was inverted (smaller τ = more candidates) and, read as "largest τ", is met by keywords alone on the reserve (97.0%) because the keyword list was tuned there. Rule used: **largest τ with reserve recall ≥ 99%** (stricter target to absorb the dev-set optimism; a missed span is lost for good).
- [x] Result on the reserve (target 99%): **e5 + top3_mean, τ = 0.0125** → 266/267, 7.3 candidates/record (e5/max 265 @ 7.8; mpnet/top3 265 @ 8.6; mpnet/max 265 @ 9.8). Written to the config, with `mpnet: 0.0025`.
- [x] **Gold, measured once with the locked setting: 281/288 = 97.6%**, 12.7 candidates/record (47% of spans); embedding alone 87.2%; keywords alone 271/288 = 94.1% (fails the 95% gate → the embedding is needed). 44% of labelled DISCARDED claims still become candidates (Pass 2 cost).
  - 7 gold misses: «Antispreco», «save the olives», «Harmony - Patto del grano buono», «Sammontana è una società benefit», «Selezioniamo i terreni più vocati», «Inchiostro a base vegetale», «Senza solfati, coloranti e ftalati» (margins −0.017…+0.012).
- [ ] Per-trigger < 90%: reserve named_endorsement 7/8; gold pollutant_free 6/7. Both n < 10 (one claim each). Add real anchors from **new** data (not gold, and not the reserve, which would inflate the dev numbers).
- [x] **Gate:** recall ≥ 95% on gold with ~13 Pass 2 calls/record — passed.
- [x] Model revisions pinned and `anchors.sha256` set in the config.

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
