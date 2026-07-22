# Changelog — Coop UCPD Golden Set redo (v1 → v2, with v3 and v4 patches)

Every line below is a specific, individually-reviewed change to `extracted_claims`.

**v3 patch:** food/cosmetic "natural" claim contamination fix (see below).

**v4 patch:** the food-composition "natural" claims moved in v3 kept their inherited MEDIUM risk level from the environmental bucket they used to sit in. That's a migration artifact, not a real risk assessment -- ordinary claims like "Solo aromi naturali" or "100% Naturale" are no riskier than "Senza grassi idrogenati", which was already LOW. 8 claims downgraded MEDIUM -> LOW for consistency.

## 1. Removed — not a claim (Part-A failure: puffery)

**48 instances.**

- **"è un autentico trionfo di pasticceria"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"per un gusto senza compromessi"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"per un'esperienza di gusto e benessere unica"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"per un gusto senza compromessi"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"per un'esperienza di gusto e benessere unica"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"Buona com'era"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"vero e proprio riferimento per i buongustai dell'epoca"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"Più che buono"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"Per un gelato eccezionale!"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"per mantenerne il gusto autentico"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"una fragranza unica e autentica"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"prodotte con la massima cura"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"Con pregiate nocciole"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"Da un'eccellenza gastronomica dell'Emilia Romagna"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"un'irresistibile tentazione italiana a cui non si deve rinunciare!"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"esclusivo"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"L'iconica lacca"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"Unico"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"Un gusto intenso, autentico, genuino"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"Bontà in ogni gesto"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"i sapori autentici della cucina asiatica"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"questa raffinatezza greca"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"L'eccellenza del nostro latte parte proprio da qui"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"un'esperienza di gusto irresistibile"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"riscoprire i sapori della memoria"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"ti stupirà per la sua bontà"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"Garanzia G.a.l.l.o. è sinonimo di eccellenza"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"Un omaggio a una terra illustre, culla di un patrimonio inestimabile di saperi e sapori"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"Genuino davvero!"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"come tradizione consiglia"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"Fatte bene, per far bene"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"L'Angelica seleziona e miscela solo gli ingredienti migliori"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"il miglior standard qualitativo possibile"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"Equilibra studia attentamente i propri prodotti ... ricerca i veicoli migliori"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"La naturale semplicità della nostra ricetta"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"qualità e trasparenza sono sempre al primo posto"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"combiniamo in un equilibrio perfetto"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"è il vino Veronese per eccellenza"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"per darti la spinta e farti mantenere la rotta durante qualsiasi tempesta"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"L'acqua per lo sport / Vivi in forma"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"Classic"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"Dai petali di rosa una delicata bontà"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"Olitalia è sinonimo di eccellenza e specializzazione"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"gusto autentico e qualità pregiata"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"sapore inconfondibile"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"selezionato con cura per darti sempre il meglio"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"una squisita crema ... un antipasto sfizioso e prelibato"** — Part-A failure: subjective/non-checkable, no attributable fact (puffery)
- **"Naturale dentro e fuori!"** — vague tagline, no checkable attribute beyond what's already covered by the product's real, specific environmental/animal-welfare claims on the same listing

## 2. Recategorized — real claim, wrong bucket

**34 instances.**

