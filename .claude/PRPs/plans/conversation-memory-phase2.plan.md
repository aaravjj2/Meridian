# Plan: Conversation Memory (Phase 2, Week 13-24)

## Summary
Add session-based conversation memory to Meridian, enabling follow-up queries to understand prior research context. The frontend stores the last 3 queries and briefs, sending them with each research request. The backend injects prior context into the system prompt, allowing GLM-5.1 to reference previous findings in its responses.

## User Story
As a financial researcher,
I want follow-up queries to remember my prior research questions and findings,
So that I can explore a thesis from multiple angles without repeating context.

## Problem → Solution
Each query currently starts fresh with no memory of prior research → Store last 3 query/brief pairs in frontend state, inject prior theses into system prompt for context-aware follow-ups

## Metadata
- **Complexity**: Medium (6-8 files, ~300 lines)
- **Source PRD**: `.claude/PRPs/prds/research-workstation-phase2.prd.md`
- **PRD Phase**: Phase 1 - Conversation Memory
- **Estimated Files**: 7

---

## UX Design

### Before
```
┌─────────────────────────────────────────────────────────────┐
│  User: "What's the recession probability?"                  │
│  → Meridian runs research, displays brief                    │
│  → User: "How does this compare to 2001?"                   │
│  → Meridian runs FRESH research, no reference to prior      │
│  → User frustrated, must restate context                    │
└─────────────────────────────────────────────────────────────┘
```

### After
```
┌─────────────────────────────────────────────────────────────┐
│  User: "What's the recession probability?"                  │
│  → Meridian runs research, displays brief                    │
│  → [Stored in conversation: Q1 + Brief1]                    │
│  → User: "How does this compare to 2001?"                   │
│  → [Sent: Q2 + {Q1, Brief1}]                                │
│  → System prompt: "Prior research found recession prob X%"  │
│  → Response: "Building on our analysis..."                  │
│  → Brief includes comparison section                        │
└─────────────────────────────────────────────────────────────┘
```

### Interaction Changes
| Touchpoint | Before | After | Notes |
|---|---|---|---|
| Query input | Single query, no context | Multi-query session with context | Last 3 queries stored |
| System prompt | Static, no history | Dynamic with prior theses | Injected via build_system_prompt |
| API request | {question, mode} | {question, mode, conversation?} | Optional conversation param |
| Brief display | Single result | Shows conversation context | Visual indicator |

---

## Mandatory Reading

Files that MUST be read before implementing:

| Priority | File | Lines | Why |
|---|---|---|---|
| P0 (critical) | `src/meridian/normalisation/schemas.py` | 1-105 | Schema patterns, add Conversation types |
| P0 (critical) | `src/meridian/agent/react.py` | 96-105, 226-270 | run() method, messages array structure |
| P0 (critical) | `src/meridian/agent/prompt.py` | 109-149 | build_system_prompt(), add context injection |
| P1 (important) | `apps/api/routers/research.py` | 16-24, 90-104 | ResearchRequest model, stream_events() |
| P1 (important) | `apps/web/app/page.tsx` | 166-205 | useState patterns, runQuery() function |
| P2 (reference) | `data/fixtures/traces/demo_trace.json` | all | Update with conversation example |

## External Documentation

| Topic | Source | Key Takeaway |
|---|---|---|
| Pydantic BaseModel | Pydantic docs | Use Field() for validation, @field_validator for custom checks |
| FastAPI optional fields | FastAPI docs | Use `field: str | None = None` for optional params |
| React useState patterns | React docs | Use functional updates `setPrev(prev => ...)` for state based on previous |

---

## Patterns to Mirror

Code patterns discovered in the codebase. Follow these exactly.

### NAMING_CONVENTION
// SOURCE: src/meridian/normalisation/schemas.py:57-69
// Pydantic models: PascalCase, snake_case fields
class ResearchBrief(BaseModel):
    question: str
    thesis: str
    bull_case: list[BriefPoint]

### ERROR_HANDLING
// SOURCE: src/meridian/agent/react.py:242-248
// Yield error TraceStep on exception
except Exception as exc:
    yield TraceStep(
        step_index=step_index,
        type="error",
        content=f"GLM call failed: {exc}",
        timestamp=_iso_now(),
    )

