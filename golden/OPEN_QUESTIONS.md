# OPEN_QUESTIONS.md — contradictions in the source remarks

Raised at Phase 1. **Not resolved here.** Each has a recommendation and the consequence of each option. Nothing in the golden file has been changed, and the Phase 2 audit will mark every affected claim **UNCERTAIN** rather than picking a side.

Four questions. Three were anticipated in the brief; §4 surfaced during the seed reproduction run.

---

## 1. Recycled content — ✅ **RESOLVED 2026-09-20**

> **Decision: the stated-basis test.** Search the whole product description for a statement of the claim's basis — calculation method, comparator, scope, or data source. Basis stated → **NEEDS_VERIFICATION**. Only a link (*Scopri di più sul sito…*) → **IN_SCOPE**. Nothing → **IN_SCOPE**.
>
> **Not** a test for a footnote marker: that tests whether the annotator captured the qualifier, not whether the trader provided one. Verified — in 1 of 19 cases (`588549`) the basis was in the description and had not been attached to the claim.
>
> **Outcome on the 19 recycled-content claims: 2 → NEEDS_VERIFICATION (`588549`, `608812`), 17 → IN_SCOPE.**
> **Seeds superseded, knowingly:** V3 *Etichetta in carta riciclata* and V10 *Qualità Pampers in cartoni 100% riciclati* move from NEEDS_VERIFICATION to IN_SCOPE. S31 *Bottiglia con il 100% di plastica riciclata* is reproduced as adjudicated.
> Encoded as **T7** and the Step-4 stated-basis test in LABELING_GUIDE.md.

<details><summary>Original statement of the problem, kept for the record</summary>

### The contradiction

### The contradiction

| Seed | Adjudicated | Quantified? | Footnote marker? | Component named? |
|---|---|---|---|---|
| Bottiglia con il 100% di plastica riciclata | **IN_SCOPE** | yes, 100% | no | yes — bottle |
| Etichetta in carta riciclata | **NEEDS_VERIFICATION** | no | no | yes — label |
| Qualità Pampers in cartoni 100% riciclati | **NEEDS_VERIFICATION** | yes, 100% | no | yes — carton |

Quantification does not separate them. Footnote presence does not separate them (none has one). Component specificity does not separate them. **No stated rule reproduces all three**, and this is why the seed run stands at 58/61 rather than 61/61.

### One correlate does separate them, and it is not a principle

All three NEEDS_VERIFICATION recycled-content seeds carry v1 `risk_level: LOW`. The IN_SCOPE one carries `risk_level: MEDIUM`. That holds across the whole census below. The most economical explanation is that the adjudication inherited the v1 risk annotation rather than applying a fresh distinction — which would mean one of the three is mislabelled, not that a distinction is hiding.

### The full census — 31 claims

**A. Recycled content (materiale riciclato) — 19 claims**

| product_id | claim_text (verbatim) | v1 risk |
|---|---|---|
| 676876 | 28% Plastica riciclata | MEDIUM |
| 588549 | 55% di plastica riciclata | MEDIUM |
| 45232 | 65% plastica riciclata | MEDIUM |
| 44721 | 65% Plastica riciclata | MEDIUM |
| 619225 | 65% Plastica riciclata | MEDIUM |
| 612212 | Bottiglia 50% plastica riciclata | MEDIUM |
| **37777** | **Bottiglia con il 100% di plastica riciclata** ← seed, IN_SCOPE | MEDIUM |
| 608812 | Bottiglia in plastica 100% riciclata\*\* ... Da filiera alimentare controllata italiana | LOW |
| **663509** | **Etichetta in carta riciclata** ← seed, NEEDS_VERIFICATION | LOW |
| **603892** | **Etichetta in carta riciclata** ← seed, NEEDS_VERIFICATION | LOW |
| 52121 | fabbricata con ben il 50% di PET Riciclato (RPET) | MEDIUM |
| 602008 | flacone 95% plastica riciclata | MEDIUM |
| 619902 | Packaging in carta riciclata | LOW |
| **617095** | **Qualità Pampers in cartoni 100% riciclati** ← seed, NEEDS_VERIFICATION | LOW |
| 37777 | Riciclami ancora | LOW |
| 52121 | Riciclando miglioriamo insieme il nostro ambiente! | MEDIUM |
| 144400 | utilizzando materiali riciclati e da fonti rinnovabili | MEDIUM |
| 47536 | Vaschetta con 70% di plastica riciclata | MEDIUM |
| 564356 | Zucchi per l'ambiente ... utilizza il 50% di plastica riciclata | LOW |

