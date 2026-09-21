# -*- coding: utf-8 -*-
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); RAG = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import nbbuild

C=[]; md=lambda s: C.append(("md",s)); co=lambda s: C.append(("code",s))

md("""# Phase 1 — Chunking at the citable unit

**What this corpus is for.** The component detects claims that fall *in scope of*
D.Lgs. 30/2026, so the prevalence of such claims can be compared before and after
27 September 2026. That purpose sets the design:

* **`regime` is the treatment variable.** A provision is either new (binding from
  2026-09-27) or pre-existing. Claims matching pre-existing text were *already*
  unlawful — they are the control arm, and should not move much across the date.
  Claims matching new text are the treated arm. Getting one provision into the
  wrong arm biases the headline result, so `regime` is derived from the document's
  own amendment apparatus and asserted, never typed in.
* **A chunk must be legally self-sufficient**, or the LLM cannot reason with it.
* **Exact letter-level precision matters less than consistency and coverage.**
  A claim routed to Art. 21 c.1 lett. b) instead of Art. 23 lett. d-ter is still
  counted as in-scope; a claim missed entirely is lost from the study.""")

co("""import os, sys, json, collections, re
sys.path.insert(0, os.path.abspath(".."))
import pandas as pd
from ucpd_rag import extract, structure, chunks as K

pd.set_option("display.max_colwidth", 200); pd.set_option("display.width", 220)
text = extract.load()
cs = K.build(text)
problems = K.verify(cs, text)
print("chunks: %d" % len(cs))
print("verification problems:", problems or "none")
K.save(cs)""")

md("""## 1. Shape of the corpus

Scope is Art. 18–23. **Art. 19 is included** and was not in the original brief: its
comma 3 is the *lex specialis* rule — where EU rules govern specific aspects, they
prevail over this title. Food health and nutrition claims are governed by
Reg. (CE) 1924/2006, so for a large slice of grocery claims Art. 19 is the rule
that says this title may be displaced. A detector that never surfaces it will
over-report in-scope claims.

Excluded, as decisions: **Art. 24–26** (aggressive practices — a claim string from
product copy cannot realise harassment or coercion) and **Art. 45/48/49/65-ter**
(touched by the same decree, but pre-contractual information duties rather than
claims).""")

co("""df = pd.DataFrame(cs)
piv = df.pivot_table(index=["article", "chunk_type"], columns="regime",
                     values="chunk_id", aggfunc="count", fill_value=0)
piv["total"] = piv.sum(axis=1)
piv""")

co("""print("chunk_type totals")
print(df.chunk_type.value_counts().to_string())
print()
print("regime totals")
print(df.regime.value_counts().to_string())
print()
print("length of `text` (chars): min %d / median %d / max %d"
      % (df.text.str.len().min(), df.text.str.len().median(), df.text.str.len().max()))""")

md("""## 2. The treatment set

These are the provisions D.Lgs. 30/2026 introduces or replaces. Everything else in
the corpus is control. This list is the experiment: if the law bites, claims
matching *these* should thin out after 2026-09-27 while control claims hold steady.""")

co("""tre = df[df.regime == "new-2026"][["citation_it", "chunk_type", "applicable_from"]]
print("provisions in the treated arm: %d\\n" % len(tre))
tre.reset_index(drop=True)""")

co("""# every treated provision must carry the same date, or the arm is incoherent
assert set(df[df.regime == "new-2026"].applicable_from) == {"2026-09-27"}
assert set(df[df.regime == "new-2026"].source) == {"D.Lgs. 30/2026"}
print("treated arm is coherent: one decree, one date")
print()
print("control arm sources:")
print(df[df.regime == "pre-existing"].source.value_counts().to_string())""")

md("""## 3. Awkward cases — before / after

The splitter's first version ended each unit at its **own line**. Three units carry
nested numbered sub-points on separate lines, and all three were silently gutted.
`before` below is that naive behaviour, reproduced rather than described.""")

co("""def naive_unit(article, letter):
    \"\"\"Reproduces the first-line-only split, for comparison.\"\"\"
    a = structure.get_article(article, text)
    body = text[a["body_start"]:a["end"]]
    for m in re.finditer(r"^.+$", body, re.M):
        ln = m.group(0)
        if ln.lstrip("(").startswith(letter + ")"):
            return structure.strip_apparatus(ln)
    return None

by = {c["chunk_id"]: c for c in cs}
cases = [
    ("18", "c-bis",     "letter with nested numbered sub-points"),
    ("18", "n-septies", "nested sub-points AND a cross-reference"),
    ("23", "f",         "blacklist letter with nested sub-points"),
]
rows = []
for art, L, why in cases:
    c = by[K._chunk_id(art, "1", L)]
    b = naive_unit(art, L)
    rows.append({"unit": c["citation_it"], "case": why,
                 "before (chars)": len(b), "after (chars)": len(c["text"]),
                 "regime before": "pre-existing" if "((57))" not in b else "new-2026",
                 "regime after": c["regime"]})
pd.DataFrame(rows)""")