### LOGGING_PATTERN
// SOURCE: src/meridian/agent/react.py:20
logger = logging.getLogger(__name__)
// Use logger.error(), logger.warning(), logger.info()

### PYDANTIC_FIELD_VALIDATION
// SOURCE: src/meridian/normalisation/schemas.py:31-36
@field_validator("source_ref")
@classmethod
def ensure_source_ref(cls, value: str) -> str:
    if ":" not in value:
        raise ValueError("source_ref must follow tool_name:id format")
    return value

### FRONTEND_STATE_PATTERN
// SOURCE: apps/web/app/page.tsx:167-172
const [traceSteps, setTraceSteps] = useState<TraceEvent[]>([])
const [brief, setBrief] = useState<ResearchBrief | null>(null)
const [running, setRunning] = useState(false)

### FUNCTIONAL_STATE_UPDATE
// SOURCE: apps/web/app/page.tsx:184
setTraceSteps((prev) => [...prev, step])

### FRONTEND_TYPES
// SOURCE: apps/web/components/Terminal/types.ts:37-48
export type ResearchBrief = {
    question: string
    thesis: string
    bull_case: BriefPoint[]
    bear_case: BriefPoint[]
    key_risks: RiskPoint[]
    confidence: number
    confidence_rationale: string
    sources: SourceItem[]
    created_at: string
    trace_steps: number[]
}

---

## Files to Change

| File | Action | Justification |
|---|---|---|
| `src/meridian/normalisation/schemas.py` | UPDATE | Add Conversation, ConversationTurn models |
| `src/meridian/agent/react.py` | UPDATE | Add conversation parameter to run(), inject into messages |
| `src/meridian/agent/prompt.py` | UPDATE | Add context injection to build_system_prompt() |
| `apps/api/routers/research.py` | UPDATE | Add conversation field to ResearchRequest |
| `apps/web/components/Terminal/types.ts` | UPDATE | Add ConversationTurn type |
| `apps/web/app/page.tsx` | UPDATE | Add conversation state, pass with queries |
| `data/fixtures/traces/demo_trace.json` | UPDATE | Add conversation example (optional) |

## NOT Building

- Session persistence across refreshes (deferred to Phase 3)
- Conversation editing/removal UI (deferred to Phase 5)
- Server-side session storage (out of scope, stateless design)
- Context window smart summarization (simple truncation: last 3 only)

---

## Step-by-Step Tasks

### Task 1: Add Conversation Schemas
- **ACTION**: Add ConversationTurn and Conversation models to schemas.py
- **IMPLEMENT**:
  ```python
  # Add to src/meridian/normalisation/schemas.py

  class ConversationTurn(BaseModel):
      """A single query and its resulting brief in the conversation history."""
      query: str
      thesis: str
      timestamp: str
      brief_summary: str  # Just thesis + confidence for context

      @field_validator("timestamp")
      @classmethod
      def validate_timestamp(cls, value: str) -> str:
          datetime.fromisoformat(value.replace("Z", "+00:00"))
          return value


  class Conversation(BaseModel):
      """Conversation history for context-aware follow-up queries."""
      turns: list[ConversationTurn] = Field(default_factory=list, max_length=3)

      @model_validator(mode="after")
      def truncate_to_max_three(self) -> "Conversation":
          """Keep only the 3 most recent turns to manage context window."""
          if len(self.turns) > 3:
              self.turns = self.turns[-3:]
          return self
  ```
- **MIRROR**: Pydantic BaseModel pattern from schemas.py:57-69
- **IMPORTS**: No new imports needed (uses existing typing, pydantic)
- **GOTCHA**: Use max_length in Field() to enforce 3-turn limit at validation level
- **VALIDATE**: Run `python -c "from meridian.normalisation.schemas import Conversation; print(Conversation().model_dump())"` — should succeed

