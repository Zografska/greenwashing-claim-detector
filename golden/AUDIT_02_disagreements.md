# AUDIT_02 — Disagreement report

Phase 2, regenerated 2026-09-20 after all seven UNCERTAINs were adjudicated. **`golden_set_coop_ucpd_250.json` is unmodified** — 250 records, 562 claims, mtime unchanged. This report is the deliverable; Phase 3 touches data only after sign-off on §3.

Rubric: `LABELING_GUIDE.md` v2.2 (ECGT perimeter, limbs 3a–3d, T1–T16).

---

## 0. Method, and two flaws declared

Appendix B requires temperature 0 and **one claim per call, never batched**. 562 separate calls was not workable, so the set was split into 12 slices given to 12 independent annotators, each judging its claims **one at a time in isolation** with no sight of neighbouring verdicts and no prior verdict offered as a template. That preserves what the no-batching rule protects against, but it is a deviation from the literal instruction.

**Self-inflicted flaw.** Slices 00–05 (282 claims) ran against the guide *before* the generic-excellence and endorsement limbs were removed; slices 06–11 (280 claims) ran after. All twelve annotators independently reported it. Affected claims were identified and repaired in a logged pass (§6).

**Three annotators (06, 08, 09) were terminated mid-run by the org spend limit.** All had already written their result files; only their closing summaries were lost. Integrity verified: 562 unique uids, no duplicates, no orphans, zero schema violations.

**Independent check.** A blind annotator re-classified a stratified 50-claim sample from the guide alone, without sight of any verdict: **94% label agreement, 98% on retain-vs-discard, 96% on reason code.** All three disagreements involved UNCERTAIN; the two passes never disagreed on a confident call.

---

## 1. Headline numbers
| Outcome | Claims | % of 562 |
|---|---|---|
| **IN_SCOPE** | 141 | 25.1% |
| **NEEDS_VERIFICATION** | 48 | 8.5% |
| **DISCARD** | 373 | 66.4% |
| **UNCERTAIN** | 0 | 0.0% |

**Retained in v2: 189 claims (33.6%). Leaving: 373 (66.4%). Unresolved: 0.**

The Phase 0 keyword screen projected ~64% would fall outside the ECGT perimeter; independent annotation returned 66.4%.

### 1.1 The discards are scope-driven, not noise — the check that matters

Whole categories left, and the environmental core survived almost intact:

| v1 category | discarded | retained |
|---|---|---|
| `unsubstantiated_health_or_efficacy_claim` | 132 | 0 |
| `environmental_unsubstantiated` | 5 | 125 |
| `misleading_authenticity_or_origin_claim` | 68 | 0 |
| `misleading_superiority_or_absolute_claim` | 62 | 3 |
| `irrelevant_claim` | 47 | 7 |
| `fake_or_unverified_label` | 16 | 28 |
| `unfair_comparison` | 13 | 11 |
| `misleading_endorsement_claim` | 15 | 0 |
| `nutrition_content_claim` | 13 | 0 |
| `misleading_composition_or_ingredient_claim` | 2 | 9 |
| `offset_based_neutrality` | 0 | 6 |

`unsubstantiated_health_or_efficacy_claim` 132→0, `misleading_authenticity_or_origin_claim` 68→0, `misleading_endorsement_claim` 15→0 and `nutrition_content_claim` 13→0 leave whole. **`environmental_unsubstantiated` retains 125 of 130 and `offset_based_neutrality` all 6.** The 66% did not come from shaving green claims.

Only **18 of 373 discards (4.8%)** contain environmental wording, of which 15 are `Etichetta Ambientale` — the mandatory mark n-sexies expressly excludes. **Five claims v1 called environmental are leaving**, each traceable to a rule adjudicated on the record:

