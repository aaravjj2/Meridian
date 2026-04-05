# Meridian API Documentation

## Overview

Meridian exposes a deterministic demo-friendly API for macro research and market dislocation analysis.

- Base URL (local): http://localhost:8000
- API prefix: /api/v1
- OpenAPI docs: /docs
- ReDoc: /redoc

## Authentication

There is currently no request-level auth enforced by API routes.

- Demo mode: no secrets required
- Live mode: server-side GLM calls require ZAI_API_KEY in backend environment

## Endpoints

### GET /api/v1/health

Returns service status and active runtime mode.

Response:

```json
{
  "status": "ok",
  "mode": "demo",
  "version": "0.1.0"
}
```

### GET /api/v1/metadata

Returns static metadata and capability flags.

Response:

```json
{
  "version": "0.1.0",
  "model": "glm-5.1",
  "demo": true,
  "data_sources": ["fred", "kalshi", "polymarket", "edgar", "news"],
  "websocket_supported": true
}
```

### POST /api/v1/research

Starts a research run and streams trace events using Server-Sent Events.

### GET /api/v1/research/templates

Returns the deterministic Wave 15 research template catalog used by query flow and persistence.

Response:

```json
{
  "templates": [
    {
      "id": "macro_outlook",
      "title": "Macro outlook",
      "description": "Build a balanced macro baseline with explicit bull, bear, and risk structure.",
      "framing": "Start from cycle position, inflation trend, and policy stance before sizing risk.",
      "query_class_default": "macro_outlook",
      "emphasis": ["Cycle and regime interpretation"],
      "evaluation_expectations": ["At least one macro signal conflict is surfaced"]
    }
  ],
  "count": 4
}
```

Request body:

```json
{
  "question": "What does the current yield curve shape imply for equities over the next 6 months?",
  "mode": "demo",
  "session_id": "sess-optional-thread-id",
  "template_id": "macro_outlook"
}
```

Request constraints:

- question: required, minimum length 3
- mode: optional, defaults to demo
- session_id: optional, 4..64 chars; reused to enable in-session follow-up continuity
- template_id: optional, defaults to `macro_outlook`

Response content type:

- text/event-stream

Wire format:

- each frame is emitted as data: <json>\n\n
- there is no event: field currently emitted

Event payload baseline:

```json
{
  "type": "tool_call|tool_result|reasoning|brief_delta|complete|error|reflection",
  "step": 0,
  "ts": "2026-04-02T00:00:00Z",
  "session_id": "sess-optional-thread-id",
  "followup": false
}
```

Type-specific fields:

- tool_call: tool, args
- tool_result: tool, preview
- reasoning: text
- brief_delta: section, text
- complete: brief, duration_ms, query_class, session_context_used, provenance, evaluation
- error: message

Brief payload additions in complete events:

- query_class: macro_outlook | event_probability | ticker_macro
- template_id: macro_outlook | event_probability_interpretation | ticker_macro_framing | thesis_change_compare
- template_title: human-readable template title
- follow_up_context: optional string summarizing prior-question linkage
- methodology_summary: optional string explaining evidence synthesis process
- bull_case[].claim_id, bear_case[].claim_id, key_risks[].claim_id: stable claim identifiers
- sources[].claim_refs: array of claim_id links for claim-to-source navigation
- sources[].preview: structured preview metadata keyed by source type
- sources[].provenance: source-level provenance metadata including `state_label`, freshness, cache_lineage, and snapshot metadata
- provenance_summary: aggregate freshness/source-count metadata (includes `state_label_counts`)
- snapshot_summary: snapshot-level provenance rollup (state labels, snapshot kinds, cache lineage, timing summary, checksum coverage)
- signal_conflicts[]: contradiction metadata with conflict_id, title, summary, severity, claim_refs, source_refs
- evaluation: deterministic quality checks with stable signature and metrics

Snapshot and cache-lineage semantics:

- `snapshot.snapshot_kind=fixture`: deterministic fixture-backed data source
- `snapshot.snapshot_kind=cache`: replay from cached snapshot state
- `snapshot.snapshot_kind=live_capture`: fresher fetch path capture
- `snapshot.snapshot_kind=derived`: computed/derived snapshot
- `provenance.state_label`: normalized user-facing state (`fixture|cached|live|derived|unknown`)
- `cache_lineage`: normalized lineage classification (`fixture|cache|fresh_pull|derived|unknown`)

