# -*- coding: utf-8 -*-
"""
PDF -> canonical normalised text for the consolidated Codice del Consumo.

Ground truth is rag/docs/consolidated.pdf (Normattiva, "Vigente al: 19-9-2026").
Nothing downstream may assert an article, letter or date that was not read out
of this file.

Why a *canonical* text artifact: every chunk carries a char_span back into the
extracted text (Appendix B). Offsets only mean something against one frozen
string, so normalisation happens exactly once, here, and the result is written
to rag/build/corpus_text.txt. Re-running is deterministic.

Normalisation performed:
  * page boundaries removed. pdftotext ends a page with "\\n\\n\\f", which reads
    as a blank line; treating that as a paragraph break cut 8 lettered units in
    half (Art. 23 lett. d-bis among them), each silently truncated mid-sentence.
    The whole boundary collapses to a single newline and the wrap rule decides.
  * hard line wraps rejoined into flowing paragraphs; a newline survives only
    when the following line opens a new structural element.
  * NBSP -> space, runs of spaces collapsed.

Deliberately NOT performed: quote/apostrophe folding, accent repair, or any
edit to the words themselves. A chunk's `text` has to be verbatim statutory
text, so whitespace is the only safe thing to touch.
"""

import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
RAG_ROOT = os.path.dirname(HERE)
PDF_PATH = os.path.join(RAG_ROOT, "docs", "consolidated.pdf")
BUILD_DIR = os.path.join(RAG_ROOT, "build")
CORPUS_TXT = os.path.join(BUILD_DIR, "corpus_text.txt")

EXPECTED_VIGENZA = "Vigente al : 19-9-2026"

# --- structural openers -----------------------------------------------------
# Italian legal lettering skips j k w x y; after z it doubles (aa, bb), and each
# letter may carry an ordinal suffix (bis .. quaterdecies). An [a-z] class would
# silently mis-parse this corpus, so the alphabet is written out.
_ORDINALS = (
    "bis|ter|quater|quinquies|sexies|septies|octies|novies|decies|"
    "undecies|duodecies|terdecies|quaterdecies"
)
LETTER_RE = re.compile(
    r"^(?P<letter>(?:[a-ik-vz]|aa|bb|cc)(?:-(?:%s))?)\)\s" % _ORDINALS
)
COMMA_RE = re.compile(r"^(?P<comma>\d+(?:-(?:%s))?)\.\s" % _ORDINALS)
SUBPOINT_RE = re.compile(r"^\d+\)\s")
ARTICLE_RE = re.compile(r"^Art\.\s*(?P<num>\d+(?:-(?:%s))?)\s*$" % _ORDINALS)
UPDATE_RE = re.compile(r"^-+AGGIORNAMENTO\s*\((?P<n>\d+)\)")
HEADING_RE = re.compile(
    r"^\(*(?:Parte|Titolo|Capo|Sezione|SEZIONE|TITOLO|PARTE|CAPO|ALLEGATO|Allegato)\b")

_OPENERS = (LETTER_RE, COMMA_RE, SUBPOINT_RE, ARTICLE_RE, UPDATE_RE, HEADING_RE)


def _opens_structure(line):
    stripped = line.lstrip("(").strip()
    for rx in _OPENERS:
        if rx.match(stripped):
            return True
    return False


def pdf_to_raw(pdf_path=PDF_PATH):
    """pdftotext in flowing (non-layout) mode; this corpus is single-column."""
    if not os.path.exists(pdf_path):
        raise IOError("consolidated PDF not found at %s" % pdf_path)
    out = subprocess.check_output(["pdftotext", "-enc", "UTF-8", pdf_path, "-"])
    return out.decode("utf-8")


def normalise(raw):
    """Rejoin wrapped lines into paragraphs. Deterministic, whitespace-only."""
    # page boundary -> single newline (see module docstring)
    text = re.sub(r"\n*[ \t]*\f[ \t]*\n*", "\n", raw)
    text = text.replace(u" ", " ")
    lines = [ln.rstrip() for ln in text.split("\n")]

    out = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            out.append("\n")
            continue
        if out and out[-1] != "\n" and not _opens_structure(line):
            out.append(" " + stripped)          # continuation -> soft join
        else:
            if out and out[-1] != "\n":
                out.append("\n")
            out.append(stripped)
    joined = "".join(out)
    joined = re.sub(r"[ \t]{2,}", " ", joined)
    joined = re.sub(r"\n{3,}", "\n\n", joined)
    return joined.strip() + "\n"


def check_integrity(text, articles=("18", "20", "21", "22", "23")):
    """Catch units truncated by a bad join. Returns a list of complaints.

    Statutory letters and commas end in ';', '.' or ':'. One that does not was
    almost certainly cut mid-sentence -- the failure mode that page-break
    handling introduced, and one that is invisible unless it is asserted on,
    because a truncated chunk still embeds and still retrieves.
    """
    from . import structure                      # local import: avoids a cycle
    bad = []
    for n in articles:
        art = structure.get_article(n, text)
        for u in structure.iter_units(art, text):
            body = structure.strip_apparatus(u["line"])
            tail = body.rstrip()
            # A list item may legitimately end in the disjunction that joins it
            # to the next one -- Art. 20, comma 4, lett. a) ends "...e 23 o".
            if re.search(r"\b(o|e|oppure|ovvero|nonche|nonch\u00e9)$", tail):
                continue
            if not tail.endswith((";", ".", ":")):
                bad.append({"article": n, "comma": u["comma"],
                            "letter": u["letter"], "kind": u["kind"],
                            "tail": body[-70:]})
    return bad


def build(pdf_path=PDF_PATH, out_path=CORPUS_TXT, verify=True):
    raw = pdf_to_raw(pdf_path)
    if EXPECTED_VIGENZA not in raw:
        raise AssertionError(
            "PDF does not carry the expected vigenza header %r -- refusing to "
            "build a corpus from an unverified document." % EXPECTED_VIGENZA)
    norm = normalise(raw)
    if not os.path.isdir(os.path.dirname(out_path)):
        os.makedirs(os.path.dirname(out_path))
    with open(out_path, "w") as fh:
        fh.write(norm)
    if verify:
        bad = check_integrity(norm)
        if bad:
            raise AssertionError(
                "%d unit(s) look truncated after normalisation, e.g. %r"
                % (len(bad), bad[:3]))
    return norm


def load(out_path=CORPUS_TXT):
    """Read the frozen canonical text. char_span values index into THIS string."""
    with open(out_path) as fh:
        return fh.read()


if __name__ == "__main__":
    t = build()
    print("wrote %s (%d chars, %d lines) -- integrity check passed"
          % (CORPUS_TXT, len(t), t.count("\n")))
