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
`src/` pipeline (`extraction.py` with its `CLAIM_KEYWORDS` prefilter,
`data.py`, `pipeline.py`, `evaluate.py`, `check_prefilter_coverage.py`,
`src/knowledge/`, …) and most of `golden/`'s audit history. **None of that
code exists on this branch** — `src/` holds only a stray `.DS_Store`. Don't
reference those modules or run `python3 -m src.extraction`. The old design
is recoverable with `git show f0f1b57~1:<path>`; treat it as historical.

What the repo contains today: cleaned golden data + the prompt design doc
(`golden/`), raw scrapes (`server/`, gitignored), two HTML data viewers
(`tools/`), and the **in-flight retriever redesign** in `retriever/`.

## The in-flight redesign: retriever replacing LLM Pass 1

**Read `HANDOFF_ECGT_RETRIEVER.md` then `ECGT_RETRIEVER_CHECKLIST.md` first**
— they are the authoritative status (what's decided, what passed its gate,
what's next). Don't re-derive decisions already settled in the checklist's
decisions log.

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

### Files (`retriever/`)

- `ecgt_retriever.yaml` — pipeline config and **single source of truth**
  for the anchor path, embedding model names/prefixes, PRE/segmentation
  settings, the lexical keyword list (`lexical.include`, word-bounded
  regexes, ECGT-only), τ per model, and Pass 2 settings. Keep tunables here,
  not in code.
- `knowledge/anchors_v3.jsonl` — **current** anchor set (121: 74 pos / 47
  neg). One JSON object per line: `id, text, polarity (pos|neg), category,
  triggers[], label_hint, origin (real|synthetic), form (joined|claim_only)`.
  Synthetic anchors must be topic-neutral (no product nouns/brand names).
  Footnoted anchors are stored pre-joined (`claim ... footnote body`).
  `anchors_v2.jsonl` (120) and `anchors.jsonl` (v1, 123) are kept only for
  comparison.
- `loo_check.py` — leave-one-out check across embedding models; rerun
  whenever the anchors or model choice change. `loo_results_v3.csv` is the
  latest output (`loo_results_v2.csv` is the v2 run, incl. bge-m3).
- `lexical_coverage.py` — runs the config's keyword list over the anchors
  (and optionally a `coop_claims.json`-style file, `--claims`), and with
  `--loo <csv>` lists positives missed by **both** embedding and keywords.

Status: Step 0 (housekeeping) and Step 1 (embedding model choice) are
done; Step 2 (gold span set) / Step 3 (segmentation module) are next.

**Chosen embedding models** (Step 1 gate — positives kept ≥ 85% alone,
≥ 95% with the lexical rule): primary `intfloat/multilingual-e5-base`
(`query: ` prefix on **both** sides), runner-up
`sentence-transformers/paraphrase-multilingual-mpnet-base-v2`. `bge-m3` was
dropped. On v3, e5 + keywords miss 0/74 positives; mpnet + keywords miss 1
(«Raccolti a mano»).

### Commands

```bash
pip install sentence-transformers pyyaml
python3 retriever/loo_check.py --anchors retriever/knowledge/anchors_v3.jsonl \
  --csv retriever/loo_results_v3.csv \
  --models charngram intfloat/multilingual-e5-base \
           sentence-transformers/paraphrase-multilingual-mpnet-base-v2
python3 retriever/lexical_coverage.py --claims golden/clean/coop_claims.json \
  --loo retriever/loo_results_v3.csv
```

`charngram` is an offline hashed character-n-gram baseline (no download),
used as a floor. There is no pipeline entry point or test suite yet.

## Data layout

- `golden/ECGT_TWO_PASS_PROMPT.md` — the current (v4) two-pass prompt
  design: full system prompts, few-shots, and JSON schemas for Pass 1
  (extraction) and Pass 2 (trigger classification), plus the PRE/MID/POST
  deterministic steps between them. This is the source of truth for prompt
  wording and schemas until they land in code. Its Pass 1 section is kept
  only as the Step 7 baseline; its open questions are resolved (see the
  "Resolved questions" section at the bottom).
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

`legal-framework-ecgt-ucpd.md` (UCPD/ECGT background + mapping to Italy's
D.Lgs. 30/2026 / Codice del Consumo) is referenced by the handoff but is
**not in this repo or its history**. If checklist Step 8 (citable article
mapping) comes up, it needs to be tracked down or rewritten.
