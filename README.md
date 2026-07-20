# Claim Detector — Italian Grocery E-Commerce

Extracts consumer-law-relevant claims from Italian grocery product descriptions
(scraped from e-commerce listings) and categorizes them. **Originally scoped to
greenwashing/environmental claims only** (ECGT, Directive 2024/825) — the table
below and the four-condition framing are what this project started as. It has
since broadened to the full **EU Unfair Commercial Practices Directive** (UCPD,
Dir. 2005/29/EC): nutrition/health, origin, composition, price/value, and
safety-instruction claims, not just environmental ones. See `CLAUDE.md` for the
detailed, current module-by-module status; this file is the higher-level map.

| condition         | RAG | distilled/fine-tuned model |
|--------------------|-----|------------------------------|
| baseline           | no  | no  |
| rag_only           | yes | no  |
| distilled_only     | no  | yes |
| rag_distilled      | yes | yes |

**Nothing wires these four conditions together yet** — `src/pipeline.py` is
still empty. The only runnable path today is calling `src/extraction.py`
directly, or running the standalone `src/knowledge/` script chain (see below).
The end goal driving current work: get a pipeline reliable enough to serve as
a **teacher for a distilled model** — i.e. good enough that its labels can be
trusted as training data, not just spot-checked by eye.

## Layout

```
data/
  raw/            scraped product records, JSON array per file
  annotations/    empty — nothing writes here yet (gold labels live in golden/ instead)
golden/           250 hand-labeled Coop products, full UCPD scope (see below)
src/
  data.py         loads data/raw/<file>.json, skips blank descriptions
  extraction.py   implemented: Ollama + JSON-schema-constrained prompt, full UCPD scope
  retrieval.py    stub — embed directive text, flat cosine similarity
  categorize.py   stub — assign a category to each extracted claim
  pipeline.py     empty — not started
  evaluate.py     stub — extraction P/R/F1 + category accuracy against gold
  knowledge/      separate, already-working retrieval+rerank pipeline (E5 + Ollama),
                  CLI/offline-script style — see "The knowledge/ pipeline" below
configs/          one yaml per condition in the table above (unread by any code)
results/          predictions + failed-record dumps per run
models/           local fine-tuned adapters (gitignored, not in repo)
```

## Running extraction directly

```bash
python -m src.extraction --file 06.25.json --model llama3.2 --out results/baseline/predictions.json
```

Requires a local Ollama server (`http://localhost:11434`). `--file` is a
filename inside `data/raw/`, not a path.

## The `knowledge/` pipeline

A separate retrieval+rerank system: embeds the ECGT/UCPD legal text and ad
copy with a multilingual E5 model, retrieves candidate legal passages per ad,
then has an Ollama model rerank them into a MATCH/NO_MATCH verdict against
a specific legal definition.

```bash
cd src/knowledge
python prepare_ads_chunks.py --file 06.25.json --out ads_chunks.json
python embed_e5.py --input ads_chunks.json --output-dir ./embeddings/06.25 --mode query
python compare_e5.py --queries 06.25 --top-k 56 --output embeddings/matches.json
python rerank_matches.py --matches embeddings/matches.json --out embeddings/reranked.json --model llama3.1:8b
python evaluate_matches.py --rerank embeddings/reranked.json --gold 25.06/gold.json
```

**Important scope gap:** `rerank_matches.py`'s prompt currently only judges
ECGT *environmental* claims, even though the legal corpus and the golden set
below span the full UCPD taxonomy. Broadening it is an open item, not done —
see the checklist.

## The golden set

`golden/golden_set_coop_ucpd_250_combined.json` — 250 Coop products across 9
categories, labeled claim-by-claim by direct manual reading (not regex),
across the full UCPD taxonomy (environmental, health/efficacy, authenticity,
superiority, endorsement, fake certifications). See
`golden/golden_set_coop_ucpd_250_README.md` for the full category taxonomy,
bucket definitions, and known judgment calls. This is the set to validate
`src/extraction.py` against — nothing in the repo reads it yet.

