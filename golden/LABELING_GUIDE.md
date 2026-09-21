# LABELING_GUIDE.md — UCPD claim detector golden set

**Version 2 rubric. This document, not any briefing message, is the durable specification.**
A second annotator working only from this file should reproduce the adjudicated labels. If it does not, this file is wrong and gets fixed — not the adjudications.

Statutory frame: **Codice del Consumo, D.Lgs. 206/2005 as amended by D.Lgs. 20 febbraio 2026, n. 30** (in force 24 March 2026, applicable from 27 September 2026), which transposes Directive (EU) 2024/825 (ECGT) into Artt. 18, 21, 22, 23.

> The Green Claims Directive proposal is **not** part of this frame. It was withdrawn by the Commission in June 2025. Do not cite it.

---

## 0. The unit of labelling

**Label the claim, not the product.** One product record can carry claims of both retained classes and claims that are discarded. Never let a product's overall impression decide a single claim's label, and never let one claim's label propagate to its neighbours.

Judge **only the text of the claim as recorded**, together with any footnote body already joined to it. Do not assume facts about the product, and do not form a view on whether the assertion is true. The question is never "is this false?" — it is "what kind of claim is this, and what would settle it?"

---

## 1. The three outcomes

| Outcome | Meaning | Where it goes |
|---|---|---|
| **IN_SCOPE** | A claim inside the ECGT perimeter (Step 3) that the detector must flag, because nothing outside the text is needed to see the problem. | Stays in the golden set as a positive. |
| **NEEDS_VERIFICATION** | An environmental or otherwise substantiation-requiring claim whose outcome depends on evidence outside the product text. | Stays in the golden set, routed to a separate review queue. Carries a `verification` object. |
| **DISCARD** | Governed by a different regime, or not a sustainability claim at all. | **Leaves the dataset.** Written to `discarded_claims_v2.json` with a reason code. Never a labelled negative — it is not data. |

**UNCERTAIN** is a working label for the audit pass only. It may not survive into the dataset. Use it rather than guessing — in particular whenever you are torn between DISCARD and either retained class, because a wrong DISCARD deletes evidence while a wrong retained label is merely a wrong label.

An UNCERTAIN rate near zero on a first pass means the annotator is guessing. Above roughly 15% means this guide is underspecified and needs work.

---

## 2. Decision procedure

Run the steps in order. The first step that fires decides.

### Step 1 — Is this a commercial claim at all?

A claim is an assertion capable of influencing a purchase decision. Pure mandatory disclosure ("Conservare in luogo fresco e asciutto", material codes such as `PAP 21`), and pure identification (net weight, product name) are not claims. If it is not a claim, → **DISCARD / `other_regime`**, note `not_a_commercial_claim`.

### Step 2 — Regime gate

Ask, in this order, and stop at the first yes. The order is load-bearing: several claims satisfy more than one test.

**2a — `health_nutrition`.** Does it assert an effect on health, on a physiological function, on digestion or absorption, or the presence/absence/level of a nutrient or substance framed as beneficial to the body when consumed? This is the territory of Reg. (EC) 1924/2006 and Reg. (EU) 1169/2011, not this detector.
> *fonte di fibre · Alta digeribilità · Speziato e Antiossidante · Contiene curcuma che possiede proprietà antiossidanti*

**2b — `product_performance`.** Does it assert what the product does to the thing it acts on, or how well it performs its own function? Efficacy, sensory quality, protection, cleaning, technical design, comfort, fit, durability of effect, dermatological or clinical testing, hypoallergenicity, odour control.
> *Pulizia profonda · Ripristina il PH · Clinicamente testate · Protegge dagli agenti esterni · ipoallergenico · limita la formazione di cattivi odori · Massima protezione e comfort · Brightening & glow boosting eye mask · protegge i capelli dal crespo e da aggressioni esterne*

**2c — `heritage_origin`.** Does it assert something about the **past** — a founding date, family history, recipe provenance, historical typicality?
> *Dal 1820 la famiglia Grondona garantisce · la cui ricetta originale, creata nel XVI secolo ai tempi di Andrea D'Oria · il più tipico dei dolci tradizionali genovesi · le inimitabili ricette di famiglia*

**2d — `ip_regulatory_status`.** Does it assert a patent, trademark, registration, or other IP or regulatory status?
> *Brevetto internazionale*

**2e — `other_regime`.** Governed by some other body of law, or simply not about sustainability. Always attach a free-text note naming the regime or the reason.

### Step 3 — Scope gate: is this within ECGT?

**Adjudicated 2026-09-20: the golden set is scoped to the ECGT perimeter only** — the material Directive (EU) 2024/825 inserted into the Codice del Consumo. Not "sustainability" loosely; the perimeter the statute draws.

A claim is in scope if it meets **one** of the following. Each is a definition in Art. 18, not a judgement call.

**3a — It is an *asserzione ambientale* (Art. 18, lett. n-quater).** A non-mandatory message, in any form, that **asserts or implies** that a product, category, brand or trader «ha un impatto positivo o nullo sull'ambiente oppure è meno dannoso per l'ambiente rispetto ad altri … oppure ha migliorato il proprio impatto nel corso del tempo».
> The test is an assertion about **environmental impact**. A description of a production input or method is not one. *Le nostre mucche vengono nutrite in modo tradizionale, con erba fresca, fieno e piante di campo. E si sente!* asserts a feeding practice and sells it on taste; it asserts no impact on the environment and is **out of scope**.

