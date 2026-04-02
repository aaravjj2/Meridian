# Meridian — Tasks

This file is the authoritative task list for building Meridian end-to-end.
Each milestone has a clear acceptance gate. A milestone is **REJECTED** if its
proof pack is missing or any gate condition is unmet. No milestone may be
marked complete by claim alone.

Proof packs live at: `artifacts/proof/<ISO-timestamp>-<milestone-slug>/`

---

## Milestone 0 — Repo Bootstrap

**Gate:** `npm run tsc` exits 0. `pytest -q` exits 0 (zero tests, zero errors).
`GET /api/v1/health` returns `{"status":"ok"}`.

### Repo structure
- [ ] `git init` meridian monorepo
- [ ] create `apps/api/`, `apps/web/`, `src/meridian/`, `tests/`, `data/fixtures/`,
      `artifacts/proof/`, `docs/`, `scripts/`
- [ ] add `pyproject.toml` with Python 3.12, dev dependencies
      (`fastapi`, `uvicorn`, `httpx`, `pytest`, `pydantic`, `duckdb`, `chromadb`,
      `python-dotenv`, `structlog`)
- [ ] add `package.json` workspace root with scripts:
      `tsc`, `vitest`, `playwright`, `dev`
- [ ] add `apps/web/package.json` (Next.js 15, TypeScript, Tailwind, shadcn/ui,
      framer-motion, recharts, eventsource-parser)
- [ ] add `.env.example` documenting all secrets (none required for demo mode)
- [ ] add `.gitignore` covering `.env`, `__pycache__`, `.next`, `node_modules`,
      `*.parquet`, `chroma_db/`
- [ ] add `CONTRIBUTING.md` with setup, dev loop, and test gate instructions
- [ ] add `README.md` skeleton (filled in Milestone 9)

### CI
- [ ] add `.github/workflows/ci.yml` running tsc + vitest + pytest on push
- [ ] configure Playwright in CI with `--reporter=list`

### Bootstrap health check
- [ ] `apps/api/main.py` — bare FastAPI app, `GET /api/v1/health` → `{"status":"ok","mode":"demo"}`
- [ ] `apps/api/main.py` — `GET /api/v1/metadata` → `{"version":"0.1.0","model":"glm-5.1","demo":true}`
- [ ] smoke pytest: `tests/unit/api/test_health.py` — assert 200, assert body

---

## Milestone 1 — Data Ingestion

**Gate:** All ingestion adapters return valid typed data in demo mode.
`pytest tests/unit/ingestion/ -q` → failed=0. Fixtures committed under
`data/fixtures/`.

### FRED adapter (`src/meridian/ingestion/fred.py`)
- [ ] `FredClient.fetch_series(series_id, start, end)` → `pd.DataFrame`
- [ ] `FredClient.search(query, limit)` → `list[FredSeriesMeta]`
- [ ] cache raw responses to `data/cache/fred/` with TTL metadata JSON sidecar
- [ ] demo mode: load from `data/fixtures/fred/{series_id}.json` — no network call
- [ ] fixture snapshots committed for: `T10Y2Y`, `UNRATE`, `CPIAUCSL`,
      `FEDFUNDS`, `GDPC1`, `BAMLH0A0HYM2`, `MORTGAGE30US`, `M2SL`
- [ ] unit tests: fetch returns DataFrame with `date` + `value` columns,
      demo mode bypasses network, cache hit skips fetch

### Kalshi adapter (`src/meridian/ingestion/kalshi.py`)
- [ ] `KalshiClient.get_markets(category)` → `list[RawMarket]`
- [ ] `KalshiClient.get_market(ticker)` → `RawMarket`
- [ ] `KalshiClient.get_history(ticker)` → `list[PricePoint]`
- [ ] demo mode: load from `data/fixtures/kalshi/`
- [ ] fixture snapshots: 5+ active macro contracts covering Fed rate,
      inflation, unemployment, recession
- [ ] unit tests: schema validation, demo mode path, no-auth requirement verified