### Task 2: Modify ResearchAgent.run() to Accept Conversation
- **ACTION**: Add optional conversation parameter, inject into messages
- **IMPLEMENT**:
  ```python
  # Update src/meridian/agent/react.py

  from meridian.normalisation.schemas import Conversation  # Add import

  class ResearchAgent:
      # ... existing __init__ ...

      async def run(
          self,
          question: str,
          mode: str | None = None,
          conversation: Conversation | None = None,  # NEW PARAMETER
      ) -> AsyncGenerator[TraceStep, None]:
          """Run research with optional conversation context."""
          resolved_mode = (mode or ("demo" if self.demo_mode else "live")).strip().lower()
          if resolved_mode == "demo":
              async for step in self._run_demo(question, conversation):
                  yield step
              return

          async for step in self._run_live(question, conversation):
              yield step

      async def _run_live(
          self,
          question: str,
          conversation: Conversation | None = None,  # NEW PARAMETER
      ) -> AsyncGenerator[TraceStep, None]:
          """Run live research with conversation context."""
          start = time.perf_counter()

          # Build messages with conversation context
          messages: list[dict[str, Any]] = [
              {
                  "role": "system",
                  "content": build_system_prompt(
                      self.tools.definitions,
                      conversation=conversation  # PASS CONTEXT
                  ),
              },
              {"role": "user", "content": question},
          ]

          # If there's conversation history, add it as context messages
          if conversation and conversation.turns:
              for turn in conversation.turns:
                  messages.append({
                      "role": "user",
                      "content": f"[Prior query] {turn.query}",
                  })
                  messages.append({
                      "role": "assistant",
                      "content": f"[Prior response] {turn.thesis}",
                  })

          tool_schema = self.tools.to_openai_tools()
          # ... rest of existing logic unchanged ...

      async def _run_demo(
          self,
          question: str,
          conversation: Conversation | None = None,  # NEW PARAMETER (unused in demo)
      ) -> AsyncGenerator[TraceStep, None]:
          """Run demo research - conversation ignored for now."""
          # ... existing demo logic unchanged ...
  ```
- **MIRROR**: Method signature pattern from react.py:96-104
- **IMPORTS**: Add `from meridian.normalisation.schemas import Conversation`
- **GOTCHA**: Keep demo mode simple - ignore conversation for now, update demo trace later
- **VALIDATE**: Run `python -c "from meridian.agent.react import ResearchAgent; import inspect; sig = inspect.signature(ResearchAgent.run); print('conversation' in sig.parameters)"` — should return True

### Task 3: Update build_system_prompt() to Inject Context
- **ACTION**: Add conversation parameter, inject prior research summary
- **IMPLEMENT**:
  ```python
  # Update src/meridian/agent/prompt.py

  from meridian.normalisation.schemas import Conversation  # Add import

  def build_system_prompt(
      tools: list[ToolDefinition],
      conversation: Conversation | None = None,  # NEW PARAMETER
  ) -> str:
      """Build system prompt with optional conversation context."""
      tool_lines: list[str] = []
      for tool in tool:
          tool_lines.append(f"- {tool.name}: {tool.description}")
          tool_lines.append(f"  parameters: {json.dumps(tool.input_model.model_json_schema(), sort_keys=True)}")
      tool_descriptions = "\n".join(tool_lines)
      prompt = SYSTEM_PROMPT_TEMPLATE.replace("[TOOL_DESCRIPTIONS_INJECTED_HERE]", tool_descriptions)

      # Inject conversation context if provided
      if conversation and conversation.turns:
          context_lines = ["\n# CONVERSATION CONTEXT\n"]
          context_lines.append("The user has asked these prior questions in this session:\n")
          for i, turn in enumerate(conversation.turns, 1):
              context_lines.append(f"{i}. Q: {turn.query}")
              context_lines.append(f"   A: {turn.thesis}\n")
          context_lines.append("When responding, reference this prior research where relevant.")
          context_lines.append("Do NOT repeat analysis already covered unless explicitly asked.\n")

          # Insert context after TOOLS section
          prompt = prompt.replace(
              "# RESEARCH PROCESS (ReAct LOOP)",
              f"{context_lines.join('')}\n\n# RESEARCH PROCESS (ReAct LOOP)"
          )

      return prompt
  ```
- **MIRROR**: String replacement pattern from prompt.py:109-115
- **IMPORTS**: Add `from meridian.normalisation.schemas import Conversation`
- **GOTCHA**: Insert context in middle of prompt, after tools, before process section
- **VALIDATE**: Run `python -c "from meridian.agent.prompt import build_system_prompt; from meridian.normalisation.schemas import Conversation; c = Conversation(turns=[]); print(build_system_prompt([], c))"` — should not error

