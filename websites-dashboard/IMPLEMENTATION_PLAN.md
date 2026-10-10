# Firm Claims Dashboard: Implementation Plan

This is the step-by-step build plan for Claude Code. It turns `PLAN.md` (the agreed design) and `src/content/METHODOLOGY.md` (currently `METHODOLOGY.md` at the repo root) into working code.

**How to use this file**

- Work through the phases in order. Don't start a phase until the previous phase's acceptance checks pass.
- **If this file and `PLAN.md` disagree, this file wins.** Section 1 lists every deviation.
- If something isn't covered here, pick the simplest option that fits `PLAN.md`, write it down under "Implementation notes" at the end of this file, and keep going. Don't stop to ask unless a step is marked **STOP**.
- After every phase, run `npm run lint && npm run typecheck && npm test` (and `npm run test:e2e` once it exists). Then make one commit, with a message like `feat(phase-3): fixture generator`.
- Never commit plaintext data, a real passcode, or the ORBIS CSV.

---

## 0. Context

- **Repo root:** the `websites-dashboard/` folder. It isn't a git repo yet. It already contains:
  - `METHODOLOGY.md`, which is moved to `src/content/METHODOLOGY.md` in Phase 1.
  - `PLAN.md`, which stays at the root.
  - `ORBIS_Italia_allsectors.csv` (210 MB). It must be **gitignored** and never staged.
  - `count_websites.py`, a research helper. Leave it untouched and commit it as is. It scans folders recursively, so run it with an explicit path rather than from the repo root once `node_modules/` exists.
- **GitHub repo name:** `websites-dashboard`, public (required for free GitHub Pages). Vite `base` is `/websites-dashboard/`.
- **Node:** 22 LTS. Add an `.nvmrc` containing `22` and set `"engines": { "node": ">=22" }`.
- **Package manager:** npm. Commit `package-lock.json`.

---

## 1. Decisions (deviations from and additions to PLAN.md)

These were agreed with the project owner on 2026-10-10.

