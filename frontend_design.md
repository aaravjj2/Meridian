# Meridian — Frontend Design

## Design objective

A judge or analyst lands on Meridian and within 10 seconds understands:

1. This is a research terminal, not a chatbot.
2. An AI agent is doing live work — I can watch it think.
3. The output is structured, cited, and auditable.

Everything in the design exists to serve that 10-second read.

---

## Aesthetic direction

**Dark analytical terminal.** Not neon crypto. Not soft SaaS. Not a Bloomberg clone.

The closest analogue is a CRT-era financial workstation reimagined with modern type
and micro-animation. Dense but structured. Monochrome base with precise semantic
color. Every pixel earns its place.

References: Bloomberg raw data screens, Grafana dark mode, Cursor IDE, Linear app.

**What this is NOT:**
- White background with a chat bubble
- Purple gradients on black (crypto aesthetic)
- Card grid of rounded pastel tiles
- Generic AI tool look (Inter font, gray border, blue button)

---

## Typography

```
Display / Terminal labels:  JetBrains Mono, weight 500
                            Used for: query input, trace steps, code values,
                            FRED series values, probability numbers

UI / Body:                  Inter, weight 400/500
                            Used for: brief text, descriptions, nav, labels

Fallbacks: system-ui, monospace (for mono); system-ui, sans-serif (for UI)
```

Font sizes (rem scale, root = 16px):

| Token | rem | Used for |
|---|---|---|
| `--fs-xs` | 0.6875rem (11px) | Status bar, timestamps, metadata |
| `--fs-sm` | 0.75rem (12px) | Table cell secondary, trace args |
| `--fs-base` | 0.875rem (14px) | Body text, table cells, brief content |
| `--fs-md` | 1rem (16px) | Section headings, screener column headers |
| `--fs-lg` | 1.125rem (18px) | Panel titles, query placeholder |
| `--fs-xl` | 1.5rem (24px) | Brief thesis headline |
| `--fs-2xl` | 2rem (32px) | Wordmark |

---

## Color system

Meridian uses a single dark background with precise semantic color. No light mode.

```css
/* Backgrounds — layered depth */
--bg-void:       #080c10;   /* page background */
--bg-surface:    #0d1117;   /* panel backgrounds */
--bg-elevated:   #141b24;   /* cards, inputs, rows */
--bg-hover:      #1c2630;   /* hover states */
--bg-active:     #1e3a4a;   /* active/selected rows */

/* Borders */
--border-subtle:  #1e2a38;  /* dividers, panel edges */
--border-default: #2a3a4c;  /* input borders, table borders */
--border-focus:   #3a8abd;  /* focus rings */

/* Text */
--text-primary:   #e2e8f0;  /* main content */
--text-secondary: #8899aa;  /* labels, metadata */
--text-muted:     #4a5a6a;  /* disabled, placeholders */
--text-mono:      #a8d8b0;  /* monospace data values */

/* Semantic — regime and status */
--green:          #22c55e;  /* healthy regime, bull case */
--green-dim:      #166534;  /* green background fills */
--amber:          #f59e0b;  /* caution regime, neutral */
--amber-dim:      #78350f;  /* amber background fills */
--red:            #ef4444;  /* stress, bear case, error */
--red-dim:        #7f1d1d;  /* red background fills */
--blue:           #3b82f6;  /* info, citations, links */
--blue-dim:       #1e3a8a;  /* blue background fills */
--purple:         #a855f7;  /* GLM agent, reasoning */
--purple-dim:     #4a1d96;  /* purple background fills */
--teal:           #14b8a6;  /* tool calls, data fetches */
--teal-dim:       #134e4a;  /* teal background fills */

/* Platform badges */
--kalshi:         #00d4aa;  /* Kalshi brand teal */
--polymarket:     #6366f1;  /* Polymarket brand indigo */

/* Accent — used sparingly */
--accent:         #3a8abd;  /* primary CTA, active nav */
--accent-hover:   #4a9acd;  /* hover on accent elements */
```

**Color usage rules:**
- Green = healthy / bullish. Amber = caution / neutral. Red = stress / bearish.
- Purple is exclusively for GLM reasoning output — nothing else is purple.
- Teal is exclusively for tool call events in the trace.
- Never use green/red for decorative purposes — only for semantic status.
- Dislocation direction arrows: green (market underpriced), red (market overpriced).

---

## Spacing system

