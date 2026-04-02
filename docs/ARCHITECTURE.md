# Meridian Architecture

GLM-5.1 Powered Agentic Financial Research Terminal

## System Overview

Meridian is a full-stack financial research platform that leverages GLM-5.1's agentic capabilities to automate complex macroeconomic analysis through multi-step reasoning, tool calling, and real-time trace streaming.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Terminal   │  │  Screener   │  │   Regime    │  │ Methodology │        │
│  │   Panel     │  │   Table     │  │  Dashboard  │  │    Page     │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │                │
│         └────────────────┴────────────────┴────────────────┘                │
│                                  │                                        │
│                         ┌────────▼────────┐                              │
│                         │ React Query /   │                              │
│                         │ WebSocket Hook  │                              │
│                         └────────┬────────┘                              │
└──────────────────────────────────┼────────────────────────────────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │      HTTP / WebSocket       │
                    └──────────────┬───────────────┘
                                   │
┌──────────────────────────────────▼────────────────────────────────────────┐
│                              API LAYER                                   │
├────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  Research    │  │  Screener    │  │    Regime    │  │    Markets  │ │
│  │  Router      │  │  Router      │  │   Router     │  │   Router    │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │
│         │                 │                 │                  │          │
│         └─────────────────┴─────────────────┴──────────────────┘         │
│                                  │                                        │
│                    ┌─────────────▼──────────────┐                         │
│                    │   WebSocket Manager       │                         │
│                    │   (Broadcast/Reconnect)   │                         │
│                    └─────────────┬──────────────┘                         │
└──────────────────────────────────┼────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼────────────────────────────────────────┐
│                            AGENT LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                      GLM-5.1 ReAct Agent                            │  │
│  │                                                                     │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │  │
│  │  │  Chain-of-   │  │   Self-      │  │   Long-      │             │  │
│  │  │   Thought    │  │ Reflection   │  │  Horizon     │             │  │
│  │  │  Reasoning   │  │  Checkpoint  │  │  Planning    │             │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │  │
│  │                                                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │                   Tool Registry (10 tools)                 │  │  │
│  │  │  fred_fetch | edgar_fetch | prediction_market_fetch       │  │  │
│  │  │  news_fetch | vector_search | compute_feature             │  │  │
│  │  │  correlation_analysis | composite_indicator              │  │  │
│  │  │  regime_transition_probability                           │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                                                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │                   Trace Emitter                             │  │  │
│  │  │  SSE / WebSocket streaming with 7 event types              │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼────────────────────────────────────────┐
│                           DATA LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │    FRED     │  │   EDGAR     │  │  Kalshi/    │  │    News     │      │
│  │  Client     │  │   Client    │  │ Polymarket  │  │   Client    │      │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │
│         │                │                │                │              │
│         └────────────────┴────────────────┴────────────────┘              │
│                                  │                                        │
│                    ┌─────────────▼──────────────┐                         │
│                    │    Feature Compute         │                         │
│                    │  (Yield Curve, Inflation,  │                         │
│                    │   Credit Stress, etc.)     │                         │
│                    └─────────────┬──────────────┘                         │
│                                  │                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                      │
│  │   DuckDB    │  │  Parquet    │  │ ChromaDB    │                      │
│  │ (Analytics) │  │  (Storage)  │  │ (Vectors)   │                      │
│  └─────────────┘  └─────────────┘  └─────────────┘                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Deep Dive

### 1. Frontend (Next.js 15)

**Location**: `apps/web/`

**Key Components**:
- **Terminal Panel**: Real-time query interface with SSE/WebSocket streaming
- **Research Panel**: Displays structured research briefs
- **Trace Panel**: Shows GLM-5.1's reasoning process
- **Regime Dashboard**: 5-dimension macro regime visualization
- **Screener Table**: Market dislocation rankings

**Technologies**:
- React 19 with TypeScript
- Tailwind CSS for styling
- Recharts for visualizations
- Custom WebSocket hooks

### 2. Backend API (FastAPI)

**Location**: `apps/api/`, `src/meridian/`

**Key Modules**:
- **Routers**: REST endpoints for research, screener, regime, markets
- **Agent**: GLM-5.1 ReAct loop implementation
- **Tools**: Type-safe tool registry with 10+ data sources
- **WebSocket**: Real-time bidirectional communication

**Architecture Patterns**:
- Dependency injection via `apps.api.deps`
- Pydantic v2 for request/response validation
- Async/await throughout
- SSE streaming for live updates

### 3. GLM-5.1 Agent

**Location**: `src/meridian/agent/`

**Core Components**:

#### ResearchAgent (`react.py`)
```python
class ResearchAgent:
    - __init__: Configure demo mode, tool executor
    - run: Main entry point for research queries
    - call_glm: Direct GLM-5.1 API calls
    - _run_live: Live mode with API calls
    - _run_demo: Demo mode with fixture traces
```

#### Tool Registry (`tools.py`)
```python
10 specialized tools:
- fred_fetch: Economic indicators
- fred_search: Series metadata search
- edgar_fetch: SEC filings
- prediction_market_fetch: Kalshi/Polymarket
- news_fetch: Financial news
- vector_search: Semantic memory
- compute_feature: Macro calculations
- correlation_analysis: Cross-series analysis
- composite_indicator: Normalized indices
- regime_transition_probability: Regime risk
```

#### Prompt Engineering (`prompt.py`)
- Chain-of-thought guidance
- Self-reflection instructions
- Citation enforcement
- JSON schema validation

### 4. Data Ingestion

**Location**: `src/meridian/ingestion/`

