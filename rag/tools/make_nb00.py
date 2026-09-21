# -*- coding: utf-8 -*-
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
RAG = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import nbbuild

C = []
md = lambda s: C.append(("md", s))
co = lambda s: C.append(("code", s))

md("""# Phase 0 — Corpus verification

Ground truth: `rag/docs/consolidated.pdf` — Normattiva's consolidated *Codice del
Consumo* (D.Lgs. 206/2005), **Vigente al: 19-9-2026**.

This notebook establishes **by assertion, not by eye**, that the document contains
the articles and letters the brief expects, and that amendment provenance can be
*read out of* the document rather than assumed. Every later phase indexes into the
canonical text frozen here.

1. the PDF is the document it claims to be (vigenza header)
2. Art. 18, 20, 21, 22, 23 are present
3. extraction did not silently truncate anything
4. each amendment the brief names exists, with its **actual** letter numbering
5. the amending decree and its application date are read from the document
6. what changed relative to the EU corpus currently in the repo""")

co("""import os, sys, re, json
sys.path.insert(0, os.path.abspath(".."))
import pandas as pd
from ucpd_rag import extract, structure

pd.set_option("display.max_colwidth", 150)
pd.set_option("display.width", 210)
print("PDF:", os.path.relpath(extract.PDF_PATH, ".."))
print("exists:", os.path.exists(extract.PDF_PATH))""")

md("""## 1. Build the canonical text

`extract.build()` refuses to emit a corpus unless the PDF carries the expected
vigenza header — so this cell succeeding *is* the identity check.

Normalisation is whitespace-only: page boundaries removed, hard wraps rejoined.
No quote folding, no accent repair, no word altered. A chunk's `text` has to stay
verbatim statutory text, so whitespace is the only safe thing to touch.""")

co("""text = extract.build()          # raises unless vigenza header + integrity both pass
print("canonical text: %d chars, frozen at %s"
      % (len(text), os.path.relpath(extract.CORPUS_TXT, "..")))
assert extract.EXPECTED_VIGENZA in extract.pdf_to_raw()
print("vigenza header asserted:", extract.EXPECTED_VIGENZA)
print()
print(text[:150])""")

md("""### 1a. Extraction integrity — the check that earned its keep

A truncated chunk is invisible: it still embeds, still retrieves, still renders a
plausible citation. It just quietly omits half the rule.

`pdftotext` ends a page with `\\n\\n\\f`. Read naively that looks like a blank line,
i.e. a paragraph break — and it cut **10 lettered units in half**, among them
Art. 23 lett. d-bis, one of the three letters this project exists to find. The
check below asserts every unit ends as statutory prose does (`;` `.` `:`, or the
disjunction that joins it to the next item, as in Art. 20 comma 4 lett. a) `…e 23 o`).""")

co("""bad = extract.check_integrity(text)
print("units failing the integrity check:", len(bad))
assert not bad, bad
print()
print("the four units that were previously truncated, now whole:\\n")
reg = structure.parse_update_registry(text)
for art, L in [("23", "d-bis"), ("18", "n-quinquies"), ("18", "n-novies"), ("23", "bb-septies")]:
    a = structure.get_article(art, text)
    u = [x for x in structure.iter_units(a, text) if x.get("letter") == L][0]
    print("Art. %s lett. %s" % (art, L))
    print("   " + structure.strip_apparatus(u["line"])[:250])
    print()""")

md("""## 2. Presence of the five target articles

Art. 20 is included because Phase 1 needs general-clause chunks from Art. 20/21/22;
its absence would matter as much as Art. 23's.""")

co("""TARGETS = ["18", "20", "21", "22", "23"]
rows = []
for n in TARGETS:
    a = structure.get_article(n, text)          # raises if absent
    rows.append({"article": "Art. %s" % n,
                 "rubric": structure.strip_apparatus(a["rubric"]),
                 "start": a["start"], "end": a["end"], "chars": a["end"] - a["start"]})
present = pd.DataFrame(rows)
assert len(present) == len(TARGETS)
present""")