The older `src/knowledge/25.06/gold.json` (28 Conad cheese ads, ECGT-only) is
still useful for catching structural bugs in the retrieval/rerank pipeline
specifically, but is too small and narrow to certify label quality at scale.

## Recent work (this session)

Two structural bugs were found and fixed in the retrieval+rerank pipeline,
diagnosed against the 28-ad gold set:

1. **Mandatory-disclosure fusion bug** (`src/extraction.py`'s
   `_split_claim_sentences`): packaging-disposal badges ("Raccolta Plastica")
   had no closing sentence boundary, so they fused with ~200 words of
   unrelated nutrition/legal boilerplate into one "claim" fragment — the
   single biggest driver of false positives. Fixed with `_LABEL_BOUNDARY`
   (isolates each spec-sheet field) and `_MANDATORY_DISCLOSURE_PATTERNS`
   (drops packaging badges / boilerplate outright).
   **Result: overall rerank accuracy 46.4% → 67.9%, positive recall 87.5% → 100%.**
2. **Reasoning-skip bug** (`src/knowledge/rerank_matches.py`): the model would
   confirm "this is a real claim" and jump straight to MATCH without ever
   separately checking "is it *environmental*." Fixed by adding a required
   `is_environmental_claim: bool` field to the response schema plus a
   deterministic backstop that forces `NO_MATCH` if the model contradicts
   itself. Validated on the 3 known-failing ads; full 28-ad re-measurement
   is still pending (see checklist).

Also added: the 250-product golden set above, and a repo cleanup — removed
~20 superseded experiment files (old `matches_*`/`reranked_*` iterations,
stale predictions dumps) and renamed the current-generation files back to
the canonical names used in the commands above.

## Checklist — next steps & goals

**Validate against the real gold set**
- [ ] Write the `src/evaluate.py` that doesn't exist yet: span-level P/R/F1 +
      category accuracy, scoring `src/extraction.py`'s predictions against
      `golden/golden_set_coop_ucpd_250_combined.json`'s `extracted_claims`
      (needs a category-name mapping between `RESPONSE_SCHEMA` and the
      golden set's taxonomy).
- [ ] Run `src/extraction.py` over the golden set's raw ad text and score it —
      this is the first real measurement of the extractor; everything so far
      was eyeballed.
- [ ] Use the mismatches to find and fix the next systematic bug, same
      diagnose → fix → re-measure loop as the two fixes above.

**Retrieval/rerank pipeline**
- [ ] Re-run the full 28-ad rerank eval with the `is_environmental_claim` fix
      (only validated on 3 ads so far) to get a clean before/after number.
- [ ] Decide whether to broaden `rerank_matches.py`'s prompt to full UCPD
      scope (to match the corpus and golden set), or shelve the
      retrieval+rerank pipeline in favor of `src/extraction.py` alone if it
      already clears the bar on the golden set.
- [ ] If keeping it: decide whether a bigger/hosted model is worth it for
      teacher-label quality now that the two structural bugs are fixed —
      shelved earlier since the rule/schema fixes accounted for most of the
      error.

**Distillation goal**
- [ ] Once `src/extraction.py` (or the rerank pipeline) clears an acceptable
      bar on the golden set, run it over the full unlabeled `data/raw/`
      corpus to generate the actual distillation training set. Keep the
      golden set held out as the scorecard — don't train on it directly.

**Repo hygiene / open decisions**
- [ ] Resolve the single-label-vs-multi-label decision flagged in
      `src/categorize.py`'s docstring before building any annotation schema
      around it.
- [ ] Decide which `data/raw/06.25*.json` variant is actually current —
      `06.25.json` (minimal ean/description/url) and `06.25-merged.json`
      (full scraped schema) aren't duplicates, they're different extracts of
      the same 28 products; `06.25-m-sm.json` is a 10-record subset.
- [ ] Either finish `src/retrieval.py`/`src/pipeline.py` against this repo's
      importable-module pattern, or standardize on the `src/knowledge/` CLI
      scripts — right now both exist and neither is wired together.
