#!/usr/bin/env python3
"""
Compare a set of product-ad embeddings (queries) against the combined
ECGT + UCPD legal-passage embeddings, and report the top-k most relevant
legal passages for each ad.

This is the retrieval step ONLY -- it tells you which legal text is most
SEMANTICALLY RELEVANT to a given ad/listing. It does NOT tell you whether
the ad complies with that law. For an actual compliance verdict, feed the
top-k matches into an NLI model or an LLM prompt like:

  "Legal text: {legal_chunk}
   Commercial text: {ad_chunk}
   Does the commercial text comply with this legal text? Explain briefly."

Reads ecgt.npy/ecgt.metadata.json and ucpd.npy/ucpd.metadata.json (passages)
from ./embeddings/, and <queries>/embeddings.npy + metadata.json (queries)
from ./embeddings/<queries>/ -- the latter produced by running
prepare_ads_chunks.py then embed_e5.py --mode query --output-dir
./embeddings/<queries>/ over a data/raw/<file>.json.

Usage:
  python compare_e5.py --queries 06.25
  python compare_e5.py --queries 06.25 --top-k 5 --output matches.json
"""

import argparse
import json
from pathlib import Path

import numpy as np

EMBEDDINGS_DIR = Path(__file__).parent / "embeddings"


def load_passage_set(name: str):
    """Legal passages, stored flat as <name>.npy / <name>.metadata.json."""
    npy_path = EMBEDDINGS_DIR / f"{name}.npy"
    json_path = EMBEDDINGS_DIR / f"{name}.metadata.json"

    if not npy_path.exists() or not json_path.exists():
        raise FileNotFoundError(f"Expected {name}.npy and {name}.metadata.json in {EMBEDDINGS_DIR}")

    embeddings = np.load(npy_path)
    with open(json_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    return embeddings, metadata


def load_query_set(name: str):
    """Ad embeddings, stored in a subdir as embeddings.npy / metadata.json --
    embed_e5.py's default --output-dir layout."""
    dir_path = EMBEDDINGS_DIR / name
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
    parser.add_argument("--queries", required=True, help="Name of the query embedding set under ./embeddings/, e.g. '06.25'")
    parser.add_argument("--top-k", type=int, default=3, help="Number of top matching legal chunks to return per ad")
    parser.add_argument("--output", type=Path, default=EMBEDDINGS_DIR / "matches.json", help="Path to write matches.json")
    args = parser.parse_args()

    query_emb, query_meta = load_query_set(args.queries)
    ecgt_emb, ecgt_meta = load_passage_set("ecgt")
    ucpd_emb, ucpd_meta = load_passage_set("ucpd")

    if query_meta["mode"] != "query":
        print(f"Warning: '{args.queries}' embeddings were embedded with mode='{query_meta['mode']}', expected 'query'")
    for name, meta in (("ecgt", ecgt_meta), ("ucpd", ucpd_meta)):
        if meta["mode"] != "passage":
            print(f"Warning: {name} embeddings were embedded with mode='{meta['mode']}', expected 'passage'")

    if not (query_emb.shape[1] == ecgt_emb.shape[1] == ucpd_emb.shape[1]):
        raise ValueError(
            f"Dimension mismatch: queries dim {query_emb.shape[1]}, ecgt dim "
            f"{ecgt_emb.shape[1]}, ucpd dim {ucpd_emb.shape[1]}. Did you use the "
            f"same model for all three?"
        )

    # Passages from both directives are searched together as one corpus; the
    # id prefix on each chunk (ECGT_.../UCPD_...) already says which directive
    # it came from, but "directive" is added explicitly too so results don't
    # depend on that naming convention holding forever.
    passage_emb = np.concatenate([ecgt_emb, ucpd_emb], axis=0)
    passage_chunks = (
        [{**c, "directive": "ecgt"} for c in ecgt_meta["chunks"]]
        + [{**c, "directive": "ucpd"} for c in ucpd_meta["chunks"]]
    )

    print(f"Comparing {query_emb.shape[0]} '{args.queries}' ads against {passage_emb.shape[0]} legal chunks (ecgt + ucpd) ...")

    # All sets are L2-normalized (done in embed_e5.py), so dot product == cosine similarity
    similarity = query_emb @ passage_emb.T  # shape: (n_queries, n_passages)

    results = []
    for i, q_chunk in enumerate(query_meta["chunks"]):
        scores = similarity[i]
        top_indices = np.argsort(scores)[::-1][: args.top_k]

        matches = [
            {
                "legal_chunk_id": passage_chunks[j]["id"],
                "legal_directive": passage_chunks[j]["directive"],
                "legal_title": passage_chunks[j]["title"],
                "legal_source": passage_chunks[j]["source"],
                "legal_text": passage_chunks[j]["text"],
                "similarity": float(scores[j]),
            }
            for j in top_indices
        ]

        results.append(
            {
                "query_chunk_id": q_chunk["id"],
                "query_title": q_chunk["title"],
                "query_source": q_chunk.get("source"),
                "query_text": q_chunk["text"],
                "top_matches": matches,
            }
        )

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(results)} comparison results -> {args.output}")


if __name__ == "__main__":
    main()