**Clients**:
- **FRED**: Federal Reserve Economic Data
- **EDGAR**: SEC filing database
- **Kalshi**: Prediction market exchange
- **Polymarket**: Prediction market exchange
- **News**: Curated financial news

**Pattern**: All clients support demo mode with deterministic fixtures.

### 5. Feature Engineering

**Location**: `src/meridian/features/`

**Indicators**:
- `yield_curve_slope`: 10Y-2Y Treasury spread
- `inflation_momentum`: 3-month annualized CPI change
- `credit_stress**: BAML high-yield spread z-score
- `monetary_regime`: Fed funds rate classification
- `recession_signal`: SAHM rule-based recession indicator
- `macro_regime_vector`: 5-dimension regime snapshot
- `cross_series_correlation`: Multi-series correlation analysis
- `composite_indicator`: Weighted multi-series index
- `regime_transition_probability`: Regime change risk estimator

---

## Data Flow

### Research Query Flow

```
1. User submits question via Terminal Panel
       ↓
2. POST /api/v1/research with question
       ↓
3. ResearchAgent.run(question) starts
       ↓
4. System prompt built with tool definitions
       ↓
5. GLM-5.1 called with initial message
       ↓
6. [LOOP] While tool_calls < max_tool_calls:
   a. Receive GLM-5.1 response
   b. If tool_call: Execute tool, emit trace, append to messages
   c. If reasoning: Emit trace as reasoning
   d. Every N steps: Self-reflection checkpoint
   e. If JSON brief found: Validate and emit complete
       ↓
7. Final ResearchBrief returned to frontend
       ↓
8. Brief rendered in ResearchPanel
```

### WebSocket Flow

```
1. Client connects to ws://.../ws/research
       ↓
2. Server sends "connected" message
       ↓
3. Client sends {"type": "query", "question": "..."}
       ↓
4. Server creates ResearchAgent for this connection
       ↓
5. [ASYNC] Stream research over WebSocket:
   - "trace" events for each step
   - "reflection_checkpoint" for self-evaluations
   - "complete" when done
       ↓
6. Connection stays open for follow-up queries
```

---

## GLM-5.1 Integration

### API Configuration

```python
async def call_glm(messages, tools):
    response = await httpx.AsyncClient().post(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        headers={"Authorization": f"Bearer {ZAI_API_KEY}"},
        json={
            "model": "glm-5.1",
            "messages": messages,
            "tools": tools,  # OpenAI-compatible tool format
            "max_tokens": 4096,
        }
    )
```

### Leveraged Capabilities

| GLM-5.1 Feature | Meridian Usage |
|-----------------|----------------|
| 200K Context | Read full 10-K + multiple economic series |
| Tool Calling | 10+ specialized tools with typed schemas |
| Long-Horizon | 25-step reasoning chains |
| JSON Mode | Structured briefs with validation |
| Streaming | Real-time trace emission |

---

## Schema Design

### TraceStep
```python
type: Literal["tool_call", "tool_result", "reasoning", 
              "reflection", "brief_delta", "complete", "error"]
step_index: int
tool_name?: str
tool_args?: dict
content?: str | dict
timestamp: str
```

### ResearchBrief
```python
question: str
thesis: str
bull_case: BriefPoint[]  # 3-5 items
bear_case: BriefPoint[]  # 2-5 items
key_risks: RiskPoint[]   # 2+ items
confidence: 1-5
confidence_rationale: str
methodology_summary?: str
sources: SourceRef[]
created_at: str
trace_steps: int[]
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Production                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    Vercel   │  │   Railway   │  │   Z.ai API  │        │
│  │  (Frontend) │  │  (Backend)  │  │  (GLM-5.1)  │        │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┘        │
│         │                │                                  │
│         └────────────────┘                                  │
│              HTTPS/WSS                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Performance Characteristics

- **Cold Start**: ~2s for agent initialization
- **First Token**: ~500ms after GLM-5.1 call
- **Tool Execution**: ~100-500ms per tool
- **Full Query**: ~10-30s for 10-20 tool calls
- **WebSocket Latency**: <50ms message delivery

---

## Security Considerations

1. **API Key Management**: `ZAI_API_KEY` stored in environment
2. **Demo Mode**: No API key required for testing
3. **Input Validation**: Pydantic schemas on all inputs
4. **CORS**: Configured for frontend origin
5. **Rate Limiting**: 100 req/min in live mode

---

## Testing Strategy

```
tests/
├── unit/          # Python unit tests (44 tests)
│   ├── agent/     # ReAct loop, tools
│   ├── api/       # Router endpoints
│   ├── features/  # Compute functions
│   ├── ingestion/ # Data source clients
│   └── vector/    # Vector store
├── e2e/           # Playwright E2E tests (5 tests)
│   ├── test_smoke.spec.ts
│   ├── test_research_flow.spec.ts
│   ├── test_screener.spec.ts
│   ├── test_regime.spec.ts
│   └── test_methodology.spec.ts
└── unit/web/      # React component tests (4 tests)
```

---

## Extension Points

1. **Add New Tools**: Extend `ToolRegistry` with new tool definitions
2. **Add Data Sources**: Create new client in `ingestion/`
3. **Add Visualizations**: Create chart components in `components/Charts/`
4. **Add API Endpoints**: Create new router in `apps/api/routers/`
5. **Custom Prompts**: Modify `SYSTEM_PROMPT_TEMPLATE` for specialized behavior

---

## Future Enhancements

- [ ] Multi-agent collaboration (specialist agents)
- [ ] Historical trace replay and analysis
- [ ] Custom alert creation
- [ ] Export to PDF/Excel
- [ ] Collaborative research sharing
- [ ] Mobile responsive design improvements
