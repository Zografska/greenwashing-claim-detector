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

Extraction requires a local Ollama server running (`OLLAMA_URL` in
`src/extraction.py` points at `http://localhost:11434`):

```bash
python -m src.extraction --file 06.25.json --model llama3.2 --out results/baseline/predictions.json
```

`--file` is a filename inside `data/raw/`, not a path. Records with an empty
`description` are skipped by `src/data.py`. Failed records are written
alongside `--out` as `failed.json` in the same directory.

Evaluation and pipeline wiring (`src/evaluate.py`, `src/pipeline.py`) are not
yet implemented — see Architecture below.

No test suite exists in this repo yet.

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
- `src/extraction.py` — implemented. Calls a local Ollama model with a
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
  — see the inline comments before changing them.
- `src/retrieval.py` and `src/categorize.py` — stubs (`raise NotImplementedError`).
  Intended to embed the directive text with `sentence-transformers` and do
  flat numpy cosine similarity, then categorize each claim optionally grounded
  by retrieved passages.
- `src/evaluate.py` — stub. Two scores kept deliberately separate: extraction
  P/R/F1 (relaxed span overlap, not exact match) and category accuracy
  (restricted to claims correctly extracted).
- `src/pipeline.py` — empty; not yet started.

`src/knowledge/` is a **separate, already-working retrieval pipeline** that
predates/parallels the stubbed `src/retrieval.py`, using a different model
(E5, not MiniLM) and a CLI/offline-script style rather than an importable
API:
- `chunker.py` — standalone script (not parameterized, run from within
  `src/knowledge/`) that parses a local `UCPD.html` with BeautifulSoup into
  per-article/per-annex-item JSON chunks. `src/knowledge/chunks/ecgt.json`
  and `ucpd.json` are the pre-built outputs for the two directives.
  `bs4` is imported here but is **not** in `requirements.txt`.
- `embed_e5.py` — embeds chunk JSON with a multilingual E5 model
  (`intfloat/multilingual-e5-large` by default) into `.npy` + metadata JSON.
  E5 needs a `"query: "` / `"passage: "` prefix per input — legal chunks are
  always embedded in `passage` mode, commercial/ad text in `query` mode.
- `compare_e5.py` — loads two `embed_e5.py` output dirs (queries vs. passages)
  and does the cosine-similarity top-k lookup, dumping matches to JSON. This
  is retrieval only — it does not itself judge compliance; the module
  docstring sketches the follow-up NLI/LLM prompt for that.

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
- `data/annotations/` — exists but is currently empty; gold labels for eval
  have not been created yet, and the single-label-vs-multi-label decision
  flagged in `src/categorize.py`'s docstring needs to be made before they are.
- `results/<condition>/` — predictions + failed-record dumps per run. Multiple
  numbered `predictions*.json` files under `results/baseline/` are from
  separate manual runs (not a versioning convention to follow).
- `models/` — gitignored; fine-tuned adapters for the distilled conditions
  are expected here but not checked in.
