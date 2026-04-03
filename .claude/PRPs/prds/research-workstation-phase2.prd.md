# Research Workstation - Phase 2 (Weeks 13-24)

## Problem Statement

Meridian Phase 1 built a compelling demo, but users can't use it for real research workflows. Each query starts fresh, sources are opaque labels, and reasoning traces are raw AI output. Users can't drill down into data or build on prior research, so they don't return for repeat sessions.

## Evidence

- Source refs like `[fred:T10Y2Y]` aren't clickable - users can't verify the data
- No way to ask "expand on point 2" or "compare with previous finding"
- Trace panel shows raw JSON for tool results, not human-readable summaries
- Demo trace shows single-query flow only
- Phase 1 user research assumption: needs validation through session analytics

## Proposed Solution

Transform Meridian from a one-query demo into a multi-query research workstation by: (1) adding conversation memory so follow-ups understand prior context, (2) making source_refs clickable links to underlying tool results, (3) improving trace readability with formatted summaries instead of raw JSON, and (4) enhancing brief structure with new section types for macro theses and ticker-plus-macro analysis.

## Key Hypothesis

We believe conversation-aware follow-ups and verifiable source lineage will increase session depth from 1 query to 3+ queries per session. We'll know we're right when average queries per session > 3 and source link click rate > 50%.

## What We're NOT Building

- Authentication/user accounts - out of scope, keeps demo mode simple
- Session persistence across refreshes - deferred to Phase 3
- Sharing/collaboration features - Phase 3 or later
- Real-time data streaming - not needed for research workflows
- Export functionality - nice to have but not blocking

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| Avg queries per session | > 3 | Session analytics (conversation length) |
| Source link click rate | > 50% | Click tracking on source_refs |
| Follow-up query rate | > 60% | Percentage of queries that reference prior context |
| Trace readability score | > 4/5 | User survey on trace clarity |
| Brief consistency | 100% | All briefs have required sections |

## Open Questions

- [ ] What's the optimal conversation window size? (3 queries? 5 queries?)
- [ ] Should context include full briefs or just theses?
- [ ] How to handle conflicting conclusions across queries?

---

## Users & Context

**Primary User**
- **Who**: Financial analysts, macro researchers, quantitative traders
- **Current behavior**: Run one query, read brief, close tab. Come back later for a fresh query.
- **Trigger**: Needs to explore a thesis from multiple angles or dig deeper into specific findings
- **Success state**: Runs 3-5 related queries in a session, clicks sources to verify data, exports findings

**Job to Be Done**
When researching a complex macro question, I want to ask follow-up questions that remember prior context, so I can build a complete view without restating everything.

**Non-Users**
- Social users (not a collaboration platform yet)
- Users requiring persistent cloud storage (deferred to Phase 3)
- Teams needing shared workspaces (deferred to Phase 3)

---

## Solution Detail

### Core Capabilities (MoSCoW)

| Priority | Capability | Rationale |
|----------|------------|-----------|
| Must | Conversation memory | Enables follow-up queries to reference prior research |
| Must | Clickable source_refs | Users need to verify claims by viewing underlying data |
| Must | Better trace formatting | Raw JSON is not human-readable |
| Must | Enhanced brief structure | Macro theses and ticker+macro need new section types |
| Should | Context-aware system prompt | Follow-ups should explicitly reference prior findings |
| Should | Conversation summary | Users should see what context is being used |
| Could | Export conversation | Nice for documentation but not blocking |
| Could | Visual conversation tree | Helpful but not required for MVP |
| Won't | Authentication | Out of scope for Phase 2 |
| Won't | Session persistence | Deferred to Phase 3 |

### MVP Scope

**Session Memory**: Store last 3 queries + briefs in session state
**Follow-up Handler**: Inject prior context into system prompt
**Source Linking**: Map source_ref → tool_result index, make clickable in UI
**Trace Formatting**: Human-readable summaries for tool results
**Brief Enhancements**: New sections for thesis breakdown, interpretation

### User Flow

**Critical Path - Multi-Query Research Session:**

1. User asks initial query: "What's the recession probability?"
2. Meridian runs research, displays trace + brief
3. User clicks source `[fred:T10Y2Y]` → sees yield curve data
4. User asks follow-up: "How does this compare to 2001?"
5. Meridian uses prior context, runs comparative analysis
6. User sees brief with comparison section
7. User asks: "What would change this view?"
8. Meridian identifies key risks from prior research
9. Session complete - user runs 3+ related queries

---

## Technical Approach

**Feasibility**: HIGH

**Architecture Notes**
- Conversation state stored in-memory (WebSocket session or frontend state)
- System prompt enhancement: inject prior theses and key findings
- Source linking: add `trace_step_index` to source_refs, link to tool_result
- Trace formatting: add `summary` field to tool_result type

