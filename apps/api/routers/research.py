from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any, AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from meridian.agent.react import ResearchAgent
from meridian.normalisation.schemas import ResearchBrief, TraceStep


router = APIRouter(tags=["research"])


class ResearchRequest(BaseModel):
    question: str = Field(min_length=3)
    mode: str = "demo"


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
            }
        )
    elif step.type == "error":
        event.update({"message": str(step.content or "Unknown error")})

    return event


@router.post("/research")
async def post_research(request: ResearchRequest) -> StreamingResponse:
    async def stream_events() -> AsyncGenerator[str, None]:
        agent = ResearchAgent(demo_mode=request.mode == "demo")
        complete_emitted = False
        last_step = -1

        try:
            async with asyncio.timeout(120):
                async for trace_step in agent.run(question=request.question, mode=request.mode):
                    last_step = max(last_step, trace_step.step_index)
                    event = _trace_to_event(trace_step)
                    if event["type"] == "complete":
                        complete_emitted = True
                    yield f"data: {json.dumps(event)}\n\n"
        except TimeoutError:
            error_step = last_step + 1
            timeout_event = {
                "type": "error",
                "step": error_step,
                "message": "research stream exceeded 120s timeout",
                "ts": _iso_now(),
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
            }
            yield f"data: {json.dumps(error_event)}\n\n"
            last_step = error_step

        if not complete_emitted:
            completion = {
                "type": "complete",
                "step": last_step + 1,
                "brief": ResearchBrief(
                    question=request.question,
                    thesis="Research stream terminated with an error state.",
                    bull_case=[
                        {"point": "Data retrieval completed for at least one source.", "source_ref": "system:error"},
                        {"point": "Termination safeguards emitted completion event.", "source_ref": "system:error"},
                        {"point": "Client can safely reset state.", "source_ref": "system:error"},
                    ],
                    bear_case=[
                        {"point": "Agent did not produce a full evidence-backed brief.", "source_ref": "system:error"},
                        {"point": "Manual retry is required for complete analysis.", "source_ref": "system:error"},
                    ],
                    key_risks=[
                        {"risk": "Execution path timed out or raised an exception.", "source_ref": "system:error"},
                        {"risk": "Downstream UI must display degraded completion.", "source_ref": "system:error"},
                    ],
                    confidence=1,
                    confidence_rationale="Fallback completion after runtime error.",
                    sources=[
                        {"type": "news", "id": "system:error", "excerpt": "Fallback completion to satisfy SSE contract."}
                    ],
                    created_at=_iso_now(),
                    trace_steps=[],
                ).model_dump(),
                "duration_ms": 0,
                "ts": _iso_now(),
            }
            yield f"data: {json.dumps(completion)}\n\n"

    return StreamingResponse(stream_events(), media_type="text/event-stream")
