# Greenwashing Claim Detector

Extracts environmental/sustainability claims from marketing text, counts them,
and assigns each a greenwashing category. Built to compare four conditions:

| condition         | RAG | distilled/fine-tuned model |
|--------------------|-----|------------------------------|
| baseline           | no  | no  |
| rag_only           | yes | no  |
| distilled_only     | no  | yes |
| rag_distilled      | yes | yes |

## Layout

```
data/
  raw/            scraped product pages, one file or jsonl per source
  annotations/    gold-labeled claim spans + categories for eval
src/
  extraction.py   pulls candidate claim spans out of raw text
  retrieval.py    embeds + indexes the directive text, retrieves relevant passages
  categorize.py   assigns a greenwashing category to each extracted claim
  pipeline.py     wires extraction -> (retrieval) -> categorize per config
  evaluate.py     extraction P/R/F1 and category accuracy against gold
configs/          one yaml per condition above
results/          metrics + predictions dumped per run, one subfolder per condition
models/           local fine-tuned adapters (gitignored, not in repo)
```

## Running a condition

```
python -m src.pipeline --config configs/rag_only.yaml
python -m src.evaluate --predictions results/rag_only/predictions.jsonl --gold data/annotations/test.jsonl
```

## Category taxonomy

Defined in `src/categorize.py`. Currently stubbed with the ECGT blacklist-derived
categories (generic_unsubstantiated, offset_based_neutrality, fake_label,
unfair_comparison, irrelevant_claim). Adjust once the labeling scheme is final
multi-label vs single-label decision still open.
# greenwashing-claim-detector