md("""## 3. Amendment provenance, read from the document

Normattiva marks amended passages with `((...))` and tags them `((NN))`, keyed to an
`AGGIORNAMENTO (NN)` block that names the decree in prose. Parsing that apparatus
means the corpus states its own provenance — nothing below hardcodes *D.Lgs. 30/2026*
or *27 September 2026*.""")

co("""print("update markers in the document:", len(reg))
used = set()
for n in TARGETS:
    a = structure.get_article(n, text)
    used |= set(structure.markers_in(text[a["start"]:a["end"]]))
print("markers appearing in Art. 18/20/21/22/23:", sorted(used, key=int))
pd.DataFrame([{"marker": "((%s))" % k, "decree": reg[k]["decree"],
               "applicable_from": reg[k]["applicable_from"]} for k in sorted(used, key=int)])""")

co("""m57 = reg["57"]
print("AGGIORNAMENTO (57), verbatim from the PDF:\\n")
print(m57["raw"][:330])
assert m57["decree"] == "D.Lgs. 30/2026", m57["decree"]
assert m57["applicable_from"] == "2026-09-27", m57["applicable_from"]
print("\\n\\nCONFIRMED: the brief's decree and application date match the document.")""")

md("""### 3a. One article whose fence carries no marker

Art. 20 sits entirely inside a `((...))` amendment fence that has **no** `((NN))`
tag, so there is no AGGIORNAMENTO block to resolve it against. Recording it as
base-2005 text would be an invention, so it gets an explicit unknown and a null
date instead.""")

co("""a20 = structure.get_article("20", text)
spans = structure.fence_spans(a20, text)
print("Art. 20 unnumbered fence spans:", spans)
print("inline markers in Art. 20:", structure.markers_in(text[a20["start"]:a20["end"]]) or "none")
print()
for u in structure.iter_units(a20, text):
    if u["kind"] == "comma":
        src, af = structure.provenance(u["line"], reg,
                                       fenced=structure.in_fence(u["start"], spans))
        print("  comma %-3s -> %-45s %s" % (u["comma"], src, af))""")

md("""## 4. Letter inventory per article

Letters are scoped by comma. Art. 21 carries a `lett. b)` in **both** comma 1 and
comma 2, so a letter alone does not identify a passage — the citation template needs
the comma.

Italian lettering skips *j k w x y* and doubles after *z* (…v, z, aa, bb), each
optionally suffixed *bis … undecies*. A naive `[a-z]` parser mis-reads this corpus,
so the alphabet is written out explicitly in `structure.py`.""")

co("""def prov(art_num, u):
    a = structure.get_article(art_num, text)
    sp = structure.fence_spans(a, text)
    return structure.provenance(u["line"], reg, fenced=structure.in_fence(u["start"], sp))

inv = []
for n in TARGETS:
    a = structure.get_article(n, text)
    sp = structure.fence_spans(a, text)
    for u in structure.iter_units(a, text):
        if u["kind"] != "letter":
            continue
        src, af = structure.provenance(u["line"], reg,
                                       fenced=structure.in_fence(u["start"], sp))
        inv.append({"article": n, "comma": u["comma"], "letter": u["letter"],
                    "new": src == "D.Lgs. 30/2026", "source": src,
                    "applicable_from": af, "chars": u["end"] - u["start"]})
inv = pd.DataFrame(inv)
print("citable lettered units across the five articles:", len(inv))
inv.groupby(["article", "new"]).size().unstack(fill_value=0).rename(
    columns={False: "pre-existing", True: "new (D.Lgs. 30/2026)"})""")

co("""for n in TARGETS:
    sub = inv[inv.article == n]
    if sub.empty:
        print("Art. %s: no lettered units (comma-only article)\\n" % n); continue
    print("Art. %s  (%d letters)" % (n, len(sub)))
    for c in sub.comma.unique():
        s = sub[sub.comma == c]
        print("   comma %s: %s" % (c, ", ".join(
            "%s%s" % (r.letter, "*" if r.new else "") for r in s.itertuples())))
    print()
print("* = inserted or replaced by D.Lgs. 30/2026")""")

md("""## 5. Assertions on the amendments the brief names

The brief names Art. 18 additions by **concept** and Art. 21/23 by **letter**. Each
is checked in the form it was given — and in both cases the notebook reports the
identifier the document actually uses, rather than the one anyone assumed.""")

