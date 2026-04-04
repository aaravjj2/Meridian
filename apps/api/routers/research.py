from __future__ import annotations

import asyncio
import json
import re
import uuid
from datetime import UTC, datetime
from typing import Any, AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from meridian.agent.react import ResearchAgent
from meridian.normalisation.schemas import ResearchBrief, TraceStep
from meridian.workspace.session_store import get_session_store


router = APIRouter(tags=["research"])


class ResearchRequest(BaseModel):
    question: str = Field(min_length=3)
    mode: str = "demo"
    session_id: str | None = Field(default=None, min_length=4, max_length=64)


SESSION_CACHE_MAX = 64
SESSION_CONTEXT: dict[str, dict[str, Any]] = {}


def _iso_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _compact_preview(payload: Any) -> list[list[Any]]:
    if isinstance(payload, dict) and "preview" in payload:
        payload = payload["preview"]
    if isinstance(payload, list):
        preview: list[list[Any]] = []
        for row in payload[:3]:
            if isinstance(row, dict):
                preview.append(list(row.values())[:2])
            elif isinstance(row, list):
                preview.append(row[:2])
            else:
                preview.append([row])
        return preview
    return []


def _resolve_session_id(value: str | None) -> str:
    if not value:
        return f"sess-{uuid.uuid4().hex[:12]}"
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-")
    if len(cleaned) < 4:
        return f"sess-{uuid.uuid4().hex[:12]}"
    return cleaned[:64]


def _update_session_context(session_id: str, brief_payload: dict[str, Any], question: str) -> None:
    sources = brief_payload.get("sources", [])
    key_sources = []
    for source in sources[:4]:
        source_type = source.get("type")
        source_id = source.get("id")
        if source_type and source_id:
            key_sources.append(f"{source_type}:{source_id}")

    SESSION_CONTEXT[session_id] = {
        "last_question": question,
        "last_thesis": brief_payload.get("thesis", ""),
        "last_query_class": brief_payload.get("query_class"),
        "key_sources": key_sources,
        "updated_at": _iso_now(),
    }

    # Keep cache bounded to avoid unbounded in-memory growth.
    if len(SESSION_CONTEXT) > SESSION_CACHE_MAX:
        oldest_id = next(iter(SESSION_CONTEXT))
        if oldest_id != session_id:
            SESSION_CONTEXT.pop(oldest_id, None)


def _restore_context_from_saved_session(session_id: str) -> dict[str, Any] | None:
    store = get_session_store()
    saved = store.get_latest_for_session(session_id)
    if saved is None:
        return None

    key_sources = [f"{source.type}:{source.id}" for source in saved.brief.sources[:4]]
    return {
        "last_question": saved.question,
        "last_thesis": saved.brief.thesis,
        "last_query_class": saved.brief.query_class,
        "key_sources": key_sources,
        "updated_at": _iso_now(),
        "restored_from_saved_session": saved.id,
    }


def _trace_to_event(step: TraceStep) -> dict[str, Any]:
    event = {
        "type": step.type,
        "step": step.step_index,
        "ts": step.timestamp,
    }

    if step.type == "tool_call":
        event.update(
            {
                "tool": step.tool_name,
                "args": step.tool_args or {},
            }
        )
    elif step.type == "tool_result":
        event.update(
            {
                "tool": step.tool_name,
                "preview": _compact_preview(step.content),
            }
        )
    elif step.type == "reasoning":
        event.update({"text": str(step.content or "")})
    elif step.type == "brief_delta":
        content = step.content if isinstance(step.content, dict) else {}
        event.update(
            {
                "section": content.get("section", "unknown"),
                "text": content.get("text", ""),
            }
        )
    elif step.type == "complete":
        content = step.content if isinstance(step.content, dict) else {}
        brief = content.get("brief", content)
        event.update(
            {
                "brief": brief,
                "duration_ms": int(content.get("duration_ms", 0)),
                "query_class": content.get("query_class"),
                "session_context_used": bool(content.get("session_context_used", False)),
            }
        )
    elif step.type == "error":
        event.update({"message": str(step.content or "Unknown error")})

    return event


