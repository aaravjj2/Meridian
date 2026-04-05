# Wave 21: Derived Indicators Layer

## Overview

Wave 21 adds a deterministic derived indicators layer to the Meridian research system. Derived indicators are computed values derived from source data that provide additional insights beyond raw source information.

## What Are Derived Indicators?

Derived indicators are computed metrics that:
- Transform raw source data into meaningful insights
- Preserve full provenance (source refs, snapshots, timestamps)
- Include deterministic signatures for reproducibility
- Are validated through the same evaluation framework as other research data

## Implemented Indicator Types

### 1. Rate of Change (`rate_of_change`)
Computes percentage change between time series data points.
- **Value:** Percentage change (positive/negative)
- **Color Coding:** Green for positive, red for negative
- **Sources:** FRED time series, market data

### 2. Spread Analysis (`spread`)
Measures imbalance between bullish and bearish signals.
- **Value:** Ratio or absolute difference
- **Color Coding:** Orange for spreads > 0.3
- **Sources:** Bull/bear case analysis

### 3. Trend Bucket (`trend_bucket`)
Classifies directional trends from time series data.
- **Values:** "bullish", "bearish", "neutral"
- **Sources:** Time series directional analysis

### 4. Aggregate Freshness (`aggregate_freshness`)
Measures overall data freshness across all sources.
- **Value:** Index from 0 (fresh) to 2 (stale)
- **Color Coding:** Green (≤0.5), Yellow (≤1.0), Red (>1.0)
- **Sources:** All sources with freshness metadata

## Data Model

Each derived indicator includes:
- `indicator_id`: Unique identifier starting with `ind-`
- `title`: Human-readable label
- `value`: Computed numeric value
- `unit`: Unit of measurement (%, ratio, index, etc.)
- `computation_kind`: Type of computation
- `source_refs`: List of source references used
- `snapshot_id`/`snapshot_kind`: Provenance tracking
- `computation_timestamp`: When computation occurred
- `observed_at`: Data observation point
- `deterministic_signature`: SHA-256 hash for reproducibility
- `reasoning`: Code-derived explanation

## UI Integration

Derived indicators appear in the ResearchPanel below signal conflicts, showing:
- Indicator kind and value with color coding
- Title and reasoning
- Source references
- Snapshot provenance

## Validation

All derived indicators are validated for:
- Required field presence
- ISO timestamp format
- Proper ID prefixes
- Source linkage completeness
- Deterministic signature consistency

## Test Coverage

- Schema validation tests
- Research response integration tests
- Persistence through save/load tests
- Determinism verification tests
- Provenance completeness tests
- Computation kind validation tests
- Frontend rendering tests
- Value coloring tests

## Deployment Status

✅ **Vercel (Frontend):** Live at https://meridian-brown.vercel.app
❌ **Railway (Backend):** Blocked - free plan limit exceeded

## Future Enhancements

- Live-mode derived indicators (using live data)
- Additional indicator types (volatility, momentum, correlation)
- Historical indicator trend visualization
- Indicator filtering and sorting
- Custom indicator computation UI
