# Handoff: ECGT claim detector, embedding-retriever redesign

Context for continuing this work in Claude Code. The session ran on 2026-09-24. Read this file first, then `ECGT_RETRIEVER_CHECKLIST.md`.

## Files (as placed in the repo, 2026-09-24)

| Repo path | What it is |
|---|---|
| `retriever/knowledge/anchors_v4.jsonl` | **Current** anchor set: 121 anchors (74 pos / 47 neg) = v3 with the gold-overlapping Pampers anchor replaced |
| `retriever/knowledge/anchors_v3.jsonl` | v2 + «Senza parabeni» |
| `eval/gold_spans_v1.jsonl` | **Frozen** gold spans (Step 2): 777 spans from 100 Carrefour records; source `golden/labeled/golden_set_ecgt_100.json` |
| `golden/labeled/golden_set_ecgt_reserve.json` | 174 more labelled records = the **dev set** for tuning keywords/anchors |
| `retriever/knowledge/anchors_v2.jsonl` | Previous set (120), kept for comparison |
| `retriever/knowledge/anchors.jsonl` | v1 (123), kept for comparison |
| `retriever/ecgt_retriever.yaml` | Pipeline config: anchor path, embedding models, segmentation, **keyword list**, τ, Pass 2 settings |
| `retriever/loo_check.py` | Leave-one-out sanity check across embedding models (`loo_results*.csv` = its output) |
| `retriever/lexical_coverage.py` | Coverage check for the keyword list over anchors and claims files |
| `retriever/segment.py` | Step 3 segmentation (PRE, units, footnote join, windows, dedupe) |
| `retriever/segment_coverage.py` | Step 3 gate: are labelled claims reproduced as spans |
| `retriever/score.py` | Step 4 candidate scoring (margin, lexical OR rule, few-shot anchors) |
| `retriever/calibrate.py` | Step 5 τ sweep and selection (`calibration_*.csv` = its output) |
| `tests/test_segment.py` | Segmentation unit tests |
| `ECGT_RETRIEVER_CHECKLIST.md` | Step-by-step plan with gates; Steps 0–1 done |
| `golden/ECGT_TWO_PASS_PROMPT.md` | Two-pass LLM design; Pass 2 and POST are reused, Pass 1 is kept as the Step 7 baseline |
| `legal-framework-ecgt-ucpd.md` | **Not in the repo** (never committed). Needs to be found or rewritten before Step 8's article mapping |

## Goal

Detect ECGT (Dir. 2024/825 amending UCPD) claims in Italian grocery and personal-care product records. The pipeline must run on local 3–8B models. Each claim is labelled either:
- **IN_SCOPE**: problematic as written, or
- **NEEDS_VERIFICATION (NV)**: specific and checkable.

## The redesign: replace LLM Pass 1 with a retriever

The original design had two LLM passes: Pass 1 extracts spans, Pass 2 classifies them into triggers. We replace **Pass 1** with deterministic segmentation plus an embedding and lexical candidate retriever. **Pass 2 and POST stay as they are.**

```
record ─► PRE ─► segment ─► footnote join ─► candidate? (lexical_hit OR margin > τ)
       ─► dedupe / source_field ─► PASS 2 (+ top-3 retrieved anchors as few-shot) ─► POST
```

**Core rule:** the retriever decides only *whether* a span is an ECGT candidate, never *which label* it gets. The IN_SCOPE/NV split depends on specificity (defined term, identifiable comparator, named body), and embeddings don't capture that. Labels come only from Pass 2 triggers and the POST code:

```python
IN_SCOPE_T = {"generic_green","undefined_natural","climate_neutral",
              "vague_comparison","brand_eco_slogan","vague_supply_chain"}

def label(triggers):
    t = set(triggers) - {"out_of_scope"}
    if not t:
        return None                        # drop
    if "defined_term" in t:
        t.discard("undefined_natural")     # a definition cancels only "undefined"
    return "IN_SCOPE" if t & IN_SCOPE_T else "NEEDS_VERIFICATION"
```