### Task 4: Update API Request Model
- **ACTION**: Add optional conversation field to ResearchRequest
- **IMPLEMENT**:
  ```python
  # Update apps/api/routers/research.py

  from meridian.normalisation.schemas import Conversation  # Add import

  class ResearchRequest(BaseModel):
      question: str = Field(min_length=3)
      mode: str = "demo"
      conversation: Conversation | None = Field(default=None, description="Prior conversation for context")
  ```
- **MIRROR**: Pydantic Field pattern from research.py:19-21
- **IMPORTS**: Add `from meridian.normalisation.schemas import Conversation`
- **GOTCHA**: Use Field(default=None) for optional, add description for docs
- **VALIDATE**: Run `curl -X POST http://localhost:8000/api/v1/research -H "Content-Type: application/json" -d '{"question":"test","conversation":{"turns":[]}}'` — should accept conversation field

### Task 5: Pass Conversation to Agent in API
- **ACTION**: Update stream_events() to pass conversation to agent.run()
- **IMPLEMENT**:
  ```python
  # Update apps/api/routers/research.py, modify stream_events() function

  @router.post("/research")
  async def post_research(request: ResearchRequest) -> StreamingResponse:
      async def stream_events() -> AsyncGenerator[str, None]:
          agent = ResearchAgent(demo_mode=request.mode == "demo")
          complete_emitted = False
          last_step = -1

          try:
              async with asyncio.timeout(120):
                  async for trace_step in agent.run(
                      question=request.question,
                      mode=request.mode,
                      conversation=request.conversation  # PASS CONVERSATION
                  ):
                      last_step = max(last_step, trace_step.step_index)
                      event = _trace_to_event(trace_step)
                      if event["type"] == "complete":
                          complete_emitted = True
                      yield f"data: {json.dumps(event)}\n\n"
          # ... rest unchanged ...
  ```
- **MIRROR**: agent.run() call pattern from research.py:93-104
- **IMPORTS**: No new imports
- **GOTCHA**: Ensure conversation is passed as keyword argument
- **VALIDATE**: Run integration test with conversation in request body

### Task 6: Add Frontend Types for Conversation
- **ACTION**: Add ConversationTurn type to types.ts
- **IMPLEMENT**:
  ```typescript
  // Add to apps/web/components/Terminal/types.ts

  export type ConversationTurn = {
    query: string
    thesis: string
    timestamp: string
    brief_summary: string
  }

  export type Conversation = {
    turns: ConversationTurn[]
  }
  ```
- **MIRROR**: Type definition pattern from types.ts:21-48
- **IMPORTS**: No new imports
- **GOTCHA**: Match Python schema exactly for type safety
- **VALIDATE**: Run `npm run tsc` — should have no type errors

