# -*- coding: utf-8 -*-
"""
Chunking at the citable unit, for a detector of claims *in scope of* D.Lgs. 30/2026.

Design follows from what the component is for. The study is a before/after on
27 September 2026: claims that the new rules reach should thin out once those
rules bind. Three consequences drive everything here.

1. `regime` is the treatment variable, not decoration.
   A provision is either new (applicable 2026-09-27) or pre-existing. Claims
   matching pre-existing text were already unlawful and are the control arm;
   claims matching new text are the treated arm. That flag is derived from the
   document's own ((NN)) apparatus, never asserted.

2. A chunk has to be legally self-sufficient or the LLM cannot reason with it.
   Art. 23 lett. d-bis reads "formulare un'asserzione ambientale generica per la
   quale il professionista non e' in grado di dimostrare l'eccellenza
   riconosciuta..." -- which is unintelligible on its own. It depends on four
   Art. 18 definitions. Two mechanisms fix that:
     * `context_text` -- the comma's chapeau, carried with every letter. A bare
       letter under Art. 21 c.1 ("le caratteristiche principali del prodotto")
       is a fragment; with its chapeau it is a rule.
     * `depends_on`  -- definition chunks whose defined term appears in the
       text, resolved automatically so retrieval can pull them in.

3. Verbatim means verbatim.
   `text` is the unit exactly as printed, and is what a citation displays.
   `embed_text` (chapeau + text, both verbatim) exists only for retrieval.
   Nothing here paraphrases, and no model ever writes either field.

Scope: Art. 18-23. Art. 24-26 (aggressive practices) are excluded -- a claim
string lifted from product copy cannot realise harassment or coercion. Art. 45,
48, 49 and 65-ter are touched by the same decree but govern pre-contractual
information duties rather than claims, and are excluded for that reason.
"""

import json
import os
import re

from . import extract, structure

ARTICLES = ["18", "19", "20", "21", "22", "23"]

NEW_DECREE = "D.Lgs. 30/2026"
NEW_FROM = "2026-09-27"

CHUNK_TYPE_BY_ARTICLE = {
    "18": "definition",
    "19": "scope-limit",
    "20": "general-clause",
    "21": "general-clause",
    "22": "general-clause",
    "23": "blacklist",
}

# EU counterparts, nullable and returned only when the caller asks. Held here so
# no model ever composes one. Art. 23's lettering does not run parallel to Annex
# I's numbering, so these are stated per letter rather than computed.
CITATION_EU = {
    ("23", "1", "b"): "Annex I, point 2, Directive 2005/29/EC",
    ("23", "1", "b-bis"): "Annex I, point 2a, Directive 2005/29/EC",
    ("23", "1", "d"): "Annex I, point 4, Directive 2005/29/EC",
    ("23", "1", "d-bis"): "Annex I, point 4a, Directive 2005/29/EC",
    ("23", "1", "d-ter"): "Annex I, point 4b, Directive 2005/29/EC",
    ("23", "1", "d-quater"): "Annex I, point 4c, Directive 2005/29/EC",
    ("23", "1", "l-bis"): "Annex I, point 10a, Directive 2005/29/EC",
    ("23", "1", "s"): "Annex I, point 17, Directive 2005/29/EC",
    ("23", "1", "bb-quinquies"): "Annex I, point 23d, Directive 2005/29/EC",
    ("23", "1", "bb-sexies"): "Annex I, point 23e, Directive 2005/29/EC",
    ("23", "1", "bb-septies"): "Annex I, point 23f, Directive 2005/29/EC",
    ("23", "1", "bb-octies"): "Annex I, point 23g, Directive 2005/29/EC",
    ("23", "1", "bb-novies"): "Annex I, point 23h, Directive 2005/29/EC",
    ("23", "1", "bb-decies"): "Annex I, point 23i, Directive 2005/29/EC",
    ("23", "1", "bb-undecies"): "Annex I, point 23j, Directive 2005/29/EC",
    ("20", None, None): "Art. 5, Directive 2005/29/EC",
    ("21", None, None): "Art. 6, Directive 2005/29/EC",
    ("22", None, None): "Art. 7, Directive 2005/29/EC",
    ("18", None, None): "Art. 2, Directive 2005/29/EC",
}

# The defined term is the quoted phrase at the head of the letter. Art. 18
# lett. d) interposes a parenthetical gloss -- "pratiche commerciali tra
# professionisti e consumatori" (di seguito denominate: "pratiche commerciali"):
# -- whose own colon must not be taken for the definition's, so the closing
# quote terminates the term rather than the first colon.
# The defined term is the quoted phrase at the head of the letter. Art. 18
# lett. d) interposes a parenthetical gloss -- "..." (di seguito denominate:
# "pratiche commerciali"): -- whose own colon must not be taken for the
# definition's, so the closing quote terminates the term, not the first colon.
DEFINED_TERM_RE = re.compile(
    u'^[^)]+\\)\\s*[\u201c\u2018"\'](?P<term>[^"\u201d\u2019]+)[\u201d\u2019"\']'
)


def _citation_it(article, comma, letter):
    bits = ["Art. %s" % article]
    if comma:
        bits.append("comma %s" % comma)
    if letter:
        bits.append("lett. %s" % letter)
    return ", ".join(bits) + ", Codice del Consumo"


def _chunk_id(article, comma, letter):
    p = "cdc-art%s" % article
    if comma:
        p += "-c%s" % comma
    if letter:
        p += "-lett-%s" % letter
    return p


def _citation_eu(article, comma, letter):
    return (CITATION_EU.get((article, comma, letter))
            or CITATION_EU.get((article, None, None)))