### Polymarket adapter (`src/meridian/ingestion/polymarket.py`)
- [ ] `PolymarketClient.get_markets(tag)` → `list[RawMarket]`
- [ ] `PolymarketClient.get_market(condition_id)` → `RawMarket`
- [ ] `PolymarketClient.get_history(condition_id)` → `list[PricePoint]`
- [ ] demo mode: load from `data/fixtures/polymarket/`
- [ ] fixture snapshots: 5+ macro contracts
- [ ] unit tests: same pattern as Kalshi

### SEC EDGAR adapter (`src/meridian/ingestion/edgar.py`)
- [ ] `EdgarClient.get_latest_filing(ticker, form_type)` → `EdgarFiling`
- [ ] `EdgarFiling` contains: `ticker`, `form_type`, `filed_date`, `accession_number`,
      `text_chunks: list[str]` (4000-token splits)
- [ ] demo mode: load from `data/fixtures/edgar/{ticker}_{form_type}.json`
- [ ] fixture snapshots: AAPL 10-K summary chunks (5 chunks, truncated for size)
- [ ] unit tests: chunking correctness, fixture load

### News adapter (`src/meridian/ingestion/news.py`)
- [ ] `NewsClient.fetch(topic, days_back)` → `list[NewsArticle]`
- [ ] `NewsArticle`: `title`, `url`, `published_at`, `snippet`, `sentiment_score`
- [ ] sentiment scoring via simple keyword model (no external API required)
- [ ] demo mode: load from `data/fixtures/news/{topic_slug}.json`
- [ ] fixture snapshots: "fed rate decision", "inflation", "recession risk"
- [ ] unit tests: sentiment scorer, fixture load, topic slug normalisation

---

## Milestone 2 — Normalisation and Schema

**Gate:** All raw sources normalise to canonical schema without data loss.
`pytest tests/unit/normalisation/ -q` → failed=0.

### Canonical schemas (`src/meridian/normalisation/schemas.py`)
- [ ] `CanonicalMarket`: `id`, `platform`, `title`, `category`, `resolution_date`,
      `market_probability`, `volume_usd`, `open_interest`, `last_updated`
- [ ] `MacroSeries`: `fred_id`, `name`, `category`, `frequency`, `last_value`,
      `series_data: list[DataPoint]`
- [ ] `ResearchBrief`: `question`, `thesis`, `bull_case`, `bear_case`,
      `key_risks`, `confidence`, `sources`, `created_at`, `trace_steps`
- [ ] `TraceStep`: `step_index`, `type` (tool_call|tool_result|reasoning|brief_delta),
      `tool_name`, `tool_args`, `content`, `timestamp`
- [ ] `MispricingScore`: `market_id`, `market_prob`, `model_prob`, `dislocation`,
      `direction`, `explanation`, `confidence`, `scored_at`

### Normalisation engine (`src/meridian/normalisation/normalise.py`)
- [ ] `normalise_kalshi(raw)` → `CanonicalMarket`
- [ ] `normalise_polymarket(raw)` → `CanonicalMarket`
- [ ] category taxonomy: `fed_policy`, `inflation`, `employment`, `recession`,
      `gdp`, `geopolitical`, `other`
- [ ] auto-assign category from title keywords + manual overrides
- [ ] unit tests: round-trip normalisation, category assignment, field coercion

### Contract-to-FRED mapping (`src/meridian/normalisation/mapping.py`)
- [ ] `ContractMapper.get_relevant_series(market)` → `list[str]` (FRED IDs)
- [ ] mapping table: `fed_policy` → `[FEDFUNDS, T10Y2Y]`,
      `inflation` → `[CPIAUCSL, PCEPI]`,
      `employment` → `[UNRATE, ICSA]`,
      `recession` → `[T10Y2Y, GDPC1, USREC]`, etc.
- [ ] unit tests: every category maps to ≥2 series

---

## Milestone 3 — Feature Engine

**Gate:** Feature pipeline produces deterministic Parquet output from fixtures.
`pytest tests/unit/features/ -q` → failed=0. Snapshot equality check passes.

