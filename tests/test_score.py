"""Unit tests for retriever/score.py (checklist Step 4). Run: python3 -m pytest tests/

The real models are swapped for loo_check's offline char-n-gram encoder, so these tests check the
plumbing (margin, candidate rule, few-shot anchors, edge cases), not embedding quality."""
import copy
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "retriever"))
import score  # noqa: E402
from loo_check import charngram_encode  # noqa: E402
from segment import load_config  # noqa: E402


@pytest.fixture
def make(monkeypatch, tmp_path):
    monkeypatch.setattr(score.Retriever, "embed", lambda self, texts: charngram_encode(texts))

    def _make(tau=None, aggregation="max"):
        cfg = copy.deepcopy(load_config())
        cfg["embedding"]["cache_dir"] = str(tmp_path)
        cfg["scoring"]["tau"] = {cfg["embedding"]["active"]: tau}
        cfg["scoring"]["aggregation"] = aggregation
        return score.Retriever(cfg)
    return _make


def test_empty_records(make):
    r = make()
    assert r.score_record({}) == []
    assert r.candidates({"description": ""}) == []


def test_zero_candidates(make):
    r = make(tau=None)
    assert r.candidates({"description": "Gustoso e croccante"}) == []


def test_lexical_hit_is_candidate_without_tau(make):
    r = make(tau=None)
    (s,) = r.candidates({"description": "Confezione in plastica riciclata"})
    assert s.lexical and s.candidate


def test_tau_controls_embedding_candidates(make):
    rec = {"description": "Gustoso e croccante"}
    (s,) = make(tau=None).score_record(rec)
    assert not s.candidate
    assert make(tau=s.margin - 1e-6).score_record(rec)[0].candidate
    assert not make(tau=s.margin + 1e-6).score_record(rec)[0].candidate


def test_margin_is_max_over_text_and_clauses(make):
    r = make()
    (s,) = r.score_record({"description": "Gustoso e croccante, amico dell'ambiente"})
    assert s.best_text in {s.span.text, *s.span.clauses}
    texts = list(dict.fromkeys([s.span.text, *s.span.clauses]))
    S = charngram_encode(texts) @ r.A.T
    m = S[:, r.is_pos].max(axis=1) - S[:, ~r.is_pos].max(axis=1)
    assert s.margin == pytest.approx(float(m.max()), abs=1e-6)


def test_exact_anchor_text_scores_high(make):
    (s,) = make().score_record({"description": "Senza microplastiche"})
    assert s.margin > 0
    assert s.anchors[0]["text"] == "Senza microplastiche"
    assert s.anchors[0]["sim"] == pytest.approx(1.0, abs=1e-4)


def test_fewshot_anchors_are_top_k_positives(make):
    r = make()
    (s,) = r.score_record({"description": "Formula biodegradabile"})
    assert len(s.anchors) == r.k == 3
    pos_ids = {a["id"] for a in r.anchors if a["polarity"] == "pos"}
    assert all(a["id"] in pos_ids for a in s.anchors)
    sims = [a["sim"] for a in s.anchors]
    assert sims == sorted(sims, reverse=True)
    assert all("triggers" in a for a in s.anchors)


def test_top3_mean_aggregation(make):
    r = make(aggregation="top3_mean")
    S = np.array([[0.9, 0.5, 0.1, 0.7]])
    assert r._agg(S)[0] == pytest.approx((0.9 + 0.7 + 0.5) / 3)


def test_anchor_hash_mismatch_refused(make):
    cfg = copy.deepcopy(load_config())
    cfg["anchors"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="sha256 mismatch"):
        score.Retriever(cfg)