**3b — It is an *etichetta di sostenibilità* (Art. 18, lett. n-sexies).** A voluntary trust mark, quality mark or equivalent, public or private, distinguishing a product, process or undertaking by its **environmental or social** characteristics — **excluding marks made mandatory by EU or national law**.
> This is the limb through which **social** claims enter. It reaches them **in mark or label form only**: n-quater is confined to environmental impact, so free-text social prose (*da allevamenti prevalentemente piccoli e a conduzione familiare*, *riconosciamo loro il giusto compenso contro ogni sfruttamento della manodopera*) has no ECGT hook and is out of scope, while *Miele Equosolidale* and *Certificazione di Filiera con Benessere Animale* are in.
> The mandatory-mark exclusion is operative: **`Etichetta Ambientale`** is Italy's compulsory packaging-labelling disclosure, therefore not an *etichetta di sostenibilità*, therefore out of scope. It appears **14 times** in the set.

**3c — It engages durability, repairability, software updates or consumables** (Art. 18 lett. n-novies to n-duodecies; Art. 21 lett. b-ter/b-quater; Art. 23 lett. bb-septies to bb-undecies).
> *Durabilità* is «la capacità dei **beni** di mantenere le loro specifiche funzioni e prestazioni attraverso un uso normale» — a good not wearing out. **It is not how long a cosmetic effect lasts.** `12h Idratazione`, `Fissaggio 48H*`, `presa sicura e duratura … fino a 12 ore` are efficacy-duration claims and remain `product_performance`. This dataset is FMCG groceries and toiletries and contains **no** genuine durability claims; the limb is stated because a future dataset of durable goods will need it.

If none of 3a–3c → **DISCARD / `other_regime`** with a note naming the governing regime. If any → Step 4.

### Step 3 — regimes that commonly take a claim out

| Regime | Typical claims | Note to record |
|---|---|---|
| Reg. (UE) 1151/2012 — quality schemes | DOP, IGP, **STG**, and prose restating a scheme specification | STG/DOP/IGP certify traditional composition, method or geographic link — **not** environmental or social characteristics, so they are not *etichette di sostenibilità* |
| Reg. (EC) 1924/2006 · Reg. (EU) 1169/2011 | nutrition and health claims | reason code `health_nutrition` |
| National/EU mandatory labelling | `Etichetta Ambientale`, material codes, sorting instructions | excluded by n-sexies |
| Origin and authenticity (Art. 21 generally) | `Prodotto in Italia*`, `Solo nocciole italiane` | Art. 21 territory but outside the ECGT perimeter |

> **Worked example — why scope decisions need the product record.** `Le nostre mucche vengono nutrite in modo tradizionale, con erba fresca, fieno e piante di campo. E si sente!` (product 48442) sits on *Mozzarella di Latte Fieno **STG*** by Brimi. *Latte Fieno/Heumilch* is a registered STG whose specification requires precisely that feeding regime. The claim is the scheme's own requirement restated in prose — governed by Reg. (UE) 1151/2012, not ECGT. Read in isolation it looks like an unfalsifiable farm boast; read with its record it is a quality-scheme restatement. **DISCARD / `other_regime`**, note *Reg. (UE) 1151/2012 — STG specification restated*. This supersedes seed V8.

### Step 4 — Evidence gate: IN_SCOPE or NEEDS_VERIFICATION

**NEEDS_VERIFICATION** when the claim's fate turns on a document, mark, or measurement that exists outside the claim text — that is, when you can write down a *specific* question a reviewer could answer by looking at the pack or a file. The triggers:

| Trigger | `verification.type` |
|---|---|
| Names or displays a certification scheme or sustainability label (FSC, biologico, DOP/IGP/STG, Fairtrade, Rainforest Alliance, Ecolabel) | `certification_scheme` |
| Names a test standard or norm (EN 13432, ISO) | `test_standard` |
| Carries a **footnote marker** (`*`, `**`, `^`) pointing to a separate printed footnote body stating the basis, comparator, method, or data source | `on_pack_disclosure` |
| Names a third-party endorser **whose mark is itself an *etichetta di sostenibilità*** — i.e. it certifies environmental or social characteristics (a fair-trade body, an animal-welfare scheme, a forestry council) | `third_party_endorsement` |
| Asserts a specific practice, figure, or percentage that a substantiation dossier could settle | `substantiation_evidence` |