8px base unit. All spacing is a multiple of 4px minimum, 8px preferred.

```css
--space-1:  4px
--space-2:  8px
--space-3:  12px
--space-4:  16px
--space-5:  20px
--space-6:  24px
--space-8:  32px
--space-10: 40px
--space-12: 48px
--space-16: 64px
```

---

## Layout

### Overall page structure

```
┌─────────────────────────────────────────────┐
│  TopBar (48px fixed)                         │
├─────────────────────────────────────────────┤
│  RegimeDashboard strip (40px, 5 pills)       │
├──────────────────┬──────────────────────────┤
│                  │                           │
│  Left panel      │  Right panel              │
│  (55% default)   │  (45% default)            │
│                  │                           │
│  Research        │  Reasoning Trace          │
│  Brief           │                           │
│                  │                           │
│                  │                           │
├──────────────────┴──────────────────────────┤
│  QueryInput (64px)                           │
├─────────────────────────────────────────────┤
│  StatusBar (32px fixed)                      │
└─────────────────────────────────────────────┘
```

- TopBar: `position: fixed; top: 0; z-index: 100`
- StatusBar: `position: fixed; bottom: 0; z-index: 100`
- Main content: `padding-top: 48px; padding-bottom: 96px` (bar heights + query input)
- QueryInput: `position: fixed; bottom: 32px` (sits above status bar)
- Split pane: `height: calc(100vh - 48px - 40px - 64px - 32px)`; overflow scroll per panel

### Screener page structure

```
┌─────────────────────────────────────────────┐
│  TopBar                                      │
├─────────────────────────────────────────────┤
│  RegimeDashboard strip                       │
├─────────────────────────────────────────────┤
│  Filter bar (platform toggle, category, sort)│
├─────────────────────────────────────────────┤
│  Full-width screener table (scrollable)      │
├──────────────────────────────────────────────┤
│  Detail drawer (slides in from right, 40%)   │
├─────────────────────────────────────────────┤
│  StatusBar                                   │
└─────────────────────────────────────────────┘
```

---

## Component specifications

### TopBar

Height: 48px. Background: `--bg-surface`. Bottom border: 1px `--border-subtle`.

Left: `MERIDIAN` wordmark — JetBrains Mono, 20px, `--text-primary`, letter-spacing 0.08em.
Followed by version tag `v0.1` in 11px `--text-muted`.

Center: nav links — `Research` | `Screener` | `Methodology`. Inter 14px.
Active link: `--accent`, bottom border 2px `--accent`.
Inactive: `--text-secondary`. Hover: `--text-primary`.

Right: mode badge → green pill `DEMO` or amber pill `LIVE`.
Badge: 10px font, all-caps, `--bg-elevated` fill, colored border, 4px radius.

`data-testid` requirements:
- `data-testid="topbar"`
- `data-testid="wordmark"`
- `data-testid="mode-badge"`
- `data-testid="nav-research"`, `"nav-screener"`, `"nav-methodology"`

### RegimeDashboard strip

Height: 40px. Background: `--bg-elevated`. Bottom border: 1px `--border-subtle`.
Horizontal scroll on mobile.

Five pills, evenly spaced. Each pill:
- Label: 10px Inter all-caps `--text-muted` (`GROWTH`, `INFLATION`, etc.)
- Value: 12px Inter `--text-primary` (e.g. `EXPANSION`, `ELEVATED`, `RESTRICTIVE`)
- Status dot: 6px circle. Green/amber/red depending on regime severity.
- Separator `|` between pills in `--border-subtle`

`data-testid` requirements:
- `data-testid="regime-strip"`
- `data-testid="regime-growth"` through `"regime-labor"`
- `data-testid="regime-{dim}-value"` for each dimension
- `data-testid="regime-{dim}-dot"` for each status dot

### QueryInput

Height: 64px. Background: `--bg-elevated`. Top border: 1px `--border-default`.
Full width of viewport. `position: fixed; bottom: 32px`.

Left: `>` prompt character in `--text-mono` 16px mono, padding-left 16px.
Input: JetBrains Mono 15px `--text-primary`, placeholder `--text-muted`,
placeholder text: `Ask a macro research question...`
No visible border on the input itself — the container provides the border.
Right: `↵ Enter` hint in `--text-muted` 12px when input is non-empty.
Submit button (icon only): chevron-right icon, `--accent`, appears on non-empty.