| # | Topic | Decision |
|---|---|---|
| D1 | Latest crawl | The **latest crawl** is the most recent crawl whose status is `ok` or `partial`. `failed` crawls never decide present/removed. They appear only as markers on the timeline and in crawl history. A `partial` latest crawl counts normally, but the firm header shows a note. |
| D2 | Last crawled | "Last crawled" on the home page and in the header is the newest crawl of **any** status. If it isn't `ok`, the status is shown next to it, for example `2 Nov 2026 (failed)`. |
| D3 | Home table | Adds a **Firm name** column (hidden below 700px). Search matches `firm_id` **or** `firm_name`, case-insensitive substring. |
| D4 | Confidence colors | A four-step scale: **none = white, low = yellow, medium = orange, high = red**. It is used for the header accent, H/M/L counters, badges and breakdown stacks. Wherever confidence appears it is labelled "confidence" and has the tooltip *"Detector confidence, not legal severity"*. |
| D5 | Demo firms | **Fictional** names and domains on the reserved `.example` TLD (`https://www.verdeluce.example`). Real ORBIS firms are never used in fixtures. |
| D6 | Tests | Vitest for `src/lib` and `scripts`, plus Playwright e2e (Chromium). Both run in CI before deploy. |
| D7 | Categories | Keep the 7 gold-set categories. The app reads `categories` from the data file. An unknown category id gets an auto-generated label and the fallback color, never an error (it still has to appear in the file's `categories` list). |
| D8 | Methodology TODOs | HTML comments are stripped before rendering. A list item left as just a bold label (e.g. `- **Firms:**`) is removed. |
| D9 | Claim ID | The exact normalization and hash are fixed in §4.3. The pipeline must use the same function (a Python version is in Appendix A). |
| D10 | Deep links through the gate | The gate renders **in place of** the routed content and the URL never changes, so after unlocking the requested route renders directly. No redirect logic is needed. |
| D11 | Filter URL behavior | Filter changes use `replace` (no history spam). Opening the drawer uses `push`, so Back closes it. |
| D12 | Home state in URL | `#/?q=<search>&page=<n>`, written with `replace`. The firm page's "← All firms" link returns to the same search and page. |
| D13 | Lock button | The header has a "Lock" button that clears the decrypted data and the stored passcode and shows the gate again. |
| D14 | Timeline split mode | "Split by category" is local component state, not stored in the URL. Only categories with at least one non-zero point get a line. |
| D15 | Breakdown click | See the exact rules in §7.4. |
| D16 | Wide layout | The timeline and breakdown sit side by side at ≥1024px (`lg`) and stack below that. |
| D17 | Dates | Formatted in **UTC** with a fixed month table (`12 Oct 2026`), never `Intl` (newer ICU writes "Sept"). |
| D18 | Passcode in CI | CI never needs the passcode, because the committed file is already encrypted. e2e tests use their own throwaway encrypted fixture served by request interception. |
| D19 | Fixture crawl dates | As in PLAN.md: weekly from Mon 5 Oct 2026, up to 5 crawls (so up to 2 Nov 2026). `generated_at` is fixed at `2026-11-02T14:00:00Z`. |

**Phase 1 task:** update `PLAN.md` so it agrees with D1–D4, then add one line at the top: `Implementation details and later decisions: see IMPLEMENTATION_PLAN.md.`

---

## 2. Tech stack and exact setup

Use the latest stable versions at scaffold time and commit the lockfile. Don't upgrade packages that shadcn installs.

| concern | package(s) |
|---|---|
| Build | `vite`, `@vitejs/plugin-react`, `typescript` (from `npm create vite@latest -- --template react-ts`) |
| Styling | `tailwindcss` v4, `@tailwindcss/vite`, `@tailwindcss/typography` |
| UI | shadcn/ui (`npx shadcn@latest`): `table input pagination card badge scroll-area sheet toggle-group dropdown-menu button chart tooltip separator alert skeleton` |
| Charts | `recharts` (installed by `shadcn add chart`) |
| Routing | `react-router` (v7, import from `react-router`, using `HashRouter`) |
| Validation | `zod` |
| Markdown | `react-markdown`, `remark-gfm` (needed for tables) |
| Scripts | `tsx` (dev) |
| Unit tests | `vitest`, `jsdom`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event` |
| e2e | `@playwright/test` (Chromium only) |

### 2.1 Scaffolding into a non-empty folder

`npm create vite` refuses to run in a folder that already has files. Instead:

1. Scaffold into `./.scaffold-tmp`.
2. Move everything except `README.md` into the repo root, then delete `.scaffold-tmp`.
3. Write your own `README.md` (Phase 9).

### 2.2 Tailwind v4 and shadcn

- In `vite.config.ts`, use plugins `[react(), tailwindcss()]` and `resolve.alias: { '@': path.resolve(__dirname, 'src') }`.
- Add `"baseUrl": "."` and `"paths": { "@/*": ["./src/*"] }` to both `tsconfig.json` and `tsconfig.app.json`, as shadcn's Vite guide requires.
- Set up `src/index.css` with `@import "tailwindcss";` and `@plugin "@tailwindcss/typography";`.
- Run `npx shadcn@latest init` with base color `neutral`, then add the components listed above.

### 2.3 Dark mode follows the system only

This replaces PLAN.md's `darkMode: "media"`, which is Tailwind v3 syntax. After `shadcn init`:

- Replace `@custom-variant dark (&:is(.dark *));` with `@custom-variant dark (@media (prefers-color-scheme: dark));`.
- Move the `.dark { --… }` variable block into `@media (prefers-color-scheme: dark) { :root { --… } }`.
- No `.dark` class may appear anywhere in `src/`. Add a unit test that greps `src/**/*.{ts,tsx,css}` for `\.dark\b` and fails if it finds one.
- Set `body` to `bg-background text-foreground`.

### 2.4 Custom breakpoint

Add this to `src/index.css`:

```css
@theme { --breakpoint-tab: 700px; }
```

This creates a `tab:` variant for ≥700px. Use `lg:` (1024px) for D16. In JS, use `useMediaQuery('(min-width: 700px)')`.

### 2.5 Color tokens

Add these to `src/index.css` under `:root`, and override them inside the dark media block.

| token | light | dark | used for |
|---|---|---|---|
| `--conf-none` | `#ffffff` | `#f4f4f5` | header accent when there are no present claims (always paired with a `border` so it's visible) |
| `--conf-low` | `#facc15` | `#fde047` | low |
| `--conf-low-fg` | `#422006` | `#422006` | text on low |
| `--conf-low-stroke` | `#a16207` | `#ca8a04` | 1px outline on low bars and dots (yellow-on-white contrast is too low) |
| `--conf-medium` | `#f97316` | `#fb923c` | medium |
| `--conf-medium-fg` | `#431407` | `#431407` | text on medium |
| `--conf-high` | `#dc2626` | `#f87171` | high |
| `--conf-high-fg` | `#ffffff` | `#450a0a` | text on high |
| `--cat-1` … `--cat-7` | `#2563eb #0d9488 #7c3aed #16a34a #db2777 #0891b2 #4f46e5` | `#60a5fa #2dd4bf #a78bfa #4ade80 #f472b6 #22d3ee #818cf8` | category lines and chip dots, assigned by index in `data.categories` |
| `--cat-fallback` | `#64748b` | `#94a3b8` | categories with index ≥ 7 |

Confidence never uses `--cat-*`, and categories never use the confidence colors.

---

## 3. Repository layout (final)

```
.
├── .github/workflows/deploy.yml
├── .gitignore
├── .nvmrc
├── count_websites.py                # untouched
├── data/                            # gitignored; firms.json lives here
├── e2e/
│   ├── global-setup.ts
│   ├── helpers.ts                   # unlock(), loadFixture(), testPasscode
│   ├── gate.spec.ts
│   ├── home.spec.ts
│   ├── firm.spec.ts
│   ├── drawer.spec.ts
│   ├── responsive.spec.ts
│   └── misc.spec.ts                 # methodology, not-found, dark mode
├── IMPLEMENTATION_PLAN.md
├── PLAN.md
├── playwright.config.ts
├── public/data/firms.enc            # ciphertext, committed (Phase 10)
├── README.md
├── scripts/
│   ├── check-no-plaintext.mjs
│   ├── encrypt.ts
│   ├── generate-fixtures.ts
│   ├── fixtures/pools.ts            # Italian text pools and name parts
│   ├── fixtures/prng.ts             # mulberry32
│   └── *.test.ts
├── src/
│   ├── App.tsx                      # HashRouter, DataProvider, AppShell, routes
│   ├── main.tsx
│   ├── index.css
│   ├── content/METHODOLOGY.md
│   ├── components/ui/               # shadcn (generated, don't hand-edit except via shadcn)
│   ├── components/
│   │   ├── AppShell.tsx
│   │   ├── PasscodeGate.tsx
│   │   ├── DataErrorScreen.tsx
│   │   ├── FirmTable.tsx
│   │   ├── FirmHeader.tsx
│   │   ├── FilterBar.tsx
│   │   ├── ClaimStrip.tsx
│   │   ├── ClaimCard.tsx
│   │   ├── ClaimDrawer.tsx
│   │   ├── Timeline.tsx
│   │   ├── CategoryBreakdown.tsx
│   │   ├── ConfidenceBadge.tsx
│   │   ├── ConfidenceCounters.tsx
│   │   └── CategoryChip.tsx
│   ├── data/DataProvider.tsx        # context + state machine
│   ├── hooks/useMediaQuery.ts
│   ├── hooks/useFirmFilters.ts
│   ├── lib/
│   │   ├── schema.ts                # zod
│   │   ├── types.ts                 # z.infer types + Filters
│   │   ├── crypto.ts
│   │   ├── claimId.ts
│   │   ├── derive.ts
│   │   ├── filters.ts               # URL <-> Filters
│   │   ├── format.ts                # dates, hostnames, labels, legal ref
│   │   ├── categories.ts            # labels and color index
│   │   ├── methodology.ts           # TODO stripping
│   │   └── *.test.ts
│   └── pages/Home.tsx, Firm.tsx, Methodology.tsx, NotFound.tsx
├── tsconfig*.json
└── vite.config.ts
```

### 3.1 `.gitignore`

Keep the Vite defaults, plus:

```
node_modules/
dist/
data/
*.csv
e2e/.tmp/
playwright-report/
test-results/
.scaffold-tmp/
.DS_Store
.env*
```

### 3.2 npm scripts

```json
{
  "dev": "vite",
  "build": "tsc -b && vite build",
  "preview": "vite preview",
  "typecheck": "tsc -b",
  "lint": "eslint . && node scripts/check-no-plaintext.mjs",
  "test": "vitest run",
  "test:watch": "vitest",
  "test:e2e": "playwright test",
  "fixtures": "tsx scripts/generate-fixtures.ts",
  "encrypt": "tsx scripts/encrypt.ts"
}
```

`scripts/check-no-plaintext.mjs` runs `git ls-files`. It exits 1 if any tracked path starts with `data/` or ends in `.csv`, or if any tracked file under `public/` ends in `.json`. When run outside a git repo it prints a warning and exits 0.

Include `scripts/` and `e2e/` in `tsconfig.node.json`, and make sure ESLint covers them.

---

## 4. Library layer (`src/lib`): exact behavior

### 4.1 `schema.ts` (zod)

```ts
const Confidence = z.enum(['high', 'medium', 'low']);
const Scope = z.enum(['IN_SCOPE', 'NEEDS_VERIFICATION']);
const CrawlStatus = z.enum(['ok', 'partial', 'failed']);
const IsoDateTime = z.string().datetime({ offset: true });   // or z.iso.datetime({ offset: true }) in zod v4
const HttpUrl = z.string().url().refine(u => /^https?:\/\//.test(u), 'must be http(s)');

const Crawl = z.object({
  crawl_id: z.string().min(1),
  crawled_at: IsoDateTime,
  pages_scraped: z.number().int().min(0),
  status: CrawlStatus,
});

const Claim = z.object({
  claim_id: z.string().min(1),
  text: z.string().min(1),
  context_snippet: z.string(),                 // may be ""
  source_url: HttpUrl,
  category: z.string().min(1),
  scope_status: Scope,
  confidence: Confidence,
  gray_zone: z.string().min(1).nullable(),
  legal_ref: z.object({ ucpd: z.string().min(1).nullable(), codice_consumo: z.string().min(1).nullable() }),
  seen_in_crawls: z.array(z.string().min(1)).min(1),
});

const Firm = z.object({
  firm_id: z.string().regex(/^[A-Za-z0-9_-]+$/),
  firm_name: z.string().min(1),
  website: HttpUrl,
  crawls: z.array(Crawl).min(1),
  claims: z.array(Claim),
});

export const DataFile = z.object({
  schema_version: z.string().regex(/^1\.\d+$/),
  generated_at: IsoDateTime,
  categories: z.array(z.string().regex(/^[a-z0-9_]+$/)).min(1),
  firms: z.array(Firm),
}).superRefine(crossChecks);
```

Unknown keys are stripped silently (zod's default), so the future `review` field won't break old builds.

`crossChecks` adds one issue per violation, each with a precise `path`:

1. `categories` has no duplicates.
2. `firm_id` is unique across firms.
3. `crawl_id` is unique within each firm.
4. `claim_id` is unique within each firm and starts with `${firm_id}-`.
5. `claim.category` is in `categories`.
6. Every id in `seen_in_crawls` refers to a crawl of the same firm.
7. No id in `seen_in_crawls` refers to a `failed` crawl. The message is `claim seen in failed crawl <id>`.
8. `seen_in_crawls` has no duplicates.

Export `parseDataFile(json: unknown): { ok: true; data } | { ok: false; issues: { path: string; message: string }[] }`. The path is rendered like `firms[3].claims[12].category`.

### 4.2 `crypto.ts`

This module is shared by the browser and `scripts/encrypt.ts`. It uses only `globalThis.crypto.subtle`, `TextEncoder`/`TextDecoder`, `btoa`/`atob`, and no `Buffer`.

```ts
export type EncFile = { v: 1; kdf: 'PBKDF2-SHA256'; iterations: number; salt: string; iv: string; ciphertext: string };
export const EncFileSchema: z.ZodType<EncFile>;    // v literal 1, iterations int >= 100_000
export const DEFAULT_ITERATIONS = 600_000;
export async function encryptString(plaintext: string, passcode: string, opts?: { iterations?: number }): Promise<EncFile>;
export async function decryptToString(enc: EncFile, passcode: string): Promise<string>; // throws WrongPasscodeError on GCM failure
export class WrongPasscodeError extends Error {}
```

- Normalize the passcode with `.normalize('NFC')` before encoding it as UTF-8.
- Salt: 16 random bytes. IV: 12 random bytes. Key: PBKDF2-SHA256 derived to AES-GCM 256, `extractable: false`, no AAD.
- base64 is standard with padding. Use chunked `String.fromCharCode` so large buffers don't overflow the stack.
- If decryption reads `iterations` from the file, `opts.iterations` exists only for tests and the script.

### 4.3 `claimId.ts` (must match the pipeline)

```ts
export function normalizeClaimText(text: string): string {
  return text
    .normalize('NFKC')
    .toLowerCase()
    .replace(/[\p{P}\p{S}]/gu, '')     // strip all Unicode punctuation and symbols (incl. « » % ® € -)
    .replace(/\s+/gu, ' ')
    .trim();
}
export async function claimHash(text: string): Promise<string>;   // sha256(UTF-8(normalizeClaimText(text))) → hex → first 6 chars
export async function makeClaimId(firmId: string, text: string): Promise<string>; // `${firmId}-${hash}`
```

Test vectors. These were checked with both this JS and the Python in Appendix A.

| input | normalized | hash |
|---|---|---|
| `Packaging 100% sostenibile` | `packaging 100 sostenibile` | `91ba7d` |
| `  PACKAGING   100 % sostenibile! ` | `packaging 100 sostenibile` | `91ba7d` |
| `«Benessere animale garantito»` | `benessere animale garantito` | `79969e` |
| `-30% di emissioni di CO₂ rispetto al 2020` | `30 di emissioni di co2 rispetto al 2020` | `f95687` |
| `Certificato FSC®` | `certificato fsc` | `f35c4c` |

The app **never recomputes** claim IDs from real data. It treats them as opaque. This module is used by the fixtures and documents the contract.

### 4.4 `derive.ts` (pure functions, unit-tested)

```ts
sortCrawlsAsc(crawls): Crawl[]                         // by crawled_at, ties by crawl_id
getLatestCrawl(firm): Crawl | null                     // newest with status !== 'failed' (D1); null if none
getNewestCrawl(firm): Crawl                            // newest of any status (D2)
isPresent(claim, latest: Crawl | null): boolean        // latest !== null && seen_in_crawls.includes(latest.crawl_id)
firstSeen(claim, firm): string                         // min crawled_at over seen_in_crawls
lastSeen(claim, firm): string                          // max crawled_at over seen_in_crawls
presentClaims(firm): Claim[]
confidenceCounts(firm): { high: number; medium: number; low: number }   // present only, unfiltered
highestConfidence(firm): 'high' | 'medium' | 'low' | null
applyFilters(claims, filters): Claim[]                 // AND across dimensions; null dimension = all
sortForStrip(claims, firm): Claim[]                    // present first; then high>medium>low; then category label A–Z; then text A–Z (deterministic)
stripCounts(claims, firm): { total; present; removed }
timelineSeries(firm, filters, splitCategories: string[] | null): TimelinePoint[]
categoryBreakdown(firm, filters, categories): BreakdownRow[]
crawlHistory(claim, firm): { crawl: Crawl; seen: boolean }[]          // all firm crawls asc
```

**`TimelinePoint`:**
`{ crawl_id, crawled_at, status, pages_scraped, total: number | null, [category]: number | null }`

- For a `failed` crawl, `total` and every category value are `null` (a gap, never 0).
- For other crawls, a value counts claims that pass `filters` and have this `crawl_id` in `seen_in_crawls`.
- When `splitCategories` is non-null, compute one key per listed category. A category's count counts only claims of that category that pass the confidence and scope filters.

**`BreakdownRow`:**
`{ category, label, high, medium, low, total }`

- One row for **every** id in `categories`, in `categories` order.
- Counts **present** claims only.
- Applies the confidence and scope filters and **ignores** the category filter.

### 4.5 `filters.ts`

```ts
export type Filters = { categories: string[] | null; confidences: Confidence[] | null; scopes: Scope[] | null }; // null = all
export function parseFilters(sp: URLSearchParams, allCategories: string[]): Filters;
export function writeFilters(sp: URLSearchParams, f: Filters, allCategories: string[]): URLSearchParams; // returns a copy
```

- The params are `cat`, `conf` and `scope`, each a comma-separated list.
- Parsing:
  - Split on `,`, trim, and drop unknown values and duplicates.
  - If nothing is left, or the result equals the full set, the dimension is `null`.
- Writing:
  - A `null` dimension, or one equal to the full set, removes its param.
  - Otherwise, write the values in canonical order: `categories` order, `high,medium,low`, then `IN_SCOPE,NEEDS_VERIFICATION`.
  - All other params (`claim` and anything else) are kept.
- The UI never produces an empty selection. If the user deselects the last selected value in a dimension, nothing happens.

### 4.6 `format.ts`, `categories.ts` and `methodology.ts`

- **`formatDate(iso)`** returns `${UTCDate} ${MONTHS[UTCMonth]} ${UTCFullYear}`, with `MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']`. For example, `2026-10-12T09:10:00Z` → `12 Oct 2026`.
- **`hostname(url)`** returns the URL's host without a leading `www.`.
- **`legalRefLabel(ref)`** returns `UCPD ${ucpd ?? '—'} / Cod. Cons. ${codice_consumo ?? '—'}`. If both are null, it returns `Not yet mapped`.
- **`CATEGORY_LABELS`:**
  - `generic_green` → Generic green
  - `certification` → Certification
  - `recycled_recyclable` → Recycled / recyclable
  - `vague_supply_chain` → Vague supply chain
  - `named_endorsement` → Named endorsement
  - `brand_eco_slogan` → Brand eco-slogan
  - `risk_reduction` → Risk reduction
- **`categoryLabel(id)`** returns the map value. Otherwise it replaces `_` with spaces and capitalizes the first letter.
- **`categoryColorVar(id, categories)`** returns `var(--cat-${i+1})` for i < 7, otherwise `var(--cat-fallback)`.
- **`CONFIDENCE_LABEL`:** `{ high: 'High', medium: 'Medium', low: 'Low' }`.
- **`CONFIDENCE_TOOLTIP`:** `'Detector confidence, not legal severity'`.
- **`cleanMethodology(md)`** does two things:
  - Removes `<!--[\s\S]*?-->`.
  - Removes any line matching `^\s*[-*]\s+\*\*[^*]+:\*\*\s*$` (a bullet left as just a label).

---

## 5. Data loading and the passcode gate

### 5.1 `DataProvider`

The state machine:

```
loading-file → locked ⇄ unlocking → ready
            ↘ file-error            ↘ data-error (bad JSON or validation)
```

1. **On mount**, fetch `${import.meta.env.BASE_URL}data/firms.enc` with `{ cache: 'no-cache' }`.
   - On a 404 or network error, go to `file-error` and show "Data file not found (data/firms.enc)."
   - If the body fails `EncFileSchema`, go to `file-error` and show "Data file is not a valid encrypted file."
2. **If the passcode is already stored:** if `sessionStorage['fcd.passcode']` exists, attempt to unlock silently. On `WrongPasscodeError`, remove the key and go to `locked`. Wrap every `sessionStorage` access in try/catch.
3. **To unlock:** run `decryptToString`, then `JSON.parse`, then `parseDataFile`.
   - A wrong passcode goes back to `locked` with `error: 'Incorrect passcode'`.
   - A JSON parse error goes to `data-error` with "Decrypted data is not valid JSON."
   - A validation failure goes to `data-error` with the issue list.
   - On success, store the passcode and go to `ready` with `{ data, firmsById: Map }`.
4. **`lock()`** removes the key, drops the data and goes to `locked`.
5. **`useData()`** throws if it's used outside `ready`. Pages are only rendered in `ready`.

### 5.2 `PasscodeGate`

- A centered card titled "Firm Claims Dashboard" with the subtitle "Enter the passcode to view the data."
- The form has a `type="password"` input (`autoComplete="current-password"`, `autoFocus`, label "Passcode") and a "Unlock" button.
- While unlocking (PBKDF2 at 600k iterations takes about 0.3–1 s), the button is disabled and shows "Unlocking…".
- Errors show under the input in `text-destructive` with `role="alert"`.
- The footer disclaimer is visible on the gate.

### 5.3 `DataErrorScreen`

- A title, a one-line explanation, and a scrollable `<ul>` of `path: message`. Show the first 50 issues, then "…and N more".
- A "Try again" button reloads the page.
- It never renders partial data.

---

## 6. Shell, routes and Home

### 6.1 Routes (`App.tsx`)

```tsx
<HashRouter>
  <DataProvider>
    <AppShell>           // the gate and error screens replace children based on provider state
      <Routes>
        <Route path="/" element={<Home/>} />
        <Route path="/firm/:firmId" element={<Firm/>} />   // unknown id → <NotFound/>
        <Route path="/methodology" element={<Methodology/>} />
        <Route path="*" element={<NotFound/>} />
      </Routes>
    </AppShell>
  </DataProvider>
</HashRouter>
```

### 6.2 `AppShell`

- **Header:** "Firm Claims Dashboard" (a link to `/`), a "Methodology" link, and a "Lock" button (only in the `ready` state).
- **Container:** `mx-auto max-w-6xl px-4`.
- **Footer** on every page, including the gate: *"Research prototype. Automated detection, not a legal assessment."*
- **`document.title`:**
  - Home: `Firm Claims Dashboard`
  - Firm page: `${firm_id} · Firm Claims Dashboard`
  - Methodology: `Methodology · Firm Claims Dashboard`

### 6.3 Home (`FirmTable`)

- **Search** `Input`, with placeholder "Search by firm ID or name" and `aria-label`. It writes `q` with `replace` and resets `page` to 1.
- **Sort:** `firm_id` ascending with `localeCompare(b, undefined, { numeric: true })`.
- **Page size:** 15. Parse `page` from the URL and clamp it to `[1, pageCount]`. An invalid value means 1.
- **Columns:**

  | ≥700px | <700px |
  |---|---|
  | Firm ID | Firm ID |
  | Firm name | — |
  | Website (`hostname`, new tab, `rel="noopener noreferrer"`, `onClick` stops propagation) | — |
  | Claims (latest): `presentClaims.length`, or `—` if there's no latest crawl | Claims |
  | Confidence: `ConfidenceCounters` (compact) | Confidence |
  | Crawls (count, all statuses) | — |
  | Last crawled: `formatDate(newest)` plus ` (failed)` / ` (partial)` if needed | — |

- **Rows:**
  - Each row has `data-testid="firm-row"`, `cursor-pointer` and `onClick` navigation.
  - The Firm ID cell holds a real `<Link>` for keyboard and accessibility.
  - Navigation passes `state: { homeSearch: location.search }`.
- **Under the table:** "Showing 16–30 of 40 firms" plus a shadcn `Pagination`.
  - Prev and Next are disabled at the ends.
  - Page numbers show with ellipses when there are more than 7 pages.
- **Empty state** (a single cell spanning all columns): `No firms match "<q>".`

---

## 7. Firm page

`Firm.tsx` looks up the firm by `useParams().firmId`. If it's not found, it renders `<NotFound/>`. Memoize every derived value with `useMemo` keyed on the firm and the filters.

Order on the page:
1. A back link
2. `FirmHeader`
3. `FilterBar`
4. `ClaimStrip`
5. A grid (`lg:grid-cols-2 gap-6`) with `Timeline` and `CategoryBreakdown`
6. `ClaimDrawer`

The back link reads "← All firms". It goes to `/` + `location.state?.homeSearch ?? ''`.

### 7.1 `FirmHeader`

- Firm ID (large, mono), firm name and a website link (new tab).
- **"Detection confidence" block:**
  - A `border-l-4` accent colored `var(--conf-<highest>)`, or `var(--conf-none)` when there are no present claims. When there are none, the block also has `border` so the white stays visible.
  - Three `ConfidenceCounters` tiles: "High n", "Medium n", "Low n", each in its own confidence color with its matching `-fg` text.
  - A tooltip on the block title: `CONFIDENCE_TOOLTIP`.
- **Meta line:** `Last crawled 2 Nov 2026 (failed) · 4 crawls`.
- **Extra notes**, each shown only when it applies:
  - If the latest crawl differs from the newest crawl: `Claims as of 26 Oct 2026 (latest successful crawl).`
  - If the latest crawl is `partial`: `Latest crawl was partial (n pages). Some claims may be missing.`
  - If there is no latest crawl: `No successful crawl yet.`

### 7.2 `FilterBar` (via `useFirmFilters`)

- `useFirmFilters()` returns `{ filters, setFilters, clear }` and reads and writes `useSearchParams` with `{ replace: true }` (D11).
- **Category:** a `DropdownMenu` with a `DropdownMenuCheckboxItem` for each category, each with its color dot.
  - The trigger reads "Category: All" or "Category: 3 selected" (or the label when one is selected).
  - The menu stays open while toggling items.
- **Confidence:** `ToggleGroup type="multiple"` with High, Medium and Low. "All" shows as all three pressed.
- **Scope:** `ToggleGroup type="multiple"` with "In scope" and "Needs verification".
- **"Clear filters"** is a `Button variant="ghost"`. It's disabled when all three dimensions are `null`.
- Deselecting the last pressed item in a group is ignored (§4.5).
- Below 700px the controls wrap, and each takes the full width.

### 7.3 `ClaimStrip` and `ClaimCard`

- The heading is "Claims", with a count: `24 claims (19 present, 5 removed)`. Counts are after filtering.
- A legend line in small, muted text: "Dashed border = needs verification · Greyed = no longer found".
- A horizontal `ScrollArea` (`data-testid="claim-strip"`) containing a flex row of cards, each `w-[280px] h-[160px] shrink-0`.
- **`ClaimCard`:**
  - It's a `<button>` with `data-testid="claim-card"` and `data-claim-id`.
  - Content:
    - Text in Italian with `line-clamp-3`. Add `lang="it"` on the text element.
    - A `CategoryChip`: an outline badge with a color dot and the label.
    - A `ConfidenceBadge`: filled in its confidence color, with text "High" / "Medium" / "Low" and a title tooltip.
  - **NEEDS_VERIFICATION:** a `border-2 border-dashed` border, plus a small "Needs verification" label (so the state isn't conveyed by the border alone).
  - **Removed:** `opacity-60 grayscale`, plus the label `Removed · last seen <date>`.
  - On click, `navigate({ search: withClaim(id) }, { state: { ...location.state, drawerFromStrip: true } })`. This is a push.
- **Empty states:**
  - If the firm has no claims at all: "No claims detected on this site yet."
  - Otherwise: "No claims match these filters." with a "Clear filters" button.

### 7.4 `Timeline`

- A shadcn `ChartContainer` holding a Recharts `LineChart`, 280px high.
- **X axis:** `dataKey="crawl_id"`, with `tickFormatter` set to `formatDate(crawled_at)`. Using the id keeps x values unique.
- **Y axis:** `allowDecimals={false}`, `domain={[0, 'auto']}`.
- **Default mode:** one `total` line in `var(--foreground)` with `connectNulls={false}`.
- **Failed crawls:** a `ReferenceLine x={crawl_id}`, dashed and muted, with the label "Crawl failed".
- **Partial crawls:** the point uses a hollow dot, and the tooltip says "Partial crawl (n pages)".
- **Tooltip:** date, status, total, and the per-category counts in split mode.
- **"Split by category" toggle** (a `Switch` or toggle `Button`, local state, D14):
  - It draws a line for each category in the selected set (filter `null` = all `categories`) that has at least one non-zero point, colored `categoryColorVar`.
  - It keeps the total line, thicker (`strokeWidth=3`).
  - It shows a legend.
- **When `firm.crawls.length === 1`:** render the single dot and the caption "Only one crawl so far".

### 7.5 `CategoryBreakdown`

- A Recharts `BarChart layout="vertical"` with the Y axis showing category labels.
- Stacked bars in the order `high`, `medium`, `low`, colored with the confidence colors. `low` bars also get `stroke="var(--conf-low-stroke)"`.
- **Highlight:** when the category filter isn't `null`, rows outside the selection render at `fillOpacity 0.3`.
- **Clicking a bar's row toggles the category in the filter (D15):**

  | current filter | click X | result |
  |---|---|---|
  | `null` (all) | X | `[X]` |
  | `[X]` | X | `null` |
  | `[X]` | Y | `[X, Y]` |
  | `[X, Y]` | X | `[Y]` |
  | a selection plus X that equals the full set | X | `null` |

- Below the chart, small muted text: "Present claims in the latest crawl. Category filter highlights; it doesn't hide."
- **Empty state:** if every row's total is 0, show "No present claims in the latest crawl." instead of the chart.

### 7.6 `ClaimDrawer`

- It is open when `claim` is in the URL and matches a claim of this firm.
- If `claim` matches nothing, remove the param with `replace` and render closed.
- **Side:** `useMediaQuery('(min-width: 700px)')`. When it matches, use `side="right"` and `sm:max-w-lg`. Otherwise use `side="bottom"`, `max-h-[85vh] overflow-y-auto`.
- **Closing** (X, Esc or overlay): if `location.state?.drawerFromStrip`, call `navigate(-1)`. Otherwise remove `claim` with `replace`.
- **Contents, in order:**
  1. `SheetTitle`: the full claim text (`lang="it"`).
  2. Badges: category, confidence, scope, and a "Removed" badge if the claim is removed.
  3. **Context:** the snippet in a blockquote (`lang="it"`), with the claim highlighted in `<mark>`.
     - To highlight, find the first case-insensitive occurrence of `text` in the snippet and split around it. If there's no match, render the snippet without highlighting.
     - Never use `dangerouslySetInnerHTML`.
     - If the snippet is empty, hide this section.
  4. **Source:** a link to `source_url` (new tab), showing the URL without the protocol.
  5. **Legal reference:** `legalRefLabel`, plus the small note "Indicative mapping, not a legal assessment."
  6. **Gray zone:** the value, or the section is hidden if it's null.
  7. **Crawl history:**
     - "First seen <date> · Last seen <date>".
     - A list with one row per crawl of the firm: the date, then "Seen", "Not seen" or "Crawl failed", plus "(partial)" when relevant.

---

## 8. Methodology and Not found

- **`Methodology.tsx`:** `import md from '@/content/METHODOLOGY.md?raw'`, then render `<ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml>{cleanMethodology(md)}</ReactMarkdown>` inside `article.prose dark:prose-invert max-w-none`. Override `a` so external links open in a new tab with `rel="noopener noreferrer"`. Add `declare module '*.md?raw'` if `vite/client` types don't cover it.
- **`NotFound.tsx`:** the heading "Not found", the text "That page or firm doesn't exist.", and a link "Back to all firms" to `/`.

---

## 9. Scripts

### 9.1 `scripts/encrypt.ts`

Usage: `npm run encrypt -- [--in data/firms.json] [--out public/data/firms.enc] [--iterations 600000]`

1. Read `--in`, then `JSON.parse` and `parseDataFile`. If either fails, print the issues and exit 1.
2. Get the passcode:
   - If `process.env.DASHBOARD_PASSCODE` is set, use it.
   - Otherwise prompt on a TTY with hidden input (`node:readline` with muted output), then confirm it. A mismatch exits 1.
   - If there's no TTY and no env variable, exit 1 with a message.
3. Strength check: the passcode must be at least 20 characters **and** at least 4 words (split on whitespace or `-`). Otherwise exit 1, unless `--allow-weak` is passed.
4. Encrypt with `crypto.ts` and write pretty JSON (2-space indent) to `--out`, creating the folder if needed.
5. Decrypt the output again and check it equals the input string. If it doesn't, delete the output and exit 1.
6. Print `Encrypted N firms, M claims → public/data/firms.enc (X KB)`.
7. Never print the passcode or log the plaintext.

### 9.2 `scripts/generate-fixtures.ts`

Usage: `npm run fixtures -- [--out data/firms.json]`

The output must be **fully deterministic**:
- Use `mulberry32(20261005)` from `fixtures/prng.ts`.
- Never use `Math.random`, `Date.now()` or `new Date()` without arguments.
- Use stable iteration orders.
- Write `JSON.stringify(data, null, 2) + '\n'`.

At the end, the generator runs `parseDataFile` and asserts every check in the "Coverage asserts" list below. It throws if any of them fails.

**Firms:** exactly 40, `F001`–`F040`.
- **Names** are built from `NAME_A × NAME_B` without repeats, plus a legal form chosen by the PRNG from `S.r.l.`, `S.p.A.` and `S.r.l.s.`.
  - Examples: `Verdeluce S.r.l.`, `Terranova S.p.A.`.
  - `NAME_A`: Verde, Terra, Aqua, Sole, Bosco, Fiore, Monte, Lago, Campo, Vigna, Olmo, Riva, Prato, Valle, Selva, Brezza, Rocca, Pietra, Fonte, Gelso.
  - `NAME_B`: luce, nova, viva, mare, sana, bella, pura, chiara, forte, dolce.
- **Website:** `https://www.<lowercased name without spaces or form>.example`.

**Crawls:**
- Crawl k (1-based) is dated `2026-10-05` + 7·(k−1) days, at `09:MM:00Z` with MM a PRNG value from 0 to 40.
- `crawl_id` = `${firm_id}-C${k padded to 2 digits}`.
- `pages_scraped`: the base is a PRNG value from 15 to 120, with ±5 drift for each crawl. A `failed` crawl has 0. A `partial` crawl has `round(base*0.3)`.
- For non-special firms: the number of crawls is a PRNG value from 1 to 5, and the status is `ok`.

**Claims:**
- Each firm draws a pool of candidate claims (texts without replacement from §9.3). Simulate presence crawl by crawl:
  - Crawl 1: each candidate is present with p = 0.7.
  - Later crawls:
    - A present claim is removed with p = 0.12.
    - A previously seen but absent claim reappears with p = 0.25.
    - A never-seen candidate appears with p = 0.15.
  - Failed crawls: nothing is seen, and the state carries over unchanged.
  - Claims never seen are dropped.
- **Attributes, assigned per claim:**
  - `confidence`: high 35%, medium 40%, low 25%.
  - `scope_status`: `IN_SCOPE` 75%, `NEEDS_VERIFICATION` 25%.
  - `gray_zone`: null 85%. Otherwise one of `natural_footnote`, `generic_plus_specific`, `renewable_energy` or `bio_based_packaging`.
  - `legal_ref`: from the pool entry. Then, at 8%, both values are null, and at 7%, `codice_consumo` alone is null.
  - `source_url`: the website plus one of `/`, `/chi-siamo`, `/sostenibilita`, `/ambiente`, `/prodotti`, `/blog/impegno-green`.
  - `context_snippet`: `…${PRE} ${text} ${POST}…`, with PRE and POST drawn from the pools. 5% of claims get `""`.
  - `claim_id`: `makeClaimId(firm_id, text)`.
- **Ordering:** claims are sorted by `claim_id`, and crawls by date.
- Non-special firms use 4–18 candidates.

**Special firms.** These override the random rules:

| firm | setup | tests |
|---|---|---|
| F001 | 5 ok crawls, about 15 candidates; at least 2 removals, at least 1 reappearance, at least 1 NEEDS_VERIFICATION, at least 1 gray zone, all three confidences | showcase firm |
| F002 | 1 ok crawl, 6 claims | single-dot timeline |
| F003 | 5 ok crawls, 34 candidates, at least 30 present in the latest | long strip |
| F004 | 3 ok crawls, 0 claims | empty states, white header |
| F005 | 4 crawls, C03 `failed` | timeline gap and marker |
| F006 | 4 crawls, C04 `failed` (newest) | D1/D2: present = as of C03, "Last crawled … (failed)" |
| F007 | 3 crawls, C03 `partial` | partial note |
| F008 | 4 ok crawls; one claim seen in C01, C02 and C04 but **not** C03 | reappearance |
| F009 | 3 ok crawls, all claims `low` | yellow header |
| F010 | 3 ok crawls, all claims `medium` | orange header |
| F011 | 2 crawls, both `failed`, 0 claims | "No successful crawl yet", `—` on home |
| F012 | 2 ok crawls; at least 1 claim with both legal values null and at least 1 with `codice_consumo` null | "Not yet mapped" |

**Coverage asserts:**
- There are 40 firms.
- Every category, confidence level and scope status appears at least 3 times among claims.
- Every gray zone value appears at least once.
- At least 10 claims are removed in their firm's latest crawl.
- All the special-firm conditions above hold.
- All claim IDs are unique within each firm.

### 9.3 `scripts/fixtures/pools.ts`

There are **at least 8 entries per category**, so at least 56 in total. This lets F003 reach 34 unique texts. Each entry is `{ text, legal_ref }`. Extend each list below to at least 8 in the same style. Use only fictional names for endorsements and brand lines. Generic real scheme names (FSC, Ecolabel UE, ISO 14001, B Corp) are acceptable in fictional-firm demo data.

**`generic_green`** — legal_ref `{ ucpd: 'Annex I 4a', codice_consumo: 'Art. 23' }`
- «Prodotto eco-friendly»
- «Packaging 100% sostenibile»
- «Rispettiamo l'ambiente in ogni fase della produzione»
- «Una scelta green per il pianeta»
- «Azienda sostenibile dal 1985»
- «Energia 100% rinnovabile nei nostri stabilimenti»
- «Amici dell'ambiente, ogni giorno»
- «Prodotti naturali e sostenibili»

**`certification`** — legal_ref `{ ucpd: 'Annex I 2a', codice_consumo: 'Art. 23' }`
- «Carta certificata FSC®»
- «Prodotto con marchio Ecolabel UE»
- «Ingredienti da agricoltura biologica certificata»
- «Stabilimento certificato ISO 14001»
- «Siamo un'azienda certificata B Corp»
- «Marchio VerdeGaranzia per la sostenibilità»
- «Certificazione ambientale di filiera»
- «Etichetta Eco Qualità 2026»

**`recycled_recyclable`** — legal_ref `{ ucpd: 'Art. 6(1)', codice_consumo: 'Art. 21' }`
- «Packaging 100% riciclato»
- «Bottiglia in plastica riciclata al 50%»
- «Confezione completamente riciclabile»
- «Vaschetta in bioplastica compostabile»
- «Carta riciclata post-consumo»
- «Imballaggi riciclabili nella raccolta della carta»
- «Tappo in materiale di origine vegetale»
- «Etichetta stampata su carta riciclata»

**`vague_supply_chain`** — legal_ref `{ ucpd: 'Art. 7', codice_consumo: 'Art. 22' }`
- «Benessere animale garantito»
- «Filiera controllata e responsabile»
- «Materie prime da fonti responsabili»
- «Coltivato nel rispetto della natura»
- «Fornitori selezionati per il loro impegno ambientale»
- «Pesca responsabile»
- «Allevamenti attenti all'ambiente»
- «Produzione etica e trasparente»

**`named_endorsement`** — legal_ref `{ ucpd: 'Annex I 4', codice_consumo: 'Art. 23' }`
- «Raccomandato dall'Associazione Consumatori Consapevoli»
- «Approvato da Rete Ambiente Italia»
- «Selezionato dall'Osservatorio Prodotti Verdi»
- «Partner ufficiale di Mare Pulito Onlus»
- «Premiato da Green Award Italia 2025»
- «Con il patrocinio del Comitato Clima Sostenibile»
- «Consigliato dalla Fondazione Terra Viva»
- «Sostenuto da Alleanza per le Foreste»

**`brand_eco_slogan`** — legal_ref `{ ucpd: 'Annex I 4a', codice_consumo: 'Art. 23' }`
- «Linea VerdeVivo: la natura in ogni gesto»
- «EcoPiù, la scelta naturale»
- «Natura Pura – il gusto del rispetto»
- «Pensa Verde, vivi meglio»
- «Gamma TerraAmica»
- «BioSorriso: buono per te, buono per il pianeta»
- «Collezione Respiro Verde»
- «Linea Zero Pensieri per l'ambiente»

**`risk_reduction`** — use per-entry legal_ref:
- Offset-based entries → `{ ucpd: 'Annex I 4c', codice_consumo: 'Art. 23' }`
  - «Carbon neutral grazie alla compensazione delle emissioni»
  - «Emissioni compensate al 100%»
  - «Impatto climatico zero»
- Future or improvement entries → `{ ucpd: 'Art. 6(2)(d)', codice_consumo: 'Art. 21' }`
  - «A ridotto impatto ambientale»
  - «-30% di emissioni di CO₂ rispetto al 2020»
  - «Riduce il consumo d'acqua del 40%»
  - «Neutrali per il clima entro il 2030»
  - «Meno plastica, meno impatto»

**`PRE`:**
- `Da sempre crediamo che`
- `Per questo motivo`
- `La nostra nuova gamma offre:`
- `Scopri di più:`
- `Nel 2025 abbiamo introdotto`
- `Come dichiarato nel nostro report,`

**`POST`:**
- `per un futuro migliore.`
- `in tutti i nostri punti vendita.`
- `Scopri i dettagli nella pagina dedicata.`
- `perché il pianeta ci sta a cuore.`
- `su tutta la gamma.`
- `(vedi note).`

All of these are synthetic, and their `legal_ref` values are indicative only, consistent with the methodology.

---

## 10. Tests

### 10.1 Unit tests (Vitest)

Configure in `vite.config.ts` with `test: { environment: 'jsdom', setupFiles: ['src/test-setup.ts'], include: ['src/**/*.test.{ts,tsx}', 'scripts/**/*.test.ts'] }`.

- `crypto.test.ts` runs with `// @vitest-environment node` and `iterations: 1000`.
- The fixture test runs with `// @vitest-environment node`.

| file | cases |
|---|---|
| `schema.test.ts` | Valid fixture passes. Each of the 8 cross-checks produces an issue with the right path. Bad enums or URLs are rejected. Unknown extra keys are stripped. |
| `crypto.test.ts` | Round trip. Wrong passcode throws `WrongPasscodeError`. Tampered ciphertext throws. NFC and NFD forms of the same passcode both decrypt. Salt and IV differ between two encryptions. The output passes `EncFileSchema`. |
| `claimId.test.ts` | The 5 test vectors in §4.3. |
| `derive.test.ts` | `getLatestCrawl` skips failed crawls (F006 shape), returns null when all failed, and accepts partial. Present/removed. `lastSeen` with reappearance. Counts and highest confidence (including null). Strip sort order. Timeline: nulls at failed crawls, filter application, split counts. Breakdown: ignores the category filter, includes all categories, counts present only. |
| `filters.test.ts` | Parse/write round trip. Unknown values dropped. Full set ↔ null. Canonical order. `claim` param preserved. |
| `format.test.ts` | `formatDate` for Sep (`Sep`, not `Sept`) and for a time near midnight UTC. `hostname`. `legalRefLabel` (both, one and no nulls). `categoryLabel` fallback. `cleanMethodology` against the real METHODOLOGY.md: no `TODO`, no `<!--`, `**Firms:**` bullet gone, the tables still there. |
| `breakdownToggle.test.ts` | The 5 rows of the D15 table (put the logic in `filters.ts` as `toggleCategory`). |
| `noDarkClass.test.ts` | §2.3 grep. |
| `scripts/generate-fixtures.test.ts` | Two runs give byte-identical output, which passes the schema and every coverage assert. |

### 10.2 e2e (Playwright)

- **`playwright.config.ts`:**
  - Chromium only, `baseURL: 'http://localhost:4173/websites-dashboard/'`.
  - `webServer: { command: 'npm run build && npm run preview -- --port 4173 --strictPort', url: 'http://localhost:4173/websites-dashboard/', reuseExistingServer: !process.env.CI }`.
  - `globalSetup: './e2e/global-setup.ts'`.
- **`global-setup.ts`:** generate fixtures to `e2e/.tmp/firms.json`, then encrypt with `TEST_PASSCODE = 'correct horse battery staple e2e'` to `e2e/.tmp/firms.enc` using the library functions directly, not the CLI.
- **`helpers.ts`:**
  - Every test does `page.route('**/data/firms.enc', r => r.fulfill({ path: 'e2e/.tmp/firms.enc', contentType: 'application/json' }))`.
  - `unlock(page)` fills the passcode and clicks Unlock.
  - `loadFixture()` reads the JSON so tests can pick claim IDs.
- **Specs.** Use `data-testid` and roles. Never depend on PRNG-specific text except through `loadFixture()`.
  1. **gate:**
     - The gate shows on `#/`.
     - A wrong passcode shows "Incorrect passcode".
     - The right passcode shows 15 `firm-row` elements and "Showing 1–15 of 40 firms".
     - After a reload there is no gate.
     - Lock brings the gate back.
  2. **deep link:** in a fresh context, go to `#/firm/F001?claim=<id>`, unlock, and check that the drawer is visible with the claim text and the URL is unchanged.
  3. **home:**
     - Searching `F00` gives 9 rows.
     - Searching part of F002's name gives that row.
     - Page 3 has 10 rows.
     - A nonsense search shows the empty state.
     - Clicking a row goes to the firm, and "← All firms" restores the search.
  4. **firm filters:**
     - On F001, click High. The URL contains `conf=high`, and every visible card's badge is "High".
     - Clear filters removes the params.
     - Clicking a breakdown bar adds `cat=`.
  5. **drawer:**
     - Clicking a card puts `claim=` in the URL and opens the drawer.
     - `page.goBack()` closes it.
     - The drawer shows "Crawl history".
     - On F012, it shows "Not yet mapped".
  6. **edge firms:**
     - F004 shows "No claims detected on this site yet."
     - F002 shows "Only one crawl so far".
     - F006 shows "(failed)" and "latest successful crawl".
     - F011 shows "No successful crawl yet".
     - F007 shows the partial note.
  7. **responsive** at 375×800:
     - The home table has no "Website" column header.
     - On the firm page, the drawer has `data-side="bottom"`, or check its bounding box sits at the bottom.
     - At 1280×800 it's on the right.
  8. **misc:**
     - `#/methodology` shows a `table` and the page text doesn't contain "TODO".
     - `#/firm/NOPE` and `#/whatever` show "Not found".
     - `emulateMedia({ colorScheme: 'dark' })` gives `body` a dark background (luminance check below 0.2).

---

## 11. Deployment

### 11.1 `vite.config.ts`

Set `base: '/websites-dashboard/'`.

### 11.2 `.github/workflows/deploy.yml`

Use the current major versions of the actions.

```yaml
name: Test and deploy
on:
  push: { branches: [main] }
  pull_request:
  workflow_dispatch:
permissions: { contents: read, pages: write, id-token: write }
concurrency: { group: pages, cancel-in-progress: false }
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version-file: .nvmrc, cache: npm }
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck
      - run: npm test
      - run: npx playwright install --with-deps chromium
      - run: npm run test:e2e
      - if: failure()
        uses: actions/upload-artifact@v4
        with: { name: playwright-report, path: playwright-report }
  deploy:
    if: github.ref == 'refs/heads/main' && github.event_name != 'pull_request'
    needs: test
    runs-on: ubuntu-latest
    environment: { name: github-pages, url: '${{ steps.deployment.outputs.page_url }}' }
    steps:
      - uses: actions/checkout@v4
      - run: test -f public/data/firms.enc || (echo "public/data/firms.enc missing — run npm run encrypt" && exit 1)
      - uses: actions/setup-node@v4
        with: { node-version-file: .nvmrc, cache: npm }
      - run: npm ci
      - run: npm run build
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with: { path: dist }
      - id: deployment
        uses: actions/deploy-pages@v4
```

---

## 12. Phases

Every phase ends with lint, typecheck and tests green, plus one commit.

### Phase 0: Repo initialization
- `git init -b main`.
- Write `.gitignore` (§3.1) **before** any `git add`.
- Run `git status` and confirm the CSV isn't listed.

**Accept:** `git status --ignored` shows `ORBIS_Italia_allsectors.csv` as ignored.

### Phase 1: Scaffold
- Do §2.1–2.5.
- Move `METHODOLOGY.md` to `src/content/METHODOLOGY.md` with `git mv` after the first commit, or a plain move before it.
- Update `PLAN.md` (§1, end).
- Create `HashRouter` with four stub pages, and an `AppShell` with the header and footer.
- Add scripts, `.nvmrc` and engines.
- Add Vitest with one trivial test.

**Accept:**
- `npm run dev` serves `/websites-dashboard/#/`, and the stubs route.
- Dark mode follows the OS.
- `npm run build` passes.

### Phase 2: Library
- `schema.ts`, `types.ts`, `crypto.ts`, `claimId.ts`, `derive.ts`, `filters.ts`, `format.ts`, `categories.ts`, `methodology.ts`, each with the tests from §10.1. Leave the fixture test for Phase 3.
- Build hand-written mini fixtures in the tests for the F006, F008 and F011 shapes.

**Accept:** all unit tests pass, and coverage of `src/lib` is at least 90% lines (`vitest --coverage`, informational).

### Phase 3: Fixtures
- `prng.ts`, `pools.ts`, `generate-fixtures.ts` and its determinism test.
- Run `npm run fixtures`.

**Accept:**
- `data/firms.json` exists, is git-ignored, and passes all asserts.
- Running it again produces an identical file (compare the sha256 of both runs).

### Phase 4: Encryption and gate
- `scripts/encrypt.ts`, `DataProvider`, `PasscodeGate`, `DataErrorScreen`, and the Lock button.
- For local dev only, run `DASHBOARD_PASSCODE='local dev only passphrase here' npm run encrypt`.
  - **Don't commit** this `public/data/firms.enc`. Run `git restore --staged` if needed.
  - Optionally add `public/data/firms.enc` to `.git/info/exclude` until Phase 10, and remove it from there in Phase 10.
- Add Playwright with `global-setup`, `helpers` and `gate.spec.ts`.

**Accept:**
- The gate works.
- A wrong passcode shows the error.
- A reload skips the gate.
- Corrupting a field in `data/firms.json` and re-encrypting (with `--allow-weak` if needed) shows the validation screen with the path.
- `gate.spec.ts` passes.

### Phase 5: Home
- `FirmTable`, search, pagination, URL state and responsive columns.
- `home.spec.ts`.

**Accept:** the spec passes, and the page looks right at 375px and 1280px.

### Phase 6: Firm page
Build in this order, checking each in the browser before moving on:
1. `FirmHeader` + `ConfidenceCounters`
2. `useFirmFilters` + `FilterBar`
3. `ClaimStrip` + `ClaimCard`
4. `ClaimDrawer`
5. `Timeline`
6. `CategoryBreakdown`

Then add `firm.spec.ts`, `drawer.spec.ts` and the edge-firm checks.

**Accept:** all those specs pass, and F001, F003, F004, F005, F006, F007, F008, F011 and F012 all look correct.

### Phase 7: Methodology and Not found
Build both pages, then add `misc.spec.ts` (minus the dark-mode check if it's done in Phase 8).

**Accept:** the spec passes.

### Phase 8: Responsive and dark-mode pass
- Check 375, 768 and 1280px in light and dark.
- Check that no part of any page scrolls horizontally except the claim strip.
- Check that the drawer switches side at 700px.
- Check that chart text is legible in dark mode.
- Add `responsive.spec.ts` and the dark-mode check.

**Accept:** all e2e tests pass. Save screenshots of every page at 375 and 1280, light and dark, to `test-results/screens/` (not committed) for the owner to review.

### Phase 9: CI and README
- Add the workflow from §11.2.
- Write `README.md`, covering:
  - What the dashboard is
  - The local dev commands
  - The data workflow: put data in `data/firms.json`, run `npm run encrypt`, commit `public/data/firms.enc`, push
  - The passphrase guidance (four or more random words)
  - The data contract (link to PLAN.md §2 and the claim-ID rule in this file, Appendix A)
  - Deployment settings

**Accept:** `act` isn't required. Check the YAML by reading it, and all local commands pass.

### Phase 10: **STOP**. Owner actions, then deploy

Claude Code must stop and ask the owner to:

1. Run `npm run fixtures && npm run encrypt` **in their own terminal** with the real demo passphrase (four or more random words). Claude Code never chooses, sees or stores the production passphrase.
2. Confirm before Claude Code creates the GitHub repo. Then:
   - Run `gh repo create websites-dashboard --public --source . --remote origin`.
   - Enable Pages for Actions with `gh api -X POST repos/{owner}/websites-dashboard/pages -f build_type=workflow`. If Pages already exists, use `-X PUT`.
   - Commit `public/data/firms.enc` (removing it from `.git/info/exclude` if it was added there).
   - Run `git push -u origin main`.
3. Before pushing, double-check `git ls-files` shows no CSV, no `data/` and no `e2e/.tmp`.

**Accept:**
- The workflow is green.
- The live URL (`https://<owner>.github.io/websites-dashboard/`) shows the gate.
- In a private window, a deep link `…/#/firm/F001?claim=<id>` opens the gate, then the drawer after unlocking.
- The browser's network tab shows only `firms.enc` and no plaintext JSON.

---

## 13. Definition of done

- [ ] Every PLAN.md v1 scope item works, with the deviations in §1.
- [ ] `npm run lint`, `typecheck`, `test` and `test:e2e` pass locally and in CI.
- [ ] The fixtures are deterministic and cover all the edge cases.
- [ ] No plaintext data, CSV or passcode is in git history (`git log --all --stat | grep -E 'csv|data/'` returns nothing).
- [ ] The live site works through a deep link in a fresh session.
- [ ] Confidence is never labelled as risk or severity anywhere in the UI.
- [ ] Claim text is shown verbatim in Italian, with `lang="it"`.

---

## Appendix A: Claim ID in Python (for the scraping pipeline)

```python
import hashlib, unicodedata

def normalize_claim_text(text: str) -> str:
    s = unicodedata.normalize("NFKC", text).lower()
    s = "".join(ch for ch in s if not unicodedata.category(ch).startswith(("P", "S")))
    return " ".join(s.split())

def claim_id(firm_id: str, text: str) -> str:
    return f"{firm_id}-{hashlib.sha256(normalize_claim_text(text).encode('utf-8')).hexdigest()[:6]}"
```

This gives the same output as `claimId.ts` on the §4.3 vectors. With 6 hex characters, a collision inside one firm is unlikely but possible, so the pipeline must assert uniqueness per firm. If two different texts collide, it should extend that firm's IDs to 8 characters.

## Implementation notes

<!-- Claude Code: record any decision you had to make that this file didn't cover. -->