co("""a18 = structure.get_article("18", text)
units18 = {u["letter"]: u for u in structure.iter_units(a18, text) if u["kind"] == "letter"}
defs = {}
for L, u in units18.items():
    body = structure.strip_apparatus(u["line"])
    m = re.match(r'^[^)]+\\)\\s*["\\u201c\\u2018\\u0027]?([^"\\u201d:]+)', body)
    defs[L] = (m.group(1) if m else body[:60]).strip(' "\\u201c\\u201d\\u2018\\u2019')

EXPECTED_TERMS = ["asserzione ambientale", "asserzione ambientale generica",
                  "etichetta di sostenibilità",
                  "eccellenza riconosciuta delle prestazioni ambientali", "durabilità"]
rows = []
for term in EXPECTED_TERMS:
    hit = [L for L, d in defs.items() if d.lower() == term.lower()]
    assert hit, "Art. 18 definition not found for %r" % term
    L = hit[0]
    src, af = prov("18", units18[L])
    rows.append({"brief calls it": term, "document puts it at": "Art. 18, c. 1, lett. %s" % L,
                 "source": src, "applicable_from": af})
print("all five concepts located\\n")
pd.DataFrame(rows)""")

co("""def unit(article, comma, letter):
    a = structure.get_article(article, text)
    for u in structure.iter_units(a, text):
        if u["kind"] == "letter" and u["comma"] == comma and u["letter"] == letter:
            return u
    return None

# Art. 21 -- brief says "new letters including b-ter"
u = unit("21", "2", "b-ter")
assert u is not None, "Art. 21 comma 2 lett. b-ter not found"
src, af = prov("21", u)
assert src == "D.Lgs. 30/2026", src
print("Art. 21, comma 2, lett. b-ter   PRESENT   %s   from %s" % (src, af))
print("   ^ the brief does not say b-ter sits in comma 2. Art. 21 has a lett. b)")
print("     in comma 1 as well, so the comma is load-bearing in the citation.\\n")

# Art. 23 -- brief says "new letters including b-bis, d-bis, d-ter"
for L in ["b-bis", "d-bis", "d-ter"]:
    u = unit("23", "1", L)
    assert u is not None, "Art. 23 lett. %s not found" % L
    src, af = prov("23", u)
    assert src == "D.Lgs. 30/2026", (L, src)
    print("Art. 23, comma 1, lett. %-6s  PRESENT   %s   from %s" % (L, src, af))""")

co("""# Art. 22 -- brief says "new comma", without numbering it
a22 = structure.get_article("22", text)
sp22 = structure.fence_spans(a22, text)
new_commas = []
for u in structure.iter_units(a22, text):
    if u["kind"] != "comma":
        continue
    src, af = structure.provenance(u["line"], reg, fenced=structure.in_fence(u["start"], sp22))
    if src == "D.Lgs. 30/2026":
        new_commas.append((u["comma"], src, af, structure.strip_apparatus(u["line"])))
assert new_commas, "no amended comma found in Art. 22"
for c, s, af, body in new_commas:
    print("Art. 22, comma %s  ->  %s, from %s\\n" % (c, s, af))
    print("   " + body[:430])""")

md("""## 6. Amendments the brief does *not* name

This list matters: Phase 1 chunks whatever the article contains, so anything inserted
by the same decree and omitted from the brief would otherwise enter the index
unremarked.""")

co("""named = {("21", "b-ter"), ("23", "b-bis"), ("23", "d-bis"), ("23", "d-ter")}
extra = inv[(inv.new) & (inv.article.isin(["21", "23"]))]
extra = extra[~extra.apply(lambda r: (r.article, r.letter) in named, axis=1)]
print("amended letters in Art. 21/23 NOT named in the brief: %d\\n" % len(extra))
for r in extra.itertuples():
    body = structure.strip_apparatus(unit(r.article, r.comma, r.letter)["line"])
    print("Art. %s, comma %s, lett. %s" % (r.article, r.comma, r.letter))
    print("   " + body.split(") ", 1)[-1][:230])
    print()""")