Focus state: `--border-focus` glow effect on container (0 0 0 2px `--border-focus`40).

Keyboard: Enter submits. Escape clears. Up arrow recalls last query.

`data-testid` requirements:
- `data-testid="query-input"`
- `data-testid="query-submit"`
- `data-testid="query-container"`

### ResearchPanel (left panel)

Background: `--bg-surface`. Right border: 1px `--border-subtle`.
Overflow-y: scroll. Padding: 20px 24px.

**Empty state:** `data-testid="brief-empty"`
Center-aligned. Icon: terminal cursor `▋` blinking at 1s. 
Text: "Ask a question to begin research." in `--text-muted` 14px.
Sub-text: "GLM-5.1 will fetch live macro data and synthesize a brief." 12px.

**Loading state:** `data-testid="brief-loading"`
Shimmer skeleton rows for each brief section. Skeleton blocks:
- Thesis: 3 lines, 90% / 80% / 60% width
- Bull/Bear: 2 items each with bullet
- Confidence: 5-dot row
Shimmer: `--bg-elevated` base, `--bg-hover` highlight, 1.5s animation.

**Complete state:** `data-testid="brief-complete"`

*ThesisSummary block:*
- Thin left border 3px `--accent`
- Padding-left: 16px
- Label: `THESIS` 10px all-caps `--text-muted`
- Text: Inter 16px `--text-primary` line-height 1.6
- data-testid="thesis-summary"

*BullCase block:*
- Label: `BULL CASE` 10px all-caps `--green` with green dot
- Items: bullet `▸` in `--green`, text 14px `--text-primary`
- Each item cites a source: inline `[FRED:T10Y2Y]` pill in `--teal-dim` / `--teal`
- data-testid="bull-case", each item "bull-case-item-{n}"

*BearCase block:*
- Same structure, `--red` accent
- data-testid="bear-case", each item "bear-case-item-{n}"

*KeyRisks block:*
- Label: `KEY RISKS` 10px all-caps `--amber` with amber dot
- Items: `⚠` in `--amber`
- data-testid="key-risks", each item "key-risks-item-{n}"

*ConfidenceMeter:*
- Label: `CONFIDENCE` 10px all-caps `--text-muted`
- 5 rectangular segments, filled = `--accent`, empty = `--bg-elevated`
- Numeric label beside: e.g. `3 / 5`
- data-testid="confidence-meter"

*SourceList:*
- Label: `SOURCES` 10px all-caps `--text-muted`
- Each source: source type badge + source ID + one-line excerpt
- Source type badges: `FRED` in teal, `EDGAR` in blue, `NEWS` in amber, `MARKET` in purple
- Click expands inline chart (SeriesChart) for FRED sources
- data-testid="source-list", each item "source-item-{n}"

**Error state:** `data-testid="brief-error"`
Red border left strip. Error message text. Retry button.

### TracePanel (right panel)

Background: `--bg-void`. Overflow-y: scroll with auto-scroll to bottom.
Monospace throughout. Padding: 16px.

Header: `REASONING TRACE` label 10px all-caps `--text-muted`. Step counter `[0/0]` right-aligned.

Each step is a row: `data-testid="trace-step-{index}"`

**Tool call step** (`data-testid="trace-tool-call-{index}"`):
- Left gutter: teal vertical bar 2px
- Icon: `→` in `--teal` 12px mono
- Tool name: `fred_fetch` in `--teal` 13px bold mono
- Args: collapsed by default — click to expand raw JSON
- Timestamp: right-aligned 11px `--text-muted`
- Background on hover: `--bg-hover`

**Tool result step** (`data-testid="trace-tool-result-{index}"`):
- Left gutter: teal 2px (lighter shade)
- Icon: `←` in `--text-secondary` 12px mono
- Preview: first 3 rows rendered as mini table — borders `--border-subtle`,
  values in `--text-mono` mono 11px
- Collapsible: click to show full result

**Reasoning step** (`data-testid="trace-reasoning-{index}"`):
- Left gutter: purple 2px
- Icon: `◈` in `--purple` 12px
- Text: Inter 13px `--text-secondary` streams in character-by-character
- Background: subtle purple tint `--purple-dim`10 (10% opacity)

**Brief delta step** (streaming final output):
- Left gutter: `--accent` 2px
- Icon: `✦` in `--accent`
- Label: section name being written (e.g. `thesis`, `bull_case`)

