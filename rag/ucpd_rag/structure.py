"""
Structural parser over the canonical corpus text: articles -> commas -> letters,
plus the Normattiva amendment apparatus.

Two Normattiva conventions carry the provenance this project needs, so they are
parsed rather than hardcoded:

  ((...))   encloses text inserted or replaced by an amending decree.
  ((57))    a trailing update marker keyed to a "--------AGGIORNAMENTO (57)"
            block further down, which names the amending decree and its
            application date in prose.

Deriving `source` and `applicable_from` from those markers means the corpus
states its own provenance. Nothing here assumes D.Lgs. 30/2026 or the date
27 September 2026 -- both are read out of the document, and a chunk whose
marker resolves to some other decree gets that decree instead.
"""

import re

from . import extract

ARTICLE_HEAD_RE = re.compile(
    r"^Art\.\s*(?P<num>\d+(?:-(?:bis|ter|quater|quinquies|sexies|septies|octies|novies|decies))?)"
    r"(?:\s+(?P<rubric>.*))?$",
    re.M,
)
UPDATE_BLOCK_RE = re.compile(r"^-+AGGIORNAMENTO\s*\((?P<n>\d+)\)\s*$", re.M)
UPDATE_MARKER_RE = re.compile(r"\(\((?P<n>\d+)\)\)")

_ORD = ("bis|ter|quater|quinquies|sexies|septies|octies|novies|decies|"
        "undecies|duodecies|terdecies|quaterdecies")
COMMA_LINE_RE = re.compile(r"^(?P<comma>\d+(?:-(?:%s))?)\.\s" % _ORD)
LETTER_LINE_RE = re.compile(r"^(?P<letter>(?:[a-ik-vz]|aa|bb|cc)(?:-(?:%s))?)\)\s" % _ORD)

DECREE_RE = re.compile(
    r"(?:Il\s+)?D\.?Lgs\.?\s*(?P<day>\d{1,2})?\s*(?P<month>[a-zà-ù]+)?\s*(?P<year>\d{4}),?\s*n\.\s*(?P<num>\d+)",
    re.I,
)
DATE_RE = re.compile(r"decorrere dal\s+(?P<d>\d{1,2})\s+(?P<m>[a-zà-ù]+)\s+(?P<y>\d{4})", re.I)

_MONTHS = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6,
    "luglio": 7, "agosto": 8, "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
}

# The base code's own entry into force, for text carrying no update marker.
BASE_SOURCE = "base D.Lgs. 206/2005"
BASE_APPLICABLE_FROM = "2005-10-08"


def parse_articles(text=None):
    """Return [{num, rubric, start, end}] over the whole code, in document order."""
    if text is None:
        text = extract.load()
    heads = list(ARTICLE_HEAD_RE.finditer(text))
    arts = []
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        arts.append({
            "num": m.group("num"),
            "rubric": (m.group("rubric") or "").strip(),
            "start": m.start(),
            "end": end,
            "body_start": m.end(),
        })
    return arts


def get_article(num, text=None):
    for a in parse_articles(text):
        if a["num"] == str(num):
            return a
    raise KeyError("Art. %s not found in corpus" % num)


def parse_update_registry(text=None):
    """Map update-marker number -> {decree, applicable_from, raw}.

    Read out of the AGGIORNAMENTO blocks; no decree or date is assumed.
    """
    if text is None:
        text = extract.load()
    blocks = list(UPDATE_BLOCK_RE.finditer(text))
    reg = {}
    for i, m in enumerate(blocks):
        end = blocks[i + 1].start() if i + 1 < len(blocks) else min(len(text), m.end() + 4000)
        body = text[m.end():end]
        # stop at the next article heading so we only read this block's prose
        nxt = ARTICLE_HEAD_RE.search(body)
        if nxt:
            body = body[:nxt.start()]
        n = m.group("n")
        if n in reg:
            continue
        entry = {"raw": body.strip()[:600], "decree": None, "applicable_from": None}
        d = DECREE_RE.search(body)
        if d and d.group("year") and d.group("num"):
            entry["decree"] = "D.Lgs. %s/%s" % (d.group("num"), d.group("year"))
        dt = DATE_RE.search(body)
        if dt:
            mon = _MONTHS.get(dt.group("m").lower())
            if mon:
                entry["applicable_from"] = "%s-%02d-%02d" % (
                    dt.group("y"), mon, int(dt.group("d")))
        reg[n] = entry
    return reg


def markers_in(segment):
    """Update-marker numbers appearing in a text segment."""
    return UPDATE_MARKER_RE.findall(segment)


# Normattiva occasionally fences a passage as amended -- ((...)) -- without
# attaching a numeric marker to it. Art. 20 is the case that matters here: the
# whole article sits inside an unnumbered fence, so there is no AGGIORNAMENTO
# block to resolve. Reporting that as base 2005 text would be an invention, so
# it gets its own value and a null date.
UNMARKED_SOURCE = "amended, marker not attached in source PDF"


