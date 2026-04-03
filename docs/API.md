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

Request body:

```json
{
  "question": "What does the current yield curve shape imply for equities over the next 6 months?",
  "mode": "demo",
  "session_id": "sess-optional-thread-id"
}
```

Request constraints:

- question: required, minimum length 3
- mode: optional, defaults to demo
- session_id: optional, 4..64 chars; reused to enable in-session follow-up continuity

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
- complete: brief, duration_ms, query_class, session_context_used
- error: message

Brief payload additions in complete events:

- query_class: macro_outlook | event_probability | ticker_macro
- follow_up_context: optional string summarizing prior-question linkage
- methodology_summary: optional string explaining evidence synthesis process
- sources[].claim_refs: array of claim pointers (for example bull_case[0])
- sources[].preview: structured preview metadata keyed by source type

Semantics:

- hard timeout: 120 seconds
- on timeout/error, an error event is emitted
- complete is always emitted before stream termination (success or fallback)

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
