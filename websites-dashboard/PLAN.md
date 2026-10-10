# Firm Claims Dashboard: Plan

A static, passcode-protected dashboard that shows environmental claims scraped from firm websites, one firm at a time. It is built with Vite + React + shadcn/ui and deployed to GitHub Pages as a clickable demo.

Status: agreed design (grilling session, 2026-10-10), updated the same day with the implementation decisions. Nothing here is implemented yet.

Implementation details and later decisions: see IMPLEMENTATION_PLAN.md. If the two disagree, IMPLEMENTATION_PLAN.md wins.

---

## 1. Scope

**In v1**
- A home page with a paginated, searchable firm table.
- One page per firm, with a header, a filter bar, a claim strip, a claim drawer, a timeline and a category breakdown.
- A methodology page.
- Passcode gate, with the data file encrypted in the repo.
- Synthetic demo data that follows the agreed schema, using fictional firms only.
- Responsive layout, with dark mode that follows the system setting.
- Unit tests (Vitest) and end-to-end tests (Playwright), both run in CI before every deploy.

**Not in v1:** see [Future work](#9-future-work).

---

## 2. Data contract

The scraping pipeline produces **one JSON file**. The dashboard derives everything else (counts, timelines, breakdowns) client-side.

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-10-10T14:00:00Z",
  "categories": ["generic_green", "certification", "recycled_recyclable", "vague_supply_chain", "named_endorsement", "brand_eco_slogan", "risk_reduction"],
  "firms": [
    {
      "firm_id": "F017",
      "firm_name": "Example S.p.A.",
      "website": "https://www.example.it",
      "crawls": [
        { "crawl_id": "F017-C01", "crawled_at": "2026-10-05T09:12:00Z", "pages_scraped": 42, "status": "ok" },
        { "crawl_id": "F017-C02", "crawled_at": "2026-10-12T09:10:00Z", "pages_scraped": 45, "status": "ok" }
      ],
      "claims": [
        {
          "claim_id": "F017-7f3a9c",
          "text": "Packaging 100% sostenibile",
          "context_snippet": "…la nostra linea usa packaging 100% sostenibile per ridurre…",
          "source_url": "https://www.example.it/sostenibilita",
          "category": "generic_green",
          "scope_status": "IN_SCOPE",
          "confidence": "high",
          "gray_zone": null,
          "legal_ref": { "ucpd": "Annex I 4a", "codice_consumo": "Art. 23" },
          "seen_in_crawls": ["F017-C01", "F017-C02"]
        }
      ]
    }
  ]
}
```

### Field rules

| field | type | rule |
|---|---|---|
| `firm_id` | string | Unique. Used in the URL and as the sort key on the home page. |
| `crawls[].crawled_at` | ISO 8601 | One crawl per firm per week. The timeline x-axis uses these dates. |
| `crawls[].status` | `ok` \| `partial` \| `failed` | Failed crawls still appear on the timeline (with a marker and a gap in the line) so a drop to 0 isn't misread. A failed crawl never decides whether a claim is present or removed, and no claim may list a failed crawl in `seen_in_crawls`. |
| `claim_id` | string | `firm_id` + `-` + the first 6 hex characters of the SHA-256 of the **normalized text**. Normalization: Unicode NFKC, lowercase, strip all Unicode punctuation and symbols (categories P\* and S\*), collapse whitespace, trim. The URL is **not** part of the hash, so a claim that moves pages keeps its ID. A reworded claim counts as a new claim. The pipeline must use the exact function in IMPLEMENTATION_PLAN.md (Appendix A) and check that IDs are unique within each firm. The app treats IDs as opaque. |
| `category` | string | Must be one of `categories`. Uses the gold-set trigger taxonomy. |
| `scope_status` | `IN_SCOPE` \| `NEEDS_VERIFICATION` | DISCARDED and out_of_scope claims are dropped in the pipeline and never reach this file. |
| `confidence` | `high` \| `medium` \| `low` | The detector's confidence. It is **not** a legal-severity rating, and the UI never labels it as risk. |
| `gray_zone` | string \| null | For example `natural_footnote` or `generic_plus_specific`. Shown in the drawer only. |
| `legal_ref` | object | Both EU and Italian numbering. Either value may be `null` until the mapping exists. |
| `seen_in_crawls` | string[] | The crawl IDs the claim was found in. This drives the timeline and the "removed" state. |

**`categories` list:** sync this with the gold-set label schema before the real data lands. The list above holds the triggers named in the gold-set decisions doc. Website copy may need extra triggers (for example environmental comparison claims), which would be added here and in the methodology page.

### Derived values (computed in the app)

- **Latest crawl:** the firm's most recent crawl whose status is `ok` or `partial`. Failed crawls are skipped. If every crawl failed, there is no latest crawl and the firm page says "No successful crawl yet".
- **Last crawled:** the newest crawl of **any** status. If it isn't `ok`, its status is shown next to the date, for example `2 Nov 2026 (failed)`.
- **Present claim:** the latest crawl's ID is in `seen_in_crawls`. **Removed claim:** it is not. A removed claim's "last seen" date is the `crawled_at` of the latest crawl in its `seen_in_crawls`.
- **H/M/L counters:** present claims grouped by confidence. They are unfiltered.
- **Header color:** the highest confidence among present claims, on a four-step scale: high → red, medium → orange, low → yellow, none → white. The same colors are used for the H/M/L counters, confidence badges and breakdown stacks. Wherever confidence appears, it is labelled "confidence" with the tooltip *"Detector confidence, not legal severity"*.

Validate the file at load with a **zod** schema. If validation fails, show an error screen that lists the issues instead of rendering partial data. The same validator will serve the future upload feature.

---

## 3. Access: passcode and encryption

Only ciphertext is ever committed. The repo is public, so a JS-only passcode check would hide nothing.

**Workflow**
1. Generate or receive `data/firms.json`. This file is **gitignored**.
2. Run `npm run encrypt`. It prompts for the passcode and writes `public/data/firms.enc`.
3. Commit `firms.enc` and push. The push triggers the deploy.

**Crypto (Web Crypto API, same parameters in the Node script and the browser)**
- Key derivation: PBKDF2-SHA256, 600,000 iterations, 16-byte random salt.
- Cipher: AES-GCM-256, 12-byte random IV.
- `firms.enc` format: `{ "v": 1, "kdf": "PBKDF2-SHA256", "iterations": 600000, "salt": "<b64>", "iv": "<b64>", "ciphertext": "<b64>" }`.
- A wrong passcode makes GCM authentication fail, and the UI shows "Incorrect passcode".

**Browser behavior**
- On first visit to any route, the passcode screen appears. On success, the decrypted data is held in memory and the passcode in `sessionStorage`, so it's asked once per browser session.
- Deep links (`#/firm/F017?claim=…`) survive the gate. The gate is rendered in place of the page and the URL never changes, so the requested route appears as soon as the data is unlocked.
- A "Lock" button in the header clears the decrypted data and the stored passcode and shows the gate again.
- To change the passcode, re-run `npm run encrypt` and push.