### Scoring
- Embed spans and anchors (normalized) and compute `margin = max_sim(pos anchors) − max_sim(neg anchors)`. Also try the mean of the top-3 for each polarity.
- A span is a candidate if `lexical_hit OR margin > τ`.
- Keep the top-3 nearest **positive** anchors (id, text, triggers) per candidate. They become dynamic few-shot examples for Pass 2.
- No vector DB is needed at this size; use a numpy matrix.

### Error costs are asymmetric
- A missed positive may be lost for good.
- A leaked negative costs one Pass 2 call, and Pass 2 drops it via `out_of_scope`.

So the gates measure **positives kept / recall**. Negatives rejected is only a cost metric.

## Anchor file format

One JSON object per line:

```
id, text, polarity (pos|neg), category, triggers[], label_hint (IN_SCOPE|NEEDS_VERIFICATION|null),
origin (real|synthetic), form (joined|claim_only)
```

- Positive `category` is the primary Pass 2 trigger. `triggers` can list more than one (e.g. «Eco pack 100% riciclabile - Con meno plastica» → generic_green, recycled_recyclable, vague_comparison).
- Negative categories: health_nutrition, performance, tests_tolerance, tradition_history, patents, origin, quality_scheme, free_from_non_pollutant, sales_rank, natural_flavour, functional_packaging.
- Footnoted anchors are stored **joined**: `claim ... footnote body`. Segmentation must therefore join footnotes *before* embedding.

## Settled decisions

- **Out of scope (negative anchors):**
  - Geographic origin
  - DOP/IGP/STG
  - «Aroma/gusto naturale»
  - Functional packaging (salvafreschezza, richiudibile, …)
  - Free-from of non-pollutants (conservanti, glutine, lattosio, …)
  - Sales rank
- **NV (`pollutant_free`):** «Senza microplastiche», «Senza siliconi».
- **Earlier scope decisions from the prompt doc still hold:**
  - recycled/recyclable → NV, unless the same line has a generic eco word or an unanchored reduction
  - approval by a named org → NV
  - vegan → NV, always
  - supply chain is in scope; recipe, tradition and history are not
  - «riduce il rischio di …» → NV
- **POST is unchanged:** a footnote definition does not cancel `generic_green` (DT5 «Packaging sostenibile* …» was rejected).
- **v2 anchor changes from v1:**
  - dropped the 3 `mandatory_disclosure` anchors; PRE regex (`_MANDATORY_DISCLOSURE_PATTERNS`) removes these texts deterministically
  - tomato pair made topic-neutral: «Raccolti a mano» (farming_practice), «Coltivati in Puglia» (origin)
- **Anchors must be topic-neutral:** no product nouns or brand names in new synthetic anchors.
- **Accepted leaks:** template-sharing negatives («Formula esclusiva», «Pack richiudibile», «Adatto alle pelli sensibili», «fonte di fibre») may slip through, since each costs one Pass 2 call.
- **Models:** `intfloat/multilingual-e5-base` is primary (use the `query: ` prefix on both sides); `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` is the runner-up. bge-m3 was dropped.
- **Step 1 gate:** positives kept ≥ 85% in LOO, and ≥ 95% combined with the lexical rule.

## Step 1 results (LOO on anchors_v2)

| Model | Positives kept | Negatives rejected | Overall |
|---|---|---|---|
| **multilingual-e5-base** | 70/74 (94.6%); **74/74 with the lexical rule** | 28/46 (60.9%) | 81.7% |
| **paraphrase-multilingual-mpnet** | 65/74 (87.8%); about 72–73/74 with the lexical rule | 30/46 (65.2%) | 79.2% |
| bge-m3 | 65/74 (87.8%) | 28/46 (60.9%) | 77.5% |
| charngram (offline baseline) | 59/74 (79.7%) | 26/46 (56.5%) | 70.8% |

The gate is passed by e5 and mpnet.

**e5's remaining misses**, all caught by keywords: «Tracciabilità e sicurezza», «Adatto a una dieta vegana», «Senza ingredienti di origine animale», «Senza fosfati».