> ### The stated-basis test — adjudicated 2026-09-20
>
> **Do not test for a footnote marker. Test for a stated basis.** A marker tests whether the annotator captured the qualifier; the basis test asks what Art. 18, lett. n-quinquies actually asks.
>
> **Search the whole product description — not just the claim string — for a statement of the claim's basis: its calculation method, its comparator, its scope, or its data source.**
>
> | What the description contains | Outcome |
> |---|---|
> | A footnote body or inline text giving the basis — *\*55% nella vaschetta* · *\*\* Da filiera alimentare controllata italiana* | **NEEDS_VERIFICATION**, `on_pack_qualifier` = the basis text, verbatim |
> | **Only a link** — *Scopri di più sul sito www.fratelliberetta.com* | **IN_SCOPE** |
> | Nothing | **IN_SCOPE** |
>
> **Why a link is not a basis.** n-quinquies requires the specification be «fornita in termini chiari ed evidenti tramite lo stesso mezzo di comunicazione» — *provided*, clearly and prominently. A URL promises the specification elsewhere; it does not provide it. Treating a link as sufficient would let any trader clear the test by printing a domain name.
>
> **Why not the marker.** Verified empirically across all 19 recycled-content claims: in one case (`588549`, *55% di plastica riciclata*) the description carries `\*55% nella vaschetta` and the annotator did not attach it to the claim. Testing for the marker would have mislabelled it. The basis test is immune to that extraction gap.
>
> ### What counts as a basis — adjudicated 2026-09-20
>
> A basis is something that makes the number **checkable**. Three qualifying forms:
>
> | Form | Example | |
> |---|---|---|
> | **Counting method** — the rule by which the figure was computed | *\*Gli ingredienti di origine naturale mantengono +50% del loro stato naturale dopo essere stati processati, inclusa l'acqua* · *water and naturally sourced ingredients with limited processing* | always a basis |
> | **Scope** — which component or portion the figure applies to | *\*55% nella vaschetta* · *\*\*Escluso tappo ed etichetta* | always a basis |
> | **Comparator** — what the figure is measured against | *rispetto alle vaschette tradizionali Rovagnati* · *rispetto alle precedenti confezioni Beretta* | a basis **only if specifically identified** |
>
> **The comparator rule.** A comparator counts only when it identifies something a reviewer could actually obtain and measure — a named product, a named company's prior line, a named standard, a dated baseline. A vague gesture at a predecessor does not: *rispetto al pack precedente*, *rispetto alla confezione precedente*, *rispetto al tappo precedente*, *rispetto al kit precedente*, *verso la stessa confezione fatta con materiali convenzionali* are **not** bases, and those claims are IN_SCOPE. This reproduces seed S5 (*-17% Plastica rispetto al pack precedente* → IN_SCOPE) and gives *asserzione ambientale generica* its natural reading: a specification that cannot be located is not a specification.
>
> Of the 9 comparative environmental claims in the set, **2 have an identified comparator** and **7 do not**.
>
> ### Two data-quality rules this forces
>
> **The claim string is not a reliable record of the qualifier.** Verified across the set:
> - `666874` and `666869` carry a bare `*` with no body attached, while the description holds the counting rule above.
> - `608812` was joined to `**Da filiera alimentare controllata italiana`, which explains nothing about its 100% figure; the description also holds `**Escluso tappo ed etichetta`, which is the actual scope qualifier. **The wrong footnote was attached.**
>
> Therefore: **`verification.on_pack_qualifier` must be re-derived from the product description at migration time, never copied from the joined claim string.** Where a marker maps to more than one footnote body, select the body that speaks to the claim's figure, and record the others nowhere.

> **An endorsement by a body that certifies something other than environmental or social characteristics does not reach Step 4 at all** — it fails Step 3 and discards. A nutritionists', dentists' or dermatologists' approval (*Approvata da A.I.Nut.*, *Approvato ANDI*, *Approvato da Skin Health Alliance*, *Testato dell'Istituto Svizzero della Vitamina*) is a health or efficacy endorsement with no ECGT hook. Seed **V4** is superseded accordingly. The `third_party_endorsement` verification type survives only for the sustainability-scheme case.

**IN_SCOPE** otherwise — the claim is in scope and nothing outside the text is needed to see the problem. The characteristic shapes:

- generic green wording with no specification: *green, eco, naturale, amico dell'ambiente, per l'ambiente, sostenibile*
- climate-neutrality and offset claims
- comparative environmental claims with no stated basis or identified comparator
- vague corporate **environmental** programmes

> **Removed 2026-09-20 — "unsubstantiated vague quality or supply-chain assurances".** This shape predates the ECGT scope gate and does not survive it: a quality or supply-chain assurance with no environmental content satisfies none of 3a–3c. Seeds **S24** *Tracciabilità e sicurezza* and **S25** *Agricoltori selezionati* are superseded and discard as `other_regime`. There is no generic-excellence limb; earlier drafts of this guide referred to one and were wrong.

### Step 5 — UNCERTAIN

Anything you cannot place with confidence. Record what the competing readings are.

---

## 3. Tie-break rules

These exist because the adjudicated examples require them. They are not optional refinements; without them the procedure above misclassifies real cases.

**T1 — Testing beats health.** A claim *about testing* (*Clinicamente testate*, *Dermatologicamente testato*) is `product_performance`, not `health_nutrition`, even on a product whose effect is bodily. The assertion is about the evidentiary process, not about a nutrient or a health outcome.

**T2 — Substrate versus body.** An effect on the substrate the product acts on — skin, hair, teeth, fabric, surfaces — is `product_performance` (*Ripristina il PH*, *protegge i capelli dal crespo*). An effect on the body's nutrition or health status through ingestion is `health_nutrition` (*Alta digeribilità*).

**T3 — Heritage takes the reason code.** When a superlative or absolute is attached to a recipe, a tradition, or a family, Step 2c fires and the discard reason is `heritage_origin`. *le inimitabili ricette di famiglia* is `heritage_origin`, not `other_regime`. (Earlier drafts said this rule beat "Step 3's generic-excellence limb"; there is no such limb — see Step 4.)

**T4 — Performance comparatives stay discarded.** An unsubstantiated comparative or superlative whose **axis of comparison is performance** is `product_performance`, however specific, quantified, or footnoted it is. *Progettato con setole dalla punta 4 volte più sottile per una pulizia delicata\*\* … rispetto a filamenti arrotondati standard* discards. The lack of substantiation does not by itself pull a claim into this detector — only the **axis** does.
> **Corollary.** If the axis of comparison is environmental (*-17% Plastica rispetto al pack precedente*, *75% In meno di plastica*), Step 2b does **not** fire. Go to Step 3.

**T5 — ~~Present practice is not heritage.~~ WITHDRAWN 2026-09-20.** T5 previously routed production- and farming-practice claims to Step 3 on the theory that they were supply-chain sustainability claims. Under the ECGT scope gate the theory fails: all **10** such claims in the set (*Vinificato con metodi tradizionali*, *Lenta stagionatura tradizionale di minimo 3 mesi*, *DISTILLATA CON METODO ARTIGIANALE IN PICCOLI ALAMBICCHI DI RAME*, *allevate secondo i metodi alpini tradizionali*, …) assert a production **method**, not an environmental **impact**, so none satisfies Art. 18 lett. n-quater. They discard — as `heritage_origin` where the appeal is to tradition, otherwise `other_regime`. The rule is deleted rather than narrowed.

