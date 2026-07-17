#!/usr/bin/env python3
"""
Compare commercial-text embeddings (queries) against legal-text embeddings
(passages) produced by embed_e5.py, and report the top-k most relevant
legal chunks for each commercial chunk.

This is the retrieval step ONLY -- it tells you which legal text is most
SEMANTICALLY RELEVANT to a given ad/listing. It does NOT tell you whether
the ad complies with that law. For an actual compliance verdict, feed the
top-k matches into an NLI model or an LLM prompt like:

  "Legal text: {legal_chunk}
   Commercial text: {ad_chunk}
   Does the commercial text comply with this legal text? Explain briefly."

Usage:
  python compare_e5.py \
      --queries-dir ./embeddings/ads \
      --passages-dir ./embeddings/legal \
      --top-k 3 \
      --output matches.json
"""

import argparse
import json
from pathlib import Path

import numpy as np


def load_embedding_set(dir_path: Path):
    npy_path = dir_path / "embeddings.npy"
    json_path = dir_path / "metadata.json"

    if not npy_path.exists() or not json_path.exists():
        raise FileNotFoundError(f"Expected embeddings.npy and metadata.json in {dir_path}")

    embeddings = np.load(npy_path)
    with open(json_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    return embeddings, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--queries-dir", required=True, type=Path, help="Output dir from embed_e5.py run with --mode query (commercial text)")
    parser.add_argument("--passages-dir", required=True, type=Path, help="Output dir from embed_e5.py run with --mode passage (legal text)")
    parser.add_argument("--top-k", type=int, default=3, help="Number of top matching legal chunks to return per commercial chunk")
    parser.add_argument("--output", required=True, type=Path, help="Path to write matches.json")
    args = parser.parse_args()

    query_emb, query_meta = load_embedding_set(args.queries_dir)
    passage_emb, passage_meta = load_embedding_set(args.passages_dir)

    if query_meta["mode"] != "query":
        print(f"Warning: --queries-dir was embedded with mode='{query_meta['mode']}', expected 'query'")
    if passage_meta["mode"] != "passage":
        print(f"Warning: --passages-dir was embedded with mode='{passage_meta['mode']}', expected 'passage'")

    if query_emb.shape[1] != passage_emb.shape[1]:
        raise ValueError(
            f"Dimension mismatch: queries have dim {query_emb.shape[1]}, "
            f"passages have dim {passage_emb.shape[1]}. Did you use the same model for both?"
        )

    print(f"Comparing {query_emb.shape[0]} commercial chunks against {passage_emb.shape[0]} legal chunks ...")

    # Both sets are L2-normalized (done in embed_e5.py), so dot product == cosine similarity
    similarity = query_emb @ passage_emb.T  # shape: (n_queries, n_passages)

    results = []
    for i, q_chunk in enumerate(query_meta["chunks"]):
        scores = similarity[i]
        top_indices = np.argsort(scores)[::-1][: args.top_k]

        matches = [
            {
                "legal_chunk_id": passage_meta["chunks"][j]["id"],
                "legal_title": passage_meta["chunks"][j]["title"],
                "legal_source": passage_meta["chunks"][j]["source"],
                "legal_text": passage_meta["chunks"][j]["text"],
                "similarity": float(scores[j]),
            }
            for j in top_indices
        ]

        results.append(
            {
                "commercial_chunk_id": q_chunk["id"],
                "commercial_title": q_chunk["title"],
                "commercial_text": q_chunk["text"],
                "top_matches": matches,
            }
        )

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(results)} comparison results -> {args.output}")


if __name__ == "__main__":
    main()