@router.post("/research")
async def post_research(request: ResearchRequest) -> StreamingResponse:
    async def stream_events() -> AsyncGenerator[str, None]:
        session_id = _resolve_session_id(request.session_id)
        prior_context = SESSION_CONTEXT.get(session_id)
        if prior_context is None and request.session_id:
            restored_context = _restore_context_from_saved_session(session_id)
            if restored_context is not None:
                prior_context = restored_context
                SESSION_CONTEXT[session_id] = restored_context

        agent = ResearchAgent(demo_mode=request.mode == "demo")
        complete_emitted = False
        last_step = -1

        try:
            async with asyncio.timeout(120):
                async for trace_step in agent.run_with_context(
                    question=request.question,
                    mode=request.mode,
                    session_context=prior_context,
                ):
                    last_step = max(last_step, trace_step.step_index)
                    event = _trace_to_event(trace_step)
                    event["session_id"] = session_id
                    event["followup"] = prior_context is not None
                    if event["type"] == "complete":
                        complete_emitted = True
                        brief_payload = event.get("brief")
                        if isinstance(brief_payload, dict):
                            _update_session_context(session_id=session_id, brief_payload=brief_payload, question=request.question)
                    yield f"data: {json.dumps(event)}\n\n"
        except TimeoutError:
            error_step = last_step + 1
            timeout_event = {
                "type": "error",
                "step": error_step,
                "message": "research stream exceeded 120s timeout",
                "ts": _iso_now(),
                "session_id": session_id,
                "followup": prior_context is not None,
            }
            yield f"data: {json.dumps(timeout_event)}\n\n"
            last_step = error_step
        except Exception as exc:  # pragma: no cover - defensive runtime path
            error_step = last_step + 1
            error_event = {
                "type": "error",
                "step": error_step,
                "message": str(exc),
                "ts": _iso_now(),
                "session_id": session_id,
                "followup": prior_context is not None,
            }
            yield f"data: {json.dumps(error_event)}\n\n"
            last_step = error_step

        if not complete_emitted:
            completion = {
                "type": "complete",
                "step": last_step + 1,
                "brief": ResearchBrief(
                    question=request.question,
                    query_class="macro_outlook",
                    follow_up_context=(
                        f"Follow-up to prior question: {prior_context.get('last_question')}"
                        if prior_context and prior_context.get("last_question")
                        else None
                    ),
                    thesis="Research stream terminated with an error state.",
                    bull_case=[
                        {
                            "claim_id": "bull-1-fallback-contract-preserved",
                            "point": "Data retrieval completed for at least one source.",
                            "source_ref": "system:error",
                        },
                        {
                            "claim_id": "bull-2-fallback-complete-emitted",
                            "point": "Termination safeguards emitted completion event.",
                            "source_ref": "system:error",
                        },
                        {
                            "claim_id": "bull-3-fallback-client-recoverable",
                            "point": "Client can safely reset state.",
                            "source_ref": "system:error",
                        },
                    ],
                    bear_case=[
                        {
                            "claim_id": "bear-1-fallback-brief-incomplete",
                            "point": "Agent did not produce a full evidence-backed brief.",
                            "source_ref": "system:error",
                        },
                        {
                            "claim_id": "bear-2-fallback-retry-required",
                            "point": "Manual retry is required for complete analysis.",
                            "source_ref": "system:error",
                        },
                    ],
                    key_risks=[
                        {
                            "claim_id": "risk-1-fallback-runtime-failure",
                            "risk": "Execution path timed out or raised an exception.",
                            "source_ref": "system:error",
                        },
                        {
                            "claim_id": "risk-2-fallback-degraded-ux",
                            "risk": "Downstream UI must display degraded completion.",
                            "source_ref": "system:error",
                        },
                    ],
                    confidence=1,
                    confidence_rationale="Fallback completion after runtime error.",
                    sources=[
                        {
                            "type": "news",
                            "id": "system:error",
                            "excerpt": "Fallback completion to satisfy SSE contract.",
                            "claim_refs": [
                                "bull-1-fallback-contract-preserved",
                                "bull-2-fallback-complete-emitted",
                                "bull-3-fallback-client-recoverable",
                                "bear-1-fallback-brief-incomplete",
                                "bear-2-fallback-retry-required",
                                "risk-1-fallback-runtime-failure",
                                "risk-2-fallback-degraded-ux",
                            ],
                        }
                    ],
                    signal_conflicts=[
                        {
                            "conflict_id": "conflict-fallback-partial-success",
                            "title": "Contract Safety Versus Analysis Completeness",
                            "summary": "The stream remains structurally safe for clients, but the analytical content is incomplete and should be retried.",
                            "severity": "high",
                            "claim_refs": [
                                "bull-2-fallback-complete-emitted",
                                "bear-1-fallback-brief-incomplete",
                                "risk-1-fallback-runtime-failure",
                            ],
                            "source_refs": ["news:system:error"],
                        }
                    ],
                    created_at=_iso_now(),
                    trace_steps=[],
                ).model_dump(),
                "duration_ms": 0,
                "ts": _iso_now(),
                "session_context_used": prior_context is not None,
                "session_id": session_id,
                "followup": prior_context is not None,
            }
            if isinstance(completion.get("brief"), dict):
                _update_session_context(session_id=session_id, brief_payload=completion["brief"], question=request.question)
            yield f"data: {json.dumps(completion)}\n\n"

    return StreamingResponse(stream_events(), media_type="text/event-stream")
