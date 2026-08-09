# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Extracts consumer-law-relevant claims from Italian grocery product descriptions
(scraped from e-commerce listings) and categorizes them. Originally scoped to
greenwashing/environmental claims only (ECGT, Directive 2024/825), but
`src/extraction.py` has since been broadened to the full EU Unfair Commercial
Practices Directive (UCPD, Dir. 2005/29/EC) scope — nutrition/health, origin,
composition, price/value, and safety-instruction claims, not just
environmental ones. `README.md` still describes the narrower
greenwashing-only design (categories in `src/categorize.py`); treat
`src/extraction.py`'s module docstring as the current source of truth on
scope, since it postdates the README.

## Commands

Extraction requires an Ollama server running (`OLLAMA_URL` in
`src/extraction.py` is currently pointed at `http://localhost:4639` — the
port a remote GPU server this project also runs on uses, not Ollama's
`11434` default; change it back if running against a local install):

```bash
python3 -m src.extraction --file 06.25.json --model llama3.2 --out results/baseline/predictions.json
```

`--file` is a filename inside `data/raw/`, not a path. Records with an empty
`description` are skipped by `src/data.py`. Failed records are written
alongside `--out` as `failed.json` in the same directory. Other flags:
`--matches <compare_e5.py output>` injects a per-product top-7 retrieved
legal-chunk grounding block; `--full-grounding` attaches the entire 56-chunk
legal corpus instead (measured to hurt category accuracy on both llama3.2:3b
and llama3.3:70b — see `src/extraction.py`'s module status below, not
recommended); `--temperature`/`--no-schema-grammar` are A/B levers, not
defaults to change; `--num-predict`/`--num-ctx` override the computed
token budgets entirely (needed for any model with a variable-length
preamble before its JSON answer, e.g. a reasoning model like deepseek-r1 —
none of the existing tiers were sized for that); `--limit N` processes only
the first N records, for cheaply measuring a new model's real token cost
before committing to a full run.

`src/evaluate.py` is implemented (see Architecture below for what it scores
and how). `src/pipeline.py` is not yet implemented (empty file).

No test suite exists in this repo yet.

The `src/knowledge/` retrieval+rerank pipeline (also Ollama-backed, plus a
local `sentence-transformers` E5 model — CPU-only runs can take minutes per
embedding pass and ~2-3 min/ad for reranking) is run as a chain of standalone
scripts from within `src/knowledge/`, in this order:

```bash
python3 prepare_ads_chunks.py --file 06.25.json --out ads_chunks.json     # data/raw/<file> -> per-sentence chunks
python3 embed_e5.py --input ads_chunks.json --output-dir ./embeddings/06.25 --mode query   # legal corpus is embedded once as ecgt.npy/ucpd.npy (--mode passage)
python3 compare_e5.py --queries 06.25 --top-k 56 --output embeddings/matches.json          # 56 = full ecgt+ucpd corpus size; rerank needs every candidate, not just top-3
python3 rerank_matches.py --matches embeddings/matches.json --out embeddings/reranked.json --model llama3.1:8b
python3 evaluate_matches.py --rerank embeddings/reranked.json --gold 25.06/gold.json
```

`evaluate_matches.py`'s default gold file (`25.06/gold.json`, 28 Conad
cheese ads, ECGT-only) is small and single-category — good enough to
diagnose systematic bugs in the pipeline itself, not enough to certify
label quality at scale. `golden/golden_set_coop_ucpd_250.json`
(250 Coop products across 9 categories, full UCPD scope) is a much larger,
more diverse candidate for that job, but nothing currently reads it —
see Data layout below.

## Architecture

Four experimental conditions (baseline / rag_only / distilled_only /
rag_distilled) are defined by yaml files in `configs/`, crossing "uses RAG
retrieval over the directive text" with "uses a distilled/fine-tuned model."
**Nothing currently reads these configs** — `src/pipeline.py`, which per
`README.md` is meant to wire extraction → retrieval → categorize per config,
is an empty file (0 lines). The only runnable path today is calling
`src/extraction.py` directly with `--model`.

Module status:

- `src/data.py` — implemented. Loads `data/raw/<file>.json` (a JSON array of
  product records), yields `(index, record)` skipping blank descriptions.