**Complete step:**
- Full-width row: `✓ RESEARCH COMPLETE` in `--green`, centered
- Duration label: `14.2s · 12 tool calls`

Auto-scroll: each new step smoothly scrolls into view.
Scroll-lock button: if user scrolls up, auto-scroll pauses. Button appears: `↓ Resume` in bottom-right.

### Screener table

Full viewport width. Sticky header row.

Column widths (approximate, flexible):
- Rank: 48px right-aligned mono `--text-muted`
- Contract: flex grow, `--text-primary` 14px truncated with tooltip on hover
- Platform: 80px — badge pill
- Category: 100px — badge pill
- Market %: 80px right-aligned mono `--text-primary`
- Model %: 80px right-aligned mono `--text-secondary`
- Gap: 80px — colored mono, `--green` or `--red` with arrow `↑`/`↓`
- Confidence: 64px — star count (★★★☆☆)
- Resolution: 100px — relative date ("3 days")
- Updated: 80px — time ago `--text-muted`

Header row: `--bg-elevated`, 12px Inter all-caps `--text-secondary`.
Sort indicator: `↑` or `↓` beside active sort column in `--accent`.

Rows: alternating `--bg-surface` / `--bg-void` very subtle.
Hover: `--bg-active`. Selected: `--bg-active` with left border `--accent`.

Platform badges:
- Kalshi: `--kalshi` text, `--teal-dim` fill, 4px radius
- Polymarket: `--polymarket` text, `--blue-dim` fill, 4px radius

Category badges: text `--text-primary`, fill `--bg-elevated`, border `--border-default`.

Dislocation cell: value in mono bold. Color: green if model > market (underpriced),
red if market > model (overpriced). Arrow ↑/↓ precedes value.

### Screener detail drawer

Slides in from right, width: 40%, min-width 360px.
Background: `--bg-surface`. Left border: 1px `--border-default`.
Close button: `✕` top-right.

Sections:
1. Contract header — title, platform badge, resolution date
2. Probability comparison — two large numbers side by side:
   "MARKET 67%" vs "MODEL 41%" with gap label "GAP −26pp (OVERPRICED)"
3. GLM explanation — purple left bar, 14px Inter text
4. FRED series charts — one SeriesChart per relevant series (2–3 charts)
5. Resolution metadata

`data-testid="screener-drawer-{id}"`, `"screener-drawer-explanation"`

### SeriesChart

Recharts LineChart. Dimensions: full width × 120px.
Background: transparent. Grid: `--border-subtle` dashed horizontal lines only.
Line: `--accent` 1.5px, no dots except on hover.
Hover: crosshair + tooltip showing `{date}: {value}`.
X-axis: date labels in `--text-muted` 11px mono, 4–6 labels visible.
Y-axis: value labels right-aligned `--text-muted` 11px mono.
No legend (series title in label above chart).
Animation: disabled when `process.env.PLAYWRIGHT === 'true'`.

---

## Pages

### / — Research Terminal

This is the default page. It is the product.

**First-screen visible elements (above the fold, no scroll):**
1. TopBar with DEMO badge
2. Regime strip — all 5 dimensions
3. Empty ResearchPanel — centered prompt
4. Empty TracePanel — "Awaiting query…" in `--text-muted`
5. QueryInput — focused and blinking cursor

**Post-submission state:**
- QueryInput disabled (opacity 50%)
- Brief loading skeleton appears immediately
- Trace panel starts populating within ~200ms (demo mode delay)
- Brief streams in as trace completes

### /screener — Mispricing Screener

Full table view. No split pane.
Default sort: dislocation descending.
Default filter: all platforms, all categories, min dislocation 0.

Page title row: `MISPRICING SCREENER` label + subtitle `Kalshi × Polymarket × FRED`.
Row count badge: `{n} contracts` in `--text-muted`.
Last-scored timestamp right-aligned.

### /methodology — How It Works

Prose page. Max-width 720px, centered.
Sections as `<h2>` with `--accent` left border.

1. What Meridian does
2. How GLM-5.1 is used (tool calls, context window, reasoning trace)
3. Data sources (table: source, type, description, update frequency)
4. Fair-value model (plain English — no math)
5. Limitations and caveats
6. Disclaimer: research only, not financial advice

---

## States — every panel must implement all