Since the encrypted file is public, anyone can try to guess the passcode offline. **Use a long passphrase** of four or more random words, not a short password.

---

## 4. Routes

Hash routing (`react-router` `HashRouter`), so GitHub Pages serves every deep link without the 404 workaround.

| route | page |
|---|---|
| `#/` | Home: firm table |
| `#/firm/:firmId` | Firm page |
| `#/firm/:firmId?claim=:claimId` | Firm page with the claim drawer open |
| `#/methodology` | Methodology |
| anything else, or an unknown `firmId` | "Not found" page with a link to `#/` |

Filters are also stored in the query string (`?cat=generic_green,certification&conf=high&scope=IN_SCOPE`), so a shared link reproduces the exact view.

- A missing parameter means "all". A selection equal to the full set removes the parameter. Values are written in a fixed order.
- Filter changes replace the current history entry. Opening the claim drawer adds one, so the browser's Back button closes it.
- The home page keeps its search and page in the URL too (`#/?q=verde&page=2`), and the firm page's "← All firms" link returns to it.

---

## 5. Pages

### 5.1 Home (`#/`)

- A **search** input that does a case-insensitive substring match on `firm_id` **or** `firm_name` and resets to page 1.
- A **table** with 15 rows per page, sorted by `firm_id` ascending. Columns:
  - Firm ID
  - Firm name
  - Website (linked, opens in a new tab)
  - Claims in the latest crawl
  - H / M / L counters
  - Number of crawls
  - Last crawled date (with the status if the newest crawl wasn't `ok`)
- Clicking a row goes to `#/firm/:firmId`.
- **Pagination** below the table, with an empty state when nothing matches the search.
- A header link to Methodology, and a footer disclaimer on every page (including the passcode screen): *"Research prototype. Automated detection, not a legal assessment."*

### 5.2 Firm page (`#/firm/:firmId`)

Top to bottom:

1. **Header.** Firm ID, firm name, and website link. A "Detection confidence" block shows the H/M/L counters, with the accent color (white / yellow / orange / red) set by the highest confidence present. Underneath: last crawled date (with its status if not `ok`) and number of crawls. Extra notes appear when they apply:
   - the latest successful crawl is older than the newest crawl: "Claims as of <date> (latest successful crawl)."
   - the latest crawl was `partial`: "Latest crawl was partial (n pages). Some claims may be missing."
   - no crawl has succeeded: "No successful crawl yet."
2. **Filter bar.** One shared bar that drives sections 3–5:
   - Category: multi-select, defaults to all.
   - Confidence: multi-select H/M/L, defaults to all.
   - Scope status: IN_SCOPE / NEEDS_VERIFICATION, defaults to both.
   - "Clear filters" button.
3. **Claim strip.** A horizontal scroll area of fixed-width cards.
   - It shows **all claims ever seen** that pass the filters.
   - Sort order: present before removed, then confidence high → low, then category A–Z.
   - Each card shows the text clamped to 3 lines, a category chip and a confidence badge. NEEDS_VERIFICATION claims get a dashed border plus a small "Needs verification" label. Removed claims are greyed out and labelled "Removed · last seen <date>".
   - The header shows a count, for example "24 claims (19 present, 5 removed)".
   - Clicking a card opens the drawer.
   - Empty states: "No claims detected on this site yet." for a firm with no claims, and "No claims match these filters." (with a Clear filters button) otherwise.
4. **Timeline.** A line chart with one point per crawl date. Each point counts the claims that pass the filters and are in that crawl's `seen_in_crawls`.
   - A firm with **one crawl** shows a single dot plus the note "Only one crawl so far".
   - Failed crawls are marked with a dashed vertical line and leave a gap in the line rather than being plotted as 0. Partial crawls get a hollow dot.
   - A **"Split by category"** toggle switches from one total line to one line per selected category plus the total. Categories with no claims at any crawl get no line. The toggle is local to the page and isn't stored in the URL.
5. **Category breakdown.** Horizontal bars stacked by confidence, one bar per category, for **present claims in the latest crawl**.
   - It applies the confidence and scope filters but **ignores the category filter**, otherwise selecting a category would collapse it to one bar. Selected categories are highlighted instead.
   - Clicking a bar toggles that category in the filter. From "all", clicking a category selects only that category. Clicking the only selected category goes back to "all". Otherwise the clicked category is added or removed.
   - Every category in the data file gets a row, even with zero claims.

**Claim drawer** (a shadcn `Sheet`):
- It opens on the right on desktop and as a bottom sheet below about 700px.
- Its state is in the URL (`?claim=`), so the link is shareable and the browser back button closes it.
- Contents:
  - Full claim text
  - Context snippet, with the claim highlighted
  - Source URL link
  - Category, confidence and scope status
  - Gray zone, if any
  - Legal reference shown as "UCPD … / Cod. Cons. …"
  - Crawl history: every crawl of the firm marked as seen, not seen or failed, plus first-seen and last-seen dates
- Claim text and the snippet are marked `lang="it"`. The highlight is found by a case-insensitive text match. If there's no match, the snippet is shown without a highlight.

### 5.3 Methodology (`#/methodology`)

This page renders `src/content/METHODOLOGY.md` (moved from the repo root) with `react-markdown` and `remark-gfm` for the tables. HTML comments (the TODO placeholders) are stripped before rendering, and a bullet left with only a bold label is removed.

### 5.4 Language and text

- The UI is in English.
- Claim text and snippets stay in the original Italian and are never machine-translated, because the exact wording is the evidence.
- Dates are shown as `12 Oct 2026`, in UTC, using a fixed month list (so September is always `Sep`).

---

## 6. Tech stack

| concern | choice |
|---|---|
| Build | Vite + React + TypeScript |
| UI | shadcn/ui on Tailwind: Table, Input, Pagination, Card, Badge, ScrollArea, Sheet, Select or ToggleGroup, Button |
| Charts | shadcn Chart (Recharts) for the line and stacked bar charts |
| Routing | react-router, `HashRouter` |
| Validation | zod |
| Markdown | react-markdown |
| Dark mode | Follows the system setting with no toggle. Tailwind v4: `@custom-variant dark (@media (prefers-color-scheme: dark));` with the shadcn dark variables under the same media query. No `.dark` class. |
| Crypto | Web Crypto API (`globalThis.crypto.subtle`), with one shared module used by both the browser and the script |
| Tests | Vitest (with jsdom) for `src/lib` and scripts; Playwright (Chromium) for end-to-end flows |

Responsive breakpoints:
- **Below 700px:** the home table shows only ID, claims and H/M/L (firm name, website, crawls and last crawled are hidden), and the remaining columns move to the firm page. The claim strip stays horizontal. The drawer becomes a bottom sheet. Charts take the full width and stack vertically.
- **700px and above:** the drawer opens on the right.
- **1024px and above:** the timeline and category breakdown sit side by side. Between 700px and 1024px they are stacked.

---

## 7. Demo data

- `scripts/generate-fixtures.ts` uses a **fixed seed** (`20261005`) so the output is byte-for-byte reproducible. It is run once, and the result is the hardcoded demo dataset. `generated_at` is fixed at `2026-11-02T14:00:00Z`.
- It follows the schema in section 2 exactly and must pass the zod validator.
- Contents:
  - Exactly 40 firms (`F001`–`F040`), which gives 3 pages on the home table.
  - **Fictional** firm names (e.g. `Verdeluce S.r.l.`) and websites on the reserved `.example` domain (e.g. `https://www.verdeluce.example`). Real firms from the ORBIS list are never used, so no real company is shown with invented claims.
  - 1–5 weekly crawls per firm, starting 5 Oct 2026.
  - All categories represented, with both scope statuses and all confidence levels.
  - Realistic Italian claim text. Endorsements and brand lines use invented organisation names.
- **Required edge cases:**
  - One firm with a single crawl (single-dot timeline).
  - One firm whose **newest** crawl failed, and one firm whose crawls all failed.
  - One firm whose latest crawl was `partial`.
  - Firms whose claims are all low or all medium (yellow and orange headers).
  - One firm with 30+ claims (long strip).
  - One firm with no claims (empty states).
  - Several claims removed between crawls.
  - A claim that reappears after an absence.
  - One `failed` crawl in the middle of a firm's history.
  - Claims with `gray_zone` and with `null` legal references.
- The demo data goes through `npm run encrypt` like real data does, so the passcode gate is tested end to end. Swapping in real data later means replacing `data/firms.json`, re-encrypting and pushing.

---

## 8. Repo layout and deployment

```
.
├── .github/workflows/deploy.yml   # build + deploy to Pages on push to main
├── data/firms.json                # plaintext, gitignored
├── e2e/                           # Playwright specs
├── public/data/firms.enc          # ciphertext, committed
├── scripts/
│   ├── encrypt.ts                 # npm run encrypt
│   └── generate-fixtures.ts       # npm run fixtures
├── src/
│   ├── components/ui/             # shadcn components
│   ├── components/                # FirmTable, ClaimStrip, ClaimCard, ClaimDrawer, Timeline, CategoryBreakdown, FilterBar, PasscodeGate
│   ├── content/METHODOLOGY.md
│   ├── lib/                       # schema.ts (zod), crypto.ts, derive.ts (counts, present/removed, series)
│   ├── pages/                     # Home, Firm, Methodology, NotFound
│   └── main.tsx
├── IMPLEMENTATION_PLAN.md
├── PLAN.md
├── playwright.config.ts
└── vite.config.ts                 # base: "/websites-dashboard/"
```

**Deployment**
- The repo is `websites-dashboard` (public, so GitHub Pages is free), with the existing `websites-dashboard` folder as its root. `ORBIS_Italia_allsectors.csv` (210 MB) is gitignored and never committed.
- In `vite.config.ts`, set `base` to `/websites-dashboard/`.
- The workflow first runs lint, typecheck, unit tests and Playwright tests. On `main` it then runs `npm ci && npm run build` and publishes `dist/` with `actions/upload-pages-artifact` and `actions/deploy-pages`. It fails if `public/data/firms.enc` is missing.
- A lint check fails if any file under `data/` or any `.csv` file is tracked by git.
- Under the repo's Settings → Pages, set the source to GitHub Actions.

---

## 9. Future work

- **Data upload.** Load a JSON file in the browser after unlocking, replacing the bundled data for the session. A banner would say "Viewing uploaded file: X — reset to default". Uses the same zod validation, with field-level error messages. JSON only.
- **Human-review status.** A per-claim `review` object (`status`: unreviewed / confirmed / rejected, plus reviewer, date and note), a "Reviewed n/m" counter on each firm, and possibly in-browser editing with an "Export reviewed JSON" button.
- **PDF export** of the current firm view.

---

## 10. Build order

1. Scaffold Vite + React + TS, Tailwind and shadcn. Add `HashRouter` and the routes as stubs.
2. Write the zod schema and `derive.ts`, with unit tests for the present/removed logic (including skipped failed crawls), counters and timeline series.
3. Write the fixture generator and produce the demo data.
4. Write the encryption script and `PasscodeGate`.
5. Build the home page (table, search, pagination).
6. Build the firm page: header, then filter bar with URL sync, then strip, then drawer, then timeline, then breakdown.
7. Add the methodology page and the not-found page.
8. Do a responsive pass at 375px, 768px and 1280px, and a dark-mode check.
9. Set up the deploy workflow and smoke-test the live URL, including opening a deep link in a fresh browser session. Before the first push, the owner runs `npm run encrypt` with the real passphrase and approves creating the GitHub repo.

Playwright tests are added alongside steps 4–8. The detailed phases are in IMPLEMENTATION_PLAN.md.