**B. Recyclability (riciclabile) — 12 claims.** A different assertion: about what can happen to the packaging after use, not what it is made of. Whether these move with A is part of the question.

| product_id | claim_text (verbatim) | v1 risk |
|---|---|---|
| 554553 | Astuccio in cartone 100% riciclabile | MEDIUM |
| 704720 | Attenti all'ambiente - confezione riciclabile | MEDIUM |
| 638347 | Attenti all'ambiente confezione riciclabile | MEDIUM |
| 554553 | Bustina salva-aroma in carta 100% riciclabile | MEDIUM |
| 47144 | Confezione riciclabile in ogni sua componente | MEDIUM |
| 41070 | Confezione senza plastica, riciclabile | LOW |
| 142195 | **Eco pack 100% riciclabile - Con meno plastica** ← seed, IN_SCOPE | MEDIUM |
| 418104 | Incarto riciclabile 100% plastica | MEDIUM |
| 145542 | Low Impact Pack: le nostre confezioni sono a basso impatto ambientale con plastica riciclabile e cartoncino certificato FSC | MEDIUM |
| 603896 | plastica riciclabile e cartoncino certificato FSC | LOW |
| 41908 | sostenibili fuori, grazie all'innovativa confezione "sbucciabile" e completamente riciclabile | MEDIUM |
| 610425 | Tubo e cartone in materiale 100% riciclabile | MEDIUM |

> Note: `Eco pack 100% riciclabile - Con meno plastica` is an IN_SCOPE seed, so group B already has an anchor pointing at IN_SCOPE.

### The options

| | Rule | Effect on the 19 content claims | Consequence |
|---|---|---|---|
| **(a)** | All recycled-content claims → **NEEDS_VERIFICATION**. Recycled percentage is a documentable fact; a reviewer can always ask for the mass-balance or supplier evidence. | 19 → NEEDS_VERIFICATION. Seed *Bottiglia con il 100% di plastica riciclata* flips out of IN_SCOPE. | Empties a recognisable greenwashing pattern out of the positive class and into the review queue. The detector would no longer be scored as wrong for failing to flag *65% plastica riciclata*. |
| **(b)** | All recycled-content claims → **IN_SCOPE**. An unqualified recycled-content percentage with no stated measurement basis is a quantified environmental claim lacking a verifiable method — Art. 23 lett. d-bis territory. | 19 → IN_SCOPE. Three seeds flip out of NEEDS_VERIFICATION. | Largest positive class. Risks the precision problem the relabel exists to fix: it treats "we can check this" as "this is a violation". |
| **(c)** | Split on the footnote rule from §2: marker-plus-body → NEEDS_VERIFICATION, everything else → IN_SCOPE. | 1 → NEEDS_VERIFICATION (608812, the only one with a marker). 18 → IN_SCOPE. | Consistent with the §2 answer and with group B. Flips three seeds. Only one recycled-content claim in the whole set ends up in the review queue. |

**Recommendation: (c).** It is the only option that makes one rule govern §1 and §2 together instead of two unrelated ones, it is grounded in Art. 18 lett. n-quinquies, and it keeps group A and group B consistent. Its cost is honest and should be stated plainly: **it overrides three of your adjudications**, which is why it is a question and not a decision.

If you prefer to keep all three seeds as adjudicated, then there is an unstated distinction and I need it in words — the census above is the set it has to cut cleanly.

</details>

---

## 2. Quantified environmental percentages — ✅ **RESOLVED 2026-09-20**