- **"Fonte di fibre"**: `irrelevant_claim` → `nutrition_content_claim` — bare NHCR Annex content/quantity claim -- real & checkable, compliance depends on nutrition-panel data not visible from ad text; not "irrelevant"
- **"Fonte di fibre"**: `irrelevant_claim` → `nutrition_content_claim` — bare NHCR Annex content/quantity claim -- real & checkable, compliance depends on nutrition-panel data not visible from ad text; not "irrelevant"
- **"Dal 1820 la famiglia Grondona garantisce"**: `misleading_endorsement_claim` → `misleading_authenticity_or_origin_claim` — heritage/continuity claim about the company's own history, not a third-party endorsement
- **"Senza grassi idrogenati"**: `irrelevant_claim` → `misleading_composition_or_ingredient_claim` — optional composition/absence claim the manufacturer chose to print -- not a compulsory disclosure, so cannot be irrelevant_claim by the category's own definition
- **"Dal 1820 la famiglia Grondona garantisce"**: `misleading_endorsement_claim` → `misleading_authenticity_or_origin_claim` — heritage/continuity claim about the company's own history, not a third-party endorsement
- **"Naturalmente priva di caffeina"**: `irrelevant_claim` → `nutrition_content_claim` — bare NHCR Annex content/quantity claim -- real & checkable, compliance depends on nutrition-panel data not visible from ad text; not "irrelevant"
- **"Solo nocciole italiane"**: `irrelevant_claim` → `misleading_authenticity_or_origin_claim` — specific ingredient-origin claim; checkable, not trivial/mandated
- **"Fonte di fibre"**: `irrelevant_claim` → `nutrition_content_claim` — bare NHCR Annex content/quantity claim -- real & checkable, compliance depends on nutrition-panel data not visible from ad text; not "irrelevant"
- **"0% di allergeni comuni*, profumi, coloranti (with disclosed NF EN 16274 test method and named allergen list)"**: `environmental_unsubstantiated` → `misleading_composition_or_ingredient_claim` — allergen/perfume/colorant absence is a composition claim, not an environmental-performance claim
- **"Brevetto internazionale"**: `irrelevant_claim` → `misleading_superiority_or_absolute_claim` — checkable IP/technology claim (patent registries exist), not trivial
- **"Ricco in proteine - 37g Per 100g di prodotto"**: `irrelevant_claim` → `nutrition_content_claim` — bare NHCR Annex content/quantity claim -- real & checkable, compliance depends on nutrition-panel data not visible from ad text; not "irrelevant"
- **"Ricca in calcio"**: `irrelevant_claim` → `nutrition_content_claim` — bare NHCR Annex content/quantity claim -- real & checkable, compliance depends on nutrition-panel data not visible from ad text; not "irrelevant"
- **"Fonte naturale di proteine"**: `irrelevant_claim` → `nutrition_content_claim` — bare NHCR Annex content/quantity claim -- real & checkable, compliance depends on nutrition-panel data not visible from ad text; not "irrelevant"
- **"Naturalmente ricco di proteine"**: `irrelevant_claim` → `nutrition_content_claim` — bare NHCR Annex content/quantity claim -- real & checkable, compliance depends on nutrition-panel data not visible from ad text; not "irrelevant"
- **"Fai la differenziata per il pianeta"**: `environmental_unsubstantiated` → `irrelevant_claim` — generic recycling-instruction PSA, not a claim about this product's own environmental performance -- same bucket as its near-duplicate 'Fare una corretta raccolta differenziata fa bene all'ambiente', already correctly in irrelevant_claim
- **"Riciclando miglioriamo insieme il nostro ambiente!"**: `environmental_unsubstantiated` → `irrelevant_claim` — generic recycling PSA, not a product-specific performance claim
- **"Fonte di fibre"**: `irrelevant_claim` → `nutrition_content_claim` — bare NHCR Annex content/quantity claim -- real & checkable, compliance depends on nutrition-panel data not visible from ad text; not "irrelevant"
- **"Fonte di fibre"**: `irrelevant_claim` → `nutrition_content_claim` — bare NHCR Annex content/quantity claim -- real & checkable, compliance depends on nutrition-panel data not visible from ad text; not "irrelevant"
- **"Fonte di proteine"**: `irrelevant_claim` → `nutrition_content_claim` — bare NHCR Annex content/quantity claim -- real & checkable, compliance depends on nutrition-panel data not visible from ad text; not "irrelevant"
- **"PANE ARABO-COTTO A LEGNA"**: `irrelevant_claim` → `misleading_authenticity_or_origin_claim` — wood-fired is a specific, checkable production-method claim, not trivial product-name text
- **"principio attivo brevettato"**: `irrelevant_claim` → `misleading_superiority_or_absolute_claim` — checkable IP claim
- **"Fonte di vitamina C"**: `irrelevant_claim` → `nutrition_content_claim` — bare NHCR Annex content/quantity claim -- real & checkable, compliance depends on nutrition-panel data not visible from ad text; not "irrelevant"
- **"1500 Controlli di qualità giornalieri"**: `irrelevant_claim` → `misleading_superiority_or_absolute_claim` — quantified quality-process claim, unverifiable from ad text alone -- same shape as 'N 1 in Italia' without disclosed source
- **"1.299 Controlli di qualità ogni giorno"**: `irrelevant_claim` → `misleading_superiority_or_absolute_claim` — quantified quality-process claim, unverifiable from ad text alone
- **"Ricco di proteine**"**: `irrelevant_claim` → `nutrition_content_claim` — bare NHCR Annex content/quantity claim -- real & checkable, compliance depends on nutrition-panel data not visible from ad text; not "irrelevant"
- **"100% Naturale"**: `environmental_unsubstantiated` → `misleading_composition_or_ingredient_claim` — flavouring/ingredient-composition claim for a tea/infusion product, not environmental
- **"di origine naturale e bio"**: `environmental_unsubstantiated` → `misleading_composition_or_ingredient_claim` — ingredient-sourcing/composition claim for a jam; not a packaging/emissions/resource-use claim
- **"cosa intendiamo quando diciamo «Natural»"**: `environmental_unsubstantiated` → `misleading_composition_or_ingredient_claim` — this is the header of a disclosure explaining a 'senza zuccheri aggiunti' / naturally-occurring-sugar claim (see product features: '**Contiene naturalmente zuccheri') -- a composition/nutrition disclosure, not environmental content
- **"Solo aromi naturali"**: `environmental_unsubstantiated` → `misleading_composition_or_ingredient_claim` — flavouring-source claim (EU Flavourings Reg. 1334/2008), not environmental performance
- **"100% Naturale"**: `environmental_unsubstantiated` → `misleading_composition_or_ingredient_claim` — flavouring/ingredient-composition claim for a tea/infusion product, not environmental
- **"100% di origine naturale"**: `environmental_unsubstantiated` → `misleading_composition_or_ingredient_claim` — fruit-juice ingredient-composition claim, not environmental
- **"100% di origine naturale"**: `environmental_unsubstantiated` → `misleading_composition_or_ingredient_claim` — fruit-juice ingredient-composition claim, not environmental
- **"100% naturale"**: `environmental_unsubstantiated` → `misleading_composition_or_ingredient_claim` — vinegar production-composition claim, not environmental
- **"100% Naturale / 100% Ingredienti naturali"**: `environmental_unsubstantiated` → `misleading_composition_or_ingredient_claim` — broth ingredient-composition claim, not environmental