- `src/extraction.py` — implemented. Calls an Ollama model with a
  JSON-Schema-constrained prompt (`RESPONSE_SCHEMA`) to pull claim spans +
  UCPD category + risk level out of a product description. Pre-filters the
  description to claim-adjacent sentences via `CLAIM_KEYWORDS` before it
  reaches the model (latency lever, not a correctness filter — falls back to
  the full description on zero keyword hits). Has several hand-tuned
  workarounds worth preserving if you touch this file: `_repair_misplaced_commas`
  fixes a grammar-decoding glitch in Ollama's structured output;
  `_validate_claims` drops empty-`claim_text` rows and `risk_level=LOW` rows
  as a deterministic backstop to a soft prompt instruction; `num_predict`/
  `num_ctx` values are sized from measured per-claim token cost, not guesses
  — see the inline comments before changing them (overridable per-call via
  `--num-predict`/`--num-ctx` for models these tiers weren't measured
  against). Also supports two legal-grounding modes: `--matches` injects a
  per-product top-7 embedding-retrieved shortlist (retrieval measured
  unreliable: Hit@7 ~37%/~16%); `--full-grounding` instead attaches the
  entire 56-chunk ecgt+ucpd corpus every time (`_load_full_legal_corpus`,
  `num_ctx=15000`/`num_predict=5000`). Full-grounding was tested against the
  20-product `golden/samples/canonical/sample_coop.json` sample on both
  llama3.2:3b and llama3.3:70b and **measured to hurt category accuracy on
  both** (3b: 0.65→0.00 category-accuracy collapse on matched claims; 70b:
  0.65→0.41, plus 2.6x slower) — the small legal corpus doesn't sharpen
  categorization, it dilutes it. Not recommended without a different
  retrieval mechanism. Full-grounding also triggered a **degenerate
  repetition loop** on llama3.2:3b (the model got stuck emitting one claim
  object verbatim for 19KB straight) — fixed via `repeat_penalty=1.3`/
  `repeat_last_n=512`, applied automatically whenever `full_grounding=True`.
  `_split_claim_sentences`
  (shared with `src/knowledge/prepare_ads_chunks.py`) also inserts boundaries
  before known product-spec-sheet field labels (`_LABEL_BOUNDARY` —
  "Denominazione di vendita", "Ingredienti e valori nutrizionali", etc.) so
  they isolate into their own fragment instead of fusing with whatever
  precedes them (the scraped source has no punctuation between fields), and
  drops fragments that are purely a mandatory disclosure
  (`_MANDATORY_DISCLOSURE_PATTERNS` — packaging bin-sorting badges, the
  "`<Brand>` per l'ambiente" header (generalized from a Conad-only regex —
  see below), "verifica le regole del tuo comune" boilerplate) even though
  they superficially match `CLAIM_KEYWORDS` — these are legally mandatory
  labeling, never a voluntary claim.

  A Phase 0 pass (triggered by `.claude/reccomendations/`'s external review,
  which named these B1/B2/B3) fixed three structural bugs here, measured
  with `src/check_prefilter_coverage.py` and the fixed `src/evaluate.py`
  (see `model_comparison_report.md` §8 for full numbers): **(B2, by far the
  largest effect)** `CLAIM_KEYWORDS` had zero coverage for whole gap
  categories — dermatological/clinical proof language, tradition/
  authenticity framing, endorsement/testimonial phrasing, superiority-
  ranking language, personal-care/cosmetic vocabulary — costing 45% of all
  gold claims on the 20-product sample before the fix (49%→93.9% survival
  after, 0 remaining prefilter-caused misses on the sample; 62.6%→77.2% on
  the full 250-set). `_MANDATORY_DISCLOSURE_PATTERNS`' "per l'ambiente"
  entry was also generalized from Conad-only to any brand prefix (real gap
  confirmed against Coop's `recycling_other` data, but currently inert
  there since `src/adapters/coop.py` doesn't join that field in). **(B1)**
  the prompt's "nutrition_content_claim always stays LOW" exception was
  removed — measured to have zero effect on any current score (100% of
  gold's own `nutrition_content_claim` claims are themselves LOW, already
  excluded from scoring), but it was still a real correctness bug: a
  genuinely risky nutrition claim would have been forced to LOW and
  silently dropped regardless of the model's own judgment. **(B3)** added
  an opt-in `--rationale-first` flag (`RESPONSE_SCHEMA_RATIONALE_FIRST` +
  `_reorder_rationale_first`) that emits `risk_rationale` before
  `risk_level` in both the schema and the prompt's worked example, instead
  of the default label-then-rationale order — Ollama honours JSON-Schema
  property order for grammar-constrained decoding, so the default order
  means the model commits to a label before ever writing the rationale
  meant to justify it. Off by default; effect size unmeasured pending a
  live A2 run (needs the `demmgpu1` Ollama endpoint). Also added
  `--no-prefilter` (bypasses `_prefilter_description` entirely) for the
  matching A0 ablation.
- `src/dissected_extraction.py` — implemented, same output shape as
  `extraction.py`'s `extract_from_file` (drop-in comparable). Built to fix a
  hypothesis that llama3.3:70b/llama3.1:70b collapse to ~1-2 claims/product
  regardless of gold's real count, by never asking the model an open-ended
  "list every claim" question: it segments the description into clauses in
  plain Python first, then forces a classification call whose response
  schema has `minItems == maxItems == clause count` (so the model
  structurally cannot submit fewer classifications than clauses), then a
  separate risk-level call over only the clauses flagged as real claims.
  **The motivating hypothesis didn't hold up** — retested after the
  `src/adapters/coop.py` fix below, plain llama3.3:70b's claim count (52)
  was already in line with gold (49); the "collapse" was confounded by that
  bug, not a real model limitation. On the 20-product sample, this pipeline
  measures worse than plain `extraction.py` on precision/recall/F1/category
  accuracy for both llama3.2:3b and llama3.3:70b, and llama3.3:70b through
  this pipeline is ~11x slower per product (162s vs 14s) for a narrower win
  (roughly half the false positives on the zero-claim/`hard_no` subset
  only). Not currently worth its cost; kept as a still-useful fallback if
  the plain pipeline's false-positive rate on `hard_no` products becomes the
  binding constraint. The same Phase 0 pass applied the B1 (nutrition
  exception removed) and B3 (`risk_rationale` before `risk_level`) fixes to
  `RISK_SYSTEM_PROMPT`/`RISK_SCHEMA_ITEM_PROPERTIES` here too, directly
  (not behind a flag) since this pipeline isn't the one being benchmarked.
- `src/adapters/` — implemented. `build.py` turns one retailer's golden set
  into the two canonical outputs `evaluate.py`/`extraction.py` need
  (`--gold-out` for canonical gold, `--extraction-out` for
  `data/raw/<name>.json`, both gitignored — regenerate per-machine after
  pulling adapter changes). Per-retailer adapters (`coop.py`, `carrefour.py`,
  `eurospin.py`, `naturasi.py`) each implement `to_extraction_input`/
  `to_canonical_gold`. `coop.py`'s `to_extraction_input` had a real bug, now
  fixed: it only joined `description`+`features`, silently dropping
  `producer_info` entirely — 178/250 Coop products (71%) had real marketing
  content (heritage/superiority/environmental claims) that lived *only* in
  `producer_info`, plus 22 products were skipped outright because their
  synthesized description was blank. Every model-comparison result from
  before this fix should be treated as run on incomplete input. Known
  remaining gap, deliberately not fixed: ~28% of gold claims still aren't
  found verbatim in description+features+producer_info (many trace to
  `certifications`/`recycling_other`, which also carry mandatory-disclosure
  boilerplate `extraction.py` deliberately filters elsewhere — a blind join
  risks reintroducing that noise).
- `golden/samples/canonical/sample_coop.json` (paired with
  `data/raw/sample_coop_extraction_input.json` via `src/adapters/build.py`)
  — a 20-product stratified sample (6 hard_yes/8 in_between/6 hard_no,
  `random.seed(42)`) of the 250-product Coop golden set, for fast
  model-comparison iteration instead of the full set. Current best result on
  it: plain, ungrounded llama3.3:70b (relaxed span-match F1 0.40, category
  accuracy 0.65) — beats every grounded/dissected variant tried so far.
- `src/retrieval.py` and `src/categorize.py` — stubs (`raise NotImplementedError`).
  Intended to embed the directive text with `sentence-transformers` and do
  flat numpy cosine similarity, then categorize each claim optionally grounded
  by retrieved passages.
- `src/evaluate.py` — implemented. Pairs `extraction.py` predictions against
  a canonical gold file (`golden/canonical/<retailer>.json`-shaped, built by
  `src/adapters/build.py --gold-out`; `golden/samples/canonical/
  sample_coop.json` is one) by `ean`, and reports three separate scores:
  `extraction_prf` (relaxed token-overlap span match, restricted to gold
  claims with `risk_level != "LOW"` — gold's LOW claims are excluded from
  scoring by design, since `extraction.py`'s own LOW-drop policy means they
  can never appear in predictions either); `category_accuracy` (direct
  string equality between predicted and gold `category`, restricted to
  matched claims — gold and `extraction.py`'s `CLAIM_CATEGORIES` are the
  same 11-value taxonomy, so this needs no coarsening); `risk_level_
  agreement` (HIGH-vs-MEDIUM agreement on matched claims, bonus metric).
  Was, until a Phase 0 pass, comparing predicted categories against a
  `GOLD_TO_COARSE`-mapped 6-category scheme that `extraction.py` stopped
  emitting once it was broadened to output gold's exact 11 categories
  directly — silently producing near-zero `category_accuracy` regardless of
  actual model quality (measured: 0.0 before the fix, 0.75 after, on the
  same predictions file). Fixed by comparing category strings directly and
  deleting `GOLD_TO_COARSE`. See `model_comparison_report.md` §8 for the
  full writeup and for `src/check_prefilter_coverage.py`, a companion
  reusable script (not part of `evaluate.py` itself) that measures how many
  gold claims survive `_prefilter_description` before ever reaching the
  model — run it after any `CLAIM_KEYWORDS` change.
- `src/pipeline.py` — empty; not yet started.

`src/knowledge/` is a **separate, already-working retrieval+rerank pipeline**
that predates/parallels the stubbed `src/retrieval.py`, using a different
model (E5, not MiniLM) and a CLI/offline-script style rather than an
importable API:

- `chunker.py` — standalone script (not parameterized, run from within
  `src/knowledge/`) that parses a local `UCPD.html` with BeautifulSoup into
  per-article/per-annex-item JSON chunks. `src/knowledge/chunks/ecgt.json`
  and `ucpd.json` are the pre-built outputs for the two directives.
  `bs4` is imported here but is **not** in `requirements.txt`.
- `prepare_ads_chunks.py` — turns `data/raw/<file>.json` product records into
  the chunk schema `embed_e5.py` expects, one chunk per claim-adjacent
  sentence (via `src/extraction.py`'s `_split_claim_sentences`, reused rather
  than duplicated). Splitting instead of concatenating a whole description
  into one chunk matters here: concatenation drowns a short embedding vector
  in boilerplate (nutrition tables, allergen warnings) that's nearly
  identical across unrelated products.
- `embed_e5.py` — embeds chunk JSON with a multilingual E5 model
  (`intfloat/multilingual-e5-large` by default) into `.npy` + metadata JSON.
  E5 needs a `"query: "` / `"passage: "` prefix per input — legal chunks are
  always embedded in `passage` mode, commercial/ad text in `query` mode.
- `compare_e5.py` — loads two `embed_e5.py` output dirs (queries vs. passages)
  and does the cosine-similarity top-k lookup, dumping matches to JSON. This
  is retrieval only — it does not itself judge compliance. Retrieval alone
  has measured 0/8 top-1 accuracy against the gold set even after a chunking
  fix, so `rerank_matches.py` below is run against the _full_ ecgt+ucpd
  corpus as candidates (`--top-k 56`), not a cheap top-3/15 shortlist.
- `rerank_matches.py` — an Ollama model reads each ad's claim-relevant text
  next to `compare_e5.py`'s retrieved candidates and returns a MATCH/NO_MATCH
  verdict + legal_chunk_id. **Its system prompt is currently scoped to ECGT
  environmental claims only** ("asserzione ambientale" recognition,
  worked examples all environmental) — even though the legal corpus it
  retrieves against (ecgt+ucpd combined) and the newer
  `golden/golden_set_coop_ucpd_250.json` gold set both span the
  _full_ UCPD taxonomy (nutrition/health, origin/authenticity, price/value,
  comparison, endorsement claims, not just environmental). Broadening this
  prompt beyond environmental claims — and adding non-environmental
  candidates' worked examples — is unstarted work, not a bug; don't assume
  it already covers UCPD scope just because the corpus and candidates do.
  Two hand-tuned fixes worth preserving if you touch this file: the response
  schema requires `is_environmental_claim: bool` between `rationale` and
  `verdict` (a smaller local model was measured answering "is this a claim"
  and jumping straight to MATCH without ever separately checking "is it
  _environmental_" — the dedicated field forces that check); and
  `_apply_environmental_backstop` deterministically overrides
  `verdict=MATCH` to `NO_MATCH` whenever `is_environmental_claim=false`
  anyway, same "soft prompt + hard backstop" pattern as `extraction.py`'s
  `_validate_claims`.
- `evaluate_matches.py` — scores `compare_e5.py`'s raw retrieval or
  `rerank_matches.py`'s verdicts against a hand-labeled gold file (default
  `25.06/gold.json`). Also fixed recently: `src/extraction.py`'s
  `_split_claim_sentences` (shared by `prepare_ads_chunks.py`) used to fuse
  mandatory packaging-disposal badges ("Raccolta Plastica/Carta") and
  DOP/IGP mentions into one giant fragment with ~200 words of unrelated
  spec-sheet text, which was the single biggest driver of false positives
  measured here. `_LABEL_BOUNDARY` and `_MANDATORY_DISCLOSURE_PATTERNS` in
  `extraction.py` fix this — see that module's own notes below.

If you pick up RAG work, decide explicitly whether to finish `src/retrieval.py`
against this repo's importable-module pattern or standardize on the
`src/knowledge/` E5 CLI scripts — right now both exist and neither is wired
into `src/pipeline.py`.

## Data layout

- `data/raw/` — scraped product records, JSON array per file (not JSONL despite
  the README's mention of "jsonl"). Several near-duplicate snapshots exist
  (`06.25.json`, `06.25-merged.json`, `06.25-m-sm.json`, `06.25-merged copy.json`);
  check which one a config or script actually points at before assuming they're
  interchangeable.
- `data/annotations/` — exists but is currently empty; nothing writes here.
  The single-label-vs-multi-label decision flagged in `src/categorize.py`'s
  docstring is still unresolved. Gold labels do exist now, just not here —
  see `golden/` below and `src/knowledge/25.06/gold.json`.
- `golden/golden_set_coop_ucpd_250.json` — 250 Coop products across
  9 categories (cura-persona, colazione-dolci-e-snack-salati, gastronomia,
  pane-pasta-riso-e-farine, acqua-e-bevande, latte-yogurt-e-uova,
  parafarmacia, prima-infanzia, condimenti-conserve-e-scatolame), labeled
  across the full UCPD taxonomy per `golden/golden_set_coop_ucpd_250_README.md`
  — not just environmental claims, but also misleading health/efficacy,
  fake/unverified labels, unfair comparisons, authenticity/origin,
  superiority/absolute, and endorsement claims. Bucketed `hard_yes` (77,
  at least one HIGH-confidence signal or 2+ distinct claims) / `hard_no`
  (77: `no_claim_content` 61, `dietary_lifestyle_only` 9,
  `legit_certification_only` 7) / `in_between` (96, one ambiguous or
  partially-substantiated claim). **`golden_bucket` and `extracted_claims`
  are direct manual, claim-by-claim reads — not regex output** (an initial
  regex/heuristic pass got the bucket wrong on 1 in 5 of the first 200
  products, almost all missed health/efficacy and authenticity claims the
  pattern list didn't cover; that original regex pass is kept alongside
  the manual one as `heuristic_bucket`/`matched_signals`, for comparison
  only — don't use those two fields as ground truth, use `golden_bucket`/
  `extracted_claims`). Single-pass human-equivalent review, no second
  reviewer — see the README's "Judgment calls worth knowing about" for
  what's still unresolved (e.g. hyperbole vs. actionable-claim boundary).
  Meat, fish, and frozen-food Coop categories aren't represented (source
  files were unavailable/overwritten at build time — see README). The
  README also references a `golden_set_coop_ucpd_50_additional_hard_no.json`
  as the 50 newest hard_no additions split out separately; only the
  combined 250-file is actually present on disk. Nothing in this repo
  reads this file yet; `evaluate_matches.py --gold` still defaults to the
  much smaller, ECGT-only `25.06/gold.json`.
- `results/<condition>/` — predictions + failed-record dumps per run. Multiple
  numbered `predictions*.json` files under `results/baseline/` are from
  separate manual runs (not a versioning convention to follow).
- `models/` — gitignored; fine-tuned adapters for the distilled conditions
  are expected here but not checked in.