> **Decision.** Governed by the same stated-basis test as §1 — there is no separate rule for percentages. A **basis** is what makes the number checkable, in three forms: **counting method** (always), **scope** (always), and **comparator** (**only when specifically identified** — a named product, company, standard or dated baseline; *rispetto al pack precedente* does not qualify).
>
> **Population: 54 quantified environmental claims.** Of the 9 comparative ones, 2 have an identified comparator (Rovagnati, Beretta) → NEEDS_VERIFICATION; 7 do not → IN_SCOPE. Reproduces seed S5.
>
> **Consequence — two data-quality rules.** The claim string is not a reliable record of the qualifier: `666874`/`666869` carry a bare `*` whose body (*Gli ingredienti di origine naturale mantengono +50% del loro stato naturale…, inclusa l'acqua*) sits unattached in the description, and `608812` was joined to the **wrong** footnote body. **`verification.on_pack_qualifier` is re-derived from the product description at migration time, never copied from the joined claim string.**
>
> Encoded in LABELING_GUIDE.md §2 Step 4.

<details><summary>Original statement of the problem, kept for the record</summary>

### The contradiction (as first stated)

### The contradiction

| Seed | Adjudicated | Footnote marker + body? |
|---|---|---|
| 94% Ingredienti di origine naturale | **IN_SCOPE** | no |
| 96% Natural origin\* … water and naturally sourced ingredients with limited processing | **NEEDS_VERIFICATION** | yes |
| Formula vegana & biodegradabile^ … 99,9% formula biodegradabile | **NEEDS_VERIFICATION** | yes |

Here the hypothesis holds cleanly: the footnote is the discriminator, and it points the right way in all three.

### It is more than plausible — it is in the statute

**Art. 18, lett. n-quinquies** defines *asserzione ambientale generica* as an environmental claim not included in a sustainability label **and whose specification is not provided in clear and prominent terms through the same medium of communication**. A percentage with a printed footnote giving its basis *has* its specification in the same medium; it is therefore not a *generica*, and Art. 23 lett. d-bis — the blacklist entry for unsubstantiated generic environmental claims — does not reach it. What remains is whether the stated basis holds up, which is exactly a substantiation question.

So the rule is not a convenience. It tracks the line the legislature drew.

### The rule, stated

> A quantified environmental claim carrying a **footnote marker** (`*`, `**`, `^`) that points to a **separate printed footnote body** stating the calculation basis, comparator, method, or data source → **NEEDS_VERIFICATION**, with the footnote body copied verbatim into `verification.on_pack_qualifier`.
> A quantified environmental claim with **no such marker** → **IN_SCOPE**.
> An inline comparator phrase inside the claim itself (*rispetto al pack precedente*) is **not** a footnote and does not trigger verification — it names a comparator class without giving a verifiable reference point.

**Consequences if adopted:** `verification.on_pack_qualifier` becomes load-bearing and must be populated verbatim for every triggering claim. **65 claims in the set carry a `*`/`**`/`^` marker and 67 use the ` ... ` join to append a footnote body** — these become the population the rule governs, and they will need the footnote body extracted into the field during migration. It also settles §1 option (c), which is why the two questions should be answered together.

**Recommendation: adopt.** It reproduces all three seeds, it has a statutory basis, and it gives `verification.on_pack_qualifier` a job. Adopting it for §2 while rejecting (c) for §1 is coherent but leaves recycled content governed by a separate unstated rule.

</details>

---

## 3. Scope — ✅ **RESOLVED 2026-09-20: the ECGT perimeter only**

> **Decision.** The golden set is scoped to the material Directive (EU) 2024/825 inserted into the Codice del Consumo — not "sustainability" loosely. A claim is in scope only if it is an *asserzione ambientale* (Art. 18 n-quater), an *etichetta di sostenibilità* (n-sexies), or engages durability/repairability/software/consumables (n-novies ff.).
>
> **Sub-decisions:**
> - **Farming and production practice (10 claims): all discard.** None asserts an environmental impact; they assert a method. **T5 is withdrawn from the guide**, not narrowed.
> - **Social claims enter through n-sexies only, in mark or label form.** *Miele Equosolidale* and *Certificazione di Filiera con Benessere Animale* are in; free-text social prose is out.
> - **Animal welfare splits 2 in / 6 out** on that same line.
> - **Geographic origin (6 claims): discard as `other_regime`** with a note.
> - **`Etichetta Ambientale` (14 claims): discard as `other_regime`** — a mandatory mark, expressly excluded by n-sexies.
> - **DOP / IGP / STG: `other_regime`, Reg. (UE) 1151/2012.** They certify traditional composition, method or geographic link, not environmental or social characteristics.
> - **Durability: no genuine instances in this dataset.** The 16 candidates are cosmetic efficacy-duration claims; *durabilità* under n-novies is about goods not wearing out. Limb retained in the guide for future datasets.
>
> **⚠ Magnitude — read before Phase 3.** Of 562 claims, **203 (36%) contain any environmental or sustainability term; 359 (64%) contain none** and are candidates to leave. This is a far larger cut than "trim the health and heritage padding". It is the intended direction, but the deletion list at the Phase 2 gate is the thing to read before signing.
>
> **Seeds superseded by this decision, knowingly:** V4 *Approvata da A.I.Nut.* · V8 *Le nostre mucche…* · S24 *Tracciabilità e sicurezza* · S25 *Agricoltori selezionati* — none has an ECGT hook. Together with V3 and V10 from §1, **6 of the 61 seeds are superseded on the record.**

<details><summary>Original statement of the problem, kept for the record</summary>

### The tension (as first stated) — the question that costs the most to get wrong

### The tension

*Dal 1820 la famiglia Grondona garantisce* is discarded as `heritage_origin`. An unsubstantiated tradition claim is squarely Art. 21 territory in the Codice del Consumo — a misleading action as to the product's origin, nature, or the trader's attributes. Both are true at once. The question is not legal; it is **what this detector is for**.

### What is actually at stake

Discards **leave the dataset**. Getting §1 or §2 wrong means flipping a label. Getting §3 wrong means the claims are gone, and restoring them requires re-annotating the category from the source product descriptions — not re-running a script. The discard log mitigates this (that is what it is for), but it preserves the claim text and a reason code, not the verification objects, rationales, or any of the adjudication work that would have to be redone.

### The size of the category

**68 claims** are currently `misleading_authenticity_or_origin_claim` — 12% of the set. **22 claims** contain *tradizional\**, and they do not form one kind:

| Reading | Examples | Count in the *tradizional\** group |
|---|---|---|
| Storytelling about the past | *il più tipico dei dolci tradizionali genovesi* · *secondo la tradizionale ricetta* · *Burro tradizionale* · *GRAPPA TRADIZIONALE* | ~13 |
| Description of a current production or farming practice | *Le nostre mucche vengono nutrite in modo tradizionale* · *prodotto con metodo tradizionale in caldaie di rame* · *allevate secondo i metodi alpini tradizionali* · *Lenta stagionatura tradizionale di minimo 3 mesi* · *Lavorazioni tradizionali (macinazione, spremitura..)* | ~6 |
| Comparator inside a performance claim | *rispetto ad un dentifricio al fluoro tradizionale* · *rispetto alle vaschette tradizionali Rovagnati* | 3 |

Your own seeds already split this group: *il più tipico dei dolci tradizionali genovesi* discards, while *Le nostre mucche vengono nutrite in modo tradizionale* is NEEDS_VERIFICATION with the check *farming-practice evidence*. **T5 in the labeling guide encodes that split** — past versus present practice — and it is the rule that reproduces both seeds. But T5 is derived from two examples, and it decides roughly six claims whose classification you have not seen.

### The options

| | Scope | Consequence |
|---|---|---|
| **(a)** | **Environmental / sustainability only.** Heritage and origin storytelling discards; production and farming practice claims stay via T5. | Matches every seed. The detector has one job and its precision is measurable against one class of material. ~13 heritage claims leave; ~6 practice claims stay. |
| **(b)** | **Full UCPD scope.** Heritage claims are retained as IN_SCOPE under Art. 21. | Contradicts four of your DISCARD seeds (D15–D18). Re-expands the set in exactly the direction §1 of the brief says it was over-scoped. Makes precision on environmental claims unmeasurable again, because the positive class mixes two regimes. |
| **(c)** | **Environmental only now, with the heritage category reconstructible later.** As (a), plus: the discard log records enough to rebuild — which it does, via `reason: heritage_origin`. | Same as (a) today. Costs one deliberate decision: accept that the verification objects and rationales for those claims are not preserved, only the text and the code. |

**Recommendation: (a), and confirm it explicitly.** The whole point of the relabel is that a golden set measuring two different regimes at once measures neither. But this needs a sentence from you in so many words — *the golden set is scoped to environmental and sustainability claims only* — because it is the sentence the entire discard list rests on, and because (c) is really (a) with the cost written down rather than a third option.

**Second, narrower confirmation needed: is T5 right?** Does *prodotto con metodo tradizionale in caldaie di rame* stay in the set as a supply-chain claim, or leave as heritage? Your two seeds point in opposite directions on the word *tradizionale* and T5 is my reconstruction of why.

</details>

---

## 4. Efficacy claims — ✅ **DISSOLVED 2026-09-20 by the §3 scope decision**

> **No separate ruling was needed.** The question was whether an *active causal claim that the product reduces a specific risk of harm to the person* should escape the `product_performance` discard. Under the ECGT scope gate the question does not arise: none of the six candidate claims has an ECGT hook — not an *asserzione ambientale* (no environmental impact asserted), not an *etichetta di sostenibilità* (not a mark), not durability. They fail Step 3 and discard as `product_performance` regardless of which answer the candidate rule would have given.
>
> **The candidate rule is therefore not adopted, and is recorded as rejected** rather than left open — it would have been a distinction with no work to do.
>
> **Seed superseded, knowingly:** V5 *aiutano a ridurre il rischio di irritazione della pelle* moves from NEEDS_VERIFICATION to DISCARD/`product_performance`. **Total seeds superseded across §1, §3 and §4: 7 of 61.**
>
> The six claims, all discarding: `aiutano a ridurre il rischio di irritazione della pelle` (144400) · `Composizione che riduce il rischio di allergie` (646175) · `Schiarisce & riduce le macchie e ne previene la ricomparsa` (554877) · `allevia anche il fastidio provocato dalle punture di insetti ...` (38080) · `riduce il tempo richiesto per prendere sonno e può contribuire ad alleviare gli effetti del jet lag` (40263) · `In aiuto per alleviare questi disturbi viene l'uso di guaine per sostenere il peso del pancione` (56473).

<details><summary>Original statement of the problem, kept for the record</summary>


**Not anticipated in the brief. Surfaced by the seed run.**

| Seed | Adjudicated | Check given |
|---|---|---|
| Clinicamente testate | **DISCARD** `product_performance` | — |
| Protegge dagli agenti esterni | **DISCARD** `product_performance` | — |
| ipoallergenico | **DISCARD** `product_performance` | — |
| aiutano a ridurre il rischio di irritazione della pelle | **NEEDS_VERIFICATION** | *efficacy evidence* |

All four are efficacy or safety claims on non-food products. Three discard, one routes to verification with a check that would apply equally to the other three. The stated rubric gives no rule that separates them, which is gap ① of the 58/61.

**Candidate rule, not adopted:** an **active causal claim that the product reduces a specific risk of harm to the person** → NEEDS_VERIFICATION. A **categorical product attribute** (*ipoallergenico*), a **claim about testing** (*Clinicamente testate*), or a **vague protective assertion** (*Protegge dagli agenti esterni*) → DISCARD.

It reproduces all four seeds. **6 claims in the set would be affected:**

| product_id | claim_text (verbatim) |
|---|---|
| 144400 | aiutano a ridurre il rischio di irritazione della pelle |
| 646175 | Composizione che riduce il rischio di allergie |
| 554877 | Schiarisce & riduce le macchie e ne previene la ricomparsa |
| 38080 | allevia anche il fastidio provocato dalle punture di insetti ... donando una sensazione di immediato sollievo |
| 40263 | riduce il tempo richiesto per prendere sonno e può contribuire ad alleviare gli effetti del jet lag |
| 56473 | In aiuto per alleviare questi disturbi viene l'uso di guaine per sostenere il peso del pancione |

**Recommendation: reject the candidate rule and discard all six as `product_performance`** — including the seed. The rule is a post-hoc reconstruction fitted to one example; the distinction between "reduces the risk of irritation" and "protects from external agents" is not one a second annotator would draw unaided, which fails the §9 definition-of-done test. And on the merits these are efficacy claims on cosmetics and hygiene products, which is the regime §2 of the brief puts outside this detector.

That means **overriding one of your adjudications** (V5). The alternative — adopt the rule and keep all six — is coherent, but it puts four claims about sleep, insect bites, skin blemishes and pregnancy support into a *sustainability* golden set, and I do not think that is what you want.

</details>

---

## 5. One mechanical inconsistency, for completeness

Appendix A's target record uses *96% Natural origin\* …* as its worked example and labels it `"label": "IN_SCOPE"` with a populated `verification` object. §3's seed table adjudicates the same claim **NEEDS_VERIFICATION**. Since Appendix A is the template the migration validates against, the mismatch would propagate.

Reading it as a typo in the template rather than a third adjudication of that claim — the seed table governs, the claim is NEEDS_VERIFICATION, and `verification.required: true` implies the NEEDS_VERIFICATION label rather than coexisting with IN_SCOPE. **Confirm**, and confirm whether an IN_SCOPE claim may ever carry a non-null `verification` object or whether the validator should reject that combination outright.

Related, from Phase 0 and already flagged: `schema_version` starting at 0 makes the current file `0` and the migrated output `1`, which collides with `changed_in: "v2"`, `golden_set_coop_ucpd_250.v1.json`, `discarded_claims_v2.json`, and §6's "bumps schema_version to 2". Treating `schema_version` as a field-shape counter independent of the dataset generation labels — to be confirmed at the Phase 3 gate.

---

## 6. Final adjudication round — ✅ **CLOSED 2026-09-20**

Raised during the Phase 2 audit, resolved with the user the same day. All are encoded in `LABELING_GUIDE.md` v2.2; each was re-scanned across all 562 claims rather than applied to the claim that raised it.

| # | Question | Decision | Rule | Set-wide impact |
|---|---|---|---|---|
| 6.1 | Unnamed certification badges (`Filiera certificata`, `Benessere animale`, `Cosmetico Certificato 100% naturale`) | **NEEDS_VERIFICATION** — Art. 23 b-bis regulates the *display*; the checkable question is which scheme attests it | **T9** | 8 claims |
| 6.2 | Private retailer line marks (`VIVI VERDE` vs `FIOR FIORE`, `CRESCENDO`, `BENE SI'`, `PROTEIN +`, `DAYTECH`) | In scope **only if the mark's content is environmental or social**; the rest are trade marks | **T10** | ~12 claims; reproduces seed S3 |
| 6.3 | Market-leadership / sales-ranking claims | **DISCARD**, `other_regime` with a fixed note; a stated basis never rescues an out-of-scope claim | **T12** | 11 claims |
| 6.4 | Naming the component inside the claim (`Vaschetta con 70% di plastica riciclata`) | **Not a basis** — it is the claim's subject | **T8** | ~6 claims; reproduces seed S31 |
| 6.5 | Fair-trade scheme named in prose rather than as a mark | **NEEDS_VERIFICATION** — n-sexies is about substance, not typography | **T11** | 2 claims |
| 6.6 | Art. 23 lett. **l-bis** (legal requirement as a distinctive feature) — in the perimeter? | **Yes — Step 3 gains limb 3d.** ECGT-inserted material belongs in the perimeter | **T13** | **2 claims set-wide** — the limb widens the perimeter almost not at all |
| 6.7 | `Da filiera corta` — does n-quater's *implica* reach implied transport impact? | **DISCARD** — the record frames it as fair pay to farmers; reading transport impact in would be the annotator supplying the environmental content | — | 1 claim |
| 6.8 | Slogans heading a green list but containing no environmental word (`#unsorsomigliore`, `Céréal si impegna per voi`) | **DISCARD** — §0 governs; seed S20 is IN_SCOPE precisely because it says *pianeta* | closed gap | 3 claims |
| 6.9 | Environmental attribute inside the mandatory disposal block | **DISCARD** where the line carries a **material-code prefix** (`7 - …`); free-standing text in the same field is judged normally | **T14** | 1 claim; no other retained claim affected |
| 6.10 | A claim carrying both a text-visible defect and a verifiable element (`Low Impact Pack … cartoncino certificato FSC`) | **IN_SCOPE** — the visible defect (Art. 23 d-ter) governs, else a trader escapes the flag list by certifying one component | **T15** | 1 claim; no other retained claim affected |
| 6.11 | A brand's stated definition of its own marketing term | **NEEDS_VERIFICATION** / `on_pack_disclosure`, definition copied verbatim into `on_pack_qualifier` | **T16** | 1 claim |

**Result: UNCERTAIN 20 → 0.** Phase 3 is unblocked.

### Verification that the tightening is clean

The concern with a 66% discard rate is that it removes green claims along with out-of-regime ones. It does not:

- `unsubstantiated_health_or_efficacy_claim` **132 → 0**, `misleading_authenticity_or_origin_claim` **68 → 0**, `misleading_endorsement_claim` **15 → 0**, `nutrition_content_claim` **13 → 0** — whole categories leave.
- `environmental_unsubstantiated` retains **125 of 130**; `offset_based_neutrality` retains **6 of 6**.
- Only **18 of 373** discards contain environmental wording, and 15 are `Etichetta Ambientale` (mandatory mark, excluded by n-sexies).
- The **5** claims v1 called environmental that are leaving each trace to a rule adjudicated on the record: `Céréal si impegna per voi` and `Il nostro impegno` (6.8), `le capre sono allevate nel rispetto del benessere animale` (n-sexies mark form), `Cannuccia e incarto cannuccia plastica compostabile` (6.9), `Da filiera corta` (6.7).

An independent blind annotator, working from `LABELING_GUIDE.md` alone with no sight of any verdict, reproduced **94%** of labels on a stratified 50-claim sample, **98%** on retain-vs-discard and **96%** on reason code — and the three disagreements all involved UNCERTAIN, never two different confident calls.