**T6 — A recognised certification does not absolve.** See §4.

**T8 — Naming the component inside the claim is not a basis.** A basis is a separate qualifier telling you something the claim does not. *Bottiglia con il 100% di plastica riciclata*, *Vaschetta con 70% di plastica riciclata* and *Brick 86% da materie di origine vegetale* name their own subject; they are IN_SCOPE. Contrast *\*55% nella vaschetta*, a separate printed footnote that narrows a figure stated elsewhere — that is a scope basis. Adjudicated 2026-09-20; reproduces seed S31.

**T9 — Unnamed certification badges go to NEEDS_VERIFICATION.** A claim asserting certification with no scheme identified anywhere in the record (*Filiera certificata*, *Filiera italiana certificata*, *Benessere animale*, *Cosmetico Certificato 100% naturale*) is exactly what Art. 23 lett. b-bis regulates: the display of a sustainability label that may or may not rest on a *sistema di certificazione*. The question is `Quale schema di certificazione sostiene la dicitura «X», ed è conforme ai requisiti dell'art. 18, lett. n-septies?` Adjudicated 2026-09-20.

**T10 — Private retailer line marks are in scope only if their content is environmental or social.** *VIVI VERDE* markets environmental credentials and is an *etichetta di sostenibilità* (seed S3). *FIOR FIORE* (gourmet), *CRESCENDO* (infant), *BENE SI'* (health), *PROTEIN +* (nutrition) and *DAYTECH* are plain trade marks distinguishing by neither environmental nor social characteristics — they discard as `other_regime`. Adjudicated 2026-09-20.

**T11 — A recognised scheme named in prose counts as naming it.** *prodotto secondo i principi del commercio equo e solidale* invokes a recognised fair-trade scheme as surely as the mark *Miele Equosolidale* does; n-sexies is about substance, not typography. → NEEDS_VERIFICATION, `certification_scheme`. This does **not** reopen free-text social prose that names no scheme (*da allevamenti prevalentemente piccoli e a conduzione familiare*), which stays out. Adjudicated 2026-09-20.

**T12 — Market-position and sales-ranking claims discard.** *N°1 in Italia*, *Brand antiforfora n.1 al mondo*, *L'assorbente più venduto in Italia* fail Step 3: the axis is sales share, not environmental impact. Reason code `other_regime`, with the fixed note `market-position claim, Art. 21 Cod. Cons. — sales-ranking axis, outside the ECGT perimeter`, so the class stays greppable without a sixth enum value. **A stated basis never rescues an out-of-scope claim** — the Nielsen and IRI footnotes these carry are irrelevant once Step 3 fails. Adjudicated 2026-09-20.

**T13 — Limb 3d: legal requirements presented as a distinctive feature.** Art. 23, comma 1, lett. **l-bis** («presentare requisiti imposti per legge sul mercato dell'Unione europea per tutti i prodotti appartenenti a una data categoria come se fossero un tratto distintivo dell'offerta») is ECGT-inserted material and is **inside the perimeter**. Step 3 therefore has a fourth limb. *vitamina B1\* … \*Come previsto per legge* is the textbook case: the footnote admits the fortification is legally required while the headline sells it as a virtue. → IN_SCOPE, citation Art. 23, comma 1, lett. l-bis. Adjudicated 2026-09-20.
> A claim of performing **better** than a legal threshold (*pesticidi -70% della soglia consentita*) is not l-bis — it asserts outperformance, not mere compliance. A systematic scan of all 562 claims found only **2** l-bis candidates, so this limb widens the perimeter barely at all.