**Watch items:**
- e5 margins are compressed (mostly 0.00–0.07), so sweep τ in fine steps, and calibrate τ separately per model.
- «Raccolti a mano» acts as a magnet anchor. In e5 it passes by only +0.003 and pulls the «Brevetto internazionale» / «Marchio registrato» negatives over the line. In mpnet it still fails, and «Coltivati in Puglia» drags «Uova da galline allevate all'aperto» down. Re-check in Step 5.

## Open items and next steps (see the checklist for detail)

### Step 0: housekeeping (done, see the checklist for results)
- «Senza parabeni» added (anchor set v3); «Latte Alto Adige» skipped. LOO positives kept unchanged.
- Pass 2 `out_of_scope` line mirrors all 11 negative categories; `Aroma naturale` added as a 5th static few-shot.
- Prompt doc open questions resolved; Pass 1 kept as baseline.
- Keyword list lives in `retriever/ecgt_retriever.yaml` (`lexical.include`), not `extraction.py`. `retriever/lexical_coverage.py` replaces `check_prefilter_coverage.py`: e5 + keywords miss 0/74 positives, mpnet + keywords 1/74 («Raccolti a mano»).
- Still open: pin model `revision`s in the config.

### Step 2: gold span set (done 2026-10-03, see the checklist)
- Frozen as `eval/gold_spans_v1.jsonl` (777 spans, 288 IN_SCOPE/NV). Reserve set = dev set. Gold keyword recall measured once: 89.6%.
- Next: Step 3 segmentation. Carrefour folds the packaging-disposal block (Largamente riciclabile, PET 1, Raccolta…, Verifica…) into `description`, so PRE needs a disposal-line pattern, not just `drop_fields: [recycling]`; the gold README lists which lines count.

### Step 3: segmentation module (done 2026-10-03, see the checklist)
- `retriever/segment.py` → `segment_record(record, cfg)` returns `Span`s (verbatim `text` with footnote join, `source_field`, `kind`, `clauses`, `also_in`). Tests: `python3 -m pytest tests/`. Coverage: `retriever/segment_coverage.py`.
- Reserve 267/267 labelled claims reproduced; gold 287/288 measured once (fixed since).

### Step 4: candidate scoring (done 2026-10-03, see the checklist)
- `retriever/score.py`: `Retriever(cfg).score_record(record)` → every span with margin, lexical hits, candidate flag and top-3 positive anchors. τ is null until Step 5.
- Reserve preview (e5): lexical only 259/267 at 4.4 candidates/record; τ=0.02 → 264/267 at 6.1/record.

### Step 5: τ calibration (done 2026-10-03, see the checklist)
- Chosen on the reserve: e5 + top3_mean, τ = 0.0125 (rule: largest τ with recall ≥ 99%). Gold once: 281/288 = 97.6% at 12.7 candidates/record; keywords alone 94.1%.

### Step 6: Pass 2 with dynamic few-shot ← suggested next task
Keep the 4 static examples and append the top-3 retrieved anchors as `CLAIM → triggers` examples. Check that the prompt still fits `num_ctx` ≈ 3k using `--limit 2-3`.

### Step 7: end-to-end comparison on the gold set
- Compare: A) original two-pass, B) retriever + static few-shot, C) retriever + dynamic few-shot.
- Metrics: claim precision and recall, label accuracy, trigger-set exact match, runtime per record.

### Later
- Swap synthetic anchors for real ones, keeping `origin` accurate.
- Once there are a few hundred labeled spans, train LogReg or SetFit on the embeddings as the candidate classifier.
- Add Codice del Consumo article mapping (Art. 21/22/23) if outputs must be citable in Italy.
- Re-embed and rerun Steps 1 and 5 whenever the model or the anchors change.

## How to rerun the LOO check

```
pip install sentence-transformers
python3 retriever/loo_check.py --anchors retriever/knowledge/anchors_v4.jsonl --csv retriever/loo_results_v4.csv \
  --models charngram intfloat/multilingual-e5-base \
           sentence-transformers/paraphrase-multilingual-mpnet-base-v2
```

`charngram` is an offline hashed character-n-gram baseline and needs no download. The script prints positives kept, negatives rejected, polarity and category accuracy, the failures, the closest pos/neg pairs, and per-category accuracy.