| State | Trigger | Required elements |
|---|---|---|
| `empty` | No data / no query | Placeholder text, data-testid="*-empty" |
| `loading` | Fetching / agent running | Shimmer skeleton, data-testid="*-loading" |
| `error` | API failure / timeout | Error message, retry button, data-testid="*-error" |
| `complete` | Data loaded / brief done | Full content, data-testid="*-complete" |

---

## data-testid master list

Every interactive or meaningful DOM element must have a `data-testid`.
No `data-testid` → not testable → Playwright E2E will fail.

### Navigation and chrome
- `topbar`
- `wordmark`
- `mode-badge`
- `nav-research`, `nav-screener`, `nav-methodology`
- `status-bar`
- `regime-strip`
- `regime-growth`, `regime-inflation`, `regime-monetary`, `regime-credit`, `regime-labor`
- `regime-{dim}-value`, `regime-{dim}-dot` for each dimension

### Query
- `query-container`
- `query-input`
- `query-submit`

### Research panel
- `split-pane`
- `research-panel`
- `brief-empty`, `brief-loading`, `brief-complete`, `brief-error`
- `thesis-summary`
- `bull-case`, `bull-case-item-{n}`
- `bear-case`, `bear-case-item-{n}`
- `key-risks`, `key-risks-item-{n}`
- `confidence-meter`
- `source-list`, `source-item-{n}`

### Trace panel
- `trace-panel`
- `trace-step-{n}`
- `trace-tool-call-{n}`
- `trace-tool-result-{n}`
- `trace-reasoning-{n}`
- `trace-complete`

### Screener
- `screener-table`
- `screener-row-{id}`
- `screener-rank-{id}`
- `screener-dislocation-{id}`
- `sort-dislocation`, `sort-confidence`, `sort-resolution`
- `filter-platform`, `filter-category`, `filter-min-dislocation`
- `screener-drawer-{id}`
- `screener-drawer-explanation`

### Charts
- `series-chart-{id}`

### Methodology
- `methodology-page`

---

## Animations and motion

Rule: every animation must be disableable via `process.env.PLAYWRIGHT === 'true'`
or `prefers-reduced-motion: reduce`.

```tsx
// At top of every component using motion:
const isE2E = process.env.PLAYWRIGHT === 'true'
const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
const motionOk = !isE2E && !prefersReduced
```

Permitted animations:
- Shimmer skeletons: 1.5s ease-in-out `opacity` + `background-position` loop
- Trace step entrance: 150ms `opacity` 0→1 + 4px Y translate
- Brief section entrance: 200ms staggered per section
- Screener row hover: 80ms `background-color`
- Cursor blink in empty state: 1s step-start `opacity` loop
- Drawer slide-in: 200ms `transform` translateX

No physics engines. No spring animations. No Three.js. No canvas animations.
Framer Motion permitted but must be import-guarded and disabled in E2E.

---

## Accessibility

- All interactive elements keyboard-reachable (Tab order logical)
- No hover-only information — everything accessible on focus
- Color alone never carries meaning — always paired with shape/text
- ARIA labels on icon-only buttons
- `role="status"` on brief loading state for screen reader announcements
- All charts have `aria-label` describing the series
- Screener table is `<table>` with `<th scope="col">` headers
- Drawer traps focus when open, restores on close

---

## E2E safety rules

These are not optional. Violating them causes Playwright to fail.

1. **Every interactive element has `data-testid`.** No exceptions.
2. **Animations disabled when `PLAYWRIGHT=true`.** All shimmer, motion, chart
   animations must check this env var.
3. **Demo mode requires no secrets.** The entire E2E suite runs without `.env`.
4. **Charts render in headless.** Recharts with SSR-compatible config. No canvas
   fallback required — SVG output only.
5. **No hover-only state.** Playwright can hover but never relies on it for
   assertions. Tooltips are permitted but not required for test assertions.
6. **No random data in demo mode.** All values deterministic from fixtures.
   `Math.random()` is banned in any code path triggered by demo mode.
7. **SSE stream must complete.** `complete` event must always be emitted,
   even on error paths (emit `error` then `complete`).
8. **No `setTimeout` with random delays.** Fixed 80ms step delay in demo replay.

---

## First-screen success criterion

A judge lands on Meridian's home page, cold, no explanation.

Within 10 seconds they can say:
> "This is a terminal where I type a macro research question,
>  an AI agent fetches live data and I can watch it work,
>  and it produces a structured research brief."

If they cannot say this in 10 seconds, the design has failed.