**Dependencies**
- Modify `ResearchAgent.run()` to accept conversation history
- Add `Conversation` schema (list of prior queries + briefs)
- Update `build_system_prompt()` to include context
- Frontend: state management for conversation history
- Frontend: enhanced trace panel with clickable source links

**Technical Risks**

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Token bloat from conversation context | MEDIUM | Limit to last 3 briefs, use theses only |
| Source ref mapping complexity | MEDIUM | Enforce strict format, add validation |
| Trace formatting inconsistency | LOW | Use templates per tool type |
| Demo trace needs updates | LOW | Record new demo with follow-up example |

---

## Implementation Phases

| # | Phase | Description | Status | Parallel | Depends | PRP Plan |
|---|-------|-------------|--------|----------|---------|----------|
| 1 | Conversation Memory | Add session state for query history, context injection | in-progress | - | - | `.claude/PRPs/plans/conversation-memory-phase2.plan.md` |
| 2 | Source Lineage | Clickable source_refs linking to tool results | pending | with 3 | 1 | - |
| 3 | Trace Formatting | Human-readable summaries instead of raw JSON | pending | with 2 | 1 | - |
| 4 | Enhanced Briefs | New section types, better structure | pending | with 3 | 1 | - |
| 5 | Follow-up UX | Context indicators, conversation summary panel | pending | - | 2, 3, 4 | - |

### Phase Details

**Phase 1: Conversation Memory**
- **Goal**: Enable follow-up queries to understand prior research context
- **Scope**:
  - Add `Conversation` schema (query, brief, timestamp)
  - Modify `ResearchAgent` to accept conversation history
  - Inject prior context into system prompt
  - Frontend state for conversation history
- **Success signal**: Follow-up query references prior finding in response

**Phase 2: Source Lineage**
- **Goal**: Make every claim verifiable by linking to underlying data
- **Scope**:
  - Add `trace_step_index` to source_refs
  - Create mapping from source_ref to tool_result
  - Make source_refs clickable in brief panel
  - Show tool result preview on click
- **Success signal**: Clicking source_ref shows the actual data behind the claim

**Phase 3: Trace Formatting**
- **Goal**: Reasoning traces that read like a research narrative
- **Scope**:
  - Add `summary` field to tool_result type
  - Format tool results by type (tables for FRED, excerpts for filings)
  - Group related reasoning steps
  - Add section headers to trace
- **Success signal**: Users can understand trace without technical knowledge

**Phase 4: Enhanced Briefs**
- **Goal**: Support wider question types with better brief structure
- **Scope**:
  - Add `thesis_breakdown` section for multi-part analysis
  - Add `interpretation` section for probability questions
  - Add `comparison` section for relative analysis
  - Standardize section ordering
- **Success signal**: All question types produce appropriately structured briefs

**Phase 5: Follow-up UX**
- **Goal**: Clear visual indicators for context-aware queries
- **Scope**:
  - Show conversation summary panel
  - Highlight context used in follow-up responses
  - Allow users to manage context (remove items)
  - Visual distinction between initial vs follow-up queries
- **Success signal**: Users understand what context is being used

### Parallelism Notes

- Phases 2, 3, 4 can run in parallel after Phase 1 (conversation memory is foundational)
- Phase 5 depends on 2, 3, 4 being complete
- Each phase can be tested independently in demo mode

---

## Decisions Log

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| Conversation storage | In-memory session state | Database, localStorage | Keeps demo mode simple, no persistence needed yet |
| Context window | Last 3 briefs (theses only) | All history, last N tokens | Balances context richness with token limits |
| Source ref format | `tool_name:id:step_index` | URL-based, UUID | Backward compatible, easy to parse |
| Trace formatting | Tool-specific templates | LLM-generated summaries | Consistent, predictable, no extra API cost |

---

## Research Summary

**Market Context**
- Research terminals (Bloomberg, Refinitiv) have deep context handling
- AI research tools (Perplexity, Claude) show conversation is expected
- Source verification is standard in institutional research

**Technical Context**

**Files to Leverage:**
- `src/meridian/agent/react.py` - Add conversation parameter to `run()`
- `src/meridian/normalisation/schemas.py` - Add `Conversation`, `SourceRef enhancements`
- `src/meridian/agent/prompt.py` - Context injection logic
- `apps/web/components/Terminal/TracePanel.tsx` - Clickable sources
- `apps/web/components/Terminal/ResearchPanel.tsx` - Enhanced brief display

**Patterns to Follow:**
- Tool result structure already has `preview` array
- Source refs already use `tool_name:id` format
- Brief schema validation enforces structure

---

*Generated: 2026-04-02*
*Status: DRAFT - ready for implementation planning*
