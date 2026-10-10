# Methodology

> **Research prototype.** Every claim on this dashboard was detected automatically. A flagged claim is not a legal finding that the firm has broken any law.

## What this dashboard shows

For each firm, the dashboard lists the **environmental and sustainability claims** found on its public website. It also shows how many of those claims were present at each crawl and which categories they fall into. The aim is to make greenwashing-relevant wording visible and trackable over time now that the EU's new rules on environmental claims apply.

## Legal background

**The Unfair Commercial Practices Directive (UCPD, Directive 2005/29/EC)** is the EU's general law against unfair business-to-consumer practices. It has four main parts:
- a general ban on unfair practices (Art. 5)
- misleading actions (Art. 6)
- misleading omissions (Art. 7)
- a blacklist of practices considered unfair in all circumstances (Annex I)

**Directive (EU) 2024/825, "Empowering Consumers for the Green Transition" (ECGT)**, amends the UCPD to target greenwashing. It:
- adds definitions such as *environmental claim*, *generic environmental claim* and *sustainability label*
- adds new misleading-action grounds, for example unsubstantiated claims about future environmental performance
- adds new blacklist items, including:
  - generic environmental claims without recognised excellent performance
  - claims about a whole product when they only apply to part of it
  - neutral or reduced-impact claims based on offsetting
  - sustainability labels not based on a certification scheme or set up by public authorities
  - presenting legal requirements as a distinctive feature

ECGT **applies from 27 September 2026**. The proposed Green Claims Directive was withdrawn in June 2025, so the UCPD as amended by ECGT is the operative EU framework.

**Italy** transposed ECGT with **D.Lgs. 20 febbraio 2026, n. 30**, which amends the **Codice del Consumo** (D.Lgs. 206/2005). The corresponding articles are:

| UCPD (EU) | Codice del Consumo (IT) | content |
|---|---|---|
| Art. 2 | Art. 18 | definitions |
| Art. 6 | Art. 21 | misleading actions |
| Art. 7 | Art. 22 | misleading omissions |
| Annex I | Art. 23 | blacklist |

Each claim's legal reference is shown in both numberings, for example *"UCPD Annex I 4a / Cod. Cons. Art. 23"*. References are indicative mappings of the claim's category to a provision. They are not an assessment of whether the specific claim is unlawful.

## Data collection

- **Firms:** <!-- TODO: how the firm list was chosen and how many firms -->
- **Scraping:** <!-- TODO: which pages are crawled (whole site vs sustainability sections), crawl depth, tooling, robots.txt policy -->
- **Cadence:** each firm's website is crawled **once a week**. The first crawls took place after ECGT began to apply, so the timeline shows changes *since* 27 Sept 2026, not a before/after comparison.
- **Crawl status:** a crawl can be `ok`, `partial` or `failed`. Failed crawls are marked on the timeline rather than counted as zero claims.

## Claim detection

<!-- TODO: describe the detector (model, prompting / RAG over the UCPD + ECGT corpus, how candidate sentences are extracted from pages) -->

Each detected claim gets a **category**, a **scope status** and a **confidence level**.

**Scope status**
- **IN_SCOPE:** an environmental claim covered by the rules above.
- **NEEDS_VERIFICATION:** a likely claim that needs a human check, for example wording that sits on a boundary. These are shown with a dashed border.

Claims judged out of scope (for example nutrition or health claims, or mandatory organic control-body codes) are discarded before they reach the dashboard.

**Confidence:** *high*, *medium* or *low*. This is how sure the detector is about the claim and its category. **It is not a measure of legal severity.** A low-confidence claim may still be serious, and a high-confidence one may be harmless.

## Categories

The taxonomy is shared with the project's product-label gold sets.

| category | meaning | example |
|---|---|---|
| `generic_green` | Broad environmental wording with no specific substantiation | «eco-friendly», «sostenibile», «green» |
| `certification` | Reference to a certification or sustainability label | organic logo, named eco-label |
| `recycled_recyclable` | Claims about recycled content or recyclability, including bio-based packaging | «packaging 100% riciclato» |
| `vague_supply_chain` | Unspecific claims about sourcing or production practices | «benessere animale garantito» with no named scheme |
| `named_endorsement` | Endorsement by a named organisation | a named association's seal |
| `brand_eco_slogan` | Eco wording built into a brand line or slogan | a "green" product-line name |
| `risk_reduction` | Claims of reduced environmental impact or risk | «a ridotto impatto ambientale» |

<!-- TODO: add any website-specific categories (e.g. environmental comparison claims) and keep this table in sync with the data file's "categories" list -->

## How to read the firm page

- **Detection confidence counters (H/M/L):** the number of claims present in the latest crawl at each confidence level.
- **Claim strip:** every claim ever seen on the site. Claims no longer found in the latest crawl are greyed out and marked *removed*, with the date they were last seen. Click a card for its source page, surrounding text and legal reference.
- **Timeline:** the number of claims found at each crawl, after applying the current filters.
- **Category breakdown:** present claims in the latest crawl, grouped by category and stacked by confidence.

Claim text is shown in the original Italian and not translated, because the exact wording is what matters.

## Limitations

- **Automated detection makes mistakes.** It produces false positives and false negatives, and claims are not yet human-reviewed.
- **Only website text is analysed.** Images, PDFs, product labels and ads are not covered unless stated above.
- **Claims are matched across crawls by their normalized text.** A reworded claim appears as one claim removed and a new one added.
- **The timeline starts after ECGT began to apply,** so it cannot show how firms prepared for the new rules.
- **Legal references are indicative,** based on the EU directive text and its Italian counterpart. They are not legal advice.
- **The public demo uses synthetic data.** <!-- update when real data is loaded -->

## Sources

- Directive 2005/29/EC (UCPD) and Directive (EU) 2024/825 (ECGT), Official Journal of the EU.
- D.Lgs. 20 febbraio 2026, n. 30: https://www.normattiva.it/eli/id/2026/03/09/26G00047/ORIGINAL
- Commission withdrawal of the Green Claims Directive proposal, June 2025.
