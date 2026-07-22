#!/usr/bin/env python3
"""
Compare a set of product-ad embeddings (queries) against the combined
ECGT + UCPD legal-passage embeddings, and report the top-k most relevant
legal passages for each ad.

Before scoring, both queries and passages are re-centered against a
centroid -- the mean embedding of a random sample of the legal corpus --
and renormalized. High-dimensional embedding spaces like E5's 1024-dim
suffer from "hubness": a handful of passages end up close to nearly every
query in raw cosine similarity regardless of actual relevance, and
dominate top-k results (e.g. UCPD_Art7 alone took 13/28 top-1 matches
before centering). Subtracting the corpus centroid removes that shared
component before ranking. See --no-center to fall back to raw cosine
similarity for comparison.

Centering removes a *global* bias shared by the whole corpus, but it does
not stop an individual passage from being unusually close to many
different queries at once (per-passage hubness) -- centering alone still
left ECGT_Art1_NuoveDefinizioni_s, UCPD_Art7 and ECGT_AnnexI_4_quater
dominating top-k for ads that share no real content with them. On top of
centering, CSLS (Cross-domain Similarity Local Scaling; Lample et al. 2018,
Dinu et al. 2015) penalizes a passage in proportion to how close it sits to
its k nearest queries on average, and symmetrically for each query's k
nearest passages, before ranking. See --no-csls to fall back to plain
(centered) cosine similarity, and --csls-k to change the neighborhood size.

Even with hub correction, a query with no real claim in it will still get
*some* top-k passages back -- ranking always returns the k best of what's
available. --min-similarity lets you require the *raw* (pre-CSLS) cosine
similarity to clear a floor before a match is reported at all; below it,
top_matches is empty and below_similarity_threshold is set on the result.
No default is set for this because there are no gold-labeled matches yet
(data/annotations/ is empty) to calibrate a floor against -- pick a value
empirically once labels exist.

Queries come in as multiple sentence-level chunks per ad (see
prepare_ads_chunks.py), not one chunk per whole ad -- a chunk's "ad_id"
field says which ad it belongs to (falls back to its own "id" if that field
is absent, so a query set built the old one-chunk-per-ad way still works).
Retrieval itself still runs per sentence-chunk, since that's the unit that
was actually embedded; results are then pooled back up per ad_id, keeping
each passage's single best-scoring sentence match and reporting which
sentence produced it, before taking that ad's top-k. This is what lets one
ad surface matches for more than one distinct claim (e.g. an environmental
line matching an ECGT passage AND a nutrition line matching a different
UCPD passage) instead of collapsing to whichever single sentence scored
highest overall.

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


def center_and_normalize(query_emb: np.ndarray, passage_emb: np.ndarray, sample_size: int, seed: int):
    """Subtract the mean of a random legal-corpus sample from both query and
    passage embeddings, then renormalize to unit length.

    Vectors are unit-norm going in (embed_e5.py L2-normalizes them), which is
    what makes a plain dot product equal cosine similarity. Subtracting a
    non-zero centroid breaks that unit norm, so vectors must be renormalized
    afterward or the dot product below stops meaning cosine similarity.
    """
    n_passages = passage_emb.shape[0]
    sample_size = min(sample_size, n_passages)
    rng = np.random.default_rng(seed)
    sample_idx = rng.choice(n_passages, size=sample_size, replace=False)
    centroid = passage_emb[sample_idx].mean(axis=0)

    def _center_and_unit_norm(emb):
        centered = emb - centroid
        norms = np.linalg.norm(centered, axis=1, keepdims=True)
        return centered / norms

    return _center_and_unit_norm(query_emb), _center_and_unit_norm(passage_emb), sample_size


def csls_correct(sim: np.ndarray, k: int):
    """CSLS (Lample et al. 2018 / Dinu et al. 2015): penalize a passage in
    proportion to its average similarity to its k nearest queries, and
    symmetrically for each query's k nearest passages, before ranking --
    counteracts hubness, where a point sits close to many points on the
    other side regardless of actual relevance. k is clamped per side to the
    number of queries/passages available, so this still works below k.
    """
    n_queries, n_passages = sim.shape
    k_passages = max(1, min(k, n_passages))
    k_queries = max(1, min(k, n_queries))
    r_query = np.partition(sim, -k_passages, axis=1)[:, -k_passages:].mean(axis=1)
    r_passage = np.partition(sim, -k_queries, axis=0)[-k_queries:, :].mean(axis=0)
    return 2 * sim - r_query[:, None] - r_passage[None, :]


def compare(
    query_emb: np.ndarray,
    query_meta: dict,
    ecgt_emb: np.ndarray,
    ecgt_meta: dict,
    ucpd_emb: np.ndarray,
    ucpd_meta: dict,
    *,
    top_k: int = 3,
    center: bool = True,
    csls: bool = True,
    csls_k: int = 10,
    min_similarity: float | None = None,
    centroid_sample_size: int = 56,
    seed: int = 42,
    verbose: bool = True,
) -> list[dict]:
    """Core ranking logic, callable directly (e.g. by tune_retrieval.py's grid
    search) without shelling out to the CLI or round-tripping through JSON
    files per config. `main()` below is a thin argparse wrapper over this."""
    if query_meta["mode"] != "query" and verbose:
        print(f"Warning: query embeddings were embedded with mode='{query_meta['mode']}', expected 'query'")
    for name, meta in (("ecgt", ecgt_meta), ("ucpd", ucpd_meta)):
        if meta["mode"] != "passage" and verbose:
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

    query_chunks = query_meta["chunks"]
    ad_ids = [c.get("ad_id", c["id"]) for c in query_chunks]
    n_ads = len(dict.fromkeys(ad_ids))  # preserves first-seen order, unlike set()

    if verbose:
        print(
            f"Comparing {len(query_chunks)} claim-sentence chunks across {n_ads} ads "
            f"against {passage_emb.shape[0]} legal chunks (ecgt + ucpd) ..."
        )

    if not center:
        # All sets are L2-normalized (done in embed_e5.py), so dot product == cosine similarity
        query_emb_scored, passage_emb_scored = query_emb, passage_emb
    else:
        query_emb_scored, passage_emb_scored, used_sample_size = center_and_normalize(
            query_emb, passage_emb, centroid_sample_size, seed
        )
        if verbose:
            print(f"Centered against a {used_sample_size}-passage random sample (seed={seed}) before scoring")

    similarity = query_emb_scored @ passage_emb_scored.T  # shape: (n_queries, n_passages)

    if not csls:
        ranking_scores = similarity
    else:
        ranking_scores = csls_correct(similarity, csls_k)
        if verbose:
            used_k = max(1, min(csls_k, min(similarity.shape)))
            print(f"Applied CSLS hub correction (k={used_k})")

    # Per-sentence candidate lists first (ranked by CSLS/cosine, floor-filtered),
    # since retrieval runs at the chunk level -- pooling across an ad's sentences
    # happens after, once each sentence already has its own ranked candidates.
    row_candidates = []
    for i in range(len(query_chunks)):
        order = np.argsort(ranking_scores[i])[::-1]
        if min_similarity is not None:
            order = [j for j in order if similarity[i, j] >= min_similarity]
        row_candidates.append(order)

    ad_rows = {}
    for i, ad_id in enumerate(ad_ids):
        ad_rows.setdefault(ad_id, []).append(i)

    results = []
    for ad_id, rows in ad_rows.items():
        # For each passage, keep only its single best-scoring sentence within
        # this ad -- a passage that several sentences weakly match shouldn't
        # occupy multiple of the ad's top-k slots.
        best_per_passage = {}
        for i in rows:
            for j in row_candidates[i]:
                rank_score = ranking_scores[i, j]
                if j not in best_per_passage or rank_score > best_per_passage[j][1]:
                    best_per_passage[j] = (i, rank_score)

        ranked_passages = sorted(best_per_passage.items(), key=lambda kv: kv[1][1], reverse=True)
        top_passages = ranked_passages[:top_k]
        below_threshold = min_similarity is not None and len(best_per_passage) == 0

        matches = [
            {
                "legal_chunk_id": passage_chunks[j]["id"],
                "legal_directive": passage_chunks[j]["directive"],
                "legal_title": passage_chunks[j]["title"],
                "legal_source": passage_chunks[j]["source"],
                "legal_text": passage_chunks[j]["text"],
                "matched_sentence": query_chunks[sent_i]["text"],
                "similarity": float(similarity[sent_i, j]),
                **({} if not csls else {"csls_similarity": float(rank_score)}),
            }
            for j, (sent_i, rank_score) in top_passages
        ]

        first_chunk = query_chunks[rows[0]]
        results.append(
            {
                "query_ad_id": ad_id,
                "query_title": first_chunk["title"],
                "query_source": first_chunk.get("source"),
                "query_sentences": [query_chunks[i]["text"] for i in rows],
                "top_matches": matches,
                "below_similarity_threshold": below_threshold,
            }
        )

    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--queries", required=True, help="Name of the query embedding set under ./embeddings/, e.g. '06.25'")
    parser.add_argument("--top-k", type=int, default=3, help="Number of top matching legal chunks to return per ad")
    parser.add_argument("--output", type=Path, default=EMBEDDINGS_DIR / "matches.json", help="Path to write matches.json")
    parser.add_argument(
        "--centroid-sample-size", type=int, default=56,
        help="Number of legal-corpus passages to randomly sample when computing the centering centroid "
             "(clamped to the corpus size; default covers the full current ecgt+ucpd corpus)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for the centroid sample")
    parser.add_argument("--no-center", action="store_true", help="Disable centroid centering, use raw cosine similarity")
    parser.add_argument(
        "--csls-k", type=int, default=10,
        help="Neighborhood size for CSLS hub correction, clamped to the query/passage-set size "
             "(default fits the current small ecgt+ucpd+ads corpora; raise it if the corpus grows a lot)",
    )
    parser.add_argument(
        "--no-csls", action="store_true",
        help="Disable CSLS hub correction, rank by plain (centered) cosine similarity",
    )
    parser.add_argument(
        "--min-similarity", type=float, default=None,
        help="Minimum raw (pre-CSLS) cosine similarity a match must clear to be reported; below it, "
             "a query's top_matches is left empty and below_similarity_threshold is set true. No default "
             "-- there are no gold-labeled matches yet in data/annotations/ to calibrate one against.",
    )
    args = parser.parse_args()

    query_emb, query_meta = load_query_set(args.queries)
    ecgt_emb, ecgt_meta = load_passage_set("ecgt")
    ucpd_emb, ucpd_meta = load_passage_set("ucpd")

    results = compare(
        query_emb, query_meta, ecgt_emb, ecgt_meta, ucpd_emb, ucpd_meta,
        top_k=args.top_k,
        center=not args.no_center,
        csls=not args.no_csls,
        csls_k=args.csls_k,
        min_similarity=args.min_similarity,
        centroid_sample_size=args.centroid_sample_size,
        seed=args.seed,
    )

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(results)} comparison results -> {args.output}")


if __name__ == "__main__":
    main()