## 3. Risk level adjusted

**12 instances.**

- **"Dopo l'utilizzo la pelle risulta più morbida e vellutata** ... Test di autovalutazione"**: LOW → MEDIUM — disclosed basis is a self-assessment test, not instrumental/clinical -- weaker evidence than the LOW label implies
- **"Nichel, Cromo e Cobalto tested"**: LOW → MEDIUM — "tested" with no disclosed result/threshold -- same ambiguity as bare "dermatologicamente testato"
- **"Il Reishi, un fungo conosciuto per le proprietà benefiche, contribuisce alle naturali difese dell'organismo"**: MEDIUM → HIGH — mimics authorized EFSA "contribuisce" phrasing for an unauthorized botanical, with no "tradizionalmente" hedge -- higher-confidence violation than a hedged traditional-use claim
- **"L'Echinacea contribuisce alle naturali difese dell'organismo e alla funzionalità delle prime vie respiratorie"**: MEDIUM → HIGH — mimics authorized EFSA "contribuisce" phrasing for an unauthorized botanical, with no "tradizionalmente" hedge -- higher-confidence violation than a hedged traditional-use claim
- **"100% Naturale"**: MEDIUM → LOW — ordinary, common ingredient/flavour-source composition claim with no specific reason to doubt it -- same tier as "Senza grassi idrogenati", which was already LOW; MEDIUM was inherited from the environmental bucket these claims used to sit in, not a real risk assessment
- **"di origine naturale e bio"**: MEDIUM → LOW — ordinary, common ingredient/flavour-source composition claim with no specific reason to doubt it -- same tier as "Senza grassi idrogenati", which was already LOW; MEDIUM was inherited from the environmental bucket these claims used to sit in, not a real risk assessment
- **"Solo aromi naturali"**: MEDIUM → LOW — ordinary, common ingredient/flavour-source composition claim with no specific reason to doubt it -- same tier as "Senza grassi idrogenati", which was already LOW; MEDIUM was inherited from the environmental bucket these claims used to sit in, not a real risk assessment
- **"100% Naturale"**: MEDIUM → LOW — ordinary, common ingredient/flavour-source composition claim with no specific reason to doubt it -- same tier as "Senza grassi idrogenati", which was already LOW; MEDIUM was inherited from the environmental bucket these claims used to sit in, not a real risk assessment
- **"100% di origine naturale"**: MEDIUM → LOW — ordinary, common ingredient/flavour-source composition claim with no specific reason to doubt it -- same tier as "Senza grassi idrogenati", which was already LOW; MEDIUM was inherited from the environmental bucket these claims used to sit in, not a real risk assessment
- **"100% di origine naturale"**: MEDIUM → LOW — ordinary, common ingredient/flavour-source composition claim with no specific reason to doubt it -- same tier as "Senza grassi idrogenati", which was already LOW; MEDIUM was inherited from the environmental bucket these claims used to sit in, not a real risk assessment
- **"100% naturale"**: MEDIUM → LOW — ordinary, common ingredient/flavour-source composition claim with no specific reason to doubt it -- same tier as "Senza grassi idrogenati", which was already LOW; MEDIUM was inherited from the environmental bucket these claims used to sit in, not a real risk assessment
- **"100% Naturale / 100% Ingredienti naturali"**: MEDIUM → LOW — ordinary, common ingredient/flavour-source composition claim with no specific reason to doubt it -- same tier as "Senza grassi idrogenati", which was already LOW; MEDIUM was inherited from the environmental bucket these claims used to sit in, not a real risk assessment

