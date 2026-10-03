"""Unit tests for retriever/segment.py (checklist Step 3). Run: python3 -m pytest tests/"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "retriever"))
from segment import load_config, segment_record  # noqa: E402

CFG = load_config()


def texts(record):
    return [s.text for s in segment_record(record, CFG)]


def by_text(record):
    return {s.text: s for s in segment_record(record, CFG)}


# Fixture from the prompt doc's Pass 1 few-shot.
BAGNOSCHIUMA = {
    "name": "Bagnoschiuma idratante",
    "features": "Formula vegana & biodegradabile^\nClinicamente testato\n"
                "Protegge la pelle dagli agenti esterni\n^99,9% formula biodegradabile",
    "producer_info": "Dal 1920 le ricette di famiglia. Flacone green 100%. "
                     "Aiuta a ridurre il rischio di irritazione della pelle.",
    "certifications": ["VEGANO"],
}


def test_fixture_expected_candidates():
    out = texts(BAGNOSCHIUMA)
    for expected in ["Formula vegana & biodegradabile^ ... ^99,9% formula biodegradabile",
                     "Flacone green 100%",
                     "Aiuta a ridurre il rischio di irritazione della pelle",
                     "VEGANO"]:
        assert expected in out


def test_fixture_footnote_body_never_standalone():
    assert not any(t.startswith("^") for t in texts(BAGNOSCHIUMA))


def test_fixture_name_not_segmented():
    assert not any(s.source_field == "name" for s in segment_record(BAGNOSCHIUMA, CFG))


def test_multiple_footnote_markers():
    rec = {"description": "Flacone con il 35% di plastica riciclata* e 100% riciclabile**\n"
                          "Tappo green*\n"
                          "*escluso lo spruzzatore\n**esclusa l'etichetta"}
    out = by_text(rec)
    both = "Flacone con il 35% di plastica riciclata* e 100% riciclabile** ... *escluso lo spruzzatore\n**esclusa l'etichetta"
    assert both in out
    assert out[both].footnotes == ["*escluso lo spruzzatore", "**esclusa l'etichetta"]
    # "*" must not pick up the "**" body
    assert "Tappo green* ... *escluso lo spruzzatore" in out
    assert not any(t.startswith("*") for t in out)


def test_footnote_body_in_other_field():
    rec = {"features": "96% Natural origin*", "description": "*according to ISO 16128"}
    assert "96% Natural origin* ... *according to ISO 16128" in texts(rec)


def test_unused_footnote_body_is_kept():
    rec = {"description": "Buono e semplice\n*prodotto con energia rinnovabile"}
    assert "*prodotto con energia rinnovabile" in texts(rec)


def test_degree_and_numero_are_not_markers():
    out = texts({"description": "N°1 in Italia\nConservare a 4 °C"})
    assert "N°1 in Italia" in out


def test_same_text_in_two_fields_keeps_most_specific():
    rec = {"features": "Senza microplastiche", "description": "Senza microplastiche.\nOttimo gusto"}
    spans = [s for s in segment_record(rec, CFG) if s.text == "Senza microplastiche"]
    assert len(spans) == 1
    assert spans[0].source_field == "features"
    assert spans[0].also_in == ["description"]


def test_never_split_at_comma():
    rec = {"description": "Coltivato senza pesticidi, raccolto a mano, confezionato in Italia."}
    out = by_text(rec)
    unit = "Coltivato senza pesticidi, raccolto a mano, confezionato in Italia"
    assert unit in out
    assert out[unit].clauses == ["Coltivato senza pesticidi", "raccolto a mano", "confezionato in Italia"]
    assert "raccolto a mano" not in out


def test_abbreviations_do_not_end_sentences():
    rec = {"description": "Approvata da A.I.Nut. Associazione Italiana Nutrizionisti. "
                          "Ricetta creata con il Dott. Giorgio Donegani."}
    out = texts(rec)
    assert "Approvata da A.I.Nut. Associazione Italiana Nutrizionisti" in out
    assert "Ricetta creata con il Dott. Giorgio Donegani" in out


def test_html_br_splits_lines_and_paragraphs():
    rec = {"description": "Senza conservanti.<br><br>Prodotto con il 100% di plastica riciclata.<br>Per il pianeta"}
    out = texts(rec)
    assert "Prodotto con il 100% di plastica riciclata" in out
    assert "Prodotto con il 100% di plastica riciclata.<br>Per il pianeta" in out   # same paragraph
    assert not any("Senza conservanti" in t and "riciclata" in t for t in out)       # across <br><br>


def test_window_merges_continuation_sentence():
    rec = {"description": "Non sprecare, ricicla.\nÈ per il bene del nostro pianeta.\nManiva S.p.A."}
    assert "Non sprecare, ricicla.\nÈ per il bene del nostro pianeta" in texts(rec)


def test_no_window_across_blank_line():
    rec = {"description": "Viva la Natura!\n\nPer un futuro migliore"}
    assert not any("\n" in t for t in texts(rec))


DISPOSAL = ("Bottiglia Plastica - Largamente riciclabile\n"
            "Tappo - HDPE 2 - Raccolta plastica\n"
            "Film - 7 - Raccolta plastica\n"
            "Verifica le disposizioni del tuo Comune")


def test_disposal_block_dropped():
    assert texts({"description": "Gustoso e leggero\n" + DISPOSAL}) == ["Gustoso e leggero"]


@pytest.mark.parametrize("heading", ["Per l'ambiente", "Rispetta l'ambiente",
                                     "La nostra confezione e l'ambiente"])
def test_bare_heading_over_disposal_dropped(heading):
    assert heading not in texts({"description": f"Gustoso\n\n{heading}\n{DISPOSAL}"})


@pytest.mark.parametrize("kept", ["Fiorentini per l'ambiente",
                                  "Attenti all'ambiente confezione riciclabile"])
def test_brand_slogan_or_specific_heading_kept(kept):
    assert kept in texts({"description": f"Gustoso\n\n{kept}\n{DISPOSAL}"})


def test_heading_rule_needs_direct_adjacency():
    out = texts({"description": "Rispetta l'ambiente\n\n" + DISPOSAL})
    assert "Rispetta l'ambiente" in out


@pytest.mark.parametrize("line", ["Questa confezione è riciclabile",
                                  "La raccolta differenziata aiuta la natura",
                                  "Bottiglia con 50% plastica riciclata"])
def test_claims_near_disposal_vocabulary_survive(line):
    assert line in texts({"description": line})


def test_origin_and_section_lines_dropped():
    rec = {"description": "Origine Altro Testo Paese di mungitura: Italia\n"
                          "Ingredienti: farina*, zucchero\n"
                          "Modalità d'uso: agitare prima dell'uso\n"
                          "Latte da allevamenti selezionati"}
    assert texts(rec) == ["Latte da allevamenti selezionati"]


def test_empty_record():
    assert segment_record({}, CFG) == []
    assert segment_record({"description": "", "certifications": []}, CFG) == []


@pytest.mark.parametrize("claim", ["Senza microplastiche", "Gustoso e leggero"])
def test_short_claim_above_disposal_is_not_a_heading(claim):
    assert claim in texts({"description": f"{claim}\n{DISPOSAL}"})


@pytest.mark.parametrize("line", [
    "I cartoni sono riciclabili nella carta, dipende dalle modalità di raccolta del tuo comune",
    "Chiedi al tuo comune come raccoglierla e proteggi l'ambiente insieme a noi!",
])
def test_comune_mention_with_claim_survives(line):
    assert line in texts({"description": line})


def test_comune_instruction_dropped():
    rec = {"description": "Per maggiori informazioni sulle modalità di raccolta differenziata "
                          "consulta il regolamento del tuo comune"}
    assert texts(rec) == []