co("""for art, L, why in cases:
    c = by[K._chunk_id(art, "1", L)]
    print("=" * 78)
    print("%s   (%s)" % (c["citation_it"], why))
    print("=" * 78)
    print("BEFORE (%d chars):" % len(naive_unit(art, L)))
    print("   " + naive_unit(art, L))
    print()
    print("AFTER (%d chars):" % len(c["text"]))
    for ln in c["text"].split("\\n"):
        print("   " + ln)
    print()""")

md("""**Art. 18 lett. c-bis** collapsed to the 14 characters `c-bis) "beni":` — the whole
definition gone, leaving a chunk that still embeds and still retrieves.

**Art. 18 lett. n-septies** is worse than truncation. Its `((57))` marker sits at the
end of the *last* sub-point, so cutting at the first line lost the marker too and
filed a provision **inserted by D.Lgs. 30/2026 into the control arm** — a silent
treatment misclassification, exactly the error that would bias a before/after study
and never show up as a crash.

Fixing this moved the treated arm from 24 provisions to **26**.""")

md("""### A fourth case: the letter that is not a rule

Art. 21 comma 1's letters are not self-contained prohibitions. They are *elements*
of one test — a practice misleads "as to" one of them — unlike Art. 23's letters,
which are per-se fact patterns. Retrieved bare, `lett. b)` is a noun phrase with no
legal operator in it at all.

`context_text` carries the comma's chapeau with every letter, and `embed_text`
(chapeau + text) is what gets embedded. `text` stays verbatim and alone, because it
is what a citation displays.""")

co("""c = by["cdc-art21-c1-lett-b"]
print("text (verbatim, what a citation shows) — note it is a fragment:\\n")
print("   " + c["text"][:300])
print("\\n\\ncontext_text (the chapeau it belongs to):\\n")
print("   " + c["context_text"][:340])
print("\\n\\nembed_text (what is actually indexed) — now a complete rule:\\n")
print("   " + c["embed_text"][:520])""")

co("""# how many chunks would be fragments without their chapeau?
frag = df[(df.context_text.str.len() > 0)]
print("chunks carrying a chapeau: %d of %d" % (len(frag), len(df)))
print()
print("mean embed_text / text length ratio for those: %.1fx"
      % (frag.embed_text.str.len() / frag.text.str.len()).mean())""")

md("""### A fifth: a long general-clause comma

Art. 22 comma 5-ter is the single new Art. 22 provision — comparison services and
environmental characteristics. It is one long sentence and is *not* split: breaking
a materiality test into sentences would produce fragments that each retrieve on
their own and none of which state the rule.""")

co("""c = by["cdc-art22-c5-ter"]
print(c["citation_it"], "|", c["regime"], "|", len(c["text"]), "chars")
print()
print(c["text"])""")

md("""## 4. Definitional dependencies

The reason a blacklist letter cannot be retrieved alone. Art. 23 lett. d-bis reads:

> *formulare un'**asserzione ambientale generica** per la quale il professionista non
> è in grado di dimostrare l'**eccellenza riconosciuta delle prestazioni ambientali**
> pertinenti all'asserzione*

Both bolded phrases are terms of art defined in Art. 18. Without them the rule is
unusable — an LLM asked "does this claim match?" has nothing to match against.
`depends_on` is resolved by finding defined terms verbatim in the rule's text,
longest term first so *asserzione ambientale generica* claims the span before
*asserzione ambientale* can.""")

co("""dep = df[df.depends_on.str.len() > 0]
print("chunks with at least one definitional dependency: %d" % len(dep))
print("most depended-upon definitions:\\n")
cnt = collections.Counter(d for ds in df.depends_on for d in ds)
pd.DataFrame([{"definition": by[k]["citation_it"],
               "term": by[k]["defined_term"], "depended on by": v}
              for k, v in cnt.most_common(10)])""")

co("""for cid in ["cdc-art23-c1-lett-b-bis", "cdc-art23-c1-lett-d-bis",
            "cdc-art23-c1-lett-d-ter", "cdc-art23-c1-lett-d-quater"]:
    c = by[cid]
    print("%s   [%s]" % (c["citation_it"], c["regime"]))
    print("   " + c["text"][:210])
    for d in c["depends_on"]:
        print("      needs -> %-42s (%s)" % (by[d]["defined_term"], by[d]["citation_it"]))
    print()""")

