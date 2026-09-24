# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Detects ECGT (Directive 2024/825, amending the UCPD) greenwashing claims in
Italian grocery/personal-care e-commerce product records, using local 3–8B
Ollama models. Each surviving claim gets one of two labels:

- **IN_SCOPE** — problematic as written (vague/undefined green language, an
  offset-based climate-neutral claim, a comparison with no comparator, a
  brand eco-slogan).
- **NEEDS_VERIFICATION (NV)** — specific and checkable (a named certification,
  a stated %, vegan, a concrete farming practice, a defined term).

## Current branch state — read this before assuming any code exists

The `rag` branch was reset to a minimal baseline in commit `f0f1b57`
("clean up everything, start from 0.1"), which deleted the entire previous
`src/` pipeline (`extraction.py`, `data.py`, `pipeline.py`, `evaluate.py`,
`src/knowledge/`, the old `CLAUDE.md`, etc.) and most of `golden/`'s audit
history. **None of that code exists on this branch right now** — `src/`
contains nothing but a stray `.DS_Store`. Don't reference those modules or
run `python3 -m src.extraction`; they aren't there. If you need the old
design for reference, it's recoverable with `git show f0f1b57~1:<path>`, but
treat it as historical, not current.

What the repo actually contains today is: cleaned golden data + the current
prompt design doc (`golden/`), raw scrapes (`server/`, gitignored), two
HTML data viewers (`tools/`), and an **in-flight redesign** of the
extraction pipeline's first stage, checked in at the repo root rather than
under `src/` yet (see below).

Two local venvs, `greenwashing-claims/` and `rag-workshop/`, sit at the repo
root (`pyvenv.cfg` + `bin/`/`lib/`/`include/`) — they're environments, not
source; skip them when searching the codebase.

## The in-flight redesign: retriever replacing LLM Pass 1