| product | claim | rule that removed it |
|---|---|---|
| 39785 | `Céréal si impegna per voi` | corporate commitment slogan with no environmental content in the claim text itself - jud |
| 609831 | `le capre sono allevate nel rispetto del benessere animale` | Asserzione sul benessere animale in prosa libera e non in forma di marchio: la lett. n-s |
| 578874 | `Cannuccia e incarto cannuccia plastica compostabile` | material identification inside the mandatory packaging-disposal block (prefixed '7 -'),  |
| 41401 | `Il nostro impegno` | Impegno aziendale generico senza contenuto ambientale — nessun aggancio ECGT (non è asse |
| 718993 | `Da filiera corta` | short-supply-chain claim framed by the record as direct contracts and fair pay to farmer |

## 2. Disagreement against v1

v1 had no claim-level label. Per the Phase 0 gate: `category != irrelevant_claim` = **positive** (508), `irrelevant_claim` = **negative** (54).

| v1 | → v2 | Claims | Reading |
|---|---|---|---|
| positive | DISCARD | **326** | **over-detection** — v1 flagged material outside the regime |
| positive | IN_SCOPE | **136** | agreement — correctly flagged |
| positive | NEEDS_VERIFICATION | **46** | v1 treated "check a certificate" as a violation |
| negative | DISCARD | **47** | agreement — correctly not flagged, and out of scope |
| negative | IN_SCOPE | **5** | **under-detection** — v1 dismissed as irrelevant what the rubric flags |
| negative | NEEDS_VERIFICATION | **2** | **under-detection** — routed to review |

**Over-detection exceeds under-detection by roughly 46×: 326 claims leave against 7 that v1 wrongly dismissed.**

### positive → NEEDS_VERIFICATION — 46 claims

| product | claim_text (verbatim) | v1 category | rationale_it |
|---|---|---|---|
| 588549 | `-38% di plastica* ... rispetto alle vaschette tradizionali Rovagnati` | unfair_comparison | Confronto su asse ambientale con comparatore specificamente identificato (le vaschette tradizionali  |
| 68928 | `100% Elettrica rinnovabile` | environmental_unsubstantiated | Asserzione ambientale quantificata sull'energia di produzione; la descrizione ne precisa il perimetr |
| 45232 | `25% Plastica* ... rispetto alle precedenti confezioni Beretta` | unfair_comparison | Comparativo su asse ambientale (T4, corollario) con nota in confezione che identifica il comparatore |
| 588549 | `55% di plastica riciclata` | environmental_unsubstantiated | Asserzione ambientale quantificata sul contenuto di riciclato: la confezione dichiara l'ambito di ap |
| 666874 | `95% Ingredienti di origine naturale*` | environmental_unsubstantiated | Asserzione ambientale quantificata sulla naturalità degli ingredienti, accompagnata nella descrizion |
| 666869 | `96% Ingredienti di origine naturale*` | environmental_unsubstantiated | Asserzione ambientale quantificata sulla naturalità degli ingredienti con regola di calcolo enunciat |
| 611508 | `96% Natural origin* ... water and naturally sourced ingredients with limited pro` | environmental_unsubstantiated | Asserzione di naturalita' quantificata (asserzione ambientale ex n-quater) accompagnata in confezion |
| 571225 | `Benessere animale` | environmental_unsubstantiated | Dicitura a sé stante sul benessere animale, presentata in forma di marchio/claim di filiera: caratte |
| 641361 | `Biodegradable mask by home compost** ... compostabile nel compostaggio domestico` | environmental_unsubstantiated | Asserzione ambientale di compostabilità domestica accompagnata da un corpo di nota separato che ne p |
| 608812 | `Bottiglia in plastica 100% riciclata** ... Da filiera alimentare controllata ita` | environmental_unsubstantiated | Asserzione ambientale quantificata sul riciclato con ambito dichiarato in confezione (nota riderivat |
| 39538 | `Cialde compostabili* ... In conformità alla norma EN 13432/2002` | environmental_unsubstantiated | Asserzione ambientale di compostabilità ancorata a una norma di prova richiamata in nota sulla confe |
| 619902 | `Con burro di karité da coltivazione etiche* ... Commercio equo e solidale degli ` | fake_or_unverified_label | Asserzione di approvvigionamento etico del burro di karité, sostenuta in nota dal richiamo al commer |
| 599157 | `Confezione con carta certificata FSC per una gestione responsabile delle foreste` | environmental_unsubstantiated | Etichetta di sostenibilità volontaria ex art. 18, lett. n-sexies, sorretta da un sistema di certific |
| 645376 | `Confezione con carta certificata FSC per una gestione responsabile delle foreste` | environmental_unsubstantiated | Asserzione ambientale che esibisce un'etichetta di sostenibilità volontaria (FSC): ai sensi dell'Art |
| 145542 | `conformità con lo standard SRP per la coltivazione sostenibile del riso` | environmental_unsubstantiated | Asserzione ambientale ancorata a uno standard di sostenibilita nominato (SRP): l'esito dipende dall' |
| 564356 | `Consigliato da Legambiente ... Sustainable product DTP112 certified, Cert. CSQA ` | environmental_unsubstantiated | Avallo di un ente che promuove caratteristiche ambientali: rileva ex art. 18 n-sexies e il suo esito |
| 704630 | `cosa intendiamo quando diciamo «Natural»` | misleading_composition_or_ingredient_claim | Asserzione di naturalita del marchio con criterio di definizione dichiarato in confezione: l'esito d |
| 612478 | `Cosmetico Certificato 100% naturale` | fake_or_unverified_label | L'asserzione rivendica uno stato di certificazione («Certificato») su una caratteristica ambientale  |
| 608641 | `Cosmetico Certificato 100% naturale` | fake_or_unverified_label | L'asserzione rivendica uno stato di certificazione su una caratteristica ambientale senza nominare l |
| 602008 | `Cosmetico Certificato 100% naturale ... Come previsto dal disciplinare NaTrue` | environmental_unsubstantiated | Rivendica una certificazione su caratteristiche ambientali del cosmetico richiamando un disciplinare |
| 564356 | `Da filera tracciata e sostenibile` | environmental_unsubstantiated | Asserzione ambientale di filiera sostenibile che il contesto di prodotto riconduce a uno schema di c |
| 603892 | `di origine naturale e bio` | misleading_composition_or_ingredient_claim | Il claim nomina l'etichetta biologica accanto all'origine naturale: poiché l'asserzione si appoggia  |
| 144287 | `Eco pack biodegradabile e compostabile ... Imballaggio compostabile ai sensi del` | environmental_unsubstantiated | Asserzione ambientale sull'imballaggio ancorata a una norma di prova nominata e a un numero di certi |
| 144400 | `Energia rinnovabile certificata` | environmental_unsubstantiated | Asserzione di una pratica specifica di approvvigionamento energetico presentata come certificata: ne |
| 703069 | `Equalitas - Cantina Sostenibile` | environmental_unsubstantiated | Marchio volontario privato che distingue l'impresa per caratteristiche ambientali e sociali: etichet |
| 39017 | `Farina di grano tenero da Agricoltura Sostenibile rispettando le 10 regole della` | environmental_unsubstantiated | Asserzione ambientale che richiama un disciplinare e uno schema di certificazione nominati (Carta de |
| 571225 | `Filiera certificata` | fake_or_unverified_label | Asserzione di filiera certificata senza schema nominato, presentata come marchio di qualità volontar |
| 101501 | `Filiera certificata` | fake_or_unverified_label | Asserzione di filiera certificata senza schema nominato, presentata come marchio di qualità volontar |
| 638347 | `Filiera italiana certificata` | fake_or_unverified_label | Dicitura di certificazione senza schema identificato: l'esito dipende dall'esistenza di un sistema d |
| 666874 | `Formula senza microplastiche^^ ... secondo la definizione dell'UNEP` | environmental_unsubstantiated | Asserzione ambientale di assenza di microplastiche corredata dalla fonte definitoria stampata in con |
| 666869 | `Formula vegana & biodegradabile^ ... 99,8% formula biodegradabile` | environmental_unsubstantiated | Asserzione ambientale di biodegradabilità con percentuale e nota stampata: l'esito dipende dalla nor |
| 666874 | `Formula vegana & biodegradabile^ ... 99,9% formula biodegradabile` | environmental_unsubstantiated | Asserzione ambientale di biodegradabilità con percentuale e nota stampata: l'esito dipende dalla nor |
| 569248 | `il 100% delle aziende agricole conferenti ha ottenuto la Certificazione di Filie` | environmental_unsubstantiated | L'asserzione richiama un marchio di certificazione su caratteristiche di benessere animale, quindi u |
| 612659 | `Il nostro cacao è certificato Rainforest Alliance` | environmental_unsubstantiated | Etichetta di sostenibilità volontaria ex art. 18, lett. n-sexies: l'esito dipende dall'esistenza e d |
| 44114 | `Imballi certificati FSC per salvaguardare le foreste` | environmental_unsubstantiated | Richiama uno schema di certificazione volontario (FSC) che è etichetta di sostenibilità ex Art. 18 n |
| 554553 | `Imballi certificati FSC per salvaguardare le foreste` | environmental_unsubstantiated | Richiama la certificazione FSC, etichetta di sostenibilità volontaria ex Art. 18 n-sexies: va verifi |
| 569248 | `La carta utilizzata è certificata e proviene da foreste gestite nel rispetto di ` | environmental_unsubstantiated | L'asserzione dichiara l'esistenza di una certificazione forestale su standard ambientali e sociali:  |
| 703021 | `La certificazione FSC supporta una buona gestione delle foreste` | environmental_unsubstantiated | Richiama uno schema di certificazione forestale volontario che è un'etichetta di sostenibilità, sicc |
| 603892 | `Le migliori albicocche bio` | misleading_superiority_or_absolute_claim | Il claim combina il richiamo all'etichetta biologica e un superlativo non sostanziato: entrambi dipe |
| 663509 | `Le migliori pesche gialle bio` | misleading_superiority_or_absolute_claim | Il claim poggia su un'etichetta di sostenibilità (biologico) e aggiunge un superlativo: entrambi gli |
| 675785 | `Miele Equosolidale` | fake_or_unverified_label | Marchio volontario che distingue il prodotto per caratteristiche sociali, quindi etichetta di sosten |
| 603896 | `plastica riciclabile e cartoncino certificato FSC` | environmental_unsubstantiated | Asserzione ambientale sull'imballaggio che si appoggia a uno schema di certificazione nominato (FSC) |
| 54275 | `prodotto secondo i principi del commercio equo e solidale` | fake_or_unverified_label | Affermazione sociale sul commercio equo e solidale riferita all'olio di argan: non e' chiaro se, non |
| 47144 | `provenienti da produttori equo solidali altromercato` | environmental_unsubstantiated | Richiamo a un circuito di commercio equo identificato (Altromercato), che distingue il prodotto per  |
| 47286 | `Questa confezione è composta per l'88% da materie prime rinnovabili` | environmental_unsubstantiated | Asserzione ambientale quantificata sull'imballaggio accompagnata nel testo di prodotto dall'indicazi |
| 718993 | `tecniche di produzione integrata a tutela della salute e dell'ambiente (pesticid` | environmental_unsubstantiated | Asserzione ambientale quantificata con comparatore identificabile (la soglia di legge consentita): i |

### negative → IN_SCOPE — 5 claims

| product | claim_text (verbatim) | v1 category | rationale_it |
|---|---|---|---|
| 701225 | `Fai la differenziata per il pianeta` | irrelevant_claim | Invito generico alla raccolta differenziata 'per il pianeta': asserzione ambientale priva di specifi |
| 42428 | `Fare una corretta raccolta differenziata fa bene all'ambiente` | irrelevant_claim | Messaggio volontario che afferma un beneficio ambientale della raccolta differenziata, eccedente l'i |
| 68928 | `L'ambiente è vita. Tienilo pulito` | irrelevant_claim | Messaggio ambientale volontario di richiamo alla cura dell'ambiente, privo di qualsiasi specificazio |
| 52121 | `Riciclando miglioriamo insieme il nostro ambiente!` | irrelevant_claim | Asserzione ambientale generica ('miglioriamo insieme il nostro ambiente') senza alcuna specificazion |
| 37815 | `vitamina B1* ... *Come previsto per legge` | irrelevant_claim | Requisito imposto per legge (fortificazione con vitamina B1) presentato come tratto distintivo dell' |

### negative → NEEDS_VERIFICATION — 2 claims

| product | claim_text (verbatim) | v1 category | rationale_it |
|---|---|---|---|
| 599962 | `formula vegana** ... Nessun ingrediente o derivato di origine animale` | irrelevant_claim | Asserzione di formula vegana con nota stampata che ne definisce il perimetro, riproduzione del seed  |
| 599963 | `formula vegana** ... Nessun ingrediente o derivato di origine animale` | irrelevant_claim | Asserzione di formula vegana con nota stampata che ne definisce il perimetro, riproduzione del seed  |
---
## 3. THE DELETION LIST — 373 claims leaving the dataset

Ordered by reason code, then by product. **This is the section to read before signing.** Every row will be absent from v2 and present in `discarded_claims_v2.json` with its code.

| Reason code | Claims | Share |
|---|---|---|
| `product_performance` | 154 | 41.3% |
| `other_regime` | 90 | 24.1% |
| `health_nutrition` | 76 | 20.4% |
| `heritage_origin` | 51 | 13.7% |
| `ip_regulatory_status` | 2 | 0.5% |
| **total** | **373** | |

### 3.1 `product_performance` — 154 claims

Efficacy, sensory, protective and technical-design facts, plus comparatives on a performance axis (T4). Cosmetics and toiletries dominate.

| product | name | claim_text (verbatim) | rationale_it |
|---|---|---|---|
| 144400 | Proteggislip normali pure sensit | `0% di allergeni comuni*, profumi, coloranti (with disclosed NF EN 16274 test method and named al` | L'assenza di allergeni comuni, profumi e coloranti è un attributo di tollerabilità cutanea del prodo |
| 144400 | Proteggislip normali pure sensit | `Cour-V - Massima adattabilità / Una tecnologia unica` | «Massima adattabilità» e «tecnologia unica» sono un superlativo di prestazione e comfort sul design  |
| 144400 | Proteggislip normali pure sensit | `aiutano a ridurre il rischio di irritazione della pelle` | Asserzione di efficacia su prodotto non alimentare: fuori dal perimetro ECGT. |
| 145542 | Riso basmati profumato per ricet | `Originale: ... il Basmati Gallo è ideale per originali ricette` | Asserisce l'idoneita d'uso del prodotto per determinate ricette, cioe una qualita d'impiego priva di |
| 164990 | Lievito vanigliato x10 | `garantisce la lievitazione perfetta` | Asserisce quanto bene il prodotto svolge la propria funzione (la lievitazione): efficacia ex Step 2b |
| 38080 | Dopopuntura penna gel derm herba | `allevia anche il fastidio provocato dalle punture di insetti ... donando una sensazione di immed` | Efficacia lenitiva sul fastidio da puntura, effetto sul corpo per applicazione topica: prestazione d |
| 38080 | Dopopuntura penna gel derm herba | `Dermatologicamente testato` | Asserzione sul processo probatorio: prestazione per la regola T1. |
| 39017 | Pane a fette pan bauletto bianco | `Il più morbido di sempre* ... rispetto alla ricetta precedente` | Superlativo comparativo su un asse prestazionale/sensoriale (morbidezza) rispetto alla ricetta prece |
| 40079 | Mutandine pannolino little swimm | `Maximum protection` | Asserisce il livello di protezione offerto dal prodotto, cioè una prestazione, come nel seed D11. |
| 40177 | Dentifricio kids anticarie con f | `aiuta a proteggere i denti dalla carie` | Protezione dei denti dalla carie: effetto sul substrato dentale, quindi prestazione del prodotto (T2 |
| 40184 | Deodorante spray deodry | `esclusiva formula ad alta efficacia` | Affermazione di eccellenza il cui asse e' l'efficacia della formula, quindi prestazione del prodotto |
| 40184 | Deodorante spray deodry | `garantire una pelle asciutta e protetta fino a 72 ore` | Efficacia sulla pelle con durata dell'effetto fino a 72 ore: durata di un effetto cosmetico, non dur |
| 40184 | Deodorante spray deodry | `Contribuisce a regolare il naturale processo di traspirazione della pelle` | Effetto sul substrato cutaneo (regolazione della traspirazione) per applicazione topica: prestazione |
| 40184 | Deodorante spray deodry | `Studiato per ridurre la formazione di macchie e aloni sui tessuti` | Effetto sul substrato tessile (riduzione di macchie e aloni): prestazione del prodotto (Step 2b). |
| 40184 | Deodorante spray deodry | `Formula clinicamente testata` | Asserzione relativa al processo probatorio (test clinico) e non a un nutriente o a un esito di salut |
| 40732 | Assorbenti normali ripiegati x12 | `Massima protezione e comfort` | Superlativo su protezione e comfort dell'assorbente: asse prestazionale (Step 2b), seed D11. |
| 40732 | Assorbenti normali ripiegati x12 | `ipoallergenico` | Attributo categoriale di tollerabilita' del materiale a contatto con la pelle: efficacia/sicurezza d |
| 40732 | Assorbenti normali ripiegati x12 | `aiutando a mantenere la pelle asciutta e a prevenire l'insorgenza di irritazioni e arrossamenti` | Asserzione di efficacia su prodotto non alimentare: fuori dal perimetro ECGT. |
| 40732 | Assorbenti normali ripiegati x12 | `limita la formazione di cattivi odori` | Controllo degli odori: funzione propria del prodotto (Step 2b), seed D13. |
| 41070 | Spazzolino denti sensibili setol | `30% Più flessibile* ... Da test di laboratorio, rispetto ad uno spazzolino a setole piatte stand` | Comparativo quantificato il cui asse è la prestazione (flessibilità del collo), per quanto sostenuto |
| 41070 | Spazzolino denti sensibili setol | `Progettato con setole dalla punta 4 volte più sottile per una pulizia delicata** ... rispetto a ` | Comparativo il cui asse di confronto e' la delicatezza della pulizia rispetto a filamenti standard,  |
| 42118 | Mutandina 10 pyjama pants 4-7 an | `Clinically Proven for a better night's sleep* ... Basato su uno studio clinico condotto nel 2020` | È un'asserzione sull'efficacia del prodotto e sul processo probatorio clinico, regolata come prestaz |
| 42428 | Salviettine igieniche baby fresh | `Pulizia profonda` | Efficacia detergente: prestazione del prodotto (seed D7). |
| 42428 | Salviettine igieniche baby fresh | `Con sistema igienizzante` | Caratteristica tecnica/funzionale del prodotto (sistema igienizzante): prestazione (passo 2b). |
| 42428 | Salviettine igieniche baby fresh | `Ripristina il PH` | Effetto sul pH del substrato cutaneo: prestazione per la regola T2 (seed D8). |
| 42428 | Salviettine igieniche baby fresh | `Dermatologicamente testate` | Asserzione sul processo probatorio: prestazione per la regola T1. |
| 47144 | Dessert coppa malù classica al c | `Una combinazione unica di cacao e zucchero di canna` | Asserzione sensoriale e di unicità gustativa della combinazione di ingredienti: nessun contenuto amb |
| 50785 | Olio corpo tutti i tipi di pelle | `Idrata e rigenera la tua pelle rendendola radiosa e vitale` | Idratazione e rigenerazione della pelle con esito estetico: effetto sul substrato cutaneo (T2). |
| 50785 | Olio corpo tutti i tipi di pelle | `ingredienti dalle proprietà rigeneranti` | Proprieta' rigeneranti degli ingredienti riferite all'azione sulla pelle: asserzione di efficacia su |
| 50785 | Olio corpo tutti i tipi di pelle | `Formula dermatologicamente testata` | Asserzione relativa al processo probatorio (test dermatologico) e non all'impatto ambientale (T1). |
| 53999 | Cannelloni al ragù | `Tradizionali e gustosi` | Asserzione di qualità sensoriale (gustosi) unita al richiamo alla tradizione, priva di qualsiasi con |
| 53999 | Cannelloni al ragù | `Sfoglia tradizionale, ruvida e casereccia` | Descrizione della consistenza e dell'aspetto della sfoglia: qualità sensoriale del prodotto, nessun  |
| 54275 | Colorazione capelli oleo intense | `Professional quality color` | Affermazione di eccellenza il cui asse e' la qualità del risultato di colorazione, quindi prestazion |
| 54275 | Colorazione capelli oleo intense | `Supremo nutrimento e colore duraturo` | Superlativo su nutrimento del capello e durata del colore: asse prestazionale e durata di un effetto |
| 54275 | Colorazione capelli oleo intense | `Copertura Professionale dei Capelli Bianchi Fino al 100%` | Asserisce quanto bene la colorazione svolge la propria funzione (copertura dei capelli bianchi): eff |
| 54275 | Colorazione capelli oleo intense | `per una Suprema Intensità e Durata del Colore` | Superlativo sull'intensita' e sulla durata dell'effetto cosmetico del colore: asse prestazionale (St |
| 54275 | Colorazione capelli oleo intense | `Capelli visibilmente sani e forti` | Effetto sul substrato su cui il prodotto agisce (il capello) ex T2: efficacia cosmetica, non asserzi |
| 554877 | Siero anti macchie luminosità | `Schiarisce & riduce le macchie e ne previene la ricomparsa` | Schiarire e ridurre le macchie prevenendone la ricomparsa è un effetto sul substrato cutaneo, quindi |
| 554877 | Siero anti macchie luminosità | `Risultati visibili dopo 4 settimane` | La visibilità dei risultati dopo quattro settimane è la durata e la tempistica di un effetto cosmeti |
| 554877 | Siero anti macchie luminosità | `Il trattamento Nivea più efficace nella riduzione delle macchie cutanee` | Superlativo il cui asse di confronto è l'efficacia nella riduzione delle macchie, scartato da T4. |
| 554877 | Siero anti macchie luminosità | `riduce le macchie causate dal sole, dall'invecchiamento cutaneo, da fattori genetici ed ormonali` | La riduzione delle macchie di varia origine è un effetto sul substrato cutaneo su cui il prodotto ag |
| 554877 | Siero anti macchie luminosità | `Dopo 8 settimane: l'intensità delle macchie è ridotta del 50%` | La riduzione del 50% dell'intensità delle macchie a otto settimane è un'asserzione di efficacia quan |
| 554877 | Siero anti macchie luminosità | `Raccomandato dalle donne / 82% ha confermato / È il prodotto più efficace nel ridurre le macchie` | Le percentuali di consenso raccolte in autovalutazione sostengono un superlativo di efficacia del pr |
| 554877 | Siero anti macchie luminosità | `Una innovazione rivoluzionaria / Dopo 10 anni di meticolosa ricerca e lo studio di più 50.000 in` | «Innovazione rivoluzionaria» con il corredo degli anni di ricerca è un vanto sul merito tecnico del  |
| 554877 | Siero anti macchie luminosità | `Dermatologicamente comprovato` | «Dermatologicamente comprovato» è un'asserzione sul processo probatorio, collocata da T1 fra le asse |
| 554877 | Siero anti macchie luminosità | `Luminous630 è efficace su tutti i fototipi` | Asserzione di efficacia dell'ingrediente sul substrato cutaneo (tutti i fototipi): rientra nel passo |
| 56473 | Guaina per gestante inferiore tg | `In aiuto per alleviare questi disturbi viene l'uso di guaine per sostenere il peso del pancione` | Asserisce l'efficacia della guaina nell'alleviare i disturbi lombari sostenendo il peso: asse presta |
| 56904 | Riso arborio | `un riso di altissima qualità` | Superlativo sulla qualita del riso: asse di confronto prestazionale, non ambientale (T4). |
| 56904 | Riso arborio | `una consistenza superiore ed a una minore collosità del grano rispetto alle stesse varietà prodo` | Comparativo su consistenza e collosita del chicco, cioe su un asse sensoriale-prestazionale (T4). |
| 573102 | Detergente fluido senza risciacq | `contribuisce a rafforzare la barriera cutanea del bambino preservando il capitale cellulare dell` | Asserisce un effetto sul substrato cutaneo trattato dal prodotto, quindi prestazione ai sensi del ti |
| 575950 | Salviettine intime per il ciclo  | `Clinicamente testate` | Asserzione sul processo probatorio: prestazione per la regola T1 (seed D5). |
| 575950 | Salviettine intime per il ciclo  | `Contribuiscono a difendere il tuo equilibrio intimo` | Asserzione protettiva generica sull'equilibrio intimo, effetto sul substrato cutaneo: prestazione pe |
| 59190 | Latte intero gusto di una volta | `mantiene il gusto e la corposità dei sapori di un tempo` | Asserzione sensoriale su gusto e corposità: qualità organolettica del prodotto, senza contenuto ambi |
| 594304 | Aceto bianco di alcol | `Condisce, conserva e pulisce* ... Come da tradizione efficace anche nelle pulizie di casa` | Elenco delle funzioni del prodotto (condire, conservare, pulire) con nota sull'efficacia nelle puliz |
| 599962 | Colorazione capelli permanente 5 | `3x Volte più luminosi***` | «3x volte più luminosi» è un comparativo quantificato sull'asse della prestazione cosmetica dei cape |
| 599962 | Colorazione capelli permanente 5 | `Massima intensità del colore` | «Massima intensità del colore» è un superlativo sulla resa del prodotto nella sua funzione propria. |
| 599962 | Colorazione capelli permanente 5 | `Copre il 100% dei capelli bianchi` | La copertura del 100% dei capelli bianchi è un'asserzione di efficacia sul substrato trattato. |
| 599962 | Colorazione capelli permanente 5 | `Migliora la qualità visibile dei capelli***` | Il miglioramento della qualità visibile dei capelli è un effetto sul substrato su cui il prodotto ag |
| 599963 | Colorazione capelli permanente 5 | `3x Volte più luminosi***` | «3x volte più luminosi» è un comparativo quantificato sull'asse della prestazione cosmetica dei cape |
| 599963 | Colorazione capelli permanente 5 | `Massima intensità del colore` | «Massima intensità del colore» è un superlativo sulla resa del prodotto nella sua funzione propria. |
| 599963 | Colorazione capelli permanente 5 | `Copre il 100% dei capelli bianchi` | La copertura del 100% dei capelli bianchi è un'asserzione di efficacia sul substrato trattato. |
| 599963 | Colorazione capelli permanente 5 | `Migliora la qualità visibile dei capelli***` | Il miglioramento della qualità visibile dei capelli è un effetto sul substrato su cui il prodotto ag |
| 603896 | Riso basmati parboiled | `Blond è sinonimo di riso sempre al dente e garanzia di qualità` | Afferma una qualita sensoriale e prestazionale del riso («sempre al dente», «garanzia di qualita»),  |
| 608812 | Olio di semi di mais | `Testato e consigliato dall'Associazione Professionale Cuochi Italiani, che riunisce migliaia di ` | Avallo di un'associazione di cuochi sulla qualità professionale del prodotto: l'ente non certifica c |
| 609170 | Assorbenti lunghi con ali a inca | `L'asciutto pulito n°1* ... L'assorbente più venduto in Italia (dati Nielsen 12 mesi Feb '25)` | Superlativo il cui asse di confronto e' la prestazione dell'assorbente ('asciutto pulito n.1'): T4 l |
| 609170 | Assorbenti lunghi con ali a inca | `Con molecola attiva N.3 Zero odori` | Controllo degli odori mediante molecola attiva: funzione propria del prodotto (Step 2b), analogo al  |
| 610425 | Dentifricio white now rimuovi ma | `Clinicamente testato` | Asserzione sul processo probatorio, non su un nutriente o un esito di salute: prestazione per la reg |
| 610425 | Dentifricio white now rimuovi ma | `3x Denti più bianchi subito* ... Clinicamente provato su 58 soggetti, rispetto ad un dentifricio` | Comparativo il cui asse di confronto è la prestazione sbiancante, per quanto quantificato e corredat |
| 610425 | Dentifricio white now rimuovi ma | `Rimuove le macchie da caffè e fumo**` | Efficacia del dentifricio sul substrato dentale (rimozione delle macchie): passo 2b. |
| 610898 | Dentifricio maximum protezione c | `Il migliore di sempre* ... per una maggiore protezione dalla carie rispetto alla formula precede` | Superlativo il cui asse, esplicitato nella nota, e' la maggiore protezione dalla carie: confronto su |
| 610898 | Dentifricio maximum protezione c | `Smalto 4x più forte** ... A 2 settimane, minerali diversi rispetto ad un regolare dentifricio al` | Comparativo quantificato sull'efficacia rimineralizzante dello smalto rispetto a un dentifricio al f |
| 610898 | Dentifricio maximum protezione c | `neutralizza gli acidi che causano la carie prima che indeboliscano lo smalto` | Asserzione di efficacia sul substrato dentale (neutralizzazione degli acidi cariogeni), regolata com |
| 610909 | Pannolini più asciutto tg.6 xl 1 | `Più asciutto* ... rispetto agli altri pannolini tradizionali` | Comparativo sull'asciuttezza rispetto agli altri pannolini tradizionali: asse prestazionale, scartat |
| 610909 | Pannolini più asciutto tg.6 xl 1 | `Dermatologicamente testato` | Dermatologicamente testato: asserzione sul processo probatorio relativo alla pelle (T1), fuori dal p |
| 611508 | Sapone liquido mani aquarium | `Wash away bacteria` | Asserisce l'efficacia detergente/antibatterica del sapone sulle mani, cioe' cio' che il prodotto fa  |
| 612460 | Dentifricio con microgranuli | `Rinforza lo smalto` | Rafforzamento dello smalto: effetto sul substrato dentale, quindi prestazione del prodotto (T2). |
| 612460 | Dentifricio con microgranuli | `aiuta a prevenire la placca, rinforza lo smalto e protegge i denti dalla carie` | Prevenzione della placca, rafforzamento dello smalto e protezione dalla carie: efficacia sul substra |
| 612460 | Dentifricio con microgranuli | `Testato sotto controllo odontoiatrico` | Asserzione relativa al processo probatorio (controllo odontoiatrico) e non a una caratteristica ambi |
| 612659 | Biscotti al nesquik | `Ancora più friabili!` | Comparativo su un asse sensoriale (la friabilità): asse non ambientale, quindi resta scartato ex T4. |
| 616477 | Pannolini progressi tg.4 maxi 7- | `Pampers N°1 protezione e comfort* ... rispetto ai pannolini tradizionali pampers più venduti` | Primato su protezione e comfort confrontato con i pannolini tradizionali più venduti: l'asse del con |
| 616477 | Pannolini progressi tg.4 maxi 7- | `Il miglior Pampers per i primi passi*` | Superlativo sull'idoneità funzionale del pannolino per i primi passi: asse prestazionale, nessun con |
| 616477 | Pannolini progressi tg.4 maxi 7- | `12h Il più asciutto*` | Asciuttezza superlativa per 12 ore: durata dell'effetto del prodotto, non durabilità del bene ex Art |
| 616477 | Pannolini progressi tg.4 maxi 7- | `Il più soffice* al tatto` | Superlativo sensoriale sulla morbidezza al tatto: asse prestazionale, fuori dal perimetro ECGT (T4). |
| 616477 | Pannolini progressi tg.4 maxi 7- | `Approvato da AIDECO - Associazione Italiana Dermatologia e Cosmetologia` | Approvazione di un'associazione di dermatologia e cosmetologia: endorsement di efficacia e compatibi |
| 617095 | Pannolini progressi xl tg.6 +16k | `Pampers N°1 protezione e comfort` | Primato su protezione e comfort: superlativo su asse prestazionale, senza contenuto ambientale. |
| 617095 | Pannolini progressi xl tg.6 +16k | `Il miglior Pampers per le prime corse*` | Superlativo sull'idoneità funzionale del pannolino per le prime corse: asse prestazionale (T4), fuor |
| 617095 | Pannolini progressi xl tg.6 +16k | `Il più asciutto* 12h` | Asciuttezza superlativa per 12 ore: durata dell'effetto, non durabilità del bene; resta product_perf |
| 619902 | Burrocacao balsamo labbra soft r | `24h Idratazione` | «24h Idratazione» è la durata di un effetto cosmetico, che la guida al passo 3c esclude espressament |
| 619902 | Burrocacao balsamo labbra soft r | `Supporta la barriera protettiva delle labbra` | Il sostegno alla barriera protettiva delle labbra è un effetto sul substrato su cui il prodotto agis |
| 619902 | Burrocacao balsamo labbra soft r | `Compatibilità cutanea dermatologicamente approvata` | L'approvazione dermatologica della compatibilità cutanea è un'asserzione sul processo probatorio, ch |
| 620290 | Crema per le mani classica | `Aiuta a Rigenerare le pelli screpolate` | Effetto rigenerante sulla pelle screpolata, cioè sul substrato su cui il prodotto agisce: prestazion |
| 620290 | Crema per le mani classica | `Protegge dagli agenti esterni` | Asserzione protettiva generica: prestazione del prodotto (seed D6). |
| 620290 | Crema per le mani classica | `Dermatologicamente testata` | Asserzione sul processo probatorio: prestazione per la regola T1. |
| 62036 | Spray orale fresco pasta del cap | `svolge un'azione antibatterica naturale grazie alla presenza della Propoli` | Azione antibatterica del prodotto nel cavo orale, cioe' effetto sul substrato su cui agisce (Step 2b |
| 62036 | Spray orale fresco pasta del cap | `assicura una sensazione di immediata e durevole freschezza` | Asserzione sensoriale sulla freschezza percepita e sulla sua durata: efficacia/sensorialita' di prod |
| 62036 | Spray orale fresco pasta del cap | `garantisce sempre e in ogni circostanza un alito fresco e pulito` | Assoluto sull'efficacia antialitosi in ogni circostanza: asse prestazionale (Step 2b, T4). |
| 62036 | Spray orale fresco pasta del cap | `Propoli ... aiuta a ridurre la fermentazione batterica, contribuendo a una migliore Igiene Orale` | Riduzione della fermentazione batterica e miglioramento dell'igiene orale: effetto sul cavo orale co |
| 62036 | Spray orale fresco pasta del cap | `Sulfetal Zn ... ad azione antibatterica che contribuisce a rinfrescare l'alito` | Azione antibatterica di un ingrediente che rinfresca l'alito: efficacia del prodotto sul substrato ( |
| 62036 | Spray orale fresco pasta del cap | `L'efficacia del prodotto è stata testata e dimostrata` | Asserzione sul processo probatorio ('testata e dimostrata'), che T1 colloca in product_performance. |
| 636091 | Collutorio denti sensibili biosm | `Abbatte rapidamente il dolore` | Efficacia propria del dispositivo (abbattimento del dolore da sensibilita' dentinale): Step 2b; ness |
| 636091 | Collutorio denti sensibili biosm | `Risultati apprezzabili anche a lungo termine` | Durata nel tempo dei risultati d'uso: durata dell'effetto, che lo Step 3c esclude espressamente dall |
| 641361 | Maschera tessuto patch occhi vit | `Brightening & glow boosting eye mask` | Asserzione di effetto cosmetico illuminante sul contorno occhi: prestazione del prodotto (corrispond |
| 641361 | Maschera tessuto patch occhi vit | `Visibily brightens eye contour in 1 mask` | Effetto illuminante visibile sul contorno occhi dopo una applicazione: efficacia sul substrato cutan |
| 641361 | Maschera tessuto patch occhi vit | `Dermatologically Tested` | Asserzione relativa al processo probatorio (test dermatologico) (T1). |
| 644995 | Solare viso fluido anti imperfez | `-66% di imperfezioni** ... Test clinico condotto su 34 donne in 56 giorni di applicazione` | Efficacia quantificata sulla pelle sostenuta da test clinico: l'asse e' prestazionale, e la presenza |
| 644995 | Solare viso fluido anti imperfez | `12h Effetto mat* ... Test consumatori, 105 soggetti` | Durata dell'effetto cosmetico (12h effetto mat), espressamente esclusa dalla durabilità n-novies e t |
| 644995 | Solare viso fluido anti imperfez | `-31% Pori visibili**` | Riduzione quantificata dei pori visibili: efficacia sul substrato cutaneo (Step 2b). |
| 644995 | Solare viso fluido anti imperfez | `per correggere e prevenire le macchie` | Efficacia correttiva e preventiva sulle macchie cutanee: prestazione del prodotto (Step 2b). |
| 644995 | Solare viso fluido anti imperfez | `-55% di punti neri e bianchi, -32% di segni d'acne` | Riduzioni quantificate di punti neri e segni d'acne: efficacia sul substrato cutaneo (Step 2b). |
| 646175 | Salviettine pelli sensibili base | `Dermatologicamente testato su pelli sensibili` | Asserzione relativa al processo probatorio (test dermatologico su pelli sensibili) (T1). |
| 646175 | Salviettine pelli sensibili base | `Composizione che riduce il rischio di allergie` | Asserzione di efficacia/sicurezza sulla pelle priva di aggancio ECGT: non e' asserzione ambientale,  |
| 646175 | Salviettine pelli sensibili base | `Nichel, Cromo e Cobalto tested` | Asserzione relativa al processo probatorio (test su nichel, cromo e cobalto) riferita alla tollerabi |
| 646701 | Strozzapreti | `la migliore semola di grano duro pugliese` | Superlativo sulla qualita della semola: asse di confronto qualitativo-prestazionale e non ambientale |
| 65569 | Solare spray lozione air soft sp | `12h Idratazione` | Durata dell'effetto idratante (12h): espressamente qualificata come efficacia-durata e non come dura |
| 65569 | Solare spray lozione air soft sp | `Altamente resistente all'acqua` | Resistenza all'acqua del solare: caratteristica tecnica e prestazionale del prodotto (Step 2b). |
| 666692 | Lacca per capelli elnett fissagg | `Fissaggio 48H* ... Test strumentale` | Durata dell'effetto di fissaggio: la guida cita espressamente 'Fissaggio 48H*' come claim di durata  |
| 666692 | Lacca per capelli elnett fissagg | `protegge i capelli dal crespo e da aggressioni esterne` | Protezione del capello da crespo e aggressioni esterne: seed D14, efficacia sul substrato (Step 2b v |
| 666869 | Crema baby pasta protettiva | `Sollievo istantaneo¹, azione riparatrice` | Sollievo istantaneo dal fastidio da irritazione e azione riparatrice: efficacia sul substrato cutane |
| 666869 | Crema baby pasta protettiva | `Si prende cura della pelle per 12 h` | Cura della pelle per 12 ore: durata dell'effetto cosmetico, espressamente esclusa dalla nozione di d |
| 666869 | Crema baby pasta protettiva | `Testato & approvato da genitori e pediatri` | Testato e approvato da genitori e pediatri: endorsement su efficacia e tollerabilità (T1), da sogget |
| 666869 | Crema baby pasta protettiva | `Compatibilità cutanea dermatologicamente testata e comprovata` | Compatibilità cutanea dermatologicamente testata e comprovata: asserzione sul processo probatorio e  |
| 666874 | Doccia gel baby latte di mandorl | `Testato dai pediatri & approvato dai genitori` | Testato dai pediatri e approvato dai genitori: endorsement su efficacia e tollerabilità (T1), da sog |
| 666874 | Doccia gel baby latte di mandorl | `Compatibilità cutanea dermatologicamente testata e comprovata` | Compatibilità cutanea dermatologicamente testata e comprovata: asserzione sul processo probatorio e  |
| 666874 | Doccia gel baby latte di mandorl | `Formula ipoallergenica** ... con fragranza ipoallergenica identificata dall'opinione SCCS/1459/1` | Formula ipoallergenica con fragranza identificata da un'opinione SCCS: attributo di tollerabilità cu |
| 668466 | Brodo di verdure | `Come fatto in casa` | 'Come fatto in casa' asserisce una qualità sensoriale del prodotto, non un impatto ambientale. |
| 668466 | Brodo di verdure | `3h Cotto Lentamente come faresti tu` | Tempo e modalità di cottura lenta: fatto tecnico-sensoriale di preparazione, privo di contenuto ambi |
| 673140 | Balsamo capelli fini acqua light | `il 50% in più di agenti protettivi* ... rispetto alla formula precedente` | Comparativo quantificato il cui asse di confronto e' la prestazione (agenti protettivi del capello): |
| 673140 | Balsamo capelli fini acqua light | `aiuta a ricostituire i capelli dall'interno` | Effetto sul capello, substrato su cui il prodotto agisce (Step 2b via T2). |
| 673140 | Balsamo capelli fini acqua light | `Aiuta a rafforzare i capelli fini` | Efficacia rinforzante sul capello: effetto sul substrato (Step 2b via T2). |
| 673140 | Balsamo capelli fini acqua light | `Testato dell'Istituto Svizzero della Vitamina` | Asserzione sul processo probatorio (prodotto testato da un istituto), che T1 colloca in product_perf |
| 673142 | Balsamo capelli infinite lunghez | `Ripara* i capelli lunghi fino all'ultimo centimetro` | Riparazione del capello lungo fino alle punte: effetto sul substrato capillare (T2). |
| 673142 | Balsamo capelli infinite lunghez | `il 50% in più di agenti protettivi** ... rispetto alla formula precedente` | Comparativo quantificato il cui asse e' la quantità di agenti protettivi del capello, quindi prestaz |
| 673142 | Balsamo capelli infinite lunghez | `Testato dell'Istituto Svizzero della Vitamina` | Asserzione relativa al processo probatorio presso un ente terzo, priva di aggancio ECGT: non asseris |
| 674356 | Scrub corpo levigante esfoliante | `Dermatologicamente e ginecologicamente testato` | Asserzione relativa al processo probatorio (test dermatologico e ginecologico) e non a una caratteri |
| 674356 | Scrub corpo levigante esfoliante | `Leviga la pelle per aiutare a prevenire i peli incarniti` | Effetto levigante sulla pelle con prevenzione dei peli incarniti: efficacia sul substrato cutaneo, p |
| 676876 | Corpo crema idratante 48h rosa i | `tutta l'efficacia antiossidante della Rosa Fermentata e le proprietà idratanti e protettive dell` | Efficacia degli attivi sulla pelle (substrato): prestazione del prodotto per la regola T2. |
| 676876 | Corpo crema idratante 48h rosa i | `Dopo 48h dall'applicazione la pelle risulta più idratata* ... Test strumentale` | Durata dell'effetto idratante misurata da test strumentale: efficacia e durata dell'effetto, non dur |
| 676876 | Corpo crema idratante 48h rosa i | `Dopo l'utilizzo la pelle risulta più morbida e vellutata** ... Test di autovalutazione` | Effetto sensoriale sulla pelle attestato da autovalutazione: prestazione del prodotto (passo 2b). |
| 676876 | Corpo crema idratante 48h rosa i | `Clinicamente testato` | Asserzione sul processo probatorio: prestazione per la regola T1 (seed D5). |
| 676876 | Corpo crema idratante 48h rosa i | `stimola le acquaporine per una idratazione istantanea e duratura nel tempo` | Meccanismo d'azione e durata dell'idratazione sul substrato cutaneo: prestazione per la regola T2. |
| 698462 | Shampoo e balsamo post trattamen | `esclusivo complesso di cheratina vegetale e acido ialuronico ... fornendo la giusta dose di idra` | Descrive l'azione del complesso attivo sulla fibra del capello: efficacia cosmetica sul substrato (S |
| 698462 | Shampoo e balsamo post trattamen | `azione anti-crespo che aiuta a mantenere e prolungare la lisciatura` | Azione anti-crespo e durata dell'effetto lisciante: efficacia cosmetica sul capello (Step 2b via T2) |
| 698877 | Scrub corpo fruity pesca e cocco | `aiutano a rendere la pelle liscia e morbida` | Effetto levigante e ammorbidente sulla pelle: efficacia sul substrato cutaneo (T2). |
| 698877 | Scrub corpo fruity pesca e cocco | `Dermatologicamente testato` | Asserzione relativa al processo probatorio (test dermatologico) (T1). |
| 700703 | Integratore alimentare collagene | `Verisol - Beauty from Within` | Marchio di ingrediente e slogan di efficacia cosmetica: non e un marchio che certifica caratteristic |
| 700703 | Integratore alimentare collagene | `scelto da Equilibra per la sua efficacia testata` | Asserzione sull'efficacia testata dell'ingrediente: riguarda il processo probatorio e la prestazione |
| 704601 | Crema adesiva per dentiere total | `assicurando una presa sicura e duratura per l'intera giornata, fino a 12 ore` | Durata della tenuta adesiva fino a 12 ore: efficacia e durata dell'effetto, non durabilità del bene  |
| 704601 | Crema adesiva per dentiere total | `migliorando la fiducia in sé stessi e la qualità della vita quotidiana` | Beneficio di comfort e fiducia derivante dalla stabilità della protesi: asserzione sulla prestazione |
| 704601 | Crema adesiva per dentiere total | `formula clinicamente testata che assicura una tenuta eccezionalmente forte e duratura` | Asserzione sul processo probatorio («clinicamente testata») unita alla tenuta del prodotto: prestazi |
| 712712 | Shampoo antiforfora classic clea | `Fino a 100% protezione dalla forfora*` | La protezione dalla forfora fino al 100% è un'asserzione di efficacia del prodotto sul cuoio capellu |
| 712712 | Shampoo antiforfora classic clea | `forfora visibile eliminata al 100% in 66 casi su 100 (test clinico)` | L'eliminazione della forfora visibile nel 100% dei casi su 66 su 100 in test clinico è un'asserzione |
| 712712 | Shampoo antiforfora classic clea | `Clinicamente testato` | «Clinicamente testato» è un'asserzione sul processo probatorio, collocata da T1 fra le asserzioni di |
| 712712 | Shampoo antiforfora classic clea | `Dermatologicamente testato` | «Dermatologicamente testato» è un'asserzione sul processo probatorio, collocata da T1 fra le asserzi |
| 99051 | Farina di castagne | `vengono lavorate in tempi brevi per garantirti il massimo della freschezza` | Asserisce il massimo della freschezza quale qualita sensoriale ottenuta dalla rapidita di lavorazion |

### 3.2 `other_regime` — 90 claims

Governed by another body of law; every row carries a note. Main sub-groups: origin and authenticity (Art. 21), market-position/sales-ranking, mandatory labelling (`Etichetta Ambientale`), private retailer line marks, quality schemes (DOP/IGP/STG, Reg. (UE) 1151/2012), free-text social prose, and production-method claims.

| product | name | claim_text (verbatim) | rationale_it | note |
|---|---|---|---|---|
| 101501 | Burro | `la cui qualità è certificata da controlli lungo tutta la filiera` | Afferma che la qualità è certificata da controlli lungo la filiera: assicurazione di qualità/filiera | Assicurazione di qualità e controllo di filiera priva di contenuto ambientale — fuori  |
| 144287 | Semola rimacinata di grano duro  | `Dedicata a tutti coloro che onorano il ricordo delle vittime delle mafie attraverso il proprio i` | Dedica di carattere etico-sociale in prosa libera: l'ECGT raggiunge le caratteristiche sociali solta | Prosa sociale libera (impegno antimafia): nessun aggancio ECGT, perche n-quater riguar |
| 144400 | Proteggislip normali pure sensit | `Approvato da Skin Health Alliance` | Approvazione di un ente che non certifica caratteristiche ambientali o sociali: fuori dal perimetro  | third-party endorsement on a health/efficacy axis - no ECGT hook (Art. 23 lett. d Cod. |
| 145542 | Riso basmati profumato per ricet | `Autentico: riso Gallo seleziona le varietà più rinomate classificate come autentico "Basmati"` | Afferma l'autenticita della varieta e la selezione delle materie prime, senza alcuna asserzione di i | Art. 21 Cod. Cons. - autenticita varietale e selezione della materia prima, fuori dal  |
| 37815 | Pastina chiccoris | `100% Ingredienti controllati rigorosamente che soddisfano i nostri elevati standard qualitativi` | Controllo rigoroso degli ingredienti e standard qualitativi elevati: eccellenza di qualità senza con | Assicurazione generica di qualità e di controllo di filiera priva di contenuto ambient |
| 37815 | Pastina chiccoris | `Il latte materno è l'alimento ideale per il lattante` | Non è un'asserzione commerciale ma una menzione obbligatoria di legge sull'allattamento al seno, qui | Dicitura obbligatoria per alimenti destinati ai lattanti (Reg. (UE) 609/2013 e D.P.R.  |
| 38239 | Acqua effervescente naturale | `1500 Controlli di qualità giornalieri` | Numero di controlli di qualità: assicurazione di qualità senza alcun contenuto ambientale, fuori dal | Art. 21 Codice del Consumo (pratiche ingannevoli in generale) - vanto di controllo qua |
| 38765 | Vino rosso marzemino DOC trentin | `Raccolto a mano` | La raccolta manuale descrive una pratica produttiva e non un impatto ambientale, e non è un marchio  | Metodo di raccolta/produzione senza asserzione di impatto ambientale - Art. 18 lett. n |
| 39285 | Bevanda optimum succo di frutta  | `N°1 in Italia* ... Fonte: banche Dati IRI` | Afferma il primato di vendita in Italia, un'asserzione di mercato priva di contenuto ambientale. | market-position claim, Art. 21 Cod. Cons. - sales-ranking axis, outside the ECGT perim |
| 39538 | Cialde caffè espresso bar | `Etichetta Ambientale` | Dicitura obbligatoria di etichettatura ambientale degli imballaggi, esclusa dalla definizione di eti | Etichettatura ambientale degli imballaggi obbligatoria ex art. 219, comma 5, D.Lgs. 15 |
| 39785 | Merendine madeleine noire | `Céréal si impegna per voi` | Slogan di impegno aziendale privo di contenuto ambientale nel testo dell'asserzione. | corporate commitment slogan with no environmental content in the claim text itself - j |
| 39785 | Merendine madeleine noire | `Si consiglia di utilizzare il prodotto nell'ambito di una dieta varia ed equilibrata ed uno stil` | Disclosure obbligatoria e non un'asserzione idonea a influenzare la decisione commerciale: si ferma  | Avvertenza obbligatoria a corredo delle indicazioni nutrizionali e sulla salute, art.  |
| 40079 | Mutandine pannolino little swimm | `No.1 Brand* ... Basato su dati Nielsen aggregati in Europa, Medio Oriente, Africa` | Afferma la posizione di mercato del marchio e non un impatto ambientale, quindi non supera il gate d | market-position claim, Art. 21 Cod. Cons. - sales-ranking axis, outside the ECGT perim |
| 41401 | Zuppa tradizionale con orzo/farr | `Zuppa tradizionale` | 'Zuppa tradizionale' è la denominazione stessa del prodotto: pura identificazione, non un'asserzione | not_a_commercial_claim — coincide con la denominazione di vendita del prodotto |
| 41401 | Zuppa tradizionale con orzo/farr | `Il nostro impegno` | 'Il nostro impegno' introduce esclusivamente attributi di ricetta e nutrizionali (senza conservanti, | Impegno aziendale generico senza contenuto ambientale — nessun aggancio ECGT (non è as |
| 41690 | Pomodori secchi con pecorino sar | `accomodate a mano` | 'Accomodate a mano' descrive una modalità di lavorazione, non un impatto ambientale. | Art. 21 Codice del Consumo - descrizione del metodo di lavorazione manuale, priva di c |
| 41690 | Pomodori secchi con pecorino sar | `FIOR FIORE` | 'FIOR FIORE' è un marchio commerciale di gamma gastronomica, privo di riferimento a caratteristiche  | Marchio privato di linea premium: non è etichetta di sostenibilità ex art. 18 n-sexies |
| 41888 | Miele di castagno | `provenienti principalmente dalle regioni italiane più vocate` | Afferma la provenienza regionale del nettare e la vocazione dei territori, non un impatto ambientale | Asserzione di origine geografica con superlativo di vocazione produttiva: territorio d |
| 42118 | Mutandina 10 pyjama pants 4-7 an | `No 1 nighttime brand** ... dati Neilsen, Dicembre 2022` | Afferma una posizione di mercato (marca n.1) e non un impatto ambientale, quindi non supera il gate  | market-position claim, Art. 21 Cod. Cons. - sales-ranking axis, outside the ECGT perim |
| 429528 | Feta DOP | `FIOR FIORE` | Insegna di gamma qualitativa priva di contenuto ambientale o sociale, fuori dal perimetro ECGT. | Marchio commerciale privato di linea premium (qualità gastronomica), riportato nella s |
| 429528 | Feta DOP | `Etichetta Ambientale` | Dicitura obbligatoria di legge, esclusa per definizione dalle etichette di sostenibilità. | Etichettatura ambientale obbligatoria degli imballaggi (D.Lgs. 116/2020, art. 219 D.Lg |
| 429649 | Pane a legna arabo | `PANE ARABO-COTTO A LEGNA` | Coincide con la denominazione del prodotto e indica il metodo di cottura: nessuna asserzione di impa | Denominazione del prodotto e metodo di cottura (forno a legna): identificazione commer |
| 43145 | Tavoletta cioccolato extra fonde | `Acquistando questa tavoletta di cioccolato contribuisci a sostenere e promuovere lo sviluppo eco` | Asserzione di impatto sociale in prosa, priva di aggancio ECGT perché non ambientale e non veicolata | Asserzione sociale in prosa libera (sviluppo economico e sociale delle comunità produt |
| 43335 | Grissini integrali | `Etichetta ambientale` | Informativa/marchio reso obbligatorio dalla normativa nazionale sull'etichettatura ambientale degli  | Etichettatura ambientale obbligatoria degli imballaggi (D.Lgs. 116/2020, art. 219 D.Lg |
| 43616 | Wafer con crema alla nocciola | `Consumo moderato per i bambini` | Avvertenza di consumo moderato per i bambini: non è un'asserzione promozionale e non tocca il perime | Avvertenza volontaria sul profilo nutrizionale del prodotto (materia del Reg. (CE) 192 |
| 43792 | Zuppa campagnola | `Etichetta Ambientale` | Informativa/marchio reso obbligatorio dalla normativa nazionale sull'etichettatura ambientale degli  | Etichettatura ambientale obbligatoria degli imballaggi (D.Lgs. 116/2020, art. 219 D.Lg |
| 43907 | Pastina gemmine | `CRESCENDO` | Marchio di linea commerciale privo di contenuto ambientale o sociale: non e un'etichetta di sostenib | private retailer line mark with no environmental or social content - a trade mark, not |
| 44114 | Infuso di zenzero e curcuma | `#unsorsomigliore` | Slogan generico di qualita privo di contenuto ambientale. | generic quality slogan with no environmental content - no ECGT hook |
| 45171 | Seitan alla piastra | `Etichetta Ambientale` | Dicitura di legge obbligatoria sull'imballaggio, espressamente esclusa dal perimetro ECGT. | Etichettatura ambientale obbligatoria degli imballaggi (D.Lgs. 116/2020, art. 219 D.Lg |
| 47106 | Succo ace optimum | `N°1 in Italia* ... Fonte: banche Dati IRI` | Il primato di mercato non è un'asserzione ambientale né un'etichetta di sostenibilità. | market-position claim, Art. 21 Cod. Cons. - sales-ranking axis, outside the ECGT perim |
| 48442 | Mozzarella fior di latte | `Le nostre mucche vengono nutrite in modo tradizionale, con erba fresca, fieno e piante di campo.` | Il contesto di prodotto indica Mozzarella di Latte Fieno STG: il regime di alimentazione descritto e | Reg. (UE) 1151/2012 - specifica dello schema STG 'Latte Fieno/Heumilch' riformulata in |
| 50746 | Pasticcini lunette | `prodotta con i migliori ingredienti reperibili sul mercato` | Asserzione generica di eccellenza priva di contenuto ambientale. | generic excellence claim, no environmental content - S24/S25 superseded |
| 54957 | Prosciutto cotto alle erbe grigl | `Cottura lenta materie prime selezionate` | Vanto generico su cottura e materie prime senza alcun riferimento all'impatto ambientale. | Asserzione generica di qualità di processo e di selezione delle materie prime, priva d |
| 552334 | Burrata burratina senza lattosio | `BENE SI'` | Marchio di linea commerciale privo di contenuto ambientale o sociale: non e un'etichetta di sostenib | private retailer line mark with no environmental or social content - a trade mark, not |
| 554553 | Tisana digestiva plus con finocc | `#unsorsomigliore` | Slogan generico di qualita privo di contenuto ambientale. | generic quality slogan with no environmental content - no ECGT hook |
| 554704 | Succo nettare alla pesca | `Etichetta Ambientale` | È una disclosure obbligatoria di legge, espressamente esclusa dalla nozione di etichetta di sostenib | Etichettatura ambientale obbligatoria degli imballaggi (art. 219, comma 5, D.Lgs. 152/ |
| 56232 | Fagioli corona giganti lessati | `considerato tra i fagioli più pregiati` | Superlativo di pregio sul legume: asserzione di eccellenza generica senza aggancio ECGT. | Art. 21 Codice del Consumo - vanto generico di pregio del prodotto, privo di contenuto |
| 56394 | Base per pizza alla napoletana | `Stesa a mano` | Asserisce una modalita di lavorazione manuale, che non e ne asserzione di impatto ambientale ne etic | Metodo di lavorazione (stesura manuale dell'impasto): nessun impatto ambientale asseri |
| 56904 | Riso arborio | `questo garantisce che il Caranaroli, l'Arborio e il S. Andrea siano le varietà originali e non s` | Garanzia di autenticita varietale del riso, priva di contenuto ambientale e non resa in forma di mar | Art. 21 Cod. Cons. - autenticita varietale; profilo di qualita certificata riconducibi |
| 569248 | Latte fresco alta qualità 100% t | `da allevamenti prevalentemente piccoli e a conduzione familiare dove le mucche rappresentato il ` | Descrizione narrativa di carattere sociale sugli allevamenti conferenti, non in forma di etichetta e | Prosa sociale in forma libera sulla dimensione e conduzione degli allevamenti: la lett |
| 578874 | Latte al cacao x3 | `Cannuccia e incarto cannuccia plastica compostabile` | Identificazione del materiale nel blocco obbligatorio di etichettatura ambientale: non e un'asserzio | material identification inside the mandatory packaging-disposal block (prefixed '7 -') |
| 59190 | Latte intero gusto di una volta | `Un latte integro perché il tenore dei grassi non viene modificato dopo la mungitura` | Descrive un metodo di lavorazione (tenore di grassi non modificato dopo la mungitura): metodo produt | Informazione sugli alimenti / metodo di lavorazione — Reg. (UE) 1169/2011; nessun agga |
| 594304 | Aceto bianco di alcol | `L'aceto di alcol n.1 in Italia** ... Fonte: Dati Nielsen` | Primato di vendita nel segmento: asserzione di posizione di mercato, fuori dal perimetro ECGT. | market-position claim, Art. 21 Cod. Cons. - sales-ranking axis, outside the ECGT perim |
| 594304 | Aceto bianco di alcol | `Casaceto è leader nel segmento di riferimento, grazie alla sua funzione polivalente` | Rivendicazione di leadership di segmento motivata dalla polivalenza d'uso: nessun contenuto ambienta | Art. 21 Codice del Consumo - asserzione di leadership di mercato priva di contenuto am |
| 594623 | Confettura di ciliegia di vignol | `FIOR FIORE` | Marchio di linea gastronomica che non asserisce caratteristiche ambientali o sociali: fuori dal peri | Denominazione di una linea commerciale premium (marchio privato di gamma gastronomica) |
| 594623 | Confettura di ciliegia di vignol | `Etichetta Ambientale` | Dicitura obbligatoria di etichettatura ambientale degli imballaggi, esclusa dalla definizione di eti | Etichettatura ambientale degli imballaggi obbligatoria ex art. 219, comma 5, D.Lgs. 15 |
| 599157 | Biscotti dolcesenza allo yogurt | `Filiera Italiana: 100% farina di grano controllato e tracciato dalla semina al prodotto finito` | Asserzione di origine e tracciabilita: fuori dal perimetro ECGT. | origin + traceability assurance, Art. 21 Cod. Cons. - outside the ECGT perimeter |
| 599962 | Colorazione capelli permanente 5 | `Colorazione senza ammoniaca N°1 in Italia**** ... Fonte IRI, Totale Italia Mass Market` | Il primato rivendicato riguarda le quote di vendita nella categoria, non un impatto ambientale né un | market-position claim, Art. 21 Cod. Cons. - sales-ranking axis, outside the ECGT perim |
| 599963 | Colorazione capelli permanente 5 | `Colorazione senza ammoniaca N°1 in Italia**** ... Fonte IRI, Totale Italia Mass Market` | Il primato rivendicato riguarda le quote di vendita nella categoria, non un impatto ambientale né un | market-position claim, Art. 21 Cod. Cons. - sales-ranking axis, outside the ECGT perim |
| 602008 | Olio detergente struccante per p | `Etichetta Ambientale` | Informazione obbligatoria di etichettatura ambientale degli imballaggi, esclusa dalla definizione di | Etichetta Ambientale: informazione/marchio obbligatorio di etichettatura ambientale de |
| 603892 | Confettura all'albicocca natural | `Approvata da A.I.Nut. - Associazione Italiana Nutrizionisti` | Approvazione di un ente che non certifica caratteristiche ambientali o sociali: fuori dal perimetro  | third-party endorsement on a health/efficacy axis - no ECGT hook (Art. 23 lett. d Cod. |
| 608641 | Sapone liquido idratante ricaric | `Etichetta Ambientale` | Informazione obbligatoria di etichettatura ambientale degli imballaggi, esclusa dalla definizione di | Etichetta Ambientale: informazione/marchio obbligatorio di etichettatura ambientale de |
| 608812 | Olio di semi di mais | `La marca preferita dagli chef italiani* ... Indagine Nielsen ... campione rappresentativo di 600` | Preferenza dichiarata dagli chef: asserzione di posizione di mercato, fuori dal perimetro ECGT. | market-position claim, Art. 21 Cod. Cons. - sales-ranking axis, outside the ECGT perim |
| 609831 | Yogurt intero di capra | `le capre sono allevate nel rispetto del benessere animale` | Dichiarazione narrativa sulle pratiche di allevamento, priva di forma di etichetta e di asserzione d | Asserzione sul benessere animale in prosa libera e non in forma di marchio: la lett. n |
| 609831 | Yogurt intero di capra | `prodotti di massima qualità` | Superlativo di qualità generale che non asserisce alcun impatto ambientale. | Vanto assoluto di eccellenza qualitativa privo di contenuto ambientale: nel perimetro  |
| 610425 | Dentifricio white now rimuovi ma | `Approvato ANDI - Associazione Nazionale Dentisti Italiani (con spiegazione: l'A.N.D.I. riconosce` | Approvazione di un ente che non certifica caratteristiche ambientali o sociali: fuori dal perimetro  | third-party endorsement on a health/efficacy axis - no ECGT hook (Art. 23 lett. d Cod. |
| 610909 | Pannolini più asciutto tg.6 xl 1 | `Proud olympic and paralympic partner` | Dichiarazione di partnership olimpica e paralimpica: nessun contenuto ambientale e nessun marchio di | Sponsorizzazione sportiva (partnership olimpica e paralimpica): relazione commerciale  |
| 612212 | Albume d'uovo | `Etichetta Ambientale` | Informativa obbligatoria di smaltimento, non asserzione volontaria di sostenibilità. | Etichettatura ambientale obbligatoria degli imballaggi (D.Lgs. 116/2020, art. 219 D.Lg |
| 612460 | Dentifricio con microgranuli | `DAYTECH` | Marchio di linea commerciale privo di contenuto ambientale o sociale: non e un'etichetta di sostenib | private retailer line mark with no environmental or social content - a trade mark, not |
| 612460 | Dentifricio con microgranuli | `Etichetta Ambientale` | Marchio obbligatorio di etichettatura ambientale degli imballaggi, escluso dalla nozione di etichett | Etichettatura ambientale obbligatoria degli imballaggi ex art. 219, comma 5, D.Lgs. 15 |
| 612478 | Shampoo per capelli spenti delic | `Etichetta Ambientale` | Marchio/informazione obbligatoria di etichettatura ambientale degli imballaggi, espressamente esclus | Etichetta Ambientale: informazione/marchio obbligatorio di etichettatura ambientale de |
| 612659 | Biscotti al nesquik | `Il cacao certificato contribuisce a migliorare la vita dei coltivatori e delle loro famiglie` | Prosa sociale sul miglioramento delle condizioni di vita dei coltivatori: fuori dal perimetro ECGT s | Asserzione sociale in prosa libera, non in forma di marchio o etichetta: l'art. 18, le |
| 619225 | Salamini con bresaola | `Originale` | Non asserisce alcun impatto ambientale, non e' un marchio su caratteristiche ambientali o sociali e  | Asserzione di autenticita'/originalita' del prodotto: territorio generale dell'Art. 21 |
| 621126 | Cioccolatini gianduiotto nero | `Solo nocciole italiane` | Asserzione sull'origine italiana delle nocciole: territorio dell'art. 21 ma fuori dal perimetro ECGT | Asserzione di origine e autenticità: materia dell'art. 21 Cod. Cons. e della disciplin |
| 636091 | Collutorio denti sensibili biosm | `ricerca di 7 anni tutta italiana, in collaborazione con ISTEC-CNR` | Asserisce durata e provenienza della ricerca e una collaborazione con ISTEC-CNR: nessuna delle tre p | Affermazione di provenienza della ricerca e di collaborazione istituzionale: non e' as |
| 638347 | Pasta mini pennette | `Tracciabilità e sicurezza garantite da Oasi nella crescita` | Tracciabilità e sicurezza sono garanzie di qualità e filiera senza contenuto ambientale, quindi ness | Assicurazione generica di tracciabilità e sicurezza priva di contenuto ambientale - se |
| 638347 | Pasta mini pennette | `Elevati standard di qualità agricoltori italiani selezionati` | Asserisce standard qualitativi elevati e selezione degli agricoltori, senza alcuna asserzione di imp | Eccellenza generica e selezione dei fornitori priva di contenuto ambientale - seed S25 |
| 644934 | Crostini speziati | `Dadini speziati di pane artigianali` | Asserisce un metodo di produzione artigianale senza richiamo alla tradizione e senza alcuna asserzio | Metodo di produzione artigianale; eventualmente Art. 21 Cod. Cons. sulla natura del pr |
| 645376 | Fette biscottate proteiche | `Filiera Italiana: 100% farina di grano controllato e tracciato dalla semina al prodotto finito` | Asserzione di origine e tracciabilita: fuori dal perimetro ECGT. | origin + traceability assurance, Art. 21 Cod. Cons. - outside the ECGT perimeter |
| 646175 | Salviettine pelli sensibili base | `Etichetta Ambientale` | Marchio obbligatorio di etichettatura ambientale degli imballaggi, escluso dalla nozione di etichett | Etichettatura ambientale obbligatoria degli imballaggi ex art. 219, comma 5, D.Lgs. 15 |
| 646175 | Salviettine pelli sensibili base | `CRESCENDO` | Denominazione della linea di prodotto a marchio Coop (nel contesto: 'salviettine detergenti Crescend | Marchio commerciale / denominazione di linea del distributore; nessun riferimento a ca |
| 663509 | Confettura di pesche gialle natù | `Approvata da A.I.Nut. - Associazione Italiana Nutrizionisti` | Approvazione di un ente che non certifica caratteristiche ambientali o sociali: fuori dal perimetro  | third-party endorsement on a health/efficacy axis - no ECGT hook (Art. 23 lett. d Cod. |
| 664452 | Acqua effervescente naturale | `In bottiglia come nasce alla fonte` | Asserzione di autenticità sull'imbottigliamento alla fonte, che non afferma né implica alcun impatto | D.Lgs. 176/2011 sulle acque minerali naturali (imbottigliamento alla fonte) - asserzio |
| 664452 | Acqua effervescente naturale | `1.299 Controlli di qualità ogni giorno` | Numero di controlli giornalieri: assicurazione di qualità senza contenuto ambientale, fuori dal peri | Art. 21 Codice del Consumo - vanto di controllo qualità privo di contenuto ambientale |
| 665410 | Gorgonzola DOP dolce al cucchiai | `FIOR FIORE` | Denominazione di gamma qualitativa senza contenuto ambientale o sociale. | Marchio privato volontario di linea premium incluso nella denominazione di vendita, ri |
| 665410 | Gorgonzola DOP dolce al cucchiai | `Etichetta Ambientale` | Adempimento informativo obbligatorio, non etichetta volontaria di sostenibilità. | Etichettatura ambientale obbligatoria degli imballaggi (D.Lgs. 116/2020, art. 219 D.Lg |
| 668466 | Brodo di verdure | `N.1 in Italia* ... Dati di vendita Nielsen` | Primato di vendita in Italia: asserzione di posizione di mercato senza contenuto ambientale. | market-position claim, Art. 21 Cod. Cons. - sales-ranking axis, outside the ECGT perim |
| 668756 | Gallette di grano saraceno | `Etichetta Ambientale` | Informativa/marchio reso obbligatorio dalla normativa nazionale sull'etichettatura ambientale degli  | Etichettatura ambientale obbligatoria degli imballaggi (D.Lgs. 116/2020, art. 219 D.Lg |
| 673274 | Minestrone saporito | `N°1 in Italia# ... Fonte: NielsenIQ Market Track` | Primato di vendite sostenuto da una fonte di mercato: nessun contenuto ambientale, sociale o di dura | market-position claim, Art. 21 Cod. Cons. - sales-ranking axis, outside the ECGT perim |
| 704601 | Crema adesiva per dentiere total | `Affidati all'esperienza di Farmaciauno per prodotti che migliorano la tua qualità di vita` | Eccellenza generica del venditore priva di contenuto ambientale. | trader-level generic excellence, no environmental content |
| 704720 | Omogenizzato verdurine miste | `Prodotto in Italia* ... *Ingredienti di origine UE e non UE` | Asserisce il luogo di produzione con precisazione sull'origine degli ingredienti, senza contenuto am | Origine e autenticità - Art. 21 Cod. Cons., fuori dal perimetro ECGT |
| 704720 | Omogenizzato verdurine miste | `Tracciabilità e sicurezza` | Garanzia di filiera senza asserzione di impatto ambientale né marchio di sostenibilità: fuori dal pe | Assicurazione generica di tracciabilità e sicurezza priva di contenuto ambientale - se |
| 704720 | Omogenizzato verdurine miste | `Agricoltori selezionati` | La selezione degli agricoltori è un'assicurazione di filiera senza contenuto ambientale, quindi non  | Selezione dei fornitori/eccellenza generica priva di contenuto ambientale - seed S25 s |
| 709781 | Formaggio grattugiato italiano | `Fatto con latte della nostra filiera` | Rassicurazione sulla filiera senza alcun contenuto ambientale, quindi fuori dal perimetro ECGT. | Asserzione di filiera e di origine della materia prima (territorio dell'art. 21 Cod. C |
| 712712 | Shampoo antiforfora classic clea | `Brand antiforfora n.1 al mondo* ... Calcolo P&G basato su rapporti annuali sui dati di vendita` | Il primato rivendicato riguarda il volume di vendite del marchio nella categoria, non un impatto amb | market-position claim, Art. 21 Cod. Cons. - sales-ranking axis, outside the ECGT perim |
| 712712 | Shampoo antiforfora classic clea | `Approvato da Aideco` | Approvazione di un ente che non certifica caratteristiche ambientali o sociali: fuori dal perimetro  | third-party endorsement on a health/efficacy axis - no ECGT hook (Art. 23 lett. d Cod. |
| 717407 | Pandolce antica genova | `prodotta con i migliori ingredienti reperibili sul mercato` | Asserzione generica di eccellenza priva di contenuto ambientale. | generic excellence claim, no environmental content - S24/S25 superseded |
| 718993 | Polpa finissima | `riconosciamo loro il giusto compenso contro ogni sfruttamento della manodopera` | Impegno sociale sul giusto compenso espresso in forma discorsiva e non come marchio: nessun aggancio | Asserzione sociale in prosa libera: non è etichetta di sostenibilità ex art. 18 n-sexi |
| 718993 | Polpa finissima | `Da filiera corta` | Asserzione di filiera corta presentata dal record in chiave sociale: nessun impatto ambientale asser | short-supply-chain claim framed by the record as direct contracts and fair pay to farm |
| 99051 | Farina di castagne | `raccolte manualmente` | Descrive una pratica di raccolta manuale, cioe un metodo di produzione, non un impatto positivo o mi | Metodo di raccolta della materia prima: nessun impatto ambientale asserito, fuori dal  |

### 3.3 `health_nutrition` — 76 claims

Nutrition and health claims — Reg. (EC) 1924/2006 and Reg. (EU) 1169/2011.

| product | name | claim_text (verbatim) | rationale_it |
|---|---|---|---|
| 38239 | Acqua effervescente naturale | `può avere effetti diuretici; aiuta la digestione; può combattere la dispepsia; può svolgere azio` | Effetti diuretici, digestivi e apporto di calcio per le ossa: indicazioni sulla salute, materia dei  |
| 38379 | Integratore salino arancia | `Energade reintegra e disseta` | Reintegro salino e azione dissetante: effetto su funzioni fisiologiche per ingestione. |
| 40263 | Integratore melatonina x75 | `riduce il tempo richiesto per prendere sonno e può contribuire ad alleviare gli effetti del jet ` | Riduzione del tempo di addormentamento e attenuazione del jet lag: effetto fisiologico da ingestione |
| 40494 | Integratore magnesio | `Il Magnesio contribuisce alla riduzione della stanchezza e dell'affaticamento, al normale funzio` | Funzioni fisiologiche del magnesio (stanchezza, sistema nervoso, ossa e denti): claim sulla salute e |
| 41185 | Integratore biofoltil forte vegi | `Zinco e Selenio contribuiscono al mantenimento di unghie normali ... Biotina contribuiscono al m` | Contributi di zinco, selenio e biotina al mantenimento di unghie e capelli normali: claim sulla salu |
| 41185 | Integratore biofoltil forte vegi | `Gli estratti di Miglio e Bambù favoriscono il benessere di unghie e capelli` | Benessere di unghie e capelli attribuito a estratti botanici assunti per via orale: claim salutistic |
| 41401 | Zuppa tradizionale con orzo/farr | `equivale ad 1 delle 5 porzioni giornaliere di frutta e verdura raccomandate dall'Organizzazione ` | Equivalenza con una porzione giornaliera di frutta e verdura raccomandata dall'OMS: claim nutriziona |
| 41401 | Zuppa tradizionale con orzo/farr | `Fonte di fibre` | Claim nutrizionale sulle fibre (cfr. seed D3). |
| 41494 | Integratore multivitamine e mine | `contribuiscono alla riduzione della stanchezza e dell'affaticamento e alla normale funzione del ` | Elenco di funzioni fisiologiche di vitamine e minerali: claim nutrizionali e sulla salute ex Reg. (C |
| 418104 | Patatine la non patatina | `65% di Grassi in Meno*` | Indica il livello di un nutriente (i grassi) presentato come vantaggioso: indicazione nutrizionale c |
| 418104 | Patatine la non patatina | `Si alla linea, no allo fame!` | Richiamo al controllo del peso e al senso di fame: asserzione dimagrante e nutrizionale di competenz |
| 41908 | Panetti pane di kamut stirati a  | `Come smaltire le calorie in eccesso? Ad esempio 7 minuti di corsa equivalgono a circa 100 kcal` | Equivalenza tra calorie e attività fisica: informazione nutrizionale/energetica. |
| 43792 | Zuppa campagnola | `Fonte di proteine` | Claim nutrizionale sul tenore di proteine, disciplinato dal Reg. (CE) 1924/2006. |
| 44114 | Infuso di zenzero e curcuma | `Speziato e Antiossidante` | Afferma una proprietà antiossidante, cioè un effetto/contenuto benefico per l'organismo: territorio  |
| 44114 | Infuso di zenzero e curcuma | `Contiene curcuma che possiede proprietà antiossidanti` | Attribuisce alla curcuma proprietà antiossidanti, cioè un effetto fisiologico da ingestione: claim s |
| 44114 | Infuso di zenzero e curcuma | `è un alleato dello stomaco e della digestione` | Afferma un effetto su stomaco e digestione, cioè su una funzione fisiologica: Reg. (CE) 1924/2006. |
| 44887 | Yogurt actimel ai frutti di bosc | `Supporta il Sistema Immunitario* ... Grazie alle vitamine D e B6, che aiutano il buon funzioname` | Claim sul supporto al sistema immunitario grazie a vitamine D e B6: disciplina dei claim salutistici |
| 44887 | Yogurt actimel ai frutti di bosc | `20 miliardi del nostro esclusivo probiotico L. casei Danone` | Asserzione sulla quantità di probiotico contenuto, presentata come benefica per l'organismo: territo |
| 44887 | Yogurt actimel ai frutti di bosc | `Le vitamine vengono assorbite nell'intestino, per poi supportare il tuo sistema immunitario` | Asserzione su assorbimento intestinale delle vitamine e funzione immunitaria: claim su una funzione  |
| 47286 | Bevanda UHT da latte parzialment | `-30% di zuccheri rispetto al latte` | Asserzione sul tenore di zuccheri ridotto rispetto al latte: claim nutrizionale ex Reg. (CE) 1924/20 |
| 47286 | Bevanda UHT da latte parzialment | `Il Calcio ... necessario per il mantenimento delle ossa e dei denti normali` | Claim salutistico autorizzato sul calcio e il mantenimento di ossa e denti: territorio del Reg. (CE) |
| 50746 | Pasticcini lunette | `Senza grassi idrogenati` | Asserzione sull'assenza di grassi idrogenati, cioè sulla composizione nutrizionale: Reg. (CE) 1924/2 |
| 552334 | Burrata burratina senza lattosio | `Alta digeribilità` | Asserzione su una funzione fisiologica (digeribilità) riferita all'ingestione del prodotto. |
| 552585 | Integratore alimentare per siste | `Propoli ... tradizionalmente utilizzata per i suoi benefici` | Attribuisce alla propoli benefici per l'organismo: claim salutistico su base botanica, territorio de |
| 552585 | Integratore alimentare per siste | `Vitamina C alto dosata, che contribuisce alla normale funzione del sistema immunitario e alla ri` | Claim salutistico sulla vitamina C (sistema immunitario, stanchezza e affaticamento): Reg. (CE) 1924 |
| 554553 | Tisana digestiva plus con finocc | `Più erbe funzionali` | «Erbe funzionali» in maggiore quantità afferma la presenza/livello di sostanze presentate come benef |
| 554553 | Tisana digestiva plus con finocc | `Le sue proprietà calmanti e distensive, aiutano e facilitano i naturali processi digestivi` | Afferma proprietà calmanti e un effetto sui processi digestivi: claim salutistico ex Reg. (CE) 1924/ |
| 554553 | Tisana digestiva plus con finocc | `Conosciuto come uno dei migliori rimedi naturali per sconfiggere il gonfiore addominale e tutti ` | Attribuisce al finocchio la capacità di contrastare gonfiore addominale e disturbi digestivi: claim  |
| 554553 | Tisana digestiva plus con finocc | `è un ottimo coadiuvante nella digestione e contribuisce al normale funzionamento del tratto inte` | Afferma un contributo alla digestione e al normale funzionamento intestinale: funzione fisiologica,  |
| 58406 | Formaggio primo sale | `Il calcio contribuisce alla normale funzione muscolare` | Indicazione sulla salute autorizzata relativa al calcio e alla funzione muscolare, disciplinata dal  |
| 58406 | Formaggio primo sale | `Le proteine contribuiscono al mantenimento della massa muscolare` | Indicazione sulla salute relativa alle proteine e al mantenimento della massa muscolare. |
| 58406 | Formaggio primo sale | `Ricca in calcio` | Indicazione nutrizionale sul tenore di calcio. |
| 58406 | Formaggio primo sale | `Fonte naturale di proteine` | Indicazione nutrizionale sul tenore di proteine. |
| 58758 | Tonno al naturale | `Ricco di proteine**` | 'Ricco di proteine' è un'indicazione nutrizionale disciplinata dal Reg. (CE) 1924/2006. |
| 588549 | Prosciutto cotto snello grancott | `Mangia sano, vivi Snello` | Slogan che collega il consumo del prodotto alla salute e alla linea: rientra nella disciplina delle  |
| 590807 | Integratore alimentare energià p | `Ginseng e Guaranà, piante ad azione tonica, utili in caso di stanchezza fisica e mentale` | Azione tonica di ginseng e guaranà in caso di stanchezza fisica e mentale: effetto su una funzione f |
| 590807 | Integratore alimentare energià p | `utili per il normale metabolismo energetico e per la riduzione di stanchezza e affaticamento` | Contributo al normale metabolismo energetico e alla riduzione della stanchezza: claim sulla salute e |
| 599157 | Biscotti dolcesenza allo yogurt | `Per un minore aumento della glicemia*` | Asserisce un effetto sulla glicemia dopo il consumo: indicazione sulla salute di competenza del Reg. |
| 599157 | Biscotti dolcesenza allo yogurt | `Fonte di fibre` | Indicazione nutrizionale sul contenuto di fibre (seme D3). |
| 603657 | Latte fresco parzialmente screma | `Il latte è una fonte naturale di Calcio, necessario per il mantenimento di ossa e denti normali` | Indicazione sulla salute relativa al calcio e al mantenimento di ossa e denti. |
| 603892 | Confettura all'albicocca natural | `Fonte di fibre` | Claim nutrizionale sul contenuto di fibre, disciplinato dal Reg. (CE) 1924/2006. |
| 612212 | Albume d'uovo | `Naturalmente ricco di proteine` | Indicazione nutrizionale sul tenore di proteine. |
| 612659 | Biscotti al nesquik | `-50% di grassi saturi* ... Fonte Unione Italiana Food Mercato Italia` | Indicazione nutrizionale comparativa sul contenuto di grassi saturi, di competenza del Reg. (CE) 192 |
| 613810 | Integratore alimentare potassio/ | `contribuisce all'equilibrio elettrolitico / alla riduzione di stanchezza e affaticamento / al no` | Elenco di funzioni fisiologiche attribuite a magnesio e potassio: claim nutrizionali e sulla salute  |
| 613815 | Integratore alimentare potassio  | `per offrire una formula Potenziata con più Potassio e più Magnesio rispetto alle precedenti form` | Il confronto con le formulazioni precedenti verte sul tenore di nutrienti (più potassio e più magnes |
| 617650 | Integratore alimentare immunity  | `Il Reishi, un fungo conosciuto per le proprietà benefiche, contribuisce alle naturali difese del` | Proprietà benefiche del reishi sulle naturali difese dell'organismo: claim salutistico su funzione i |
| 617650 | Integratore alimentare immunity  | `L'Echinacea contribuisce alle naturali difese dell'organismo e alla funzionalità delle prime vie` | Contributo dell'echinacea alle difese dell'organismo e alla funzionalità delle vie respiratorie: cla |
| 617650 | Integratore alimentare immunity  | `Lo Zinco contribuisce alla normale funzione del sistema immunitario` | Contributo dello zinco alla normale funzione del sistema immunitario: claim sulla salute autorizzato |
| 617651 | Integratore alimentare botanico  | `L'escolzia e il tiglio contribuiscono al rilassamento (sonno, in caso di stress)` | Contributo di escolzia e tiglio al rilassamento e al sonno: effetto su una funzione fisiologica, fuo |
| 617651 | Integratore alimentare botanico  | `La passiflora contribuisce al rilassamento e al benessere mentale` | Contributo della passiflora al rilassamento e al benessere mentale: claim sulla salute, disciplina d |
| 617926 | Dessert proteico creme caramel h | `Oltre il 50% di zuccheri in meno* ... Fonte IRI` | Comparativa sul tenore di zuccheri: claim nutrizionale comparativo ex Reg. (CE) 1924/2006. |
| 617926 | Dessert proteico creme caramel h | `Ricco in proteine. Le proteine contribuiscono alla crescita della massa muscolare` | Claim nutrizionale e salutistico su proteine e massa muscolare. |
| 617926 | Dessert proteico creme caramel h | `PROTEIN +` | Marchio/dicitura 'PROTEIN +' riferita al contenuto proteico: non distingue caratteristiche ambiental |
| 619225 | Salamini con bresaola | `Ricco in proteine - 37g Per 100g di prodotto` | Indicazione nutrizionale sul tenore di proteine, governata dal Reg. (CE) 1924/2006 e dal Reg. (UE) 1 |
| 63679 | Infuso collection aromatizzati | `Naturalmente priva di caffeina` | Indica l'assenza di una sostanza (la caffeina): indicazione di contenuto di competenza del Reg. (CE) |
| 645376 | Fette biscottate proteiche | `Ricca di Proteine che contribuiscono alla crescita e al mantenimento della massa muscolare` | Indicazione nutrizionale e sulla salute relativa alle proteine e alla massa muscolare, di competenza |
| 645376 | Fette biscottate proteiche | `PROTEIN +` | Il marchio «PROTEIN +» afferma il tenore di un nutriente presentato come benefico, materia del Reg.  |
| 663509 | Confettura di pesche gialle natù | `Fonte di fibre` | Claim nutrizionale sul contenuto di fibre disciplinato dal Reg. (CE) 1924/2006 e dal Reg. (UE) 1169/ |
| 664157 | Integratore alimentare collagene | `formulato per contribuire a contrastare i fattori di invecchiamento della pelle` | Integratore presentato come formulato per contrastare l'invecchiamento cutaneo per via di assunzione |
| 664157 | Integratore alimentare collagene | `La Vitamina C contribuisce alla normale formazione del collagene` | Funzione della vitamina C sulla formazione del collagene: claim sulla salute autorizzato ex Reg. (CE |
| 664452 | Acqua effervescente naturale | `Facilita la digestione / È indicata per le diete iposodiche / Può avere effetti diuretici ... D.` | Digestione, dieta iposodica ed effetti diuretici: indicazioni su funzioni fisiologiche, disciplinate |
| 672184 | Integratore alimentare al mirtil | `Mirtillo antiossidante, utile per il benessere della vista e la funzionalità del microcircolo` | Attribuisce al mirtillo proprieta antiossidanti e benefici per vista e microcircolo: claim salutisti |
| 672184 | Integratore alimentare al mirtil | `Zinco ... contribuisce al normale metabolismo della vitamina A e al normale funzionamento del si` | Claim salutistico sullo zinco (metabolismo della vitamina A e sistema immunitario): Reg. (CE) 1924/2 |
| 672184 | Integratore alimentare al mirtil | `Vitamina B2 ... contribuisce alla protezione delle cellule dallo stress ossidativo e contribuisc` | Claim salutistico sulla vitamina B2 (stress ossidativo e capacita visiva): Reg. (CE) 1924/2006. |
| 673274 | Minestrone saporito | `Fonte di fibre` | Claim nutrizionale sulle fibre (cfr. seed D3). |
| 675785 | Caramelle con erbe alpine echina | `Supporta le difese immunitarie` | Asserisce un effetto sulla funzione immunitaria: indicazione sulla salute di competenza del Reg. (CE |
| 700703 | Integratore alimentare collagene | `Aiuta a ridurre l'aspetto delle rughe` | Integratore che asserisce un effetto sull'aspetto delle rughe conseguente all'ingestione: effetto fi |
| 700703 | Integratore alimentare collagene | `Favorisce l'elasticità e il tono della pelle` | Asserisce un effetto su elasticita e tono della pelle ottenuto per via alimentare: effetto fisiologi |
| 700703 | Integratore alimentare collagene | `Un'assunzione costante per 8 settimane aiuta a migliorare l'aspetto della pelle favorendo elasti` | Effetto su elasticità, tonicità e rughe ottenuto per assunzione: claim salutistico ex Reg. (CE) 1924 |
| 700710 | Integratore alimentare sonno&rel | `1 mg di Melatonina, utile per ridurre il tempo richiesto per prendere sonno` | Attribuisce alla melatonina un effetto fisiologico sul tempo di addormentamento: claim salutistico e |
| 700710 | Integratore alimentare sonno&rel | `estratti di Valeriana e Passiflora tradizionalmente noti per favorire il rilassamento e il sonno` | Attribuisce a valeriana e passiflora un effetto sul rilassamento e sul sonno: claim salutistico su b |
| 700710 | Integratore alimentare sonno&rel | `Passiflora e Melissa sono utili per il benessere mentale` | Attribuisce a passiflora e melissa un effetto sul benessere mentale: claim salutistico ex Reg. (CE)  |
| 700710 | Integratore alimentare sonno&rel | `La Niacina completa la formulazione contribuendo al normale funzionamento del sistema nervoso` | Claim salutistico autorizzato sulla niacina e sul funzionamento del sistema nervoso: Reg. (CE) 1924/ |
| 701225 | Alternativa vegetale allo yogurt | `Con 5 nutrienti essenziali ... contribuisce all'assunzione quotidiana di 5 tra i Nutrienti Essen` | Asserzione sull'apporto di nutrienti essenziali: claim nutrizionale ex Reg. (CE) 1924/2006 e Reg. (U |
| 703021 | Succo di pera intenso | `Fonte di vitamina C` | Indicazione nutrizionale sul contenuto di vitamina C, regolata dal Reg. (CE) 1924/2006. |
| 704601 | Crema adesiva per dentiere total | `Questo si traduce in una migliore digestione e un maggiore piacere nel mangiare` | Afferma un effetto sulla digestione, materia del Reg. (CE) 1924/2006 e del Reg. (UE) 1169/2011, non  |

### 3.4 `heritage_origin` — 51 claims

Claims about the past: founding dates, family history, recipe provenance, historical typicality.

| product | name | claim_text (verbatim) | rationale_it |
|---|---|---|---|
| 104322 | Vermouth rosso | `Traditional recipe` | 'Traditional recipe' asserisce la provenienza tradizionale della ricetta, quindi il passato del prod |
| 104322 | Vermouth rosso | `rispetta la tradizione poiché viene prodotto secondo un'antica ricetta` | Rispetto della tradizione e antica ricetta: asserzione sulla provenienza storica della ricetta. |
| 164990 | Lievito vanigliato x10 | `Con 80 anni di tradizione` | Richiamo a ottant'anni di tradizione: asserzione sul passato ex Step 2c. |
| 37815 | Pastina chiccoris | `Oltre 100 anni di storia / L'amore per la tradizione` | Riferimento a oltre cento anni di storia e all'amore per la tradizione: asserzione sul passato dell' |
| 38130 | Fagioli borlotti lamon lessati | `La coltivazione dei fagioli "Phaseolus vulgaris" ebbe inizio in America ... introdotto in Veneto` | Racconto storico sull'introduzione del fagiolo in Veneto nel 1550: asserzione sul passato. |
| 38202 | Funghi trifolati in olio girasol | `secondo la tradizionale ricetta` | Preparazione secondo la ricetta tradizionale: asserzione sulla provenienza della ricetta. |
| 38765 | Vino rosso marzemino DOC trentin | `Celebrato nel "Don Giovanni" di Mozart` | Riferimento culturale-storico al 'Don Giovanni' di Mozart: asserzione sul passato, priva di contenut |
| 38771 | Vino rosso lambrusco di castelve | `Vinificato con metodi tradizionali` | Asserzione su un metodo produttivo tradizionale, che non afferma alcun impatto ambientale (T5 ritira |
| 40713 | Caramelle alla liquirizia puriss | `Fatto in Italia da sempre` | Unisce origine italiana e continuità storica («da sempre»): asserzione sul passato ex Step 2c e comu |
| 41567 | Vol au vent | `Artigianale sfogliato a mano` | Asserisce un metodo di lavorazione artigianale con appello alla tradizione e non un impatto ambienta |
| 41908 | Panetti pane di kamut stirati a  | `Artigianali dentro` | 'Artigianali dentro' richiama la lavorazione artigianale e la tradizione produttiva: nessuna asserzi |
| 429528 | Feta DOP | `il formaggio greco più antico, risalente all'età omerica` | Asserzione sull'antichità e sulla tipicità storica del formaggio: riguarda il passato, non l'ambient |
| 43335 | Grissini integrali | `prodotti con un metodo tradizionale` | Metodo tradizionale di produzione: asserzione su un metodo e sulla tradizione, non su un impatto amb |
| 45183 | Burro | `Burro tradizionale` | 'Burro tradizionale' richiama la tipicità e il metodo di lavorazione tradizionale, non un impatto am |
| 50746 | Pasticcini lunette | `la tradizionale, autentica pastafrolla di Grondona` | Afferma tradizione e autenticità della ricetta di pastafrolla: asserzione di provenienza storica, St |
| 50746 | Pasticcini lunette | `È una ricetta di inizio Ottocento` | Data la ricetta all'inizio dell'Ottocento: asserzione sul passato, Step 2c. |
| 50746 | Pasticcini lunette | `le inimitabili ricette di famiglia` | Superlativo agganciato alle ricette di famiglia: prevale la qualificazione di provenienza storica (T |
| 50746 | Pasticcini lunette | `Dal 1820 la famiglia Grondona garantisce` | Richiama la data di fondazione e la garanzia familiare: asserzione sul passato, Step 2c. |
| 53999 | Cannelloni al ragù | `Ragù secondo la tradizione` | Richiamo alla provenienza tradizionale della ricetta, privo di contenuto ambientale. |
| 55274 | Capocollo di martina franca | `Salume tipico artigianale della Puglia` | Tipicita' territoriale e artigianalità del salume: asserzione di origine e tradizione, senza contenu |
| 55274 | Capocollo di martina franca | `Conosciuto ed apprezzato già nel XVII secolo` | Riferimento esplicito al passato (XVII secolo) come elemento di tipicità storica. |
| 55274 | Capocollo di martina franca | `prodotto con metodi artigianali` | Metodo produttivo artigianale richiamato come tradizione: pratica di lavorazione, non impatto ambien |
| 56232 | Fagioli corona giganti lessati | `pare che il suo nome gli fosse stato attribuito perché ambito e presente sulla tavola dei Re` | Aneddoto storico sull'origine del nome del fagiolo: asserzione sul passato. |
| 56394 | Base per pizza alla napoletana | `La ricetta della tradizione` | Richiamo alla ricetta della tradizione: provenienza storica della ricetta, Step 2c. |
| 59190 | Latte intero gusto di una volta | `hanno conservato il patrimonio genetico delle "mucche di un tempo"` | Riferimento al patrimonio genetico delle 'mucche di un tempo': asserzione sul passato e sulla tipici |
| 59190 | Latte intero gusto di una volta | `betacaseina è unicamente A2, come era una volta` | Asserzione compositiva ancorata alla tipicità del passato ('come era una volta'), priva di contenuto |
| 594304 | Aceto bianco di alcol | `L'originale` | 'L'originale' rivendica priorità e autenticità del prodotto rispetto alle imitazioni, senza alcun co |
| 598057 | Yogurt extra goloso con caramell | `allevate secondo i metodi alpini tradizionali` | Metodo di allevamento presentato come tradizione alpina (peraltro coerente con il disciplinare Latte |
| 603896 | Riso basmati parboiled | `Siamo stati tra le prime aziende a introdurre il riso parboiled in Italia` | Asserzione sul passato dell'impresa (essere stati fra i primi a introdurre il parboiled in Italia):  |
| 603896 | Riso basmati parboiled | `tra i più antichi che la storia tramandi` | Afferma l'antichita storica del processo di parboilizzazione: tipicita storica, Step 2c. |
| 609831 | Yogurt intero di capra | `mantenendo l'artigianalità` | Richiamo all'artigianalità come metodo tradizionale di lavorazione, senza asserzione di impatto ambi |
| 63837 | Pandolce antico | `il più tipico dei dolci tradizionali genovesi` | Afferma la tipicità storica di un dolce tradizionale genovese: asserzione sul passato, Step 2c. |
| 63837 | Pandolce antico | `la cui ricetta originale, creata nel XVI secolo ai tempi di Andrea D’Oria` | Afferma la provenienza storica della ricetta (XVI secolo, Andrea D'Oria): asserzione sul passato, St |
| 639927 | Alici filetti | `Antica tradizione` | 'Antica tradizione' richiama esplicitamente il passato del prodotto, senza contenuto ambientale. |
| 639927 | Alici filetti | `Lavorazione artigianale` | Lavorazione artigianale: metodo produttivo presentato come richiamo alla tradizione, privo di asserz |
| 641458 | Caramelle gommose liquirizia kim | `L'originale` | Asserzione di autenticità e primogenitura del prodotto: appello alla provenienza originaria ex Step  |
| 646701 | Strozzapreti | `macinato nei mulini locali secondo tecniche secolari` | Metodo di macinazione presentato come tecnica secolare presso mulini locali: richiamo alla tradizion |
| 646701 | Strozzapreti | `attenzione e cura artigianale, imitando le antiche tecniche della pasta fatta in casa, tramandat` | Richiamo esplicito ad antiche tecniche tramandate da generazioni: Step 2c. |
| 65971 | Olio extravergine d'oliva | `selezionato dalla famiglia Santagata assaggiatori di olio dal 1907` | Selezione da parte della famiglia con data di fondazione 1907: storia familiare e anno di fondazione |
| 66541 | Grappa tradizione barricata | `GRAPPA TRADIZIONALE` | Qualifica la grappa come tradizionale, richiamo alla tipicità storica senza contenuto ambientale. |
| 66541 | Grappa tradizione barricata | `DISTILLATA CON METODO ARTIGIANALE IN PICCOLI ALAMBICCHI DI RAME` | Descrive un metodo di distillazione artigianale, cioè una pratica produttiva di tradizione e non un' |
| 675785 | Caramelle con erbe alpine echina | `Contiene la tradizionale miscela di 13 erbe` | Richiama la tipicità storica di una miscela «tradizionale» di erbe: asserzione sul passato ex Step 2 |
| 68928 | Patatine 1936 multipack | `Antica ricetta` | Richiama l'antichità della ricetta: asserzione sul passato, Step 2c. |
| 68928 | Patatine 1936 multipack | `tramandata di generazione in generazione` | Afferma la trasmissione generazionale del sapere produttivo: asserzione di tradizione e provenienza  |
| 702976 | Coppa taglio fresco | `Lenta stagionatura tradizionale di minimo 3 mesi` | Metodo di produzione presentato come tradizionale: T5 e' stata ritirata, il claim asserisce un metod |
| 709781 | Formaggio grattugiato italiano | `prodotto con metodo tradizionale in caldaie di rame` | Metodo di produzione presentato come tradizionale: asserisce una pratica produttiva, non un impatto  |
| 713295 | Succo di frutta pesca/limone mix | `Lavorazioni tradizionali (macinazione, spremitura..)` | Asserisce un metodo di lavorazione tradizionale, cioè un richiamo alla tradizione e non un impatto a |
| 717407 | Pandolce antica genova | `le "ricette di famiglia"` | Provenienza della ricetta e storia familiare: asserzione sul passato ex Step 2c, vicinissima al seme |
| 717407 | Pandolce antica genova | `Dal 1820 la famiglia Grondona garantisce` | Data di fondazione e garanzia familiare: asserzione sul passato (seme D17). |
| 87990 | Trofie artigianali | `Trofie artigianali` | «Artigianali», nel contesto di un prodotto presentato come espressione della tradizione pastaia ligu |
| 87990 | Trofie artigianali | `Il formato che più definisce la tradizione della pasta in Liguria` | Tipicita tradizionale regionale del formato di pasta: Step 2c, come il seed D15. |

### 3.5 `ip_regulatory_status` — 2 claims

Patents, trademarks, registrations.

| product | name | claim_text (verbatim) | rationale_it |
|---|---|---|---|
| 573102 | Detergente fluido senza risciacq | `principio attivo brevettato` | Afferma lo status brevettuale del principio attivo, come nel seed D19. |
| 636091 | Collutorio denti sensibili biosm | `Brevetto internazionale` | Asserzione di status brevettuale: seed D19, Step 2d. |
---
## 4. The retained set — what v2 will contain

### 4.1 NEEDS_VERIFICATION — 48 claims (the review queue)

| product | claim_text (verbatim) | type | scheme | on_pack_qualifier | question |
|---|---|---|---|---|---|
| 588549 | `-38% di plastica* ... rispetto alle vaschette tradizionali Rov` | on_pack_disclosure | — | `-38% rispetto alle vaschette tradizionali Rovagnati.` | Quale misurazione sostiene il -38% di plastica e quale è la vaschetta tradizionale Rovagnati usata come termine di parag |
| 68928 | `100% Elettrica rinnovabile` | substantiation_evidence | — | `Le chips 1936 sono prodotte con energia elettrica proven` | Quali garanzie di origine o contratti di fornitura documentano che l'energia elettrica impiegata per produrre le chips 1 |
| 45232 | `25% Plastica* ... rispetto alle precedenti confezioni Beretta` | on_pack_disclosure | — | `*rispetto alle precedenti confezioni Beretta. Scopri di ` | Quale metodo di calcolo sostiene la riduzione del 25% di plastica, e quali sono le precedenti confezioni Beretta specifi |
| 588549 | `55% di plastica riciclata` | on_pack_disclosure | — | `*55% nella vaschetta.` | Quale metodo di calcolo e quale documentazione sostengono il 55% di plastica riciclata riferito alla sola vaschetta? |
| 666874 | `95% Ingredienti di origine naturale*` | on_pack_disclosure | — | `*Gli ingredienti di origine naturale mantengono +50% del` | Quale metodo di calcolo sostiene il 95% di ingredienti di origine naturale, e la nota che fissa la soglia del +50% di st |
| 666869 | `96% Ingredienti di origine naturale*` | on_pack_disclosure | — | `*Gli ingredienti di origine naturale mantengono +50% del` | Quale metodo di calcolo sostiene il 96% di ingredienti di origine naturale, e la nota sulla soglia del +50% di stato nat |
| 611508 | `96% Natural origin* ... water and naturally sourced ingredient` | on_pack_disclosure | — | `*water and naturally sourced ingredients with limited pr` | Quale metodo di calcolo sostiene il 96% di origine naturale, e la nota '*water and naturally sourced ingredients with li |
| 571225 | `Benessere animale` | certification_scheme | — | `—` | Esiste per questa filiera una certificazione di benessere animale (es. SQNBA o schema equivalente), quale ente la rilasc |
| 641361 | `Biodegradable mask by home compost** ... compostabile nel comp` | on_pack_disclosure | — | `**Questa maschera in tessuto è compostabile nel composta` | La precisazione in confezione sulla compostabilità domestica e' effettivamente stampata e leggibile, e quale norma di pr |
| 608812 | `Bottiglia in plastica 100% riciclata** ... Da filiera alimenta` | on_pack_disclosure | — | `**Escluso tappo ed etichetta` | Quale evidenza sostiene il 100% di plastica riciclata nella bottiglia, tenuto conto che tappo ed etichetta sono esclusi  |
| 39538 | `Cialde compostabili* ... In conformità alla norma EN 13432/200` | test_standard | — | `*Cialde compostabili In conformità alla norma EN 13432/2` | Esiste, per le cialde di questo prodotto, un certificato di conformità alla norma EN 13432:2002 rilasciato da un organis |
| 619902 | `Con burro di karité da coltivazione etiche* ... Commercio equo` | certification_scheme | commercio equo e solidale | `—` | Il prodotto e effettivamente certificato da uno schema di commercio equo e solidale riconosciuto (es. Fairtrade, Altrome |
| 599157 | `Confezione con carta certificata FSC per una gestione responsa` | certification_scheme | FSC | `—` | Il marchio FSC e il codice di licenza sono effettivamente presenti sulla confezione, e il certificato di catena di custo |
| 645376 | `Confezione con carta certificata FSC per una gestione responsa` | certification_scheme | FSC | `—` | Il marchio FSC e il codice di licenza sono effettivamente presenti sulla confezione, e il certificato di catena di custo |
| 145542 | `conformità con lo standard SRP per la coltivazione sostenibile` | certification_scheme | SRP - Sustainable Rice Platform | `—` | Il riso e effettivamente coltivato in conformita allo standard SRP, con verifica di terza parte e certificazione in cors |
| 564356 | `Consigliato da Legambiente ... Sustainable product DTP112 cert` | third_party_endorsement | Legambiente | `Questo prodotto 100% italiano rispetta le linee guida su` | L'uso della dicitura 'Consigliato da Legambiente' è autorizzato da Legambiente, e a quali linee guida di produzione vege |
| 704630 | `cosa intendiamo quando diciamo «Natural»` | on_pack_disclosure | — | `Non intendiamo che tutto quello che si trova nelle nostr` | Il criterio di definizione di «Natural» dichiarato in confezione (ingredienti di origine naturale, puliti/essiccati/lavo |
| 612478 | `Cosmetico Certificato 100% naturale` | certification_scheme | — | `—` | Quale schema di certificazione sostiene la dicitura «Cosmetico Certificato 100% naturale», quale organismo terzo lo veri |
| 608641 | `Cosmetico Certificato 100% naturale` | certification_scheme | — | `—` | Quale schema di certificazione sostiene la dicitura «Cosmetico Certificato 100% naturale», quale organismo terzo lo veri |
| 602008 | `Cosmetico Certificato 100% naturale ... Come previsto dal disc` | certification_scheme | NaTrue | `Senza oli minerali - siliconi - coloranti e profumi sint` | Il prodotto è effettivamente certificato secondo il disciplinare NaTrue, il certificato è in corso di validità e il disc |
| 564356 | `Da filera tracciata e sostenibile` | certification_scheme | DTP112 - Sustainable product (CSQA) | `Sustainable product DTP112 certified, Cert. CSQA n. 5702` | La certificazione 'Sustainable product' DTP112 (Cert. CSQA n. 57027) copre l'intera filiera di questo olio di girasole e |
| 603892 | `di origine naturale e bio` | certification_scheme | Biologico (Reg. (UE) 2018/848) | `—` | Gli ingredienti descritti come «bio» sono coperti da certificazione biologica valida ai sensi del Reg. (UE) 2018/848, e  |
| 144287 | `Eco pack biodegradabile e compostabile ... Imballaggio compost` | test_standard | UNI EN 13432 - DIN CERTCO n° 7P1317 | `Imballaggio compostabile ai sensi della UNI EN 13432 / P` | L'imballaggio e effettivamente certificato conforme alla UNI EN 13432 e il certificato DIN CERTCO n. 7P1317 e in corso d |
| 144400 | `Energia rinnovabile certificata` | substantiation_evidence | — | `—` | Quale certificazione di energia rinnovabile (ad es. garanzie di origine) sostiene l'asserzione, per quali siti produttiv |
| 703069 | `Equalitas - Cantina Sostenibile` | certification_scheme | Equalitas - Cantina Sostenibile | `—` | La certificazione Equalitas 'Cantina Sostenibile' è in corso di validità per questa cantina e copre l'annata imbottiglia |
| 39017 | `Farina di grano tenero da Agricoltura Sostenibile rispettando ` | certification_scheme | Carta del Mulino / ISCC Plus | `La Carta del Mulino prevede il rispetto dei criteri di s` | La farina è effettivamente coltivata secondo il disciplinare Carta del Mulino, la conformità ai criteri ISCC Plus è cert |
| 571225 | `Filiera certificata` | certification_scheme | — | `—` | Quale schema di certificazione di filiera è applicato, copre caratteristiche ambientali o di benessere animale, ed è in  |
| 101501 | `Filiera certificata` | certification_scheme | — | `—` | Quale schema di certificazione di filiera è applicato, copre caratteristiche ambientali o di benessere animale, ed è in  |
| 638347 | `Filiera italiana certificata` | certification_scheme | — | `—` | Quale schema di certificazione sostiene la dicitura «Filiera italiana certificata», ed e conforme ai requisiti dell'art. |
| 666874 | `Formula senza microplastiche^^ ... secondo la definizione dell` | on_pack_disclosure | — | `^^secondo la definizione dell'UNEP` | Quale definizione UNEP di microplastica è stata applicata, e l'assenza di microplastiche nella formula è documentata sec |
| 666869 | `Formula vegana & biodegradabile^ ... 99,8% formula biodegradab` | test_standard | — | `^99,8% formula biodegradabile` | Quale norma di prova sostiene il 99,8% di biodegradabilità della formula, e quale porzione del prodotto è stata sottopos |
| 666874 | `Formula vegana & biodegradabile^ ... 99,9% formula biodegradab` | test_standard | — | `^99,9% formula biodegradabile` | Quale norma di prova sostiene il 99,9% di biodegradabilità della formula, e in quale arco temporale e su quale matrice è |
| 599962 | `formula vegana** ... Nessun ingrediente o derivato di origine ` | on_pack_disclosure | — | `**Nessun ingrediente o derivato di origine animale` | La precisazione «Nessun ingrediente o derivato di origine animale» è presente e leggibile in confezione, e su quale sche |
| 599963 | `formula vegana** ... Nessun ingrediente o derivato di origine ` | on_pack_disclosure | — | `**Nessun ingrediente o derivato di origine animale` | La precisazione «Nessun ingrediente o derivato di origine animale» è presente e leggibile in confezione, e su quale sche |
| 569248 | `il 100% delle aziende agricole conferenti ha ottenuto la Certi` | certification_scheme | Certificazione di Filiera con Benessere Animale (valutazione ClassyFarm) | `—` | Il 100% delle aziende agricole conferenti possiede una Certificazione di Filiera con Benessere Animale in corso di valid |
| 612659 | `Il nostro cacao è certificato Rainforest Alliance` | certification_scheme | Rainforest Alliance | `—` | Il marchio Rainforest Alliance e il relativo codice di licenza sono esibiti in confezione, e il certificato è in corso d |
| 44114 | `Imballi certificati FSC per salvaguardare le foreste` | certification_scheme | FSC | `—` | Il marchio FSC e il codice di licenza sono effettivamente presenti sulla confezione e il certificato di catena di custod |
| 554553 | `Imballi certificati FSC per salvaguardare le foreste` | certification_scheme | FSC | `—` | Il marchio FSC e il codice di licenza sono effettivamente presenti sulla confezione e il certificato di catena di custod |
| 569248 | `La carta utilizzata è certificata e proviene da foreste gestit` | certification_scheme | — | `—` | Quale schema di certificazione forestale copre la carta della confezione, e il relativo certificato di catena di custodi |
| 703021 | `La certificazione FSC supporta una buona gestione delle forest` | certification_scheme | FSC | `—` | Il marchio FSC e il relativo codice di licenza sono effettivamente presenti sulla confezione, e il certificato di catena |
| 603892 | `Le migliori albicocche bio` | certification_scheme | Biologico (Reg. (UE) 2018/848) | `—` | La certificazione biologica delle albicocche è valida ai sensi del Reg. (UE) 2018/848 e quale sostanziazione sostiene il |
| 663509 | `Le migliori pesche gialle bio` | certification_scheme | Biologico (Reg. (UE) 2018/848) | `—` | La certificazione biologica delle pesche gialle è valida ai sensi del Reg. (UE) 2018/848 e quale sostanziazione sostiene |
| 675785 | `Miele Equosolidale` | certification_scheme | — | `—` | Quale sistema di certificazione del commercio equo e solidale sostiene la dicitura «Miele Equosolidale», il relativo mar |
| 603896 | `plastica riciclabile e cartoncino certificato FSC` | certification_scheme | FSC | `—` | Il cartoncino della confezione reca il marchio FSC con il relativo codice di licenza, e il certificato di catena di cust |
| 54275 | `prodotto secondo i principi del commercio equo e solidale` | certification_scheme | commercio equo e solidale | `—` | Il prodotto e effettivamente certificato da uno schema di commercio equo e solidale riconosciuto (es. Fairtrade, Altrome |
| 47144 | `provenienti da produttori equo solidali altromercato` | certification_scheme | Altromercato — commercio equo e solidale | `—` | Il cacao e lo zucchero di canna provengono effettivamente da filiere equo solidali Altromercato, e la relativa certifica |
| 47286 | `Questa confezione è composta per l'88% da materie prime rinnov` | substantiation_evidence | — | `perché tappo e strati protettivi sono fatti con plastica` | Con quale metodo di calcolo e su quale base (massa dell'imballaggio) è determinato l'88% di materie prime rinnovabili, e |
| 718993 | `tecniche di produzione integrata a tutela della salute e dell'` | substantiation_evidence | — | `(pesticidi -70% della soglia consentita)` | Quali dati e quale periodo di rilevazione sostengono la riduzione del 70% dei pesticidi rispetto alla soglia di legge co |

**23 of 48 carry a re-derived on-pack qualifier**, taken from the product description rather than the joined claim string — the guide records cases where that string was missing or attached to the wrong footnote.

### 4.2 IN_SCOPE — 141 claims

**Offset / climate neutrality — 9**

| product | claim_text (verbatim) | rationale_it |
|---|---|---|
| 47286 | `-18% di CO2eq verso la stessa confezione fatta con materiali convenzionali` | Asserzione ambientale comparativa (-18% CO2eq) il cui termine di paragone, 'la stessa confez |
| 39285 | `11% di emissioni CO2 in meno rispetto alla confezione precedente` | Comparativa ambientale il cui comparatore ('confezione precedente') non è specificamente ide |
| 47106 | `11% di emissioni CO2 in meno rispetto alla confezione precedente` | Comparativa ambientale con comparatore vago ('confezione precedente'), che per la regola sul |
| 619902 | `CO2 100% prodotto a impatto climatico neutralizzato` | Asserzione di neutralità climatica fondata sulla compensazione delle emissioni residue, ripr |
| 44114 | `Emissioni di CO2 ridotte e compensate` | Asserzione di riduzione e compensazione delle emissioni di CO2 basata su compensazione, senz |
| 603657 | `Emissioni zero / Questa confezione è Carbon Neutral: ciò significa che neutralizziam` | Neutralita' climatica della confezione ottenuta tramite compensazione delle emissioni: asser |
| 144400 | `Il nostro obiettivo è ridurre l'impronta di carbonio dei nostri articoli per l'igien` | Impegno di prestazione ambientale futura (-30% di impronta di carbonio entro il 2030) privo  |
| 554553 | `Produzione a zero emissioni di CO2` | Asserzione di neutralità climatica della produzione senza indicazione del perimetro, del met |
| 569248 | `Questa confezione proviene esclusivamente da fonti rinnovabili di origine vegetale e` | Asserzione di azzeramento delle emissioni di CO2 della confezione, priva di metodo di calcol |

**Recycled content / recyclability — 28**

| product | claim_text (verbatim) | rationale_it |
|---|---|---|
| 676876 | `28% Plastica riciclata` | Contenuto di riciclato senza base dichiarata: la riga «Tubo con plastica riciclata» indica s |
| 45232 | `65% plastica riciclata` | Contenuto di riciclato quantificato (T7): la nota presente in confezione riguarda la riduzio |
| 44721 | `65% Plastica riciclata` | Contenuto di riciclato quantificato (T7) accompagnato nel contesto soltanto da un rimando al |
| 619225 | `65% Plastica riciclata` | Contenuto di riciclato quantificato (T7): nel contesto compare solo il rimando al sito, che  |
| 554553 | `Astuccio in cartone 100% riciclabile` | Asserzione ambientale quantificata sulla riciclabilità dell'astuccio: la descrizione riporta |
| 704720 | `Attenti all'ambiente - confezione riciclabile` | Asserzione ambientale che accosta l'attenzione all'ambiente alla riciclabilità della confezi |
| 638347 | `Attenti all'ambiente confezione riciclabile` | Unisce un'affermazione generica di attenzione all'ambiente alla riciclabilità della confezio |
| 612212 | `Bottiglia 50% plastica riciclata` | Asserzione quantificata sul contenuto di plastica riciclata della bottiglia priva di metodo  |
| 37777 | `Bottiglia con il 100% di plastica riciclata` | Asserzione di contenuto riciclato al 100% senza alcuna base (metodo, ambito o comparatore) d |
| 554553 | `Bustina salva-aroma in carta 100% riciclabile` | Asserzione ambientale quantificata sulla riciclabilità della bustina, priva nella descrizion |
| 47144 | `Confezione riciclabile in ogni sua componente` | Asserzione ambientale di riciclabilità totale dell'imballaggio senza alcuna base indicata: l |
| 41070 | `Confezione senza plastica, riciclabile` | Asserzione ambientale sull'imballaggio (assenza di plastica e riciclabilità): il contesto di |
| 142195 | `Eco pack 100% riciclabile - Con meno plastica` | Asserzione ambientale sull'imballaggio (eco pack, riciclabilità al 100%, minore plastica) pr |
| 663509 | `Etichetta in carta riciclata` | Asserzione di contenuto riciclato sull'etichetta senza alcuna base dichiarata nella descrizi |
| 603892 | `Etichetta in carta riciclata` | Asserzione di contenuto riciclato priva di base dichiarata nella descrizione: per il test de |
| 52121 | `fabbricata con ben il 50% di PET Riciclato (RPET)` | Asserzione di contenuto riciclato quantificata (50% RPET) senza metodo di calcolo, ambito ul |
| 602008 | `flacone 95% plastica riciclata` | Contenuto di plastica riciclata al 95% senza metodo di calcolo né ambito dichiarati: l'indic |
| 418104 | `Incarto riciclabile 100% plastica` | Asserzione ambientale sulla riciclabilità dell'incarto priva di base dichiarata: l'invito a  |
| 145542 | `Low Impact Pack: le nostre confezioni sono a basso impatto ambientale con plastica r` | Asserzione ambientale sull'imballaggio nel suo complesso mentre la certificazione riguarda u |
| 619902 | `Packaging in carta riciclata` | Asserzione di contenuto riciclato dell'imballaggio senza percentuale, perimetro o metodo dic |
| 617095 | `Qualità Pampers in cartoni 100% riciclati` | Asserzione ambientale sul contenuto di riciclato dei cartoni: la descrizione non enuncia né  |
| 37777 | `Riciclami ancora` | Invito promozionale al riciclo che implica un beneficio ambientale della confezione senza al |
| 52121 | `Riciclando miglioriamo insieme il nostro ambiente!` | Asserzione ambientale generica ('miglioriamo insieme il nostro ambiente') senza alcuna speci |
| 41908 | `sostenibili fuori, grazie all'innovativa confezione "sbucciabile" e completamente ri` | Asserzione ambientale generica ('sostenibili fuori') unita alla riciclabilità completa della |
| 610425 | `Tubo e cartone in materiale 100% riciclabile` | Asserzione di riciclabilità al 100% priva di base dichiarata: la descrizione riporta solo i  |
| 144400 | `utilizzando materiali riciclati e da fonti rinnovabili` | Asserzione di impiego di materiali riciclati e da fonti rinnovabili senza alcuna percentuale |
| 47536 | `Vaschetta con 70% di plastica riciclata` | Contenuto di riciclato quantificato (T7): il contesto di prodotto non enuncia ne' metodo di  |
| 564356 | `Zucchi per l'ambiente ... utilizza il 50% di plastica riciclata` | Contenuto di riciclato al 50% senza metodo di calcolo, ambito o comparatore: il contesto off |

**Plastic reduction / packaging — 15**

| product | claim_text (verbatim) | rationale_it |
|---|---|---|
| 56017 | `-17% Plastica rispetto al pack precedente` | Confronto ambientale quantificato il cui comparatore (il pack precedente) non è specificamen |
| 703021 | `13% di plastica in meno rispetto al tappo precedente` | Comparativa ambientale il cui comparatore ('tappo precedente') non è specificamente identifi |
| 599962 | `45% di plastica in meno / Rispetto al kit precedente` | Comparativo ambientale quantificato il cui unico riferimento è «rispetto al kit precedente», |
| 599963 | `45% di plastica in meno / Rispetto al kit precedente` | Comparativo ambientale quantificato il cui unico riferimento è «rispetto al kit precedente», |
| 608641 | `75% In meno di plastica` | Asserzione ambientale comparativa quantificata (–75% di plastica) il cui termine di paragone |
| 39285 | `brik-eco sostenibile` | Definisce il brik 'eco sostenibile' con formula verde generica e priva di specificazione for |
| 47106 | `brik-eco sostenibile` | Formula verde generica sul brik 'eco sostenibile' senza specificazione fornita nello stesso  |
| 39285 | `cannuccia di carta per ridurre l'impatto sull'ambiente` | Asserisce una riduzione dell'impatto ambientale grazie alla cannuccia di carta senza alcuna  |
| 608641 | `fai risparmiare il 75% di plastica e contribuisci a ridurre la massa dei rifiuti` | Asserzione di impatto ambientale positivo (risparmio di plastica e riduzione dei rifiuti) pr |
| 554553 | `Filtro in cellulosa biodegradabile senza microplastiche` | Asserzione ambientale sul filtro (biodegradabile e senza microplastiche) senza norma di prov |
| 672184 | `Flacone green 100%` | «Flacone green 100%» e un'asserzione ambientale generica sul contenitore: il 100% non e acco |
| 569248 | `Il tappo e la plastica sono ricavati dalla canna da zucchero, una risorsa che opport` | La rinnovabilità infinita della canna da zucchero è presentata come pregio dell'imballaggio, |
| 41070 | `Manico realizzato con plastica di origine biologica` | Materiale di origine biologica presentato come pregio del manico, senza percentuale, norma o |
| 672184 | `Progetto sostenibilità / Il Nostro Flacone Green` | Programma ambientale aziendale vago unito a un claim «green» sul flacone, privo di qualunque |
| 44114 | `Senza microplastiche` | L'assenza di microplastiche è presentata, nell'elenco delle caratteristiche dell'imballo, co |

**Naturalness / natural origin — 18**

| product | claim_text (verbatim) | rationale_it |
|---|---|---|
| 713295 | `100% di origine naturale` | Asserzione 'naturale' quantificata al 100% senza alcun metodo di calcolo o altra base fornit |
| 703021 | `100% di origine naturale` | Asserzione 'naturale' quantificata al 100% priva di metodo di calcolo o altra base nel testo |
| 44114 | `100% Naturale` | Asserzione ambientale/di naturalità generica sul prodotto nel suo complesso, senza alcuna sp |
| 63679 | `100% Naturale` | Asserzione di naturalità assoluta e non specificata (seme S6); nella descrizione non compare |
| 594304 | `100% naturale` | '100% naturale' è wording verde generico senza alcuna specificazione del metodo di calcolo n |
| 668466 | `100% Naturale / 100% Ingredienti naturali` | '100% Naturale / 100% Ingredienti naturali' è wording verde quantificato ma privo di metodo  |
| 610425 | `94% Ingredienti di origine naturale` | Percentuale di ingredienti di origine naturale senza metodo di calcolo dichiarato: le uniche |
| 676876 | `97% di origine naturale` | Percentuale di origine naturale ripetuta in descrizione ma senza alcuna regola di conteggio  |
| 554704 | `Brick 86% da materie di origine vegetale` | Percentuale ambientale sulla composizione del brick priva di metodo di calcolo, ambito quali |
| 37815 | `Ingredienti di origine 100% naturale` | Asserzione di naturalità totale degli ingredienti (cfr. semi S6, S9, S13) priva di ogni spec |
| 619902 | `Ingredienti di origine naturale` | Asserzione di ingredienti di origine naturale priva di qualsiasi metodo di conteggio o perim |
| 698877 | `Origine naturale` | Asserzione ambientale generica sull'origine naturale della formula: il contesto di prodotto  |
| 703021 | `più dell'80% da materiali vegetali` | Percentuale ambientale sulla composizione della confezione senza metodo di calcolo, ambito q |
| 68928 | `prodotte con energia elettrica proveniente esclusivamente da fonti rinnovabili` | Asserisce l'impiego esclusivo di energia elettrica da fonti rinnovabili nella produzione, il |
| 50785 | `Prodotto con ingredienti di origine naturale` | Asserzione ambientale generica sull'origine naturale degli ingredienti: nessun metodo di cal |
| 39285 | `realizzati per l'83% da materiali rinnovabili vegetali` | Asserzione ambientale quantificata sulla composizione dell'imballaggio priva di metodo di ca |
| 47106 | `realizzati per l'83% da materiali rinnovabili vegetali` | Percentuale ambientale sulla composizione del brik senza metodo di calcolo, ambito qualifica |
| 63854 | `Solo aromi naturali` | Asserzione di naturalità della composizione priva di specificazione, nella linea dei semi S6 |

**Generic green wording — 65**

| product | claim_text (verbatim) | rationale_it |
|---|---|---|
| 56017 | `+ Gusto + sostenibile` | Asserzione di maggiore sostenibilità del tutto generica e senza base dichiarata: l'unica not |
| 38765 | `Agricoltura sostenibile` | Asserzione ambientale generica sulla coltivazione ('sostenibile') priva di qualsiasi specifi |
| 63854 | `Aiutiamo l'ambiente` | Asserzione ambientale generica («Aiutiamo l'ambiente») senza alcuna specificazione, posta a  |
| 621126 | `Aiutiamo l'ambiente` | Asserzione ambientale generica priva di specificazione, posta a capo delle istruzioni di rac |
| 642705 | `Bahlsen per l'ambiente` | Asserzione ambientale generica di impegno del produttore verso l'ambiente, priva di specific |
| 45232 | `BGreen` | Marchio verde proprio del produttore, privo di specificazione e non fondato su uno schema di |
| 44721 | `BGreen` | Marchio verde proprio del produttore privo di specificazione, non riconducibile a un sistema |
| 619225 | `BGreen` | Marchio verde proprio del produttore privo di specificazione e non fondato su uno schema di  |
| 594304 | `Casaceto per l'ambiente` | Programma ambientale d'impresa formulato in modo del tutto generico ('per l'ambiente'), senz |
| 702976 | `Citterio per l'ambiente` | Asserzione ambientale generica di impegno aziendale senza alcuna specificazione, della stess |
| 716821 | `Citterio per l'ambiente` | Programma ambientale aziendale generico, privo di qualsiasi specificazione nel testo del pro |
| 39785 | `Con cacao da coltivazione più sostenibile` | Confronto ambientale sulla coltivazione del cacao («più sostenibile») senza comparatore iden |
| 673274 | `Con ingredienti da Agricoltura Sostenibile` | Asserzione ambientale generica sugli ingredienti da 'agricoltura sostenibile' senza schema n |
| 43145 | `Coop per l'ambiente` | Asserzione ambientale generica riferita all'insegna nel suo complesso, senza alcuna specific |
| 41888 | `Coop per l'ambiente` | Asserzione ambientale generica riferita all'insegna, priva di qualunque specificazione forni |
| 44300 | `Coop per l'ambiente` | Asserzione ambientale generica dell'insegna, priva di specificazione (seme S2). |
| 43616 | `Coop per l'ambiente` | Asserzione ambientale generica dell'insegna, priva di specificazione (seme S2). |
| 46529 | `Coop per l'ambiente` | Asserzione ambientale generica di impegno d'impresa priva di qualunque specificazione: seed  |
| 46840 | `Coop per l'ambiente` | Asserzione ambientale generica di impegno d'impresa priva di specificazione: seed S2, testo  |
| 552334 | `Coop per l'ambiente` | Impegno ambientale aziendale formulato in modo generico e privo di specificazione fornita co |
| 41908 | `Coop per l'ambiente` | Slogan ambientale aziendale generico privo di specificazione (cfr. seed S2). |
| 43907 | `Coop per l'ambiente` | Asserzione ambientale generica di impegno aziendale per l'ambiente, priva di qualsiasi speci |
| 40954 | `Coop per l'ambiente` | Programma ambientale d'impresa formulato genericamente ('per l'ambiente'), senza specificazi |
| 41950 | `Ecologico!` | «Ecologico!» e un'asserzione ambientale generica sul prodotto: la descrizione ne da una moti |
| 701225 | `Fai la differenziata per il pianeta` | Invito generico alla raccolta differenziata 'per il pianeta': asserzione ambientale priva di |
| 42428 | `Fare una corretta raccolta differenziata fa bene all'ambiente` | Messaggio volontario che afferma un beneficio ambientale della raccolta differenziata, ecced |
| 418104 | `Fiorentini per l'ambiente` | Asserzione ambientale generica di impegno del produttore verso l'ambiente, senza alcuna spec |
| 603896 | `Gallo green` | Claim «green» generico riferito al marchio e alla confezione, privo di qualunque specificazi |
| 598057 | `garantisce una produzione sostenibile in armonia con la natura` | Asserzione di produzione sostenibile e in armonia con la natura, formulata in modo generico  |
| 609831 | `gestito con ecosostenibilità` | Asserzione di gestione ecosostenibile dell'attività priva di qualsiasi specificazione verifi |
| 703021 | `Ho a cuore l'ambiente` | Slogan ambientale generico di attenzione all'ambiente privo di specificazione (seed S29). |
| 39285 | `Il gusto di amare il pianeta` | Slogan ambientale generico che implica un beneficio per il pianeta senza alcuna specificazio |
| 47106 | `Il gusto di amare il pianeta` | Slogan ambientale generico di amore per il pianeta privo di specificazione (seed S27). |
| 569248 | `il latte amico dell'ambiente` | Asserzione ambientale generica sul prodotto nel suo complesso (latte amico dell'ambiente) se |
| 673274 | `Il nostro impegno per te e per il pianeta` | Impegno aziendale ambientale vago ('per il pianeta') privo di specificazione (cfr. seed S20) |
| 41950 | `Il sacchetto di carta rispetta l'ambiente` | Afferma che l'imballaggio «rispetta l'ambiente», cioe un impatto ambientale positivo o nullo |
| 144400 | `Il Tuo Ciclo. Il Tuo Pianeta. Teniamo A Entrambi.` | Slogan ambientale generico sul pianeta privo di qualunque specificazione del suo fondamento, |
| 68928 | `L'ambiente è vita. Tienilo pulito` | Messaggio ambientale volontario di richiamo alla cura dell'ambiente, privo di qualsiasi spec |
| 571225 | `Latteria Soresina per l'ambiente` | Slogan aziendale ambientale generico ('per l'ambiente') privo di qualsiasi specificazione (c |
| 554704 | `Ogni ape conta - Difendiamo la biodiversità` | Asserisce un impatto positivo sulla biodiversità in forma di slogan, senza alcuna specificaz |
| 38771 | `ottenuto esclusivamente da uve a produzione integrata nel pieno rispetto della natur` | 'Nel pieno rispetto della natura' implica un impatto ambientale positivo o nullo senza alcun |
| 609831 | `proteggendo la natura in cui vivono` | Asserzione di protezione della natura priva di qualsiasi specificazione: asserzione ambienta |
| 663509 | `Rigoni di Asiago per l'ambiente` | Asserzione ambientale generica riferita all'impresa nel suo complesso, priva di qualunque sp |
| 603892 | `Rigoni di Asiago per l'ambiente` | Asserzione ambientale generica riferita all'impresa, senza specificazione fornita con lo ste |
| 144400 | `Rispetta l'ambiente` | Esortazione ambientale volontaria e generica posta in testa alle istruzioni di smaltimento,  |
| 101501 | `rispettando l'ambiente e il benessere animale` | Asserzione ambientale generica ('rispettando l'ambiente') implicante un impatto positivo o r |
| 164990 | `Rispettiamo l'ambiente` | Asserzione ambientale generica di rispetto per l'ambiente, priva di qualsiasi specificazione |
| 666874 | `si prendono cura della pelle delicata del tuo bambino e del pianeta` | Asserzione ambientale generica riferita al prodotto nel suo complesso (le formule si prendon |
| 39285 | `Un nuovo passo del nostro impegno per il pianeta` | Programma ambientale aziendale vago ('impegno per il pianeta') privo di qualsiasi specificaz |
| 608812 | `Viva la Natura! / Per un futuro migliore` | Slogan verde e promessa di futuro migliore senza alcuna specificazione: asserzione ambiental |
| 43145 | `VIVI VERDE` | Marchio privato a connotazione ambientale usato come asserzione verde generica, senza specif |
| 41888 | `vivi verde` | Marchio privato a connotazione ambientale impiegato come asserzione verde generica, priva di |
| 612478 | `VIVI VERDE` | Marchio privato volontario di linea «verde» che implica un impatto ambientale migliore senza |
| 608641 | `VIVI VERDE` | Marchio privato volontario di linea «verde» che implica un impatto ambientale migliore senza |
| 602008 | `VIVI VERDE` | Marchio privato volontario di linea «verde» che implica un impatto ambientale migliore senza |
| 46529 | `VIVI VERDE` | Marchio commerciale proprio a connotazione verde del distributore, non uno schema di certifi |
| 46840 | `VIVI VERDE` | Marchio verde proprio del distributore, privo di specificazione e non riconducibile a un sis |
| 45171 | `VIVI VERDE` | Marchio verde di linea del distributore che evoca genericamente un beneficio ambientale senz |
| 612212 | `VIVI VERDE` | Marchio verde di linea che evoca un beneficio ambientale generico senza specificazione forni |
| 43335 | `VIVI VERDE` | Marchio di linea a connotazione ambientale generica 'VIVI VERDE' privo di specificazione (cf |
| 668756 | `VIVI VERDE` | Marchio volontario privato di linea «verde» impiegato come asserzione ambientale generica, p |
| 43792 | `VIVI VERDE` | Marchio volontario privato di linea «verde» impiegato come asserzione ambientale generica, p |
| 554704 | `VIVI VERDE` | Marchio ambientale privato generico esposto senza specificazione del suo contenuto nello ste |
| 40954 | `VIVI VERDE` | Denominazione di linea verde usata come messaggio ambientale generico, priva di specificazio |
| 41908 | `vivi verde Coop` | Marchio di linea a connotazione ambientale generica ('vivi verde') privo di specificazione ( |

**Other — 6**

| product | claim_text (verbatim) | rationale_it |
|---|---|---|
| 47286 | `#Bontàresponsabile ... il nostro impegno per un futuro più buono` | Programma aziendale vago (#Bontàresponsabile, 'impegno per un futuro più buono') che nel con |
| 575950 | `100% Tessuto biodegradabile` | Asserzione ambientale quantificata sulla biodegradabilità del tessuto priva di norma di prov |
| 641361 | `50% Paper-based sachet` | Asserzione ambientale quantificata sul materiale della bustina (50% a base carta): nel conte |
| 704601 | `Acquistarlo da Farmaciauno garantisce non solo l'autenticità e la freschezza del pro` | Autenticita e freschezza, obblighi comuni a ogni venditore, presentate come tratto distintiv |
| 44114 | `Filtro in cellulosa biodegradabile` | Asserzione ambientale sulla biodegradabilità del filtro priva di norma di prova, metodo o al |
| 37815 | `vitamina B1* ... *Come previsto per legge` | Requisito imposto per legge (fortificazione con vitamina B1) presentato come tratto distinti |

---
## 5. UNCERTAIN — none

The first pass produced 20 (3.6%). All were adjudicated with you on 2026-09-20: 11 by the four scope rulings and the repair pass, 7 individually in the final round, 2 by the fair-trade ruling. **Phase 3 is unblocked** — the validator refuses to run while any UNCERTAIN survives.

The four rulings in the final round were general rules, so each was re-scanned across all 562 claims rather than applied locally: limb 3d (Art. 23 l-bis) found **2** candidates set-wide; the material-code test and the d-ter precedence rule found **no** further retained claim affected.

## 6. Repair pass — 18 logged label changes

Applied after the scope rulings and after the guide inconsistency was found. Listed so none is silent.

| product | claim | from → to | why |
|---|---|---|---|
| 663509 | `Approvata da A.I.Nut. - Associazione Italiana Nutrizioni` | NV → DISCARD | health/efficacy endorsement, no ECGT hook |
| 603892 | `Approvata da A.I.Nut. - Associazione Italiana Nutrizioni` | NV → DISCARD | health/efficacy endorsement |
| 144400 | `Approvato da Skin Health Alliance` | NV → DISCARD | health/efficacy endorsement |
| 712712 | `Approvato da Aideco` | NV → DISCARD | health/efficacy endorsement |
| 610425 | `Approvato ANDI - Associazione Nazionale Dentisti Italian` | NV → DISCARD | health/efficacy endorsement |
| 612460 | `DAYTECH` | UNCERTAIN → DISCARD | private line mark |
| 552334 | `BENE SI'` | UNCERTAIN → DISCARD | private line mark |
| 43907 | `CRESCENDO` | UNCERTAIN → DISCARD | private line mark |
| 638347 | `Filiera italiana certificata` | DISCARD → NV | unnamed certification badge → n-septies check |
| 44114 | `#unsorsomigliore` | UNCERTAIN → DISCARD | slogan, no ECGT hook |
| 554553 | `#unsorsomigliore` | UNCERTAIN → DISCARD | slogan, no ECGT hook |
| 50746 | `prodotta con i migliori ingredienti reperibili sul merca` | UNCERTAIN → DISCARD | generic excellence |
| 717407 | `prodotta con i migliori ingredienti reperibili sul merca` | IN_SCOPE → DISCARD | generic excellence |
| 599157 | `Filiera Italiana: 100% farina di grano controllato e tra` | UNCERTAIN → DISCARD | origin + traceability |
| 645376 | `Filiera Italiana: 100% farina di grano controllato e tra` | UNCERTAIN → DISCARD | origin + traceability |
| 144400 | `aiutano a ridurre il rischio di irritazione della pelle` | UNCERTAIN → DISCARD | efficacy, OQ4 dissolved |
| 40732 | `aiutando a mantenere la pelle asciutta e a prevenire l'i` | UNCERTAIN → DISCARD | efficacy, OQ4 dissolved |
| 704601 | `Affidati all'esperienza di Farmaciauno per prodotti che ` | UNCERTAIN → DISCARD | trader generic excellence |

Plus **11 market-position claims** given the fixed note `market-position claim, Art. 21 Cod. Cons. — sales-ranking axis, outside the ECGT perimeter`, keeping the class greppable without a sixth reason code.

## 7. Claims per product, before and after

| Claims on product | Products (v1) | Products (v2) |
|---|---|---|
| 0 | 74 | 153 |
| 1 | 28 | 43 |
| 2 | 52 | 34 |
| 3 | 33 | 9 |
| 4 | 24 | 5 |
| 5 | 18 | 5 |
| 6 | 11 | 1 |
| 7 | 6 | 0 |
| 9 | 3 | 0 |
| 10 | 1 | 0 |

Mean **2.25 → 0.76** · median **2 → 0** · max **10 → 6**

> **Zero-claim products: 74 → 153 (61% of the set).** Records are kept per your rule, so v2 is still 250 products. Adjudicated: the harness **skips zero-claim products in per-product metrics**, and Phase 3 adds a `has_claims` flag so it can filter without recounting.

## 8. Reconciliation
| Check | Value |
|---|---|
| claims in v1 | 562 |
| retained in v2 | 189 |
| discarded (all logged) | 373 |
| unresolved | 0 |
| **sum** | **562** |
| verdicts with no source claim | 0 |
| claims with no verdict | 0 |
| schema violations | 0 |

## 9. Sign-off needed

**§3 is the deletion list.** Sign off on it, or name the rows you want back. Everything else at this gate is settled: 0 UNCERTAIN, all rules encoded in `LABELING_GUIDE.md` v2.2, blind check at 94/98/96%.