md("""**The one to notice is Art. 23, comma 1, lett. d-quater** — offset-based neutrality
claims. That is precisely where the golden set's `offset_based_neutrality` claims
belong, and the brief's list of new Art. 23 letters stops at `d-ter`.""")

md("""## 7. Diff against the corpus currently in the repo

The repo's corpus is `src/knowledge/chunks/{ucpd,ecgt}.json` — 56 chunks of **EU
directive** text, with ECGT modelled as a standalone instrument.

A line-level diff would be meaningless: these are different instruments, in
different languages of enactment. The meaningful comparison is structural — what
each corpus can cite, and what changes about citation identity.""")

co("""kroot = os.path.abspath("../../src/knowledge/chunks")
old = []
for f in ["ucpd.json", "ecgt.json"]:
    with open(os.path.join(kroot, f)) as fh:
        old += json.load(fh)
old_ids = [c["id"] for c in old]
print("existing corpus: %d chunks  (UCPD_* %d, ECGT_* %d)" % (
    len(old), sum(i.startswith("UCPD") for i in old_ids),
    sum(i.startswith("ECGT") for i in old_ids)))

n_commas = sum(1 for n in TARGETS
               for u in structure.iter_units(structure.get_article(n, text), text)
               if u["kind"] == "comma")
print("consolidated corpus, Art. 18/20/21/22/23: %d lettered + %d comma-level units"
      % (len(inv), n_commas))""")

co("""pd.DataFrame([
 {"dimension": "instrument",
  "before": "Dir. 2005/29/EC + Dir. (EU) 2024/825, held separately",
  "after":  "D.Lgs. 206/2005 consolidated, as amended by D.Lgs. 30/2026"},
 {"dimension": "language of enactment",
  "before": "Italian translation of EU directives (not the enforceable text in IT)",
  "after":  "Italian statutory text actually binding on Italian traders"},
 {"dimension": "ECGT status",
  "before": "standalone instrument (ECGT_* chunk family)",
  "after":  "merged into host articles; visible only as ((...)) + marker (57)"},
 {"dimension": "blacklist citation",
  "before": "Annex I point n  (e.g. AnnexI_4_quater)",
  "after":  "Art. 23, comma 1, lett. x  (e.g. lett. d-quater)"},
 {"dimension": "general clause",
  "before": "UCPD Art. 5 / 6 / 7",
  "after":  "Codice del consumo Art. 20 / 21 / 22"},
 {"dimension": "definitions",
  "before": "UCPD Art. 2 + ECGT Art. 1 new letters o..w",
  "after":  "Art. 18 c.1 lett. a..n-duodecies (environmental terms at n-quater..n-novies)"},
 {"dimension": "temporal metadata",
  "before": "absent",
  "after":  "per-unit applicable_from, derived from the ((NN)) apparatus"},
 {"dimension": "blacklist size",
  "before": "31 Annex I points + 12 ECGT insertions",
  "after":  "%d lettered units in Art. 23 alone" % (inv.article == "23").sum()},
])""")

co("""# Where the old ECGT/UCPD chunks now live. Matched on defined term and fact
# pattern. PROVISIONAL -- a reading offered for review, not a verified mapping.
crosswalk = pd.DataFrame([
 ("ECGT_AnnexI_2_bis",    "23", "1", "b-bis",     "sustainability label with no certification scheme"),
 ("ECGT_AnnexI_4_bis",    "23", "1", "d-bis",     "generic env. claim, no recognised excellence"),
 ("ECGT_AnnexI_4_ter",    "23", "1", "d-ter",     "whole-product claim true of one aspect only"),
 ("ECGT_AnnexI_4_quater", "23", "1", "d-quater",  "offset-based neutrality claim"),
 ("ECGT_AnnexI_10_bis",   "23", "1", "l-bis",     "legal requirement presented as distinctive"),
 ("ECGT_Art1_NuoveDefinizioni_o", "18", "1", "n-quater",    "asserzione ambientale"),
 ("ECGT_Art1_NuoveDefinizioni_p", "18", "1", "n-quinquies", "asserzione ambientale generica"),
 ("ECGT_Art1_NuoveDefinizioni_q", "18", "1", "n-sexies",    "etichetta di sostenibilità"),
 ("ECGT_Art1_NuoveDefinizioni_r", "18", "1", "n-septies",   "sistema di certificazione"),
 ("ECGT_Art1_NuoveDefinizioni_s", "18", "1", "n-octies",    "eccellenza riconosciuta"),
 ("UCPD_AnnexI_2",  "23", "1", "b",  "trust/quality mark without authorisation"),
 ("UCPD_AnnexI_4",  "23", "1", "d",  "false claim of approval by a public/private body"),
 ("UCPD_AnnexI_17", "23", "1", "s",  "false claim that a product cures illness"),
 ("UCPD_Art5", "20", None, None, "divieto delle pratiche commerciali scorrette"),
 ("UCPD_Art6", "21", None, None, "azioni ingannevoli (general clause)"),
 ("UCPD_Art7", "22", None, None, "omissioni ingannevoli (general clause)"),
], columns=["old_chunk_id", "article", "comma", "letter", "basis"])

for r in crosswalk.itertuples():
    if r.letter:
        assert unit(r.article, r.comma, r.letter) is not None, (r.old_chunk_id, r.letter)
    else:
        structure.get_article(r.article, text)
print("every crosswalk target exists in the consolidated corpus\\n")
crosswalk""")