### Feature computation (`src/meridian/features/compute.py`)
- [ ] `yield_curve_slope(series_df)` — T10Y minus T2Y, current and 3-month delta
- [ ] `recession_signal(series_dict)` — Sahm rule approximation from UNRATE
- [ ] `inflation_momentum(cpi_df)` — 3-month annualised rate of change
- [ ] `credit_stress(spread_df)` — HY spread vs 12-month average z-score
- [ ] `monetary_regime(fedfunds_df)` — classify: accommodative / neutral / restrictive
- [ ] `macro_regime_vector(all_series)` → `dict[str, str]` — 5-dimension regime
- [ ] all functions accept DataFrames, return typed dicts

### Feature export (`src/meridian/features/export.py`)
- [ ] `export_feature_snapshot(output_dir)` — write `features.parquet` + `features.json`
- [ ] snapshot equality test: re-run on same fixtures produces byte-identical Parquet
- [ ] `features.json` schema documented in `docs/schema.md`

---

## Milestone 4 — GLM-5.1 Agent Core

**Gate:** Agent loop completes a demo research question end-to-end from fixtures.
`pytest tests/unit/agent/ -q` → failed=0.
`POST /api/v1/research` with demo question returns streaming response with ≥5 trace steps.

### Tool registry (`src/meridian/agent/tools.py`)
- [ ] `fred_fetch(series_id, start_date, end_date)` — calls FRED adapter, returns JSON
- [ ] `fred_search(query)` — semantic search over FRED catalog metadata
- [ ] `prediction_market_fetch(platform, event_slug)` — fetches contract from Kalshi/Polymarket
- [ ] `edgar_fetch(ticker, form_type)` — fetches filing chunks
- [ ] `news_fetch(topic, days_back)` — fetches news with sentiment
- [ ] `vector_search(query, top_k)` — ChromaDB semantic retrieval
- [ ] `compute_feature(series_id, feature_name)` — runs feature function on fetched series
- [ ] each tool: typed Pydantic input model, JSON-serialisable output, max execution 10s
- [ ] tool registry: `TOOLS: list[ToolDefinition]` — used in GLM system prompt

### ReAct loop (`src/meridian/agent/react.py`)
- [ ] `ResearchAgent.run(question, mode)` → `AsyncGenerator[TraceStep, None]`
- [ ] call GLM-5.1 via Z.ai API with full tool definitions
- [ ] parse tool call from response, execute tool, append result to messages
- [ ] emit `TraceStep` for every tool_call, tool_result, reasoning chunk, brief_delta
- [ ] hard cap: 25 tool calls per session (prevent runaway loops)
- [ ] brief is emitted only after agent emits `BRIEF_COMPLETE` signal in reasoning
- [ ] demo mode: replay pre-recorded trace from `data/fixtures/traces/demo_trace.json`
- [ ] unit tests: tool execution (mocked GLM), trace step sequence, hard cap enforcement

### System prompt (`src/meridian/agent/prompt.py`)
- [ ] `build_system_prompt(tools)` → `str`
- [ ] role section: identity, output schema, citation requirements
- [ ] tool descriptions: name, description, parameters with examples
- [ ] output schema: strict JSON for ResearchBrief
- [ ] constraint section: every claim must cite a tool call result

### Vector store (`src/meridian/vector/store.py`)
- [ ] `VectorStore.upsert(doc_id, text, metadata)` — embed + store in ChromaDB
- [ ] `VectorStore.search(query, top_k)` → `list[SearchResult]`
- [ ] seeded on startup with: FRED series descriptions, MacroFair methodology,
      macro event calendar, Meridian research primer
- [ ] unit tests: upsert + search round-trip, top_k respected, metadata preserved

---

## Milestone 5 — Mispricing Screener

**Gate:** Screener produces ranked dislocation table from fixture data.
`pytest tests/unit/screener/ -q` → failed=0.
`GET /api/v1/screener` returns ≥5 scored contracts.

