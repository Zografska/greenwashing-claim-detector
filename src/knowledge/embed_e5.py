#!/usr/bin/env python3
"""
Embed chunked text with a multilingual E5 model (e.g. intfloat/multilingual-e5-large)
and save results as .npy (vectors) + .json (metadata).

Built for an asymmetric retrieval setup: legal/regulatory chunks as the
searchable corpus ("passage"), commercial text (ads, listings) as the
queries ("query") used to retrieve relevant legal passages.

E5 models REQUIRE a prefix on every input string or quality drops noticeably:
  - "passage: <text>"  for corpus / reference documents (your legal chunks)
  - "query: <text>"    for search inputs (your commercial text)

This script adds the correct prefix based on --mode, so don't pre-add it
to your text field yourself.

Input format (JSON array of objects):
[
  {"id": "...", "title": "...", "source": "...", "text": "..."},
  ...
]

Usage:
  # Embed your legal/regulatory corpus as passages
  python embed_e5.py --input legal_chunks.json --output-dir ./embeddings/legal \
      --mode passage --model intfloat/multilingual-e5-large

  # Embed your commercial/ad text as queries
  python embed_e5.py --input ads_chunks.json --output-dir ./embeddings/ads \
      --mode query --model intfloat/multilingual-e5-large

Then compare with cosine similarity (vectors are L2-normalized already,
so cosine similarity == dot product):
  similarity = ads_embeddings @ legal_embeddings.T

Install deps:
  pip install sentence-transformers torch numpy

Outputs:
  <output-dir>/embeddings.npy   -> float32 array, shape (n_chunks, dim)
  <output-dir>/metadata.json    -> model, mode, dim, count, and chunk list
                                    (each tagged with "row" = index into .npy)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List

import numpy as np


def load_chunks(input_path: Path) -> List[dict]:
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        sys.exit(f"Expected a JSON array of chunk objects, got {type(data).__name__}")

    required = {"id", "title", "source", "text"}
    for i, item in enumerate(data):
        missing = required - item.keys()
        if missing:
            sys.exit(f"Chunk at index {i} is missing fields: {missing}")

    return data


def add_e5_prefix(texts: List[str], mode: str) -> List[str]:
    prefix = "query: " if mode == "query" else "passage: "
    return [prefix + t for t in texts]


def embed(model_name: str, texts: List[str], batch_size: int) -> np.ndarray:
    from sentence_transformers import SentenceTransformer

    print(f"Loading model '{model_name}' ...")
    model = SentenceTransformer(model_name)

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,  # so cosine similarity == dot product later
    )
    return embeddings.astype("float32")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, type=Path, help="Path to chunked JSON file")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory to save embeddings.npy + metadata.json")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["query", "passage"],
        help="Use 'passage' for your legal/regulatory corpus, 'query' for the commercial text you're checking against it",
    )
    parser.add_argument(
        "--model",
        default="intfloat/multilingual-e5-large",
        help="E5 model name. e.g. intfloat/multilingual-e5-large or intfloat/multilingual-e5-base (faster, smaller)",
    )
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    if not args.input.exists():
        sys.exit(f"Input file not found: {args.input}")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading chunks from {args.input} ...")
    chunks = load_chunks(args.input)
    print(f"Loaded {len(chunks)} chunks. Mode: {args.mode}")

    raw_texts = [c["text"] for c in chunks]
    prefixed_texts = add_e5_prefix(raw_texts, args.mode)

    embeddings = embed(args.model, prefixed_texts, args.batch_size)
    print(f"Embeddings shape: {embeddings.shape}, dtype: {embeddings.dtype}")

    npy_path = args.output_dir / "embeddings.npy"
    np.save(npy_path, embeddings)
    print(f"Saved vectors -> {npy_path}")

    # Preserves any extra fields a chunk producer adds (e.g. prepare_ads_chunks.py's
    # "ad_id", used to group sentence-level chunks back up to their ad), not just
    # the required id/title/source/text. "text" here is the original, un-prefixed
    # string -- not what actually got embedded.
    metadata = [{"row": i, **c} for i, c in enumerate(chunks)]

    json_path = args.output_dir / "metadata.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "model": args.model,
                "mode": args.mode,
                "dim": int(embeddings.shape[1]),
                "count": int(embeddings.shape[0]),
                "chunks": metadata,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"Saved metadata -> {json_path}")

    print("Done.")


if __name__ == "__main__":
    main()
