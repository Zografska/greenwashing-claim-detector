"""
Embeds and indexes the directive text (articles/recitals), retrieves the
passages most relevant to a given claim. Directive corpus is small, a flat
numpy similarity search is plenty, no need for faiss here.

Confirm which directive this is actually indexing before filling this in:
ECGT / Directive 2024/825 (applies Sept 2026, amends UCPD) is what's
currently in force. The Green Claims Directive proposal is paused, don't
index that one as if it were live law unless you're explicitly comparing
against it.
"""

import numpy as np
from sentence_transformers import SentenceTransformer

EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


def build_index(directive_path: str, model_name: str = EMBED_MODEL):
    """
    Chunk the directive (by article, ideally) and embed each chunk.

    TODO:
    - decide chunking granularity, per-article is probably right given
      how short and self-contained each article is
    - persist embeddings + chunk text + article number alongside each other
      so retrieval results carry a citeable label
    """
    raise NotImplementedError


def retrieve(query: str, index, top_k: int = 3):
    """
    Return the top_k directive passages most relevant to `query`.

    TODO: cosine similarity over the embedding matrix, return
    (article_label, passage_text, score) tuples
    """
    raise NotImplementedError
