# Meridian

Meridian is an agentic financial research terminal built for the Z.ai GLM-5.1 Challenge. A user asks a macro question, then watches GLM-5.1 run a multi-step tool loop over FRED, prediction markets, EDGAR, and news while the reasoning trace streams live in a dedicated panel. The result is a structured, cited brief plus a dislocation screener that ranks market-vs-model probability gaps.

## Reasoning Trace Preview

- TOUR video: [artifacts/TOUR.webm](artifacts/TOUR.webm)

## Why GLM-5.1

GLM-5.1 is the only open-source model with a 200K context window and agentic tool-calling capable of reading a full 10-K filing and 20 FRED series in one reasoning pass. Meridian is the terminal that makes this usable.

Meridian uses GLM-5.1 in a ReAct-style loop with typed tools and trace emission for each step:

- `tool_call`
- `tool_result`
- `reasoning`
- `brief_delta`
- `complete`

Every final brief claim is citation-backed through `source_ref` enforcement in schema validation.

## 5-Command Quick Start (Demo)

1. `git clone <repo-url> && cd meridian`
2. `python -m venv .venv && . .venv/bin/activate`
3. `pip install -e .[dev]`
4. `npm install`
5. `MERIDIAN_MODE=demo npm run dev`

Open `http://localhost:3000` and run a research query.

## Architecture

- Frontend: Next.js 15 + TypeScript + Tailwind + Recharts
- Backend: FastAPI + Pydantic v2 + httpx + structlog
- Agent: GLM-5.1 ReAct loop with typed tool registry
- Data: deterministic demo fixtures under `data/fixtures`
- Scoring: fair-value model + dislocation ranking pipeline
- Storage: DuckDB/Parquet + local ChromaDB vector store

### Flow

1. User submits question in Research Terminal.
2. Backend streams SSE trace events from `POST /api/v1/research`.
3. Frontend appends trace steps in real-time and renders brief sections.
4. Screener page ranks contracts by `abs(model_prob - market_prob)`.

## API Reference

- `GET /api/v1/health` -> service status, mode, version
- `GET /api/v1/metadata` -> version, model, demo flag, data sources
- `POST /api/v1/research` -> SSE stream of trace + complete brief
- `GET /api/v1/screener` -> ranked mispricing contracts
- `GET /api/v1/regime` -> 5-dimension macro regime snapshot
- `GET /api/v1/markets` -> paginated canonical markets
- `GET /api/v1/markets/{market_id}` -> market detail with history
- `GET /api/v1/markets/{market_id}/explain` -> mispricing explanation

## Test Gates

- `python -m pytest -q`
- `npm run tsc`
- `npm run vitest`
- `npm run playwright`

## Disclaimer

Meridian is a research tool for informational purposes only and is not investment advice, legal advice, or a solicitation to trade.
