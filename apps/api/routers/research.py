from __future__ import annotations

import asyncio
from collections import Counter
import copy
import hashlib
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


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _freshness_from_hours(hours: float | None) -> str:
    if hours is None:
        return "unknown"
    if hours <= 24 * 7:
        return "fresh"
    if hours <= 24 * 180:
        return "aging"
    return "stale"


def _source_tool_name(source_type: str) -> str:
    mapping = {
        "fred": "fred_fetch",
        "market": "prediction_market_fetch",
        "news": "news_fetch",
        "edgar": "edgar_fetch",
    }
    return mapping.get(source_type, "unknown")


def _derive_observed_at(source: dict[str, Any], captured_at: str) -> str:
    preview = source.get("preview")
    if isinstance(preview, dict):
        points = preview.get("points")
        if isinstance(points, list) and points:
            last_point = points[-1]
            if isinstance(last_point, dict):
                date_value = last_point.get("date")
                if isinstance(date_value, str) and date_value.strip():
                    if "T" in date_value:
                        return date_value
                    return f"{date_value}T00:00:00Z"

        for key in ["last_updated", "updated_at", "as_of", "timestamp", "scored_at", "filed_date"]:
            value = preview.get(key)
            if isinstance(value, str) and value.strip():
                if "T" in value:
                    return value
                return f"{value}T00:00:00Z"

    return captured_at


def _compute_freshness(observed_at: str, captured_at: str) -> tuple[str, float | None]:
    observed_dt = _parse_iso(observed_at)
    captured_dt = _parse_iso(captured_at)
    if observed_dt is None or captured_dt is None:
        return "unknown", None
    age_hours = max(0.0, (captured_dt - observed_dt).total_seconds() / 3600)
    return _freshness_from_hours(age_hours), round(age_hours, 2)