### Fair-value model (`src/meridian/models/fair_value.py`)
- [ ] `FairValueModel.score(market, macro_series)` → `float` — model probability 0–1
- [ ] baseline: weighted combination of:
      - relevant FRED series normalised signals
      - historical base rate for this contract category
      - macro regime adjustment factor
- [ ] calibration layer: Platt scaling applied on top of raw score
- [ ] uncertainty band: return `(score, lower, upper)` at 80% confidence

### Dislocation scorer (`src/meridian/scoring/score.py`)
- [ ] `score_dislocation(market, model_prob)` → `MispricingScore`
- [ ] dislocation magnitude: `abs(market_prob - model_prob)`
- [ ] direction: `"market_overpriced"` | `"market_underpriced"`
- [ ] confidence: scale 1–5 based on macro signal strength and model uncertainty band
- [ ] GLM explanation: 1-sentence natural-language summary of the gap

### Screener pipeline (`src/meridian/scoring/screener.py`)
- [ ] `run_screener(markets, macro_series)` → `list[MispricingScore]` sorted by magnitude desc
- [ ] filter: only include contracts with resolution within 90 days
- [ ] unit tests: scoring correctness, sort order, direction assignment, confidence range

---

## Milestone 6 — FastAPI Backend

**Gate:** All endpoints return correct schemas. `pytest tests/unit/api/ -q` → failed=0.
OpenAPI docs render at `/docs`.

### Research endpoint (`apps/api/routers/research.py`)
- [ ] `POST /api/v1/research` — body: `{"question": str, "mode": "demo"|"live"}`
- [ ] streams `text/event-stream` SSE with events: `tool_call`, `tool_result`,
      `reasoning`, `brief_delta`, `complete`, `error`
- [ ] each SSE event: `data: <JSON>\n\n`
- [ ] timeout: 120s hard limit, emits `error` event if exceeded
- [ ] demo mode: replays `data/fixtures/traces/demo_trace.json` with 80ms step delay

### Screener endpoint (`apps/api/routers/screener.py`)
- [ ] `GET /api/v1/screener` — query params: `category`, `platform`, `min_dislocation`,
      `limit` (default 20)
- [ ] returns `{"contracts": list[MispricingScore], "scored_at": ISO, "count": int}`
- [ ] demo mode: load from `data/fixtures/screener_snapshot.json`

### Regime endpoint (`apps/api/routers/regime.py`)
- [ ] `GET /api/v1/regime` — returns current 5-dimension macro regime
- [ ] schema: `{"dimensions": {growth, inflation, monetary, credit, labor}, "narrative": str, "updated_at": ISO}`
- [ ] demo mode: load from `data/fixtures/regime_snapshot.json`

### Markets endpoints (`apps/api/routers/markets.py`)
- [ ] `GET /api/v1/markets` — all normalised markets, pagination, filter by category/platform
- [ ] `GET /api/v1/markets/{market_id}` — single market with full history
- [ ] `GET /api/v1/markets/{market_id}/explain` — MispricingScore + GLM explanation
- [ ] demo mode: load from `data/fixtures/markets/`

### API tests (`tests/unit/api/`)
- [ ] `test_health.py` — 200, schema correct
- [ ] `test_research.py` — SSE stream opens, ≥5 events, `complete` event emitted,
      brief JSON valid against ResearchBrief schema
- [ ] `test_screener.py` — 200, ≥5 contracts, sorted by dislocation desc
- [ ] `test_regime.py` — 200, all 5 dimensions present
- [ ] `test_markets.py` — list 200, detail 200, explain 200
- [ ] all tests use demo mode — no network, no secrets required

---

## Milestone 7 — Frontend Terminal UI

**Gate:** `npm run tsc` → 0 errors. `npm run vitest` → failed=0.
All pages render in headless Chromium (verified in Milestone 8 Playwright run).
Every interactive element has `data-testid`.