co("""# How much of the golden set this provisional crosswalk would cover
sys.path.insert(0, os.path.abspath("../.."))
from src.adapters.legal_mapping import assign_legal_chunk_id
import collections
g = json.load(open("../../golden/golden_set_coop_ucpd_250.json"))
claims = [c for p in g for c in (p.get("extracted_claims") or [])]
dist = collections.Counter(assign_legal_chunk_id(c)["chunk_id"] for c in claims)
known = set(crosswalk.old_chunk_id)
cov = pd.DataFrame([
    {"old_chunk_id": k or "(none / abstain)", "claims": v,
     "in crosswalk": (k in known) if k else "n/a"}
    for k, v in dist.most_common()])
mapped = sum(v for k, v in dist.items() if k in known)
print("golden-set claims: %d" % len(claims))
print("covered by the provisional crosswalk: %d (%.1f%%)" % (mapped, 100.0*mapped/len(claims)))
print("gold says abstain: %d (%.1f%%)" % (dist[None], 100.0*dist[None]/len(claims)))
cov""")

md("""## 8. Gate summary

**Verified against the PDF**

* `Vigente al : 19-9-2026` present; the builder refuses to run without it.
* Art. 18, 20, 21, 22, 23 all present.
* Extraction integrity asserted — **10 units were being silently truncated** at page
  boundaries before the fix, Art. 23 lett. d-bis among them.
* Every amendment the brief names exists, carrying `((57))` → **D.Lgs. 30/2026**,
  applicable from **2026-09-27**. Decree and date read out of the document.
* Italian lettering parses cleanly; corpus has no page furniture to strip.

**Discrepancies and cautions**

1. **`lett. b-ter` is in Art. 21 *comma 2*, not comma 1.** Art. 21 has a `lett. b)`
   in each comma, so a citation without the comma is ambiguous. `citation_it` must
   carry it.
2. **The brief's list of new letters is partial.** §6 lists the rest — notably
   **Art. 23 lett. d-quater** (offset-based neutrality), which is exactly where the
   golden set's `offset_based_neutrality` claims belong.
3. **Art. 18's new definitions are at `n-quater … n-duodecies`**, not at letters
   mirroring the EU directive's `o…w`. Any mapping assuming EU letter identity is wrong.
4. **Art. 20 is fenced as amended but carries no marker**, so its `applicable_from`
   is `None` rather than a guessed date.
5. **`chunk_type` will not partition by article.** Art. 21 comma 1's letters are
   *elements of a test* (a claim misleads "as to" one of them), whereas Art. 23's
   letters are self-contained per-se prohibitions. Both are "letters"; they must not
   be chunked or judged alike. This is the main open design question for Phase 1.
6. **The §7 crosswalk is provisional** — a reading, not a verified mapping, and the
   piece that decides whether any golden-set number means anything.""")

bad = nbbuild.build(C, os.path.join(RAG, "notebooks", "00_corpus_verification.ipynb"),
                    os.path.join(RAG, "notebooks"))
print("CELL ERRORS:", bad if bad else "none")