def _defined_term(body):
    m = DEFINED_TERM_RE.match(body)
    if not m:
        return None
    term = m.group("term").strip(u' "“”‘’\'')
    return term if 3 < len(term) <= 80 else None


# Normattiva's own typesetting defect, carried through faithfully: Art. 18
# lett. d-bis prints  'microimprese:  where the source should read
# <<microimpresa>>. Both pdftotext and pdfplumber agree, so it is in the PDF,
# not in extraction. `text` stays verbatim -- repairing statutory text silently
# is worse than carrying a flagged defect -- and the term simply does not parse.
_DEFECTS = [(u"'microimpres\u00e9", "mangled quotation marks around the defined term")]


def _source_defect(body):
    for needle, note in _DEFECTS:
        if needle in body:
            return note
    return None


def build(text=None):
    """Return the chunk list. Deterministic; no model involved at any point."""
    if text is None:
        text = extract.load()
    reg = structure.parse_update_registry(text)
    out = []

    for art in ARTICLES:
        a = structure.get_article(art, text)
        spans = structure.fence_spans(a, text)
        units = list(structure.iter_units(a, text))

        # chapeau per comma: the comma's own opening line, which the letters
        # beneath it complete. Without it a letter is a sentence fragment.
        chapeau = {}
        for u in units:
            if u["kind"] == "comma":
                chapeau[u["comma"]] = structure.strip_apparatus(u["line"])

        for u in units:
            body = structure.strip_apparatus(u["line"])
            letter, comma = u["letter"], u["comma"]

            # a comma that only introduces letters is kept as context, not as a
            # chunk of its own -- it would retrieve as a near-duplicate of every
            # letter beneath it.
            if u["kind"] == "comma":
                has_letters = any(x["kind"] == "letter" and x["comma"] == comma
                                  for x in units)
                if has_letters and body.rstrip().endswith(":"):
                    continue

            src, af = structure.provenance(
                u["line"], reg, fenced=structure.in_fence(u["start"], spans))
            ctx = chapeau.get(comma, "") if letter else ""

            out.append({
                "chunk_id": _chunk_id(art, comma, letter),
                "article": art,
                "comma": comma,
                "letter": letter,
                "chunk_type": CHUNK_TYPE_BY_ARTICLE[art],
                "text": body,                       # verbatim, what a citation shows
                "context_text": ctx,                # verbatim chapeau, for reasoning
                "embed_text": ((ctx + " " + body).strip() if ctx else body),
                "citation_it": _citation_it(art, comma, letter),
                "citation_eu": _citation_eu(art, comma, letter),
                "source": src,
                "applicable_from": af,
                "regime": "new-2026" if src == NEW_DECREE else "pre-existing",
                "defined_term": _defined_term(body) if art == "18" else None,
                "source_defect": _source_defect(body),
                "depends_on": [],
                "char_span": [u["start"], u["end"]],
                "extracted_from": "docs/consolidated.pdf (Vigente al: 19-9-2026)",
            })

    _link_definitions(out)
    return out


def _link_definitions(chunks):
    """Resolve which definitions each operative rule leans on.

    Matched on the defined term appearing verbatim in the rule's text. Longest
    term first, so "asserzione ambientale generica" claims the match before
    "asserzione ambientale" does; the shorter one is then only credited if it
    occurs somewhere the longer one does not.
    """
    defs = [(c["defined_term"].lower(), c["chunk_id"])
            for c in chunks if c.get("defined_term")]
    defs.sort(key=lambda kv: -len(kv[0]))

    for c in chunks:
        if c["chunk_type"] == "definition":
            continue
        hay = (c["embed_text"] or "").lower()
        claimed, deps = [], []
        for term, cid in defs:
            for m in re.finditer(re.escape(term), hay):
                if not any(s <= m.start() < e for s, e in claimed):
                    claimed.append((m.start(), m.end()))
                    deps.append(cid)
                    break
        c["depends_on"] = sorted(set(deps))


def save(chunks, path=None):
    if path is None:
        path = os.path.join(extract.BUILD_DIR, "chunks.json")
    with open(path, "w") as fh:
        json.dump(chunks, fh, ensure_ascii=False, indent=1)
    return path


def load(path=None):
    if path is None:
        path = os.path.join(extract.BUILD_DIR, "chunks.json")
    with open(path) as fh:
        return json.load(fh)


def verify(chunks, text=None):
    """Every invariant the contract depends on, asserted rather than assumed."""
    if text is None:
        text = extract.load()
    problems = []
    seen = set()
    for c in chunks:
        if c["chunk_id"] in seen:
            problems.append(("duplicate chunk_id", c["chunk_id"]))
        seen.add(c["chunk_id"])

        # text must be recoverable from the canonical text at char_span
        s, e = c["char_span"]
        if structure.strip_apparatus(text[s:e]) != c["text"]:
            problems.append(("char_span does not reproduce text", c["chunk_id"]))
        if not c["text"].strip():
            problems.append(("empty text", c["chunk_id"]))
        if c["regime"] == "new-2026" and c["applicable_from"] != NEW_FROM:
            problems.append(("new-2026 without the right date", c["chunk_id"]))
        for d in c["depends_on"]:
            if d not in {x["chunk_id"] for x in chunks}:
                problems.append(("dangling depends_on", c["chunk_id"], d))
    return problems


if __name__ == "__main__":
    cs = build()
    p = save(cs)
    probs = verify(cs)
    print("%d chunks -> %s" % (len(cs), p))
    print("verification problems:", probs if probs else "none")