### Task 7: Add Frontend Conversation State
- **ACTION**: Add conversation state to page.tsx, manage last 3 turns
- **IMPLEMENT**:
  ```typescript
  // Update apps/web/app/page.tsx

  import type { Conversation, ConversationTurn } from '@/components/Terminal/types'

  export default function HomePage() {
    const [traceSteps, setTraceSteps] = useState<TraceEvent[]>([])
    const [briefState, setBriefState] = useState<'empty' | 'loading' | 'error' | 'complete'>('empty')
    const [brief, setBrief] = useState<ResearchBrief | null>(null)
    const [error, setError] = useState('')
    const [running, setRunning] = useState(false)
    const [lastQuery, setLastQuery] = useState('')
    const [conversation, setConversation] = useState<Conversation>({ turns: [] })  // NEW

    async function runQuery(question: string) {
      setLastQuery(question)
      setRunning(true)
      setError('')
      setBrief(null)
      setTraceSteps([])
      setBriefState('loading')

      try {
        await streamResearch(question, (step) => {
          setTraceSteps((prev) => [...prev, step])

          if (step.type === 'complete' && step.brief) {
            const completedBrief = step.brief
            setBrief(completedBrief)
            setBriefState('complete')

            // Add to conversation after completion
            setConversation((prev) => {
              const newTurn: ConversationTurn = {
                query: question,
                thesis: completedBrief.thesis,
                timestamp: completedBrief.created_at,
                brief_summary: `${completedBrief.thesis} (Confidence: ${completedBrief.confidence}/5)`,
              }
              const newTurns = [...prev.turns, newTurn]
              // Keep only last 3
              const trimmedTurns = newTurns.slice(-3)
              return { turns: trimmedTurns }
            })
          }
          if (step.type === 'error') {
            setError(step.message ?? 'Research failed')
            setBriefState('error')
          }
        })
      } catch {
        // ... fallback logic unchanged ...
      } finally {
        setRunning(false)
      }
    }

    // Pass conversation to streamResearch
    async function streamResearch(
      question: string,
      onEvent: (step: TraceEvent) => void,
      conversation?: Conversation  // NEW PARAM
    ): Promise<void> {
      const response = await fetch('/api/v1/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          mode: 'demo',
          conversation: conversation || undefined  // PASS CONVERSATION
        }),
      })
      // ... rest unchanged ...
    }

    // Update runQuery to pass conversation
    async function runQuery(question: string) {
      // ... existing setup ...

      try {
        await streamResearch(question, (step) => {
          // ... existing event handler ...
        }, conversation)  // PASS CONVERSATION
      } catch {
        // ... fallback ...
      }
    }
  ```
- **MIRROR**: useState pattern from page.tsx:167-172, functional update from Task 1
- **IMPORTS**: Add `import type { Conversation, ConversationTurn } from '@/components/Terminal/types'`
- **GOTCHA**: Use slice(-3) to keep last 3 turns; convert undefined to not send in JSON
- **VALIDATE**: Run 4 queries in session, verify conversation has 3 turns max

### Task 8: Add Unit Tests for Conversation Schema
- **ACTION**: Add tests for Conversation validation and truncation
- **IMPLEMENT**:
  ```python
  # Create tests/unit/normalisation/test_conversation.py

  import pytest
  from meridian.normalisation.schemas import Conversation, ConversationTurn
  from datetime import UTC, datetime


  def test_conversation_turn_valid():
      """Test a valid conversation turn."""
      turn = ConversationTurn(
          query="What is the recession probability?",
          thesis="Recession probability is 25% based on yield curve.",
          timestamp="2026-04-02T00:00:00Z",
          brief_summary="Recession probability is 25% (Confidence: 3/5)",
      )
      assert turn.query == "What is the recession probability?"
      assert turn.thesis.startswith("Recession probability")


  def test_conversation_turn_invalid_timestamp():
      """Test conversation turn rejects invalid timestamp."""
      with pytest.raises(ValueError):
          ConversationTurn(
              query="Test",
              thesis="Test",
              timestamp="invalid-timestamp",
              brief_summary="Test",
          )


  def test_conversation_empty():
      """Test empty conversation is valid."""
      conv = Conversation()
      assert conv.turns == []


  def test_conversation_truncates_to_three():
      """Test conversation truncates to max 3 turns."""
      turns_data = [
          {
              "query": f"Query {i}",
              "thesis": f"Thesis {i}",
              "timestamp": datetime.now(UTC).isoformat(),
              "brief_summary": f"Summary {i}",
          }
          for i in range(5)
      ]

      conv = Conversation(turns=turns_data)
      assert len(conv.turns) == 3
      assert conv.turns[0].query == "Query 2"  # Last 3 kept
      assert conv.turns[2].query == "Query 4"


  def test_conversation_exactly_three():
      """Test conversation with exactly 3 turns is unchanged."""
      turns_data = [
          {
              "query": f"Query {i}",
              "thesis": f"Thesis {i}",
              "timestamp": datetime.now(UTC).isoformat(),
              "brief_summary": f"Summary {i}",
          }
          for i in range(3)
      ]

      conv = Conversation(turns=turns_data)
      assert len(conv.turns) == 3
  ```
- **MIRROR**: Test pattern from tests/unit/normalisation/test_normalise.py
- **IMPORTS**: `from meridian.normalisation.schemas import Conversation, ConversationTurn`
- **GOTCHA**: Use pytest.raises for validation error testing
- **VALIDATE**: Run `python -m pytest tests/unit/normalisation/test_conversation.py -v` — all tests pass