### Design tokens and theme (`apps/web/styles/`)
- [ ] implement full design token set per `frontend_design.md`
- [ ] CSS custom properties: all colors, spacings, font sizes, border radii
- [ ] dark theme only — Meridian does not have a light mode
- [ ] custom fonts: JetBrains Mono (monospace), Inter (UI)
- [ ] Tailwind config extended with Meridian token names
- [ ] global reset: box-sizing, no default margin, smooth scrolling

### Layout and navigation (`apps/web/components/Layout/`)
- [ ] `TopBar` — wordmark "MERIDIAN", mode badge (DEMO|LIVE), nav links,
      `data-testid="topbar"`, `data-testid="mode-badge"`
- [ ] `StatusBar` — bottom bar: model label, latency, last-updated timestamp,
      `data-testid="status-bar"`
- [ ] `Layout` — wraps all pages, TopBar + children + StatusBar

### Regime Dashboard strip (`apps/web/components/RegimeDashboard/`)
- [ ] 5 colored indicator pills: Growth, Inflation, Monetary, Credit, Labor
- [ ] each pill: label + regime value + color-coded status dot
- [ ] color: green=healthy, amber=caution, red=stress, gray=neutral
- [ ] data-testids: `regime-strip`, `regime-{dimension}`, `regime-{dimension}-value`
- [ ] loads from `GET /api/v1/regime`
- [ ] states: loading skeleton, error fallback, populated

### Research Terminal (`apps/web/components/Terminal/`)
- [ ] `QueryInput` — full-width command-line style input, placeholder "Ask a macro research question...",
      monospace font, enter to submit, data-testid="query-input"
- [ ] `SplitPane` — left 55% ResearchPanel, right 45% TracePanel, resizable divider
      data-testid="split-pane"
- [ ] `ResearchPanel` — renders ResearchBrief sections:
      - `ThesisSummary` block, data-testid="thesis-summary"
      - `BullCase` expandable list, data-testid="bull-case"
      - `BearCase` expandable list, data-testid="bear-case"
      - `KeyRisks` expandable list, data-testid="key-risks"
      - `ConfidenceMeter` 1–5 scale visual, data-testid="confidence-meter"
      - `SourceList` citations with inline preview, data-testid="source-list"
      - streams in token-by-token as `brief_delta` events arrive
- [ ] `TracePanel` — live streaming reasoning trace:
      - each `tool_call` renders as a collapsible row with tool name + args
        data-testid="trace-step-{index}", data-testid="trace-tool-call-{index}"
      - each `tool_result` renders as a data preview row (first 3 rows of series)
        data-testid="trace-tool-result-{index}"
      - each `reasoning` chunk appended to current reasoning block
        data-testid="trace-reasoning-{index}"
      - auto-scroll to bottom as steps arrive
      - data-testid="trace-panel"
- [ ] `BriefStates` — empty (no query yet), loading (agent running), completed, error
      data-testids: "brief-empty", "brief-loading", "brief-complete", "brief-error"

### Mispricing Screener page (`apps/web/app/screener/`)
- [ ] full-width table: Rank, Contract, Platform badge, Category badge,
      Market Prob, Model Prob, Dislocation (with direction arrow), Confidence stars,
      Resolution, Last Updated
- [ ] data-testids: `screener-table`, `screener-row-{id}`, `screener-rank-{id}`,
      `screener-dislocation-{id}`
- [ ] sort controls: dislocation (default desc), confidence, resolution date
      data-testid="sort-dislocation", "sort-confidence", "sort-resolution"
- [ ] filter bar: platform toggle (Kalshi/Polymarket/All), category multi-select,
      min-dislocation slider
      data-testids: "filter-platform", "filter-category", "filter-min-dislocation"
- [ ] click row → opens detail drawer with GLM explanation
      data-testid="screener-drawer-{id}", "screener-drawer-explanation"
- [ ] states: loading, empty, error, populated with count

### Macro Series Charts (`apps/web/components/Charts/`)
- [ ] `SeriesChart` — Recharts LineChart, responsive, date axis, value axis,
      hover tooltip with date+value, data-testid="series-chart-{id}"