**T14 — A material-code prefix marks mandatory disclosure.** Inside `recycling_other`, a line carrying a material-code prefix — `7 - Cannuccia e incarto cannuccia plastica compostabile`, `C/PAP 84 - Brick - Carta` — is material identification under D.Lgs. 116/2020, expressly excluded from *etichetta di sostenibilità* by n-sexies. **DISCARD / `other_regime`.** Free-standing text in the same field with no code prefix (*Coop per l'ambiente*, *Fai la differenziata per il pianeta*) is a voluntary claim and is judged normally. The code prefix is the test. Adjudicated 2026-09-20.

**T15 — A text-visible defect beats a pending check.** Where one claim carries **both** a defect visible in the text and an element that would otherwise route to verification, the visible defect governs and the claim is **IN_SCOPE**. *Low Impact Pack: le nostre confezioni sono a basso impatto ambientale con plastica riciclabile e cartoncino certificato FSC* names FSC — normally a Step-4 certification trigger — but no certificate is needed to see that a whole-packaging claim rests on one certified component. That is Art. 23 lett. **d-ter**, and it governs. Without this rule a trader could leave the flag list by attaching a certification to a single component, which is the behaviour d-ter exists to catch. Adjudicated 2026-09-20.

**T16 — A brand's stated definition of its own term is an on-pack qualifier.** Where a record supplies the trader's own definitional criterion for a term it markets on (*Noi di Eat Natural cosa intendiamo quando diciamo «Natural»? … i nostri ingredienti sono di origine naturale; alcuni di loro devono essere puliti, essiccati e talvolta lavorati … senza aromi artificiali, senza additivi conservanti e coloranti*), that definition is a stated basis under Step 4. → NEEDS_VERIFICATION / `on_pack_disclosure`, with the definition copied verbatim into `on_pack_qualifier`. Adjudicated 2026-09-20.

> **RESOLVED 2026-09-20 — slogans heading a green list.** A slogan that heads a bulleted sustainability list but contains no environmental word of its own — *#unsorsomigliore*, *Céréal si impegna per voi* — sits between §0's rule ("judge only the text of the claim as recorded; never let the product's overall impression decide", which discards) and seed **S20** *Il nostro impegno per te e per il pianeta* (which is IN_SCOPE). The only thing distinguishing S20 is the word *pianeta*. Both blind and main annotation flagged this independently as the most likely point of disagreement. **Decided: DISCARD.** §0 governs — never let the product's overall impression decide a single claim's label. A slogan with no environmental content is not an *asserzione ambientale* whatever sits beneath it; seed S20 *Il nostro impegno per te e per il pianeta* is IN_SCOPE precisely because it says *pianeta*. Affects *#unsorsomigliore* (×2) and *Céréal si impegna per voi*.

**T7 — Recycled content follows the stated-basis test.** A recycled-content claim (*65% plastica riciclata*, *Etichetta in carta riciclata*) is governed by the Step-4 stated-basis test like any other quantified environmental claim — no separate rule. Adjudicated 2026-09-20; it overrides two seeds, V3 and V10, which move from NEEDS_VERIFICATION to IN_SCOPE. Recyclability claims (*riciclabile* — what can happen to the packaging later) are a different assertion from recycled content (*riciclato* — what it is made of) and follow the same test independently.

---
## 4. Certification schemes — the FSC rule, checked against the statute

**The rule: a recognised certification scheme does not auto-clear a claim. It moves it to NEEDS_VERIFICATION with a specific checkable question.**

This was to be confirmed against the Italian definition of *etichetta di sostenibilità* before being applied across the set. It was. **The text confirms it, and gives a sharper basis than "not per-se unfair".**

**Art. 18, lett. n-sexies** — *etichetta di sostenibilità*:

> «qualsiasi marchio di fiducia, marchio di qualità o equivalente, pubblico o privato, avente carattere volontario, che mira a distinguere e promuovere un prodotto, un processo o un'impresa con riferimento alle sue caratteristiche ambientali o sociali oppure a entrambe, esclusi i marchi obbligatori richiesti a norma del diritto dell'Unione europea o nazionale»

FSC is voluntary, private, and distinguishes a product by environmental characteristics. It is squarely an *etichetta di sostenibilità*.

**Art. 18, lett. n-septies** — *sistema di certificazione*: third-party verification against publicly accessible requirements, meeting four criteria — open to all operators on transparent, fair and non-discriminatory terms; requirements developed with experts and stakeholders; procedures for non-conformity including revocation or suspension of the label; and compliance monitoring by an objective procedure carried out by a third party independent of both scheme owner and operator, on international, EU or national standards.

FSC satisfies this. So FSC **is** a `sistema di certificazione`.

**Art. 23, comma 1, lett. b-bis** — unfair in every case:

> «esibire una etichetta di sostenibilità che non è basata su un sistema di certificazione o non è stabilita da autorità pubbliche»

**What this establishes.** Because FSC is a certification scheme, displaying the FSC mark is *not* per-se unfair under b-bis — the briefing's reading holds. But b-bis makes the **act of displaying** the regulated conduct. So the live question is not "is FSC a good scheme?" — that is settled — but "is this pack actually displaying a mark backed by a live certification?" That is precisely a NEEDS_VERIFICATION question, and it is checkable:

> *Il marchio FSC e il codice di licenza sono effettivamente presenti sulla confezione, e il certificato di catena di custodia è in corso di validità?*

The same reasoning applies to *biologico* (Reg. (UE) 2018/848), DOP/IGP/STG, Fairtrade, Rainforest Alliance, and Ecolabel.

**One distinction the statute adds, which the rubric must carry.** Art. 18, lett. n-quinquies defines *asserzione ambientale generica* as an environmental claim **not included in a sustainability label** and whose specification is not given clearly and prominently through the same medium. So a claim that genuinely sits inside a certification label is, by definition, *not* generic — which is why it cannot be handled as a Step-4 IN_SCOPE generic green claim and must instead be verified.

**And one the rubric must not overreach on.** A certification scheme under n-septies is **not** the same as *eccellenza riconosciuta delle prestazioni ambientali* under n-octies, which means EU Ecolabel, an officially recognised ISO 14024 Type I national scheme, or best environmental performance under other EU law. **FSC is not an n-octies ecolabel.** Do not treat an FSC claim as demonstrating recognised excellent environmental performance for the purposes of Art. 23 lett. d-bis.

---

## 5. Writing the `verification` object

Every NEEDS_VERIFICATION claim carries one. The question must name what is being checked. A question that would read the same on any other claim is not a question.

| | |
|---|---|
| ✗ | *Serve una verifica.* — generic, forbidden |
| ✗ | *Verificare la certificazione.* — which one, and what about it? |
| ✓ | *Il marchio FSC e il codice di licenza sono presenti in confezione, e il certificato di catena di custodia è valido?* |
| ✓ | *Quale metodo di calcolo sostiene il 96%?* |
| ✓ | *Quale norma di prova sostiene il 99,9% di biodegradabilità?* |
| ✓ | *L'approvazione di A.I.Nut. è autorizzata da quell'ente, e qual è l'ambito dell'approvazione?* |

Write the question in Italian. Fill `on_pack_qualifier` with the **verbatim** footnote body when one exists, including its marker; leave it `null` when none is printed. Fill `scheme` with the scheme name when one is named; otherwise `null`.

---

## 6. Citations — when to fill `expected_citation`, and when not to

**Default: `null`.** Fill it only where the mapping is unambiguous on the face of the claim. Inventing an article or letter to make a record look complete is worse than leaving it empty: it manufactures a legal position the dataset then teaches.

Unambiguous mappings, safe to use:

| Claim shape | Citation |
|---|---|
| Offset-based neutrality (*impatto climatico neutralizzato*, *Carbon Neutral … neutralizziamo le emissioni*) | Art. 23, comma 1, lett. **d-quater** |
| Generic environmental claim with no specification and no recognised excellent environmental performance | Art. 23, comma 1, lett. **d-bis** |
| Environmental claim about the product or business as a whole when only one aspect is concerned | Art. 23, comma 1, lett. **d-ter** |
| Displaying a sustainability label not based on a certification scheme or public authority | Art. 23, comma 1, lett. **b-bis** |
| Legal requirements presented as a distinctive feature of the offer | Art. 23, comma 1, lett. **l-bis** |
| Future environmental performance without a verified, detailed implementation plan | Art. 21, comma 1, lett. **b-ter** |
| Irrelevant benefits advertised as consumer advantages | Art. 21, comma 1, lett. **b-quater** |

`citation_it` renders as: `Art. 23, comma 1, lett. d-bis, Codice del Consumo`.

Everything else — and **every NEEDS_VERIFICATION item whose outcome is by definition undecided** — gets `null`. A claim awaiting a certificate check has no determined violation, so it has no determined citation.

---

## 7. Discard reason codes

| Code | Covers |
|---|---|
| `health_nutrition` | Nutrition and health claims. Reg. (EC) 1924/2006, Reg. (EU) 1169/2011. |
| `product_performance` | Ordinary efficacy, sensory, protective, or technical-design facts, and comparatives on a performance axis. |
| `heritage_origin` | Tradition, family history, recipe provenance, founding dates, historical typicality. |
| `ip_regulatory_status` | Patents, trademarks, registrations. |
| `other_regime` | Anything else. **Always** with a free-text note. |

**Every discard gets a code and a row in `discarded_claims_v2.json`.** A discard without a code is a deletion, and deletions are not permitted. The log is never loaded by the evaluation harness; it exists so the deletions are auditable, and so a later widening of scope can pull back a whole category without re-reviewing 250 products by hand.

---

## 8. Handling rules that bind during migration

- **Quote verbatim.** Footnote markers (`*`, `**`, `^`) and footnote bodies are evidence of an on-pack qualifier, not noise. Never normalise, trim, or re-case a claim string.
- **The join separator in this file is `' ... '`** — space, three ASCII full stops, space. It is *not* the ellipsis character `…`. Do not convert it.
- **A product whose every claim is discarded keeps its record**, with an empty claims array and its product-level fields intact. Products are never dropped. 74 of the 250 already carry zero claims.
- **Duplicate claim texts are adjudicated once and applied to every copy.** 562 claims span 481 distinct texts; `Etichetta Ambientale` appears 14 times, `VIVI VERDE` 13, `Coop per l'ambiente` 10.

---

## 9. Seed examples — human-adjudicated ground truth

These 61 are the calibration set. If the procedure above disagrees with one of them, the procedure is wrong.

> **Transcription note.** The seeds are reproduced here as they were adjudicated, which renders the claim/footnote join as `…`. **In the dataset itself the join is `' ... '`** (three ASCII full stops) — see §8. When matching a seed against a record, match on the claim text, not on the separator, and never rewrite the separator in either direction.
### 9.1 DISCARD — 19 seeds

| # | Claim (verbatim) | Reason code | Which step fires |
|---|---|---|---|
| D1 | Speziato e Antiossidante | `health_nutrition` | 2a |
| D2 | Contiene curcuma che possiede proprietà antiossidanti | `health_nutrition` | 2a |
| D3 | fonte di fibre | `health_nutrition` | 2a |
| D4 | Alta digeribilità | `health_nutrition` | 2a via T2 |
| D5 | Clinicamente testate | `product_performance` | 2b via T1 |
| D6 | Protegge dagli agenti esterni | `product_performance` | 2b |
| D7 | Pulizia profonda | `product_performance` | 2b |
| D8 | Ripristina il PH | `product_performance` | 2b via T2 |
| D9 | Progettato con setole dalla punta 4 volte più sottile per una pulizia delicata\*\* … rispetto a filamenti arrotondati standard | `product_performance` | 2b via T4 |
| D10 | Brightening & glow boosting eye mask | `product_performance` | 2b |
| D11 | Massima protezione e comfort | `product_performance` | 2b |
| D12 | ipoallergenico | `product_performance` | 2b |
| D13 | limita la formazione di cattivi odori | `product_performance` | 2b |
| D14 | protegge i capelli dal crespo e da aggressioni esterne | `product_performance` | 2b |
| D15 | il più tipico dei dolci tradizionali genovesi | `heritage_origin` | 2c |
| D16 | la cui ricetta originale, creata nel XVI secolo ai tempi di Andrea D'Oria | `heritage_origin` | 2c |
| D17 | Dal 1820 la famiglia Grondona garantisce | `heritage_origin` | 2c |
| D18 | le inimitabili ricette di famiglia | `heritage_origin` | 2c via T3 |
| D19 | Brevetto internazionale | `ip_regulatory_status` | 2d |

### 9.2 NEEDS_VERIFICATION — 10 seeds

| # | Claim (verbatim) | What has to be checked | `verification.type` |
|---|---|---|---|
| V1 | Imballi certificati FSC per salvaguardare le foreste | FSC mark + licence code on pack; chain-of-custody valid | `certification_scheme` |
| V2 | Le migliori pesche gialle bio | organic certification (Reg. (UE) 2018/848) and substantiation for the superlative *le migliori* | `certification_scheme` |
| V3 | Etichetta in carta riciclata | recycled-content evidence for the label stock | `substantiation_evidence` |
| V4 | Approvata da A.I.Nut. - Associazione Italiana Nutrizionisti | endorsement authorised by that body; scope of the approval | `third_party_endorsement` |
| V5 | aiutano a ridurre il rischio di irritazione della pelle | efficacy evidence | `substantiation_evidence` |
| V6 | formula vegana\*\* … Nessun ingrediente o derivato di origine animale | on-pack qualifier present; scheme or self-declaration basis | `on_pack_disclosure` |
| V7 | 96% Natural origin\* … water and naturally sourced ingredients with limited processing | calculation method behind 96%; footnote present and legible | `on_pack_disclosure` |
| V8 | Le nostre mucche vengono nutrite in modo tradizionale, con erba fresca, fieno e piante di campo. E si sente! | farming-practice evidence | `substantiation_evidence` |
| V9 | Formula vegana & biodegradabile^ … 99,9% formula biodegradabile | biodegradability test standard behind 99,9% | `test_standard` |
| V10 | Qualità Pampers in cartoni 100% riciclati | recycled-content evidence for the carton | `substantiation_evidence` |

### 9.3 IN_SCOPE — 32 seeds

| # | Claim (verbatim) |
|---|---|
| S1 | Rigoni di Asiago per l'ambiente |
| S2 | Coop per l'ambiente |
| S3 | Vivi Verde |
| S4 | Fiorentini per l'ambiente |
| S5 | -17% Plastica rispetto al pack precedente |
| S6 | 100% Naturale |
| S7 | Con cacao da coltivazione più sostenibile |
| S8 | Il Tuo Ciclo. Il Tuo Pianeta. Teniamo A Entrambi. |
| S9 | Ingredienti di origine naturale |
| S10 | CO2 100% prodotto a impatto climatico neutralizzato |
| S11 | 75% In meno di plastica |
| S12 | 94% Ingredienti di origine naturale |
| S13 | Prodotto con ingredienti di origine naturale |
| S14 | Eco pack 100% riciclabile - Con meno plastica |
| S15 | il latte amico dell'ambiente |
| S16 | Emissioni zero / Questa confezione è Carbon Neutral: ciò significa che neutralizziamo le emissioni di CO2 generate dalla sua produzione |
| S17 | gestito con ecosostenibilità |
| S18 | garantisce una produzione sostenibile in armonia con la natura |
| S19 | Fai la differenziata per il pianeta |
| S20 | Il nostro impegno per te e per il pianeta |
| S21 | Gallo green |
| S22 | Flacone green 100% |
| S23 | Progetto sostenibilità / Il Nostro Flacone Green |
| S24 | Tracciabilità e sicurezza |
| S25 | Agricoltori selezionati |
| S26 | brik-eco sostenibile |
| S27 | Il gusto di amare il pianeta |
| S28 | cannuccia di carta per ridurre l'impatto sull'ambiente |
| S29 | Ho a cuore l'ambiente |
| S30 | Agricoltura sostenibile |
| S31 | Bottiglia con il 100% di plastica riciclata |
| S32 | Viva la Natura! / Per un futuro migliore |

---

## 10. Seed reproduction run

The procedure in §2–§3 was run over all 61 seeds and nothing else.

**Result at first writing: 58/61 reproduced. After the OQ1 adjudication of 2026-09-20: 59/61, with two seeds knowingly superseded.** Not 61/61 — and the gap is reported rather than closed, because closing it would require inventing distinctions the adjudications do not state, which is the one thing a golden-set rubric must never do quietly.

Three rules in §2–§3 exist **because** the first run missed a seed, and were added as rubric repairs in the intended direction:

| Repair | Seed it was missing | What was added |
|---|---|---|
| ~~Step 3, third limb~~ **WITHDRAWN 2026-09-20** | V4 *Approvata da A.I.Nut.* | Added an endorsement limb to rescue V4. The ECGT scope gate replaced it: an endorsement by a body certifying neither environmental nor social characteristics has no hook, and **V4 is superseded** rather than rescued. |
| **T5** | V8 *Le nostre mucche vengono nutrite in modo tradizionale* | Step 2c was discarding it on the word *tradizionale*. Restricted 2c to claims about the past; present production practice goes to Step 3. |
| Step 4 footnote narrowing | S5 *-17% Plastica rispetto al pack precedente* | The `on_pack_disclosure` trigger was firing on any inline comparator. Narrowed to marker-plus-separate-body. |

### The three that remain

**① V5 — *aiutano a ridurre il rischio di irritazione della pelle*.** The procedure discards it at 2b as `product_performance`; it is adjudicated NEEDS_VERIFICATION with the check *efficacy evidence*.

No rule stated anywhere in the brief separates it from D5 *Clinicamente testate*, D6 *Protegge dagli agenti esterni* or D12 *ipoallergenico*, all of which are efficacy claims on non-food products and all of which discard. The DISCARD and NEEDS_VERIFICATION tables genuinely overlap on efficacy.

*Candidate rule, not adopted:* **an active causal claim that the product reduces a specific risk of harm to the person** routes to NEEDS_VERIFICATION, whereas a **categorical product attribute** (*ipoallergenico*), a **claim about testing** (*Clinicamente testate*), and a **vague protective assertion** (*Protegge dagli agenti esterni*) discard. It reproduces all four seeds. It is also unstated, and adopting it silently would move a class of claims. **6 claims in the 250 would be affected** — see OPEN_QUESTIONS.md §4.

**② V3 — *Etichetta in carta riciclata*** and **③ S31 — *Bottiglia con il 100% di plastica riciclata***. Both were unqualified recycled-content claims about packaging, adjudicated in opposite directions, and no rule reproduced both.

**RESOLVED 2026-09-20** by the stated-basis test (T7). Neither description states a basis, so both are **IN_SCOPE**. S31 is reproduced as adjudicated. V3 and V10 (*Qualità Pampers in cartoni 100% riciclati*) are **deliberate overrides** of the original adjudication, made on the record. Seed reproduction after this resolution: **59/61**, with V3 and V10 knowingly superseded and ① still open.

**Consequence for Phase 2 — superseded 2026-09-20.** ① was **dissolved** by the ECGT scope gate (OPEN_QUESTIONS.md §4): the six risk-reduction claims fail Step 3 and discard as `product_performance` whichever way the candidate rule would have gone. ② and ③ were **resolved** by T7. **No claim should now be recorded UNCERTAIN on the ground that it depends on ①, ② or ③.** Reserve UNCERTAIN for genuine annotator uncertainty.

---

## 11. Classifier system prompt (Phase 2 audit pass)

> ### ⚠ SUPERSEDED — use `CLASSIFIER_PROMPT_v2.md`
> The prompt reproduced below is the original brief's Appendix B with a 2026-09-20 amendment
> to the IN_SCOPE line. It **predates limb 3d (Art. 23 lett. l-bis) and tie-breaks T8–T16**,
> and it does not carry the stated-basis test in operational form. It is kept here for the
> record only.
>
> **The prompt actually used, and the one to run, is `golden/CLASSIFIER_PROMPT_v2.md`.**


Temperature 0. **One claim per call.** Do not batch — batching leaks labels between items.

> **Amended 2026-09-20** to match the adjudicated ECGT scope gate. The IN_SCOPE line and rule 7 differ from the original brief; the divergence is deliberate and is the point of this document being the durable artifact.

```
Sei un annotatore esperto per un dataset di riferimento sulle pratiche commerciali scorrette
(Codice del Consumo, D.Lgs. 206/2005 come modificato dal D.Lgs. 30/2026).

Classifica UNA singola asserzione commerciale in una delle seguenti categorie:

IN_SCOPE — asserzione che rientra nel perimetro ECGT (asserzione ambientale ai sensi dell'art. 18
  lett. n-quater; etichetta di sostenibilità ai sensi della lett. n-sexies; durabilità/riparabilità)
  e che il rilevatore deve segnalare, perché il problema è visibile dal solo testo.
NEEDS_VERIFICATION — asserzione ambientale o comunque bisognosa di sostanziazione, il cui esito
  dipende da prove esterne al testo: schema di certificazione, norma di prova, dossier di
  sostanziazione, o una precisazione stampata sulla confezione.
DISCARD — asserzione regolata da altra disciplina o non attinente alla sostenibilità: va rimossa
  dal dataset. Indica sempre il motivo: health_nutrition, product_performance, heritage_origin,
  ip_regulatory_status, other_regime.
UNCERTAIN — non collocabile con sicurezza. Usala. Non indovinare.

REGOLE
1. Una certificazione riconosciuta (FSC, biologico) non assolve automaticamente: sposta
   l'asserzione in NEEDS_VERIFICATION con una domanda verificabile e precisa.
2. Un confronto non sostanziato su un asse diverso da quello ambientale (prestazione, comfort,
   efficacia) va in DISCARD, non in IN_SCOPE.
3. DISCARD elimina l'asserzione dal dataset: in caso di dubbio fra DISCARD e una delle due classi
   conservate, scegli UNCERTAIN.
4. Giudica solo il testo fornito. Non presumere fatti sul prodotto né sulla veridicità
   dell'affermazione.
5. Conserva i rimandi in nota (*, **, ^) e il loro testo: sono prova della precisazione in
   confezione, non rumore.
6. Non citare la proposta di Green Claims Directive (ritirata nel giugno 2025).
7. Il perimetro è quello ECGT. Un'asserzione generica di qualità, eccellenza, filiera o origine priva
   di contenuto ambientale NON rientra: va in DISCARD. Un'approvazione di terzi rileva solo se il
   marchio dell'ente certifica caratteristiche ambientali o sociali.

FORMATO — solo JSON:
{"label":"...","discard_reason":null|"...","verification_question":null|"<italiano>",
"rationale_it":"<una frase>","confidence":0.0-1.0}
```

---

## 12. Change log for this guide

| Version | Date | Change |
|---|---|---|
| 2.2 | 2026-09-20 | All 7 remaining UNCERTAINs adjudicated; **UNCERTAIN rate now 0**. Limb **3d** added (Art. 23 lett. l-bis inside the perimeter). T13–T16 added. Slogan-heading-a-green-list gap closed in favour of DISCARD. Systematic re-scans confirmed T13 affects 2 claims, T14 and T15 affect no retained claim beyond the one each was decided on. |
| 2.1 | 2026-09-20 | ECGT scope gate replaces the loose "sustainability" scope (Step 3 rewritten around Art. 18 n-quater / n-sexies / n-novies). T5 withdrawn. Generic-excellence and endorsement limbs removed; seeds S24, S25, V4, V5, V8 superseded. Stated-basis test replaces the footnote-marker test (T7). T8–T12 added. **Blind re-annotation of a stratified 50-claim sample: 94% label agreement, 98% on retain-vs-discard, 96% on reason code.** |
| 2.0-draft | 2026-09-19 | First written form of the rubric. Two retained classes plus discard. FSC reading confirmed against Art. 18 lett. n-sexies/n-septies and Art. 23 lett. b-bis. Tie-breaks T1–T6 derived from the 61 seeds. Seed reproduction 58/61, with three gaps recorded in OPEN_QUESTIONS.md rather than closed by invention. |
