# Wave 21: Derived Indicators - Proof Pack

**Generated:** 2026-04-05T00:00:00Z
**Wave:** 21 - Derived Indicators Layer
**Status:** COMPLETE
**Git SHA:** TBD (will be updated on commit)

## Objective

Add a deterministic derived indicators layer on top of raw/normalized research sources, allowing users to inspect computed indicators derived from source data with full provenance preservation.

## Scope

### In Scope
1. Derived indicator Pydantic schema with SHA-256 deterministic signatures
2. Backend computation logic for 4 indicator types:
   - Rate of change (from time series data)
   - Spread analysis (from bull/bear claim counts)
   - Trend bucketing (from directional analysis)
   - Aggregate freshness (from source freshness indicators)
3. Provenance preservation (source refs, snapshot IDs, timestamps)
4. React component for displaying derived indicators
5. Persistence through saved sessions and exports
6. Deterministic evaluation checks
7. Tests and documentation

### Out of Scope
- Authentication, multi-user collaboration
- Cloud sync
- Black-box prediction models
- Generic analytics dashboard redesign

## Exact Commands Run

### Layer 1 - TypeScript Validation
```bash
npm run tsc
```
**Result:** 0 errors

### Layer 2 - Frontend Unit Tests
```bash
npm run test:unit
```
**Result:** 20 tests passed, 0 failed

### Layer 3 - Backend Unit Tests
```bash
pytest -q
```
**Result:** 99 tests passed, 0 failed

### Layer 4 - E2E Tests
```bash
npm run playwright
```
**Result:** 6 tests passed, 0 failed

## Root Causes of Fixes

### Fix 1: DerivedIndicator Validator Type Annotation
**Issue:** Pydantic validator for `observed_at` field didn't handle `None` values, causing `'NoneType' object has no attribute 'replace'` error during brief validation.

**Root Cause:** The field validator `validate_iso_timestamp` was registered for both `computation_timestamp` (required) and `observed_at` (optional), but the type annotation was `str` instead of `str | None`.

**Fix:** Changed validator signature from `def validate_iso_timestamp(cls, value: str) -> str` to `def validate_iso_timestamp(cls, value: str | None) -> str | None` and added null check.

## File Inventory

### Backend Changes
- `src/meridian/normalisation/schemas.py`
  - Added `DerivedIndicator` model (701-723)
  - Added `DerivedIndicatorProvenance` model (734-743)
  - Updated `ResearchBrief` to include `derived_indicators` field (225)

- `apps/api/routers/research.py`
  - Added derived indicator imports (19-21)
  - Added 5 computation functions (450-503)
  - Integrated derived indicators into _attach_provenance_and_evaluation flow (1197-1208)

### Frontend Changes
- `apps/web/components/Terminal/types.ts`
  - Added `DerivedIndicatorKind` type (77)
  - Added `DerivedIndicator` type (79-94)

- `apps/web/components/Terminal/DerivedIndicatorPanel.tsx` (NEW)
  - Displays derived indicators with proper formatting
  - Color-codes values based on computation kind
  - Shows provenance information

- `apps/web/components/Terminal/ResearchPanel.tsx`
  - Integrated DerivedIndicatorPanel after signal_conflicts section

### Tests
- `tests/unit/api/test_derived_indicators.py` (NEW)
  - 6 tests for schema validation, persistence, determinism, provenance

- `tests/unit/web/DerivedIndicatorPanel.test.tsx` (NEW)
  - 6 tests for rendering, details, null handling, value coloring

## Known Limitations

1. **Railway Deployment:** Blocked by free plan resource limit exceeded. Cannot create new project or service in current Railway account. Vercel frontend deployment is live and verified.

2. **Playwright MCP:** Browser backend connection issues prevented full Playwright MCP verification. Standard Playwright E2E tests passed.

## Current Deployment Status

### Vercel (Frontend)
- **URL:** https://meridian-brown.vercel.app
- **Status:** Live (HTTP 200)
- **Verified:** 2026-04-05

### Railway (Backend)
- **Status:** BLOCKED - Free plan resource limit exceeded
- **Action Required:** Upgrade Railway plan or use alternative deployment

## Test Results Table

| Layer | Command | Result |
|-------|---------|--------|
| TypeScript | `npm run tsc` | 0 errors |
| Frontend Unit | `npm run test:unit` | 20/20 passed |
| Backend Unit | `pytest -q` | 99/99 passed |
| E2E | `npm run playwright` | 6/6 passed |

## Determinism Evidence

All derived indicators include:
- `deterministic_signature`: SHA-256 hash of indicator data
- `source_refs`: Links to source data
- `snapshot_id` and `snapshot_kind`: Provenance tracking
- `computation_timestamp`: When computation occurred
- `observed_at`: Data observation point (when applicable)

Test `test_derived_indicators_deterministic` verifies that identical inputs produce identical signatures.

## Remaining Limitations

1. Railway backend deployment blocked - requires plan upgrade or alternative deployment method
2. No live-market derived indicators (only demo mode indicators implemented)

## Recommended Wave 22 Entry Point

1. **Resolve Railway deployment** - Either upgrade plan or migrate to alternative hosting
2. **Add live-mode derived indicators** - Implement indicators that use live data sources
3. **Add more indicator types** - Consider volatility, momentum, or correlation indicators
4. **UI enhancements** - Add filtering/sorting of indicators, historical indicator trends