- [ ] used in: research brief citation expand, screener drawer
- [ ] headless-safe: animations disabled when `PLAYWRIGHT=true` env var set
- [ ] loading skeleton matches final chart dimensions

### Methodology page (`apps/web/app/methodology/`)
- [ ] sections: How GLM-5.1 works in Meridian, Tool architecture, Data sources table,
      Fair-value model description, Disclaimer
- [ ] data-testid="methodology-page"

### Frontend unit tests (`tests/unit/web/`)
- [ ] `TracePanel.test.tsx` — renders tool_call steps, auto-scroll fires, empty state
- [ ] `ResearchPanel.test.tsx` — brief sections render, confidence meter displays
- [ ] `Screener.test.tsx` — sort changes order, filter hides rows, drawer opens
- [ ] `RegimeDashboard.test.tsx` — all 5 dimensions render with correct colour class
- [ ] all tests use MSW to mock API endpoints
- [ ] `vitest` with jsdom, `@testing-library/react`

---

## Milestone 8 — E2E Tests and Proof Pack

**Gate:** All Playwright tests pass. failed=0, skipped=0, retries=0.
Proof pack written with MANIFEST.md, screenshots, traces, and TOUR.webm.

### Playwright config (`playwright.config.ts`)
```
retries: 0
workers: 1
video: 'on'
trace: 'on'
screenshot: 'on'
```
- [ ] base URL: `http://localhost:3000`
- [ ] `PLAYWRIGHT=true` env var set in all test runs (disables animations)
- [ ] reporter: `list` for CI, `html` for local

### E2E test suite (`tests/e2e/`)

#### `test_smoke.spec.ts`
- [ ] health endpoint returns 200
- [ ] homepage loads, `data-testid="topbar"` visible
- [ ] `data-testid="mode-badge"` contains "DEMO"
- [ ] `data-testid="regime-strip"` visible with 5 pills
- [ ] `data-testid="query-input"` visible and focusable

#### `test_research_flow.spec.ts`
- [ ] type demo question into `query-input`, press Enter
- [ ] `data-testid="brief-loading"` appears within 500ms
- [ ] `data-testid="trace-panel"` receives ≥5 trace steps
- [ ] first trace step has `data-testid="trace-step-0"` visible
- [ ] `data-testid="brief-complete"` appears (timeout 30s in demo mode)
- [ ] `data-testid="thesis-summary"` is non-empty text
- [ ] `data-testid="bull-case"` contains ≥2 items
- [ ] `data-testid="bear-case"` contains ≥2 items
- [ ] `data-testid="confidence-meter"` shows value 1–5
- [ ] `data-testid="source-list"` contains ≥3 citations

#### `test_screener.spec.ts`
- [ ] navigate to `/screener`
- [ ] `data-testid="screener-table"` renders ≥5 rows
- [ ] first row `data-testid="screener-rank-{id}"` shows "1"
- [ ] click `data-testid="sort-confidence"` — row order changes
- [ ] click `data-testid="filter-platform"` Kalshi — Polymarket rows hidden
- [ ] click `data-testid="screener-row-{id}"` — drawer opens
- [ ] drawer `data-testid="screener-drawer-explanation"` is non-empty

#### `test_regime.spec.ts`
- [ ] `data-testid="regime-growth"` visible
- [ ] `data-testid="regime-inflation"` visible
- [ ] `data-testid="regime-monetary"` visible
- [ ] `data-testid="regime-credit"` visible
- [ ] `data-testid="regime-labor"` visible
- [ ] each `regime-{dim}-value` has non-empty text

#### `test_methodology.spec.ts`
- [ ] navigate to `/methodology`
- [ ] `data-testid="methodology-page"` visible
- [ ] page contains text "GLM-5.1"
- [ ] page contains text "FRED"

### TOUR recording
- [ ] record `TOUR.webm` via Playwright `--video=on` on `test_research_flow.spec.ts`
- [ ] video ≥ 60 seconds, shows: query input → trace activating → brief streaming → complete

