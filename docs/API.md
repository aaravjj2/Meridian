# Meridian API Documentation

GLM-5.1 Powered Financial Research Terminal API

## Overview

Meridian provides a RESTful API with real-time streaming capabilities for financial research powered by GLM-5.1 agentic reasoning.

**Base URL**: `http://localhost:8000` (default)
**API Version**: v1
**Model**: GLM-5.1 by Z.ai

---

## Authentication

The API supports both demo mode (no authentication) and live mode (requires `ZAI_API_KEY`).

### Headers

```http
Authorization: Bearer YOUR_ZAI_API_KEY
Content-Type: application/json
```

---

## Endpoints

### Health Check

```http
GET /api/v1/health
```

Check API health status.

**Response**:
```json
{
  "status": "ok",
  "mode": "demo",
  "version": "0.1.0"
}
```

---

### Metadata

```http
GET /api/v1/metadata
```

Get API metadata and capabilities.

**Response**:
```json
{
  "version": "0.1.0",
  "model": "glm-5.1",
  "demo": true,
  "data_sources": ["fred", "kalshi", "polymarket", "edgar", "news"],
  "websocket_supported": true
}
```

---

### Research Query (SSE)

```http
POST /api/v1/research
Content-Type: application/json
```

Start a GLM-5.1 research query with Server-Sent Events streaming.

**Request Body**:
```json
{
  "question": "What is the current recession probability?"
}
```

**Response**: `text/event-stream` stream

**Event Types**:
- `tool_call`: GLM-5.1 calls a tool
- `tool_result`: Tool execution result
- `reasoning`: GLM-5.1's reasoning
- `reflection`: Self-reflection checkpoint
- `brief_delta`: Brief being constructed
- `complete`: Research complete with final brief

**Example Event**:
```
event: trace
data: {"step_index": 1, "type": "tool_call", "tool_name": "fred_fetch", ...}
```

---

### Screener

```http
GET /api/v1/screener
```

Get ranked market dislocations (model probability vs market probability).

**Query Parameters**:
- `limit` (optional): Number of results (default: 50)
- `min_dislocation` (optional): Minimum gap threshold (default: 0.1)

**Response**:
```json
{
  "markets": [
    {
      "id": "kalshi-fed-rate-cut",
      "title": "Fed will cut rates by June",
      "platform": "kalshi",
      "market_prob": 0.35,
      "model_prob": 0.62,
      "dislocation": 0.27,
      "direction": "market_underpriced",
      "explanation": "Model suggests higher probability...",
      "confidence": 4
    }
  ],
  "total": 42
}
```

---

### Regime Snapshot

```http
GET /api/v1/regime
```

Get current macro regime across 5 dimensions.

**Response**:
```json
{
  "dimensions": {
    "growth": "EXPANSION",
    "inflation": "COOLING",
    "monetary": "RESTRICTIVE",
    "credit": "NORMAL",
    "labor": "SOFTENING"
  },
  "narrative": "Economy shows expansion but with tightening...",
  "updated_at": "2026-04-02T12:00:00Z"
}
```

---

### Markets

```http
GET /api/v1/markets
```

List all prediction markets.

**Query Parameters**:
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)
- `platform` (optional): Filter by platform (kalshi, polymarket)

**Response**:
```json
{
  "markets": [...],
  "page": 1,
  "limit": 20,
  "total": 156
}
```

---

### Market Detail

```http
GET /api/v1/markets/{market_id}
```

Get specific market details with history.

**Response**:
```json
{
  "id": "kalshi-recession-2026",
  "title": "US recession in 2026",
  "platform": "kalshi",
  "category": "economics",
  "resolution_date": "2027-01-01",
  "market_probability": 0.25,
  "volume_usd": 125000,
  "open_interest": 45000,
  "history": [
    {"date": "2026-03-01", "value": 0.22},
    {"date": "2026-03-15", "value": 0.25}
  ]
}
```

---

### Market Explanation

```http
GET /api/v1/markets/{market_id}/explain
```

Get AI-generated explanation for market dislocation.

**Response**:
```json
{
  "market_id": "kalshi-recession-2026",
  "explanation": "Based on FRED indicators...",
  "factors": [
    {"source": "fred", "indicator": "UNRATE", "impact": "bearish"},
    {"source": "fred", "indicator": "T10Y2Y", "impact": "neutral"}
  ],
  "confidence": 4
}
```

---

## WebSocket Endpoints

### Research WebSocket

```
ws://localhost:8000/api/v1/ws/research
```

Real-time bidirectional communication for GLM-5.1 agent streaming.

**Client Message Format**:
```json
{
  "type": "query",
  "question": "What is the recession probability?"
}
```

**Supported Client Types**:
- `ping`: Health check
- `query`: Start research query
- `status`: Get current status

**Server Message Types**:
- `connected`: Connection established
- `trace`: Trace step data
- `reflection_checkpoint`: Self-reflection event
- `complete`: Research complete
- `error`: Error occurred

**Example Flow**:
```
Client → {"type": "query", "question": "..."}
Server → {"type": "connected", "timestamp": "..."}
Server → {"type": "trace", "data": {...}}
Server → {"type": "reflection_checkpoint", "step": 5}
Server → {"type": "complete", "total_steps": 12}
```

---

### Broadcast WebSocket

```
ws://localhost:8000/api/v1/ws/broadcast
```

Multi-client broadcast channel for updates and collaboration.

**Features**:
- Real-time market data updates
- System announcements
- Collaborative research sharing

---

## Schemas

### ResearchBrief

```typescript
{
  question: string
  thesis: string
  bull_case: Array<{point: string, source_ref: string}>
  bear_case: Array<{point: string, source_ref: string}>
  key_risks: Array<{risk: string, source_ref: string}>
  confidence: number  // 1-5
  confidence_rationale: string
  methodology_summary?: string
  sources: Array<{
    type: "fred" | "edgar" | "news" | "market"
    id: string
    excerpt: string
  }>
  created_at: string
  trace_steps: number[]
}
```

### TraceStep

```typescript
{
  step_index: number
  type: "tool_call" | "tool_result" | "reasoning" | "reflection" | "brief_delta" | "complete" | "error"
  tool_name?: string
  tool_args?: object
  content?: string | object
  timestamp: string
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid API key |
| 429 | Rate Limited - Too many requests |
| 500 | Internal Server Error |
| 503 | Service Unavailable - GLM-5.1 API down |

---

## Rate Limits

- Demo mode: No rate limiting
- Live mode: 100 requests/minute per IP

---

## SDK Examples

### Python

```python
import httpx

async def query_research(question: str):
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/api/v1/research",
            json={"question": question},
            timeout=120.0
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    print(f"Step: {data['type']}")
```

### JavaScript

```javascript
async function queryResearch(question) {
  const response = await fetch('/api/v1/research', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question})
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const {done, value} = await reader.read();
    if (done) break;
    const text = decoder.decode(value);
    // Parse SSE events...
  }
}
```

### WebSocket (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/research');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'query',
    question: 'What is the recession probability?'
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message.type, message.data);
};
```

---

## OpenAPI Specification

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