Semantics:

- hard timeout: 120 seconds
- on timeout/error, an error event is emitted
- complete is always emitted before stream termination (success or fallback)

### Workspace Session Persistence

The workspace API is single-user and file-backed for local/demo-safe operation.

### GET /api/v1/research/sessions

Lists saved research session summaries.

Response:

```json
{
  "sessions": [
    {
      "id": "rs-20260403235959-8f2c1a3d",
      "question": "What does the current yield curve imply for equities?",
      "mode": "demo",
      "session_id": "sess-abcd1234",
      "label": "Baseline curve view",
      "query_class": "macro_outlook",
      "template_id": "macro_outlook",
      "template_title": "Macro outlook",
      "follow_up_context": "Follow-up to prior question: ...",
      "archived": false,
      "archived_at": null,
      "saved_at": "2026-04-03T23:59:59Z",
      "updated_at": "2026-04-03T23:59:59Z",
      "canonical_signature": "<sha256>",
      "evaluation_passed": true,
      "evaluation_signature": "<sha256>",
      "snapshot_kind_counts": {"fixture": 3, "cache": 0, "live_capture": 0, "derived": 0, "unknown": 0},
      "cache_lineage_counts": {"fixture": 3, "cache": 0, "fresh_pull": 0, "derived": 0, "unknown": 0},
      "state_label_counts": {"fixture": 3, "cached": 0, "live": 0, "derived": 0, "unknown": 0},
      "latest_fetched_at": null,
      "latest_cached_at": null,
      "latest_generated_at": "2026-04-03T23:59:59Z"
    }
  ],
  "count": 1
}
```

Query parameters:

- `search`: optional substring filter over id/question/label/session_id/query_class
- `include_archived`: optional boolean (default `false`)
- `query_class`: optional `macro_outlook | event_probability | ticker_macro`

### POST /api/v1/research/sessions

Saves a completed research workspace state.

Request body includes:

- question
- mode (demo | live)
- session_id (runtime thread id)
- label (optional operator label)
- template_id (optional selected template id)
- brief (full ResearchBrief payload)
- trace_events (SSE-compatible trace payload)
- evidence_state (active_claim_id, expanded_source_id)
- evaluation (optional; server recomputes deterministic report for persistence)

Response is the full saved session record including `id` and `canonical_signature`.

### PATCH /api/v1/research/sessions/{saved_id}/rename

Renames a saved session label.

Request body:

```json
{
  "label": "Optional new label"
}
```

### PATCH /api/v1/research/sessions/{saved_id}/archive

Archives or unarchives a saved session.

Request body:

```json
{
  "archived": true
}
```

### DELETE /api/v1/research/sessions/{saved_id}

Deletes a saved session JSON record from local storage.

Response:

```json
{
  "deleted": true,
  "id": "rs-..."
}
```

### GET /api/v1/research/sessions/{saved_id}

Returns a full saved session record including brief, trace, and evidence state.

### GET /api/v1/research/sessions/compare

Compares two saved sessions and returns structured diffs.

Query parameters:

- `left_id`
- `right_id`

Response includes:

- `signature_match`
- `metadata_diffs`
- `claim_diffs`
- `source_diffs`
- `snapshot_drift`
- `conflict_diffs`
- `trace_diffs`
- `summary`

Wave 8 snapshot drift fields:

- `snapshot_drift.snapshot_ids_changed`: list of source refs where snapshot ids diverged
- `snapshot_drift.freshness_changed`: list of source refs where freshness class/hours diverged
- `snapshot_drift.source_set_changed`: whether source membership changed between sessions
- `snapshot_drift.evaluation_signature_changed`: whether deterministic evaluation signature changed
- `snapshot_drift.drift_signature`: deterministic hash of the snapshot-drift payload

Wave 11 conflict drift fields:

- `conflict_diffs.resolved`: conflicts removed or improved in severity
- `conflict_diffs.unchanged`: conflicts with unchanged severity/state
- `conflict_diffs.worsened`: conflicts added or worsened in severity
- each conflict drift item links claim/source/snapshot drift via `claim_delta`, `source_delta`, `snapshot_delta`
- `conflict_diffs.drift_signature`: deterministic hash of the conflict-drift payload

### POST /api/v1/research/sessions/{saved_id}/recapture