def provenance(segment, registry, fenced=None):
    """(source, applicable_from) for a chunk body, read from its own markers.

    `fenced` says whether the passage sits inside a (( )) amendment fence that
    opened earlier in the article; pass it for passages whose fence is not
    visible in `segment` itself.
    """
    ns = markers_in(segment)
    if not ns:
        if fenced or ("((" in segment and "))" not in segment):
            return UNMARKED_SOURCE, None
        return BASE_SOURCE, BASE_APPLICABLE_FROM
    # newest marker wins when a passage was touched more than once
    n = sorted(ns, key=lambda x: int(x))[-1]
    e = registry.get(n) or {}
    return (e.get("decree") or BASE_SOURCE,
            e.get("applicable_from") or BASE_APPLICABLE_FROM)


def fence_spans(article, text):
    """Character ranges inside an unnumbered (( )) fence within an article.

    Only unnumbered fences are returned: a fence carrying ((NN)) resolves on its
    own through `provenance`.
    """
    body = text[article["start"]:article["end"]]
    base = article["start"]
    spans = []
    depth = 0
    start = None
    i = 0
    while i < len(body) - 1:
        two = body[i:i + 2]
        if two == "((":
            if depth == 0:
                start = i
            depth += 1
            i += 2
            continue
        if two == "))":
            depth -= 1
            if depth <= 0 and start is not None:
                seg = body[start:i + 2]
                if not UPDATE_MARKER_RE.search(seg) and "\n" in seg:
                    spans.append((base + start, base + i + 2))
                start, depth = None, 0
            i += 2
            continue
        i += 1
    return spans


def in_fence(pos, spans):
    for a, b in spans:
        if a <= pos < b:
            return True
    return False


def strip_apparatus(s):
    """Remove Normattiva editorial apparatus, leaving statutory words untouched.

    Only (( )) fences and ((NN)) markers go; no word is altered, so the result
    is still verbatim.
    """
    s = UPDATE_MARKER_RE.sub("", s)
    s = s.replace("((", "").replace("))", "")
    return re.sub(r"[ \t]{2,}", " ", s).strip()


def iter_units(article, text=None):
    """Yield the citable units inside an article, in document order.

    Each unit is {kind: 'letter'|'comma', comma, letter, start, end, line}.

    A unit runs to the start of the NEXT unit, not to the end of its own line.
    That matters because several units carry nested numbered sub-points on
    their own lines -- Art. 18 lett. c-bis ("beni": 1) 2) 3)), lett. n-septies
    (four certification criteria), Art. 23 lett. f (1) 2) 3)). Ending a unit at
    its first line reduced lett. c-bis to the 14 characters `c-bis) "beni":`,
    dropped n-septies' four criteria, and -- because the ((57)) marker sits at
    the end of the LAST sub-point -- silently filed n-septies as pre-existing
    text when D.Lgs. 30/2026 had in fact inserted it.

    Sub-points are deliberately not split out: they are parts of their letter's
    fact pattern, not separately citable units.

    Letters are scoped by the comma they sit in -- Art. 21 has a lett. b) in
    both comma 1 and comma 2, so a letter alone does not identify a passage.
    """
    if text is None:
        text = extract.load()
    body = text[article["body_start"]:article["end"]]
    base = article["body_start"]

    ub = UPDATE_BLOCK_RE.search(body)
    if ub:
        body = body[:ub.start()]

    # pass 1: locate the openers
    found = []
    cur_comma = None
    for m in re.finditer(r"^.+$", body, re.M):
        line = m.group(0)
        cm = COMMA_LINE_RE.match(line)
        lm = LETTER_LINE_RE.match(line.lstrip("("))
        if cm:
            cur_comma = cm.group("comma")
            found.append({"kind": "comma", "comma": cur_comma, "letter": None,
                          "start": base + m.start()})
        elif lm:
            found.append({"kind": "letter", "comma": cur_comma,
                          "letter": lm.group("letter"), "start": base + m.start()})

    # pass 2: each unit runs to the next unit's start
    # The last unit must not swallow the section heading that follows the
    # article -- Art. 20 comma 5 was absorbing "SEZIONE I Pratiche commerciali
    # ingannevoli", which is navigation, not statute.
    limit = base + len(body)
    tail = re.search(
        r"^\(*(?:Parte|Titolo|Capo|Sezione|SEZIONE|TITOLO|PARTE|CAPO)\b", body, re.M)
    if tail and found and base + tail.start() > found[-1]["start"]:
        limit = base + tail.start()

    for i, u in enumerate(found):
        u["end"] = found[i + 1]["start"] if i + 1 < len(found) else limit
        u["line"] = text[u["start"]:u["end"]].strip()
        yield u


def letters_of(article_num, text=None):
    """[(comma, letter)] inventory for one article."""
    if text is None:
        text = extract.load()
    art = get_article(article_num, text)
    return [(u["comma"], u["letter"]) for u in iter_units(art, text)
            if u["kind"] == "letter"]