md("""## 5. Known defect in the source

Carried, not repaired.""")

co("""bad = df[df.source_defect.notna()]
for r in bad.itertuples():
    print("%s  ->  %s" % (r.citation_it, r.source_defect))
    print("   verbatim: " + r.text[:110])
print()
print("pdftotext and pdfplumber agree on this rendering, so it is in the PDF.")
print("`text` stays verbatim; `defined_term` is null rather than guessed.")
print("No impact on the study: 'microimpresa' scopes B2B protection, not product claims.")""")

md("""## 6. Full chunk table

Everything in the index, readable.""")

co("""view = df[["chunk_id", "citation_it", "chunk_type", "regime", "defined_term"]].copy()
view["text (truncated)"] = df.text.str.replace("\\n", " ", regex=False).str.slice(0, 115)
view["deps"] = df.depends_on.str.len()
with pd.option_context("display.max_rows", 200, "display.max_colwidth", 118):
    display(view.set_index("chunk_id"))""")

md("""## 7. Self-sufficiency check

A chunk that mentions a defined term it does not link, or that is too short to state
a rule, is a chunk the LLM will misread. Both are asserted here rather than eyeballed.""")

co("""short = df[(df.chunk_type != "definition") & (df.embed_text.str.len() < 120)]
print("operative chunks under 120 chars after adding context:", len(short))
if len(short):
    print(short[["citation_it", "embed_text"]].to_string())

terms = {c["defined_term"].lower(): c["chunk_id"] for c in cs if c.get("defined_term")}
unlinked = []
for c in cs:
    if c["chunk_type"] == "definition":
        continue
    for t_, cid in terms.items():
        if t_ in c["embed_text"].lower() and cid not in c["depends_on"]:
            covered = any(t_ in by[d]["defined_term"].lower() for d in c["depends_on"])
            if not covered:
                unlinked.append((c["chunk_id"], t_))
print("\\nunlinked defined-term mentions:", len(unlinked))
for u in unlinked[:10]:
    print("   ", u)""")

co("""# citation identity must be unique -- Art. 21 carries a lett. b) in both commas
ids = collections.Counter((c["article"], c["comma"], c["letter"]) for c in cs)
assert not [k for k, v in ids.items() if v > 1], "ambiguous citation identity"
print("citation identity unique across all %d chunks" % len(cs))
both = [c["citation_it"] for c in cs if c["article"] == "21" and c["letter"] == "b"]
print("\\nthe reason the comma is load-bearing:")
for b in both:
    print("   " + b)""")

md("""## 8. Gate summary

**106 chunks** over Art. 18–23: 25 definitions, 7 scope-limit, 31 general-clause,
39 blacklist. Verification (char_span reproduces text, unique ids, no dangling
dependencies, coherent treated arm) passes with no problems.

**The treated arm is 26 provisions, not 24.** Two were misfiled as pre-existing
because their amendment marker sits at the end of a nested sub-point that the first
splitter discarded (Art. 18 lett. c-bis and lett. n-septies). That is the failure
mode worth remembering: it produced no error, no empty field and no crash — just a
quietly wrong control/treatment split, which is precisely what a before/after study
cannot survive.

**Decisions taken, open to reversal**

1. **Art. 19 added** to scope, as `scope-limit`. It is the rule that says this title
   may be displaced by sector-specific EU law — load-bearing for food health and
   nutrition claims.
2. **`scope-limit` added** to Appendix B's `chunk_type` enum. Art. 19 is neither
   definition, blacklist nor general clause, and should surface *alongside* a match
   to qualify it, never as the primary answer.
3. **Sub-points are not separate chunks.** They are parts of their letter's fact
   pattern, not independently citable.
4. **Chapeaux are carried, not merged.** `text` stays verbatim and citable;
   `embed_text` = chapeau + text is what gets indexed.
5. **Art. 24–26 and Art. 45/48/49/65-ter excluded**, for the reasons in §1.

**Next**, once these chunks look right: embed `embed_text`, and check whether
retrieval surfaces the correct *provision family* for a claim — measured as
in-scope / not-in-scope, which is what the study actually needs, rather than
exact-letter top-1.""")

bad = nbbuild.build(C, os.path.join(RAG,"notebooks","01_chunking.ipynb"),
                    os.path.join(RAG,"notebooks"))
print("CELL ERRORS:", bad if bad else "none")
