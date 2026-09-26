# GOLDEN_SET_CURATION_PROMPT.md

Prompt for a Claude agent with file and Python tools. It picks 100 products from the
product files it receives and writes gold ECGT labels for every claim in them.

Attach the product files (JSON arrays of product records, one or more retailers) and paste
the prompt below.

---

## Prompt

```
You are building a GOLD evaluation set for a detector of claims under the EU ECGT rules
(Directive 2024/825) in Italian grocery and personal-care product listings. The set will be
used to score models, so every label must be defensible and every claim must be copied
exactly from the source.

INPUT: the product files attached to this conversation. Each is a JSON array of product
records. Retailers may use different field names; map them yourself and note the mapping.

GOAL: pick exactly 100 products and label every claim in them.

═══ STEP 1 - INVENTORY (use Python, not reading by eye) ═══
For each file report: record count, field names, records with no marketing text (empty
description/features/producer_info), product categories present, and duplicate products
(same EAN, or same brand + name) within and across files.
IGNORE any existing annotation fields (golden_bucket, extracted_claims, risk_level,
matched_signals, labels). Never copy labels from them.

═══ STEP 2 - QUOTAS ═══
Per file: proportional to its usable record count, minimum 10, maximum 40 of the 100.
Adjust so the total is exactly 100.

Buckets across the whole set:
  hard_yes    35  at least one claim that is clearly IN_SCOPE or NEEDS_VERIFICATION
  in_between  35  the decisive claim sits on a rule boundary (see GRAY ZONES)
  hard_no     30  no ECGT claim at all: at least 20 of these carry DISCARDED decoy claims
                  (health, performance, heritage, tests); the rest have no claims

Diversity limits:
  - at most 3 products per brand
  - at least 5 product categories per file where the file has them
  - at least 25 personal-care / household products and at least 40 food and drink products
    overall, if the files allow it
  - no duplicates: one EAN or brand+name once in the whole set
  - label coverage: across the set, at least 60 IN_SCOPE claims, 40 NEEDS_VERIFICATION
    claims and 60 DISCARDED claims
  - trigger coverage: every trigger in the table below appears in at least 3 products
If a limit cannot be met from the files, say so in the report; do not fake it.

═══ STEP 3 - CANDIDATES ═══
Use a keyword pre-screen in Python only to FIND candidates (environment, plastic, riciclat,
naturale, bio, vegan, sostenibil, pianeta, CO2, agricoltor, allevament, tracciabil,
approvat, certificat, rischio, and decoy words such as antiossidante, testat, tradizion,
dal 18/19). Sample with random.seed(42) inside each file x bucket cell.
Then READ every candidate yourself. The bucket and labels come from your reading, never
from keyword hits. Replace a candidate if its bucket turns out wrong.

═══ STEP 4 - EXTRACT CLAIMS (for each selected product) ═══
A claim is a statement that could influence a purchase. Take claims from every marketing
field, including certifications and life_style.
- Copy VERBATIM: each claim_text must be an exact substring of its source field.
- Cut only at a sentence end, a line break or a bullet; never at a comma. Drop leading "-" "•".
- Footnotes: if a claim carries a marker (*, **, ^) and the note body appears elsewhere,
  join as  <claim> ... <note body>  and put the body in `footnote` too.
- Same text in two fields: once, from the most specific field.
- Do NOT extract: sales names, weights, piece counts, ingredient lists, storage or cooking
  instructions, mandatory allergen warnings, packaging material codes («PAP 21», «C/PAP 84»,
  «7 - ...»), the `recycling` field, «Raccolta differenziata», «Verifica le disposizioni del
  tuo Comune», educational prose, usage directions.
- DO extract out-of-scope marketing claims too: they are the DISCARDED negatives.

═══ STEP 5 - LABEL EACH CLAIM ═══
List every trigger that applies, then derive the label:
  only out_of_scope           -> DISCARDED
  any group A trigger         -> IN_SCOPE (even if group B also applies)
  otherwise (group B only)    -> NEEDS_VERIFICATION
  defined_term cancels undefined_natural; out_of_scope never beats A or B.

GROUP A - problem as written
  generic_green       eco, green, sostenibile, amico dell'ambiente, per il pianeta, ridurre
                      l'impatto  «brik-eco sostenibile» «Il nostro impegno per te e per il pianeta»
  undefined_natural   naturale / di origine naturale / % naturale, undefined
                      «100% Naturale» «94% Ingredienti di origine naturale»
  climate_neutral     carbon/climate neutral, zero emissions, offsets, EVEN IF explained
                      «CO2 100% prodotto a impatto climatico neutralizzato»
  vague_comparison    reduction with no comparator or only «il pack precedente»
                      «75% In meno di plastica» «-17% Plastica rispetto al pack precedente»
  brand_eco_slogan    «Coop per l'ambiente» «Vivi Verde» «Gallo green» «Il gusto di amare il pianeta»
  vague_supply_chain  «Agricoltori selezionati» «Tracciabilità e sicurezza» «Agricoltura sostenibile»
GROUP B - specific, needs checking
  recycled_recyclable «Etichetta in carta riciclata» «Qualità Pampers in cartoni 100% riciclati»
  biodegradable       «Formula vegana & biodegradabile^ ... 99,9% formula biodegradabile»
  certification       bio/organic, FSC, Fairtrade, Ecolabel, unnamed "certificato"
                      «Le migliori pesche gialle bio»
  named_endorsement   «Approvata da A.I.Nut. - Associazione Italiana Nutrizionisti»
  vegan               «VEGANO» «formula vegana** ... Nessun ingrediente o derivato di origine animale»
  farming_practice    «Le nostre mucche vengono nutrite in modo tradizionale, con erba fresca, fieno e piante di campo. E si sente!»
  defined_term        «96% Natural origin* ... water and naturally sourced ingredients with limited processing»
  risk_reduction      «aiutano a ridurre il rischio di irritazione della pelle»
  named_comparison    «rispetto alle precedenti confezioni Beretta»
  pollutant_free      «Senza microplastiche»
OUT OF SCOPE (DISCARDED)
  health/nutrition «Speziato e Antiossidante» «fonte di fibre» «Alta digeribilità»
  performance «Pulizia profonda» «Protegge dagli agenti esterni» «limita la formazione di cattivi odori»
  tests «Clinicamente testate» «ipoallergenico»
  heritage «Dal 1820 la famiglia Grondona garantisce» «le inimitabili ricette di famiglia»
  patents «Brevetto internazionale»
  also: country of origin, DOP/IGP, «senza conservanti», «senza parabeni», sales rank

GRAY ZONES (the in_between bucket is built from these)
  - generic word + specific fact in one line («Eco pack 100% riciclabile»)
  - natural claim with vs. without a defining footnote
  - farming practice vs. heritage («nutrite in modo tradizionale» vs «ricetta del 1820»)
  - named endorsement vs. generic «approvato dai dermatologi»
  - risk_reduction vs. plain performance («riduce il rischio di irritazioni» vs «lenisce»)
  - vague vs. named comparator
  - organic/eco words inside a health or heritage sentence
  - «senza X» where X is a pollutant vs. an additive
  - slogans split across lines («Viva la Natura! / Per un futuro migliore»)
If a claim fits no rule cleanly, pick the closest label, set confidence "low", and explain
in `note`. Do not invent new labels.

═══ STEP 6 - OUTPUT ═══
Write golden_set_ecgt_100.json: a JSON array of 100 objects:
{"product_id": "...", "ean": "...", "source_file": "...", "source_index": 0,
 "retailer": "...", "category": "...", "brand": "...", "name": "...",
 "golden_bucket": "hard_yes|in_between|hard_no",
 "bucket_reason": "<one sentence>",
 "gray_zone": null | "<which gray zone>",
 "claims": [{"claim_text": "...", "source_field": "...", "footnote": null | "...",
             "triggers": ["..."], "label": "IN_SCOPE|NEEDS_VERIFICATION|DISCARDED",
             "confidence": "high|low", "note": null | "..."}]}

Write golden_set_ecgt_100_README.md with: the field mapping per retailer, the counts table
(file x bucket, label totals, trigger coverage, categories, brands), unmet quotas, and a
"Judgment calls" list of every low-confidence claim with your reasoning.

═══ STEP 7 - VALIDATE WITH PYTHON BEFORE FINISHING ═══
- exactly 100 products; bucket and per-file quotas met or reported
- every claim_text (and each part around " ... ") is an exact substring of the record
- every label equals the label derived from its triggers
- hard_no products have no IN_SCOPE or NEEDS_VERIFICATION claim; hard_yes and in_between
  have at least one
- no duplicate EAN or brand+name; brand cap respected
Fix every failure and rerun until clean. Report the final check output.
```
