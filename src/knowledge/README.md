# src/knowledge/ — retrieval + rerank pipeline

Standalone scripts, run from within this directory, in the order below. Each
step reads the previous step's output file; nothing here is wired into a
single CLI. See each script's own docstring for design rationale — this file
is just the runbook.

## Setup

```bash
pip install -r ../../requirements.txt
```

**Python 3.6 note:** the scripts in this directory (and the modules they
import from `src/`) are syntax-compatible with Python 3.6 — no walrus
operator, no PEP 585 subscripted generics (`list[int]`), no PEP 604 unions
(`X | None`), all replaced with `typing.List`/`Optional`/etc. That said,
**dependency versions are a separate risk**: recent `torch`,
`sentence-transformers`, and `httpx` releases have dropped 3.6 support
entirely (most now require 3.8+). If `pip install` fails resolving a 3.6
wheel for any of these, that's a version-pinning problem, not a syntax one —
you'll need to pin an older compatible release.

The E5 embedding model (`intfloat/multilingual-e5-large`, ~2.1GB) downloads
on first use and is cached under `~/.cache/huggingface/hub` — one-time cost.
The rerank step needs a local Ollama server with your model already pulled.

## 1. Build canonical gold + extraction input (from the repo root)

Turns one retailer's golden set into (a) canonical gold with per-claim
`gold_legal_chunk_id` (`src/adapters/legal_mapping.py`), and (b) a
`data/raw/`-shaped file with a `description` field, for both
`src.extraction` and this pipeline's chunking step to read.

```bash
python -m src.adapters.build --retailer coop \
    --in golden/golden_set_coop_ucpd_250.json \
    --gold-out golden/canonical/coop.json \
    --extraction-out data/raw/coop_extraction_input.json
```

Repeat `--retailer` for `carrefour` / `eurospin` / `naturasi`. `--extraction-out`
lands under `data/raw/`, which is gitignored — regenerate it on every machine
you run this on. `--gold-out` (`golden/canonical/`) is not gitignored, but
still isn't committed until you `git add` it — check `git status` before
assuming a teammate's machine already has it.

For a quick/cheap first look instead of the full retailer, point `--in` at
`golden/samples/sample_<retailer>.json` (9 products, checked into git) and
name the outputs accordingly (`sample_<retailer>_extraction_input.json`,
etc.) — `golden/samples/canonical/sample_<retailer>.json` is already
pre-built and checked in, so you can skip this step entirely for a sample run.

## 2. Chunk + embed the product text (from `src/knowledge/`)

```bash
python prepare_ads_chunks.py --file coop_extraction_input.json --out /tmp/coop_chunks.json
python embed_e5.py --input /tmp/coop_chunks.json --output-dir ./embeddings/coop --mode query
```

The legal corpus (`ecgt`/`ucpd`) is already embedded and checked in
(`embeddings/{ecgt,ucpd}.npy` + `.metadata.json`) — only the per-retailer
query embeddings need building.

## 3. Retrieve: tuned embedding-only config

`tune_retrieval.py` already grid-searched `compare_e5.py`'s centering/CSLS
knobs against `gold_legal_chunk_id` — winner: `center=True, csls=True,
csls_k=15`. Re-run the grid search yourself with:

```bash
python tune_retrieval.py
```

Or just retrieve directly with the tuned config:

```bash
python compare_e5.py --queries coop --top-k 7 --csls-k 15 --output embeddings/coop_matches.json
```

(`--csls-k 15` is the only non-default flag needed — centering and CSLS are
already on by default.)

## 4a. Score retrieval alone against gold

```bash
python evaluate_claim_matches.py --matches embeddings/coop_matches.json --gold ../../golden/canonical/coop.json
```

Measured pooled Hit@7 across all 4 retailers: ~37% for claims with a real
specific legal chunk (environmental, endorsement, medicinal-cure,
offset-neutrality), ~16% for the generic `UCPD_Art6`/`Art7` catch-all most
other categories map to, ~3% for NaturaSì specifically (its "description" is
synthesized from certification tags, not real prose, and doesn't embed like
real legal prose does). This is *why* `src/extraction.py`'s grounding
(`--matches` flag) treats retrieved chunks as unlabeled candidate context,
never as an asserted fact — see its `SYSTEM_PROMPT`.

## 4b. Compare retrieval-only vs. + LLM rerank (needs Ollama)

```bash
python compare_retrieval_vs_rerank.py --retailer coop --model llama3.2:3b
```

Feeds rerank the SAME top-7 candidates retrieval already produced (fair
comparison — reranking over a bigger candidate pool would confound "does
rerank help" with "does rerank see more"). Reports embedding top-1 (naive
baseline), embedding top-k (oracle ceiling), +rerank ad-level accuracy, and
rerank's wall-clock cost, so the accuracy-vs-resource-cost tradeoff is a
number you can read off, not something to intuit.

**Model choice:** `llama3.2:3b` first — same tier as `src/extraction.py`'s
own model, cheap enough to iterate. A larger model (e.g. `llama3.3:70b`) is
worth a second data point if you want to know whether the 3b model itself is
the bottleneck. Avoid `deepseek-r1` for now — it's a reasoning model whose
`<think>` traces can be long, and `rerank_ad`'s `num_predict=600` is sized
for a verbose *rationale*, not a full chain-of-thought trace; would need a
raised `num_predict` as a deliberate follow-up, not a drop-in swap.

## 5. Run extraction with grounding

```bash
python -m src.extraction --file coop_extraction_input.json --model llama3.2 \
    --matches src/knowledge/embeddings/coop_matches.json --out results/coop/predictions.json
```

Omitting `--matches` runs the exact same prompt/token-budget every prior run
used (grounding is fully additive/optional).

## Standalone rerank (original convention, no comparison)

If you just want `rerank_matches.py`'s output on its own (e.g. to feed
`evaluate_matches.py`'s ad-level scoring against the older `25.06/gold.json`
set), its original convention reranks over the FULL 56-chunk corpus, not the
tuned top-7:

```bash
python compare_e5.py --queries coop --top-k 56 --output embeddings/coop_matches_full.json
python rerank_matches.py --matches embeddings/coop_matches_full.json --model llama3.2:3b --out embeddings/coop_reranked.json
python evaluate_claim_matches.py --rerank embeddings/coop_reranked.json --gold ../../golden/canonical/coop.json
```

Note `rerank_matches.py`'s `SYSTEM_PROMPT` is still scoped to ECGT
environmental claims only (broadening it to full UCPD scope is unstarted,
separate work) — expect it to under-match non-environmental categories
regardless of candidate pool size.