Creates a new saved session by recapturing an existing session against a refreshed snapshot baseline.

Behavior:

- does not overwrite the source saved session
- returns `saved` (the new session) and `lineage` (before/after snapshot provenance)
- in demo mode, applies deterministic pseudo-refresh semantics for fixture-backed snapshots

Response lineage fields:

- `source_session_id`
- `recaptured_session_id`
- `recapture_mode` (`demo_pseudo_refresh` | `live_refresh`)
- `before_snapshot_signature`
- `after_snapshot_signature`
- `snapshot_id_changes`
- `source_set_changes`
- `transition_count`
- `transitions[]` with `source_ref`, before/after snapshot ids, and before/after cache lineage

### GET /api/v1/research/sessions/integrity

Runs integrity checks across matching saved sessions.

Query parameters:

- `search` (optional)
- `include_archived` (optional, default `true`)

Response includes per-session `signature_valid`, trace ordering checks, evidence-state validity, and issue lists.

Phase 7 integrity fields:

- `provenance_complete`
- `freshness_valid`
- `freshness_policy_valid`
- `freshness_policy_violation_count`
- `snapshot_complete`
- `snapshot_consistent`
- `snapshot_summary_present`
- `snapshot_checksum_complete`
- `evaluation_present`
- `evaluation_valid`
- `evaluation_signature`
- `bundle_snapshot_signature`

Wave 10 evaluation check:

- `freshness_policy_compliance`: verifies source freshness against policy thresholds by source type

### GET /api/v1/research/sessions/evaluation/dashboard

Builds the Wave 18 deterministic workspace evaluation dashboard across matching saved sessions.

Query parameters:

- `search` (optional)
- `include_archived` (optional, default `false`)
- `query_class` (optional `macro_outlook | event_probability | ticker_macro`)

Response highlights:

- `session_count`, `passed_count`, `failed_count`, `pass_rate`
- `common_failure_types[]` (`check_id`, `count`)
- `provenance_gap_session_count`, `provenance_gap_total_count`
- `stale_source_session_count`, `stale_source_total_count`
- `claim_linking_gap_session_count`, `claim_linking_gap_total_count`
- `template_usage` (template-id frequency map)
- `sessions[]` compact per-session quality rows
- `deterministic_signature` (stable hash over dashboard projection)
- `ready_for_export` (true only when the dashboard is clean enough for export)

### GET /api/v1/research/sessions/evaluation/dashboard/export

Exports the Wave 18 dashboard as downloadable JSON when `ready_for_export` is true.

Behavior:

- returns `application/json` attachment when clean
- returns HTTP `409` if dashboard quality is not clean enough for export

### GET /api/v1/research/sessions/{saved_id}/integrity

Runs integrity checks for a single saved session.

### GET /api/v1/research/sessions/{saved_id}/review

Runs the Wave 16 guided review checklist for a saved session.

Response includes:

- `status`: `pass | fail`
- `completed`: `true` when all review checks pass
- `passed_count`, `failed_count`, `total_count`
- `summary`: compact review outcome text
- `deterministic_signature`: stable hash over review projection
- `items[]`: deterministic checklist entries:
  - `claim_source_coverage`
  - `conflict_linkage`
  - `freshness_acceptability`
  - `provenance_completeness`
  - `evaluation_pass_fail`
  - `template_metadata`
  - `snapshot_completeness`

### GET /api/v1/research/sessions/{saved_id}/export

Exports a saved session for offline review.

Query parameter:

- format: `json` | `markdown`

Behavior:

- `format=json`: structured machine-readable full session payload
- `format=markdown`: analyst-readable report with thesis, claims, sources, conflicts, and trace payload

### GET /api/v1/research/sessions/{saved_id}/bundle

Exports a self-contained **bundle v2** JSON payload for offline audit replay.

Top-level fields:

- `bundle_version: "wave14-v2"`
- `bundle_kind: "session"`
- `exported_at`
- `manifest`
- `files`

`manifest` includes:

- deterministic bundle signature
- per-section SHA256 signatures and byte inventory
- integrity/equality checks (session signature parity, integrity recomputation parity, evaluation signature parity, snapshot signature parity)
- timeline and compare-previous linkage metadata

`files` contains section payloads equivalent to offline artifacts:

- `session.json`
- `trace.json`
- `provenance.json`
- `evaluation.json`
- `integrity.json`
- `report.md`
- `timeline.json`
- `compare.json`

Wave 17 live/cached metadata in `files.provenance.json`:

- `live_mode_metadata.state_label_counts`
- `live_mode_metadata.cache_lineage_counts`
- `live_mode_metadata.timing_summary` (`latest_fetched_at`, `latest_cached_at`, `latest_generated_at`)

### Research Collections (Wave 12)

Collections are single-user, local notebooks that group saved sessions into ordered research timelines.

### GET /api/v1/collections

Lists collection summaries.

Response:

```json
{
  "collections": [
    {
      "id": "coll-20260404223000-a1b2c3d4",
      "title": "Yield Curve Notebook",
      "summary": "Threaded recession and event-probability sessions",
      "session_count": 2,
      "created_at": "2026-04-04T22:30:00Z",
      "updated_at": "2026-04-04T22:34:00Z",
      "collection_signature": "<sha256>"
    }
  ],
  "count": 1
}
```

### POST /api/v1/collections

Creates a collection.

Request:

```json
{
  "title": "Yield Curve Notebook",
  "summary": "Threaded recession and event-probability sessions",
  "notes": "Track how policy odds evolve against the same evidence chain"
}
```

### GET /api/v1/collections/{collection_id}

Returns collection detail plus ordered timeline metadata for each session id.

Response shape:

```json
{
  "collection": {
    "id": "coll-...",
    "title": "...",
    "summary": "...",
    "notes": "...",
    "session_ids": ["rs-a", "rs-b"],
    "created_at": "...",
    "updated_at": "...",
    "collection_signature": "<sha256>"
  },
  "timeline": [
    {
      "session_id": "rs-a",
      "exists": true,
      "label": "Baseline",
      "question": "...",
      "query_class": "macro_outlook",
      "template_id": "macro_outlook",
      "template_title": "Macro outlook",
      "saved_at": "...",
      "evaluation_passed": true,
      "snapshot_signature": "<sha256>",
      "archived": false,
      "thesis_state": {
        "thesis": "...",
        "confidence": 3,
        "claim_ids": ["bull-1-..."],
        "claim_count": 7,
        "freshness_policy_violation_count": 0,
        "freshness_policy_warning_count": 0,
        "conflict_ids": ["conflict-..."],
        "conflict_count": 1,
        "evaluation_passed": true,
        "evaluation_signature": "<sha256>"
      },
      "thesis_delta": {
        "previous_session_id": "rs-previous",
        "thesis_changed": true,
        "confidence_changed": false,
        "claims_changed": true,
        "freshness_policy_changed": false,
        "conflicts_changed": true,
        "evaluation_changed": true,
        "delta_signature": "<sha256>"
      }
    }
  ],
  "missing_session_count": 0,
  "timeline_signature": "<sha256>"
}
```

### GET /api/v1/research/sessions/{saved_id}/timeline

Returns ordered thesis evolution for the runtime thread referenced by `saved_id`.

Query parameters:

- `include_archived`: optional boolean (default `true`)

Response shape:

```json
{
  "thread_session_id": "sess-abcd1234",
  "timeline": [
    {
      "session_id": "rs-...",
      "exists": true,
      "saved_at": "2026-04-05T00:00:00Z",
      "thesis_state": { "thesis": "...", "confidence": 3, "claim_count": 7 },
      "thesis_delta": {
        "previous_session_id": "rs-prior",
        "thesis_changed": true,
        "confidence_changed": true,
        "claims_changed": false,
        "freshness_policy_changed": false,
        "conflicts_changed": true,
        "evaluation_changed": true,
        "delta_signature": "<sha256>"
      }
    }
  ],
  "timeline_signature": "<sha256>"
}
```

### PATCH /api/v1/collections/{collection_id}

Updates collection title/summary/notes.

Request body supports any subset of:

- `title`
- `summary`
- `notes`

### DELETE /api/v1/collections/{collection_id}

Deletes a collection record.

### POST /api/v1/collections/{collection_id}/sessions

Adds a saved session to a collection.

Request:

```json
{
  "session_id": "rs-20260404223311-11223344",
  "position": 0
}
```

Notes:

- `position` is optional; omission appends to end.
- adding requires the target saved session to exist.

### DELETE /api/v1/collections/{collection_id}/sessions/{session_id}