### Proof pack script (`scripts/proof.py`)
- [ ] collect: test results JSON, screenshots dir, traces dir, TOUR.webm
- [ ] write `MANIFEST.md` listing all files with SHA256 checksums
- [ ] write `manifest.json` machine-readable equivalent
- [ ] output to `artifacts/proof/<ISO-timestamp>-milestone-8-e2e/`

---

## Milestone 9 — Demo Mode Hardening and Submission

**Gate:** App runs fully from fixtures with zero network calls.
`data-testid="mode-badge"` shows "DEMO". README complete. Devpost page ready.

### Demo fixture completeness
- [ ] all 8 FRED series fixtures present in `data/fixtures/fred/`
- [ ] Kalshi + Polymarket fixtures: ≥5 contracts each
- [ ] EDGAR fixture: 1 ticker (AAPL, 10-K, 5 chunks)
- [ ] news fixtures: 3 topics
- [ ] `data/fixtures/traces/demo_trace.json` — complete pre-recorded research trace
      (15 steps minimum: 5 tool_calls, 5 tool_results, 3 reasoning, 1 brief, 1 complete)
- [ ] `data/fixtures/screener_snapshot.json` — 10 scored contracts
- [ ] `data/fixtures/regime_snapshot.json` — 5-dimension regime

### Demo trace authoring (`scripts/author_trace.py`)
- [ ] script replays `demo_trace.json` and validates schema correctness
- [ ] every `tool_call` step has a matching `tool_result` step
- [ ] `complete` step is last
- [ ] ResearchBrief embedded in `complete` step validates against schema

### README (`README.md`)
- [ ] project title + one-paragraph description with GLM-5.1 angle
- [ ] demo GIF or screenshot at top (linked from `artifacts/screenshots/`)
- [ ] quick start: 5 commands to clone + run demo mode
- [ ] architecture section with mermaid diagram
- [ ] GLM-5.1 integration section: which capabilities used, why GLM specifically
- [ ] data sources table
- [ ] API endpoint reference (all 7 endpoints, schema, example curl)
- [ ] roadmap section linking to `docs/product_plan.md`
- [ ] disclaimer: research only, not financial advice

### Devpost submission checklist
- [ ] public repo URL set
- [ ] live demo URL set (Render free tier or Railway)
- [ ] 3-minute demo video uploaded (sourced from TOUR.webm)
- [ ] Devpost description includes: GLM-5.1 angle, reasoning trace, FRED integration
- [ ] tech stack tags: GLM-5.1, FastAPI, Next.js, FRED, Kalshi, Polymarket
- [ ] screenshots: homepage, trace panel active, brief complete, screener table

### Final proof pack
- [ ] run all test gates: tsc, vitest, pytest, playwright
- [ ] all failed=0, skipped=0, retries=0
- [ ] write final proof pack to `artifacts/proof/<ISO>-milestone-9-submission/`
- [ ] public access verification: curl live URL `/api/v1/health` → 200
- [ ] record final public-facing TOUR.webm from live URL

---

## Acceptance Matrix

| Milestone | Gate Command | Pass Condition |
|---|---|---|
| 0 — Bootstrap | `pytest tests/unit/api/test_health.py -q` | failed=0 |
| 1 — Ingestion | `pytest tests/unit/ingestion/ -q` | failed=0 |
| 2 — Normalisation | `pytest tests/unit/normalisation/ -q` | failed=0 |
| 3 — Features | `pytest tests/unit/features/ -q` + snapshot check | failed=0, deterministic |
| 4 — Agent | `pytest tests/unit/agent/ -q` + SSE smoke | failed=0, ≥5 trace steps |
| 5 — Screener | `pytest tests/unit/screener/ -q` | failed=0 |
| 6 — API | `pytest tests/unit/api/ -q` | failed=0 |
| 7 — Frontend | `npm run tsc && npm run vitest` | 0 type errors, failed=0 |
| 8 — E2E | `npm run playwright` | failed=0, proof pack exists |
| 9 — Submission | all gates + live URL verified | all pass, URLs public |

A milestone with a missing proof pack is **REJECTED** regardless of test output.