---

## Testing Strategy

### Unit Tests

| Test | Input | Expected Output | Edge Case? |
|---|---|---|---|
| Conversation validation | 5 turns | Truncated to 3 | Yes |
| Conversation empty | [] | Empty conversation | Yes |
| ConversationTurn timestamp | invalid ISO format | ValueError | Yes |
| build_system_prompt with conversation | 2 turns | Prompt includes context section | No |
| build_system_prompt without conversation | None | Prompt unchanged | No |
| ResearchAgent.run() with conversation | query + conversation | Messages include prior context | No |
| ResearchAgent.run() without conversation | query + None | Messages unchanged | No |
| Frontend conversation state | 4 queries | State has 3 turns | Yes |

### Edge Cases Checklist
- [ ] Empty conversation (no prior queries)
- [ ] Single turn conversation
- [ ] Exactly 3 turns (boundary)
- [ ] More than 3 turns (truncation)
- [ ] Invalid timestamp format
- [ ] Conversation with None thesis
- [ ] Concurrent queries (race condition)

---

## Validation Commands

### Static Analysis
```bash
# Run Python type checker
cd /home/aarav/Aarav/Meridian && python -m py_compile src/meridian/normalisation/schemas.py src/meridian/agent/react.py src/meridian/agent/prompt.py apps/api/routers/research.py
```
EXPECT: No SyntaxError or TypeError

```bash
# Run TypeScript type checker
cd /home/aarav/Aarav/Meridian/apps/web && npm run tsc
```
EXPECT: No type errors

### Unit Tests
```bash
# Run backend tests for conversation
python -m pytest tests/unit/normalisation/test_conversation.py -v
```
EXPECT: All tests pass

```bash
# Run all backend tests
python -m pytest -q
```
EXPECT: All tests pass, no regressions

```bash
# Run frontend unit tests
cd apps/web && npm run test:unit
```
EXPECT: All tests pass

### Full Test Suite
```bash
# Run complete test suite
python -m pytest -q && cd apps/web && npm run test:unit && npx playwright test
```
EXPECT: No regressions

### Manual Validation
- [ ] Start dev server: `npm run dev`
- [ ] Run query 1: "What's the recession probability?"
- [ ] Verify brief displays
- [ ] Run query 2: "Expand on point 2"
- [ ] Verify response references prior findings
- [ ] Run query 3, 4, 5 to test truncation
- [ ] Check browser console for errors
- [ ] Verify conversation state updates (check React DevTools)

---

## Acceptance Criteria
- [ ] All tasks completed
- [ ] All validation commands pass
- [ ] Tests written and passing (8 new tests for conversation)
- [ ] No type errors (Python or TypeScript)
- [ ] No lint errors
- [ ] Follow-up queries reference prior research
- [ ] Conversation truncates to 3 turns

## Completion Checklist
- [ ] Code follows discovered patterns (Pydantic, FastAPI, React hooks)
- [ ] Error handling matches codebase style (yield TraceStep errors)
- [ ] Logging follows codebase conventions (logger = logging.getLogger)
- [ ] Tests follow test patterns (pytest, functional updates)
- [ ] No hardcoded values (3-turn limit is in schema validator)
- [ ] Documentation updated (if needed)
- [ ] No unnecessary scope additions (no persistence, no UI editing)
- [ ] Self-contained — no questions needed during implementation

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Token bloat from conversation context | MEDIUM | API costs increase | Enforced 3-turn limit, theses only (not full briefs) |
| Demo trace not updated | LOW | Demo mode shows no context | Acceptable for Phase 1, update in Phase 2 |
| Frontend state lost on refresh | LOW | Poor UX | Acceptable (deferred to Phase 3) |
| Concurrent query race condition | LOW | State corruption | Functional updates prevent races |

## Notes
- Conversation is intentionally kept in-memory on frontend (no persistence)
- Demo mode ignores conversation for now — update demo trace in future phase
- Context injection uses simple prompt engineering (no smart summarization yet)
- 3-turn limit is enforced at both schema (max_length=3) and model_validator level
- Frontend uses functional state updates to prevent race conditions
- API field is optional — existing clients work without changes