Removes a session from the collection.

### PUT /api/v1/collections/{collection_id}/sessions/reorder

Reorders the entire collection timeline.

Request:

```json
{
  "session_ids": ["rs-b", "rs-a"]
}
```

Validation rules:

- The reordered list must contain exactly the same session ids as current collection contents.
- Duplicate session ids are rejected.

### GET /api/v1/collections/{collection_id}/bundle

Exports an optional collection bundle v2 payload for offline notebook audits.

Top-level fields:

- `bundle_version: "wave14-v2"`
- `bundle_kind: "collection"`
- `manifest`
- `files`

`files` contains:

- `collection.json`
- `timeline.json`
- `sessions.json`
- `compare.json` (adjacent timeline pair comparisons)
- `provenance.json`
- `report.md`

### GET /api/v1/screener

Returns ranked dislocation contracts from fixture-backed snapshot in demo mode.

Query parameters:

- category: optional string exact match
- platform: optional string exact match (kalshi or polymarket)
- min_dislocation: optional float, default 0.0, minimum 0.0
- limit: optional integer, default 20, range 1..200

Response shape:

```json
{
  "contracts": [
    {
      "market_id": "pm-fed-cut-june-2026",
      "platform": "polymarket",
      "category": "fed_policy",
      "title": "Fed cuts rates by at least 50bps before July 2026",
      "resolution_date": "2026-06-30",
      "market_prob": 0.67,
      "model_prob": 0.41,
      "dislocation": 0.26,
      "direction": "market_overpriced",
      "explanation": "Model probability differs by 26.0pp from market-implied odds, indicating potential overpricing.",
      "confidence": 4,
      "scored_at": "2026-04-02T00:00:00Z"
    }
  ],
  "scored_at": "2026-04-02T00:00:00Z",
  "count": 1
}
```

### GET /api/v1/regime

Returns current five-dimension regime snapshot.

Response:

```json
{
  "dimensions": {
    "growth": "EXPANSION",
    "inflation": "ELEVATED",
    "monetary": "RESTRICTIVE",
    "credit": "CAUTION",
    "labor": "TIGHT"
  },
  "narrative": "Growth remains positive but decelerating while restrictive policy and moderately wider credit spreads keep recession risk elevated.",
  "updated_at": "2026-04-02T00:00:00Z"
}
```

### GET /api/v1/markets

Lists normalized market contracts with optional filters and pagination.

Query parameters:

- category: optional string exact match
- platform: optional string exact match
- page: optional integer, default 1, minimum 1
- page_size: optional integer, default 20, range 1..100

Response:

```json
{
  "markets": [],
  "count": 10,
  "page": 1,
  "page_size": 20
}
```

### GET /api/v1/markets/{market_id}

Returns market detail for a single id.

Success response includes canonical fields:

- id, platform, title, category, resolution_date
- market_probability, volume_usd, open_interest, last_updated
- history

Error response:

- 404 with detail: Market not found: {market_id}

### GET /api/v1/markets/{market_id}/explain

Returns screener score/explanation for a market id.

Error response:

- 404 with detail: Market score not found: {market_id}

## WebSocket Endpoints

### WS /api/v1/ws/research

Client message types:

- ping
- status
- query

Client query message:

```json
{
  "type": "query",
  "question": "What is the recession probability?"
}
```

Server message types used by this endpoint:

- connected
- pong
- status
- query_started
- trace
- reflection_checkpoint
- complete
- error

Notes:

- trace events wrap TraceStep payload as data
- query starts background streaming task per request

### WS /api/v1/ws/broadcast

Server emits:

- connected with connection_id and active_connections

Client may send:

- ping

Server replies:

- pong with connection count

## Error and Validation Semantics

Common status codes:

- 200: success
- 404: unknown market/score id (market detail and explain)
- 422: request validation error (for example, short question or invalid query params)

There is currently no explicit API-level 401/429 route behavior implemented.

## Limits and Determinism Notes

- research stream timeout: 120 seconds
- demo mode is fixture-backed and deterministic
- Playwright path runs with PLAYWRIGHT=true and MERIDIAN_MODE=demo

## Deployment Notes

- Frontend can proxy API requests under /api/v1/* via Next.js rewrites
- Vercel config is present in vercel.json and points API traffic to meridian-api.railway.app