**Read `HANDOFF_ECGT_RETRIEVER.md` then `ECGT_RETRIEVER_CHECKLIST.md` first**
— they are the authoritative, up-to-date status (what's decided, what
passed its gate, what's next) for this work. Don't re-derive decisions
that are already settled there.

The design in one line: `golden/ECGT_TWO_PASS_PROMPT.md`'s two-pass LLM
design had Pass 1 (LLM extracts candidate spans) → Pass 2 (LLM assigns
triggers) → POST (Python maps triggers to a label). The redesign replaces
**Pass 1 only** with deterministic segmentation plus an embedding + lexical
candidate retriever; Pass 2 and POST are unchanged:

```
record ─► PRE ─► segment ─► footnote join ─► candidate? (lexical_hit OR margin > τ)
       ─► dedupe / source_field ─► PASS 2 (+ top-3 retrieved anchors as few-shot) ─► POST
```

**Core rule, load-bearing for everything else:** the retriever decides only
*whether* a span is a candidate, never *which label* it gets — that split
depends on specificity (defined term vs. undefined, named comparator vs.
none), which embeddings don't capture. Labels come only from Pass 2's
`triggers` and this POST function:

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

**Error costs are asymmetric and this governs every gate in the checklist:**
a missed positive (false negative) can be lost for good; a leaked negative
only costs one extra Pass 2 call, which then drops it via `out_of_scope`.
So every gate in the checklist is stated in terms of **positives kept /
recall** — negatives rejected is tracked only as a cost metric, never gated.

Files for this work, currently at repo root (not yet moved to the
checklist's suggested destinations — `src/knowledge/anchors/`, `scripts/`,
`docs/` — don't assume those paths exist):

- `anchors_v2.jsonl` — **current** anchor set (120: 74 pos / 46 neg), one
  JSON object per line: `id, text, polarity (pos|neg), category, triggers[],
  label_hint, origin (real|synthetic), form (joined|claim_only)`. Anchors
  must be topic-neutral (no product nouns/brand names in synthetic ones).
  Footnoted anchors are stored pre-joined (`claim ... footnote body`).
- `anchors.jsonl` — previous set (123), kept only for comparison.
- `loo_check.py` — leave-one-out sanity check across embedding models; run
  it to compare/recalibrate whenever the anchor set or model choice changes.
  `loo_results.csv` is its most recent output.
- `ECGT_RETRIEVER_CHECKLIST.md` — step-by-step plan (Steps 0–8) with gates;
  Step 1 (embedding model choice) has passed its gate, Step 3 (segmentation
  module) is the suggested next task as of the last session.
- `HANDOFF_ECGT_RETRIEVER.md` — narrative handoff for this same session;
  has the full Step 1 results table and open decisions.
- `files/` and `files.zip` — a redundant duplicate bundle of the four files
  above, exported from the session that produced them; not a separate
  source of truth.

**Chosen embedding models** (from the Step 1 leave-one-out gate — positives
kept ≥ 85% alone, ≥ 95% combined with the lexical rule): primary
`intfloat/multilingual-e5-base` (use the `query: ` prefix on **both** sides
when embedding), runner-up `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`.
`bge-m3` was tried and dropped (largest model, scored last both times).

### Rerunning the LOO check

```bash
pip install sentence-transformers
python3 loo_check.py --anchors anchors_v2.jsonl --csv loo_results_v2.csv \
  --models charngram intfloat/multilingual-e5-base \
           sentence-transformers/paraphrase-multilingual-mpnet-base-v2
```

`charngram` is an offline hashed character-n-gram baseline needing no
download, used as a floor. The script reports positives kept, negatives
rejected, polarity/category accuracy, per-failure detail, closest pos/neg
pairs, and per-category accuracy.

There is no other runnable pipeline entry point on this branch yet, and no
test suite.

## Data layout

- `golden/ECGT_TWO_PASS_PROMPT.md` — the current (v4) two-pass prompt
  design: full system prompts, few-shots, and JSON schemas for Pass 1
  (extraction) and Pass 2 (trigger classification), plus the PRE/MID/POST
  deterministic steps between them. This is the source of truth for prompt
  wording and schemas until they land in code. Its "Open questions" section
  at the bottom is stale — origin, DOP/IGP, and «Senza microplastiche»/
  «Senza siliconi» are already resolved in `ECGT_RETRIEVER_CHECKLIST.md`'s
  decisions log; don't re-litigate them from this file alone.
- `golden/clean/` — cleaned, per-retailer product data:
  - `coop.json`, `carrefour.json`, `eurospin.json`, `naturasi.json` —
    canonical product records (list of objects with `product_id`, `name`,
    `brand`, `description`, `features`, `producer_info`, etc.).
  - `coop_claims.json` / `coop_claims.jsonl` — actual Pass 2 LLM run output
    for Coop: per product, `claims[]` with `claim_text`, `source_field`,
    `label` (IN_SCOPE/NEEDS_VERIFICATION/DISCARD — note this predates the
    v4 "no DISCARD in output" change, so older runs may still carry it),
    `discard_reason`, `verification`, `rationale_it`, `confidence`.
  - `cleaner.py` — generic CLI: recursively keeps only whitelisted fields
    in a JSON document (`--keep field1 field2 ...`), input/output can be
    `-` for stdin/stdout.
- `server/` — raw scraped retailer catalogs, gitignored, layout
  `server/<retailer>/<scrape-date>/<category>.json` (Carrefour, Eurospin,
  NaturaSì), each a JSON array of minimally-processed scrape records (field
  names vary by retailer — Carrefour's are prefixed `C4_`). Also has
  `run_summary.json`/`run_failures.json` per scrape.
- `tools/json_viewer.html`, `tools/jsonl_viewer.html` — standalone,
  build-free HTML viewers; open directly in a browser to eyeball a data
  file.

## Legal/domain reference

`HANDOFF_ECGT_RETRIEVER.md` lists `legal-framework-ecgt-ucpd.md` (UCPD/ECGT
background + mapping to Italy's D.Lgs. 30/2026 / Codice del Consumo) as an
existing, unchanged file — but it is **not actually present anywhere in
this repo or its history**. If checklist Step 8 (citable article mapping)
comes up, that file needs to be tracked down or rewritten, not assumed to
exist.