def _hash_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _claim_ids_from_brief(brief: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for section, field in (("bull_case", "point"), ("bear_case", "point"), ("key_risks", "risk")):
        items = brief.get(section, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            claim_id = item.get("claim_id")
            if isinstance(claim_id, str) and claim_id.strip() and field in item:
                ids.add(claim_id)
    return ids


def _attach_provenance_and_evaluation(
    brief_payload: dict[str, Any],
    mode: str,
    trace_events: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    brief = copy.deepcopy(brief_payload)
    captured_at = str(brief.get("created_at") or _iso_now())
    sources = brief.get("sources", [])
    freshness_counts: Counter[str] = Counter()

    if not isinstance(sources, list):
        sources = []
        brief["sources"] = sources

    for source in sources:
        if not isinstance(source, dict):
            continue
        source_type = str(source.get("type") or "")
        source_id = str(source.get("id") or "")
        source_ref = f"{source_type}:{source_id}"
        existing = source.get("provenance") if isinstance(source.get("provenance"), dict) else {}
        observed_at = str(existing.get("observed_at") or _derive_observed_at(source, captured_at))
        freshness, freshness_hours = _compute_freshness(observed_at=observed_at, captured_at=captured_at)
        freshness_value = str(existing.get("freshness") or freshness)
        if freshness_value not in {"fresh", "aging", "stale", "unknown"}:
            freshness_value = freshness
        source_mode = str(existing.get("mode") or mode)
        if source_mode not in {"demo", "live"}:
            source_mode = "demo" if mode == "demo" else "live"

        source["provenance"] = {
            "source_ref": source_ref,
            "tool_name": str(existing.get("tool_name") or _source_tool_name(source_type)),
            "mode": source_mode,
            "observed_at": observed_at,
            "captured_at": str(existing.get("captured_at") or captured_at),
            "freshness": freshness_value,
            "freshness_hours": existing.get("freshness_hours", freshness_hours),
            "deterministic": bool(existing.get("deterministic", mode == "demo")),
        }
        freshness_counts[source["provenance"]["freshness"]] += 1

    brief["provenance_summary"] = {
        "captured_at": captured_at,
        "mode": mode,
        "deterministic": mode == "demo",
        "source_count": len(sources),
        "freshness_counts": {
            "fresh": freshness_counts.get("fresh", 0),
            "aging": freshness_counts.get("aging", 0),
            "stale": freshness_counts.get("stale", 0),
            "unknown": freshness_counts.get("unknown", 0),
        },
    }

    claim_ids = _claim_ids_from_brief(brief)
    source_claim_refs = {
        claim_ref
        for source in sources
        if isinstance(source, dict)
        for claim_ref in (source.get("claim_refs") or [])
        if isinstance(claim_ref, str)
    }
    trace_steps = [int(event.get("step", 0)) for event in trace_events]
    trace_step_order_valid = all(previous <= current for previous, current in zip(trace_steps, trace_steps[1:]))
    trace_step_unique = len(trace_steps) == len(set(trace_steps))
    unknown_count = freshness_counts.get("unknown", 0)
    deterministic_sources = sum(
        1
        for source in sources
        if isinstance(source, dict)
        and isinstance(source.get("provenance"), dict)
        and bool(source["provenance"].get("deterministic"))
    )

    checks = [
        {
            "check_id": "claim_source_coverage",
            "passed": claim_ids.issubset(source_claim_refs),
            "detail": "Every claim_id is linked by at least one source claim_ref.",
            "value": f"{len(source_claim_refs)}/{len(claim_ids)}",
        },
        {
            "check_id": "provenance_attached",
            "passed": all(
                isinstance(source, dict) and isinstance(source.get("provenance"), dict)
                for source in sources
            ),
            "detail": "Every source includes provenance metadata.",
            "value": len(sources),
        },
        {
            "check_id": "trace_step_order",
            "passed": trace_step_order_valid and trace_step_unique,
            "detail": "Trace steps are monotonic and unique.",
            "value": len(trace_steps),
        },
        {
            "check_id": "freshness_visibility",
            "passed": unknown_count == 0,
            "detail": "Every source has a resolved freshness state.",
            "value": len(sources) - unknown_count,
        },
        {
            "check_id": "deterministic_mode_alignment",
            "passed": (mode != "demo") or (deterministic_sources == len(sources)),
            "detail": "Demo mode sources should all be deterministic.",
            "value": deterministic_sources,
        },
    ]

    signature_payload = {
        "mode": mode,
        "query_class": brief.get("query_class"),
        "claim_ids": sorted(claim_ids),
        "source_refs": sorted(
            [
                f"{source.get('type')}:{source.get('id')}"
                for source in sources
                if isinstance(source, dict)
            ]
        ),
        "source_freshness": {
            f"{source.get('type')}:{source.get('id')}": (
                source.get("provenance", {}).get("freshness")
                if isinstance(source, dict)
                else "unknown"
            )
            for source in sources
            if isinstance(source, dict)
        },
        "trace_steps": trace_steps,
        "trace_types": [str(event.get("type", "")) for event in trace_events],
    }

    evaluation = {
        "version": "phase-6",
        "deterministic_signature": _hash_payload(signature_payload),
        "passed": all(bool(check.get("passed")) for check in checks),
        "checks": checks,
        "metrics": {
            "claim_count": len(claim_ids),
            "source_count": len(sources),
            "trace_event_count": len(trace_events),
            "stale_source_count": freshness_counts.get("stale", 0),
            "unknown_source_count": unknown_count,
            "deterministic_source_count": deterministic_sources,
        },
    }

    return brief, evaluation


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
        run_mode = request.mode.strip().lower()
        prior_context = SESSION_CONTEXT.get(session_id)
        if prior_context is None and request.session_id:
            restored_context = _restore_context_from_saved_session(session_id)
            if restored_context is not None:
                prior_context = restored_context
                SESSION_CONTEXT[session_id] = restored_context

        agent = ResearchAgent(demo_mode=run_mode == "demo")
        complete_emitted = False
        last_step = -1
        emitted_events: list[dict[str, Any]] = []

        try:
            async with asyncio.timeout(120):
                async for trace_step in agent.run_with_context(
                    question=request.question,
                    mode=run_mode,
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
                            enriched_brief, evaluation = _attach_provenance_and_evaluation(
                                brief_payload=brief_payload,
                                mode=run_mode,
                                trace_events=[*emitted_events, event],
                            )
                            event["brief"] = enriched_brief
                            event["evaluation"] = evaluation
                            event["provenance"] = enriched_brief.get("provenance_summary")
                            _update_session_context(
                                session_id=session_id,
                                brief_payload=enriched_brief,
                                question=request.question,
                            )
                    emitted_events.append(event)
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
            emitted_events.append(timeout_event)
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
            emitted_events.append(error_event)
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
                enriched_brief, evaluation = _attach_provenance_and_evaluation(
                    brief_payload=completion["brief"],
                    mode=run_mode,
                    trace_events=[*emitted_events, completion],
                )
                completion["brief"] = enriched_brief
                completion["evaluation"] = evaluation
                completion["provenance"] = enriched_brief.get("provenance_summary")
                _update_session_context(
                    session_id=session_id,
                    brief_payload=enriched_brief,
                    question=request.question,
                )
            yield f"data: {json.dumps(completion)}\n\n"

    return StreamingResponse(stream_events(), media_type="text/event-stream")
