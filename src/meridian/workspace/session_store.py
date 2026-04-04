from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from meridian.normalisation.schemas import ResearchBrief
from meridian.settings import ROOT_DIR


def _iso_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _default_store_dir() -> Path:
    configured = os.getenv("MERIDIAN_SESSION_STORE_DIR", "").strip()
    if configured:
        path = Path(configured)
        if not path.is_absolute():
            path = ROOT_DIR / path
        return path
    return ROOT_DIR / "data" / "processed" / "research_sessions"


class SavedTraceEvent(BaseModel):
    type: Literal["tool_call", "tool_result", "reasoning", "brief_delta", "complete", "error", "reflection"]
    step: int = Field(ge=0)
    ts: str
    session_id: str | None = None
    followup: bool | None = None
    query_class: Literal["macro_outlook", "event_probability", "ticker_macro"] | None = None
    session_context_used: bool | None = None
    tool: str | None = None
    args: dict[str, Any] | None = None
    preview: list[Any] | None = None
    text: str | None = None
    section: str | None = None
    brief: ResearchBrief | None = None
    duration_ms: int | None = None
    message: str | None = None
    content: dict[str, Any] | None = None


class EvidenceNavigationState(BaseModel):
    active_claim_id: str | None = None
    expanded_source_id: str | None = None


class SaveResearchSessionRequest(BaseModel):
    question: str = Field(min_length=3)
    mode: Literal["demo", "live"] = "demo"
    session_id: str = Field(min_length=4, max_length=64)
    brief: ResearchBrief
    trace_events: list[SavedTraceEvent] = Field(default_factory=list)
    evidence_state: EvidenceNavigationState | None = None


class SavedResearchSession(BaseModel):
    id: str
    question: str
    mode: Literal["demo", "live"]
    session_id: str
    query_class: Literal["macro_outlook", "event_probability", "ticker_macro"] | None = None
    follow_up_context: str | None = None
    brief: ResearchBrief
    trace_events: list[SavedTraceEvent] = Field(default_factory=list)
    evidence_state: EvidenceNavigationState | None = None
    created_at: str
    saved_at: str
    updated_at: str
    canonical_signature: str

    @field_validator("id")
    @classmethod
    def ensure_id(cls, value: str) -> str:
        session_id = value.strip()
        if not session_id:
            raise ValueError("id must be non-empty")
        return session_id


class SavedResearchSessionSummary(BaseModel):
    id: str
    question: str
    mode: Literal["demo", "live"]
    session_id: str
    query_class: Literal["macro_outlook", "event_probability", "ticker_macro"] | None = None
    follow_up_context: str | None = None
    saved_at: str
    canonical_signature: str


class ResearchSessionStore:
    def __init__(self, root_dir: Path | None = None) -> None:
        self.root_dir = root_dir or _default_store_dir()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _path_for_id(self, saved_id: str) -> Path:
        return self.root_dir / f"{saved_id}.json"

    def _compute_signature(self, payload: SaveResearchSessionRequest) -> str:
        canonical_events: list[dict[str, Any]] = []
        for event in payload.trace_events:
            event_payload = event.model_dump(exclude_none=True)
            event_payload.pop("session_id", None)
            event_payload.pop("followup", None)
            event_payload.pop("duration_ms", None)
            canonical_events.append(event_payload)

        canonical_payload = {
            "question": payload.question,
            "mode": payload.mode,
            "query_class": payload.brief.query_class,
            "follow_up_context": payload.brief.follow_up_context,
            "brief": payload.brief.model_dump(),
            "trace_events": canonical_events,
            "evidence_state": payload.evidence_state.model_dump(exclude_none=True) if payload.evidence_state else None,
        }
        encoded = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _build_record(self, saved_id: str, payload: SaveResearchSessionRequest, timestamp: str) -> SavedResearchSession:
        return SavedResearchSession(
            id=saved_id,
            question=payload.question,
            mode=payload.mode,
            session_id=payload.session_id,
            query_class=payload.brief.query_class,
            follow_up_context=payload.brief.follow_up_context,
            brief=payload.brief,
            trace_events=payload.trace_events,
            evidence_state=payload.evidence_state,
            created_at=payload.brief.created_at,
            saved_at=timestamp,
            updated_at=timestamp,
            canonical_signature=self._compute_signature(payload),
        )

    def save(self, payload: SaveResearchSessionRequest) -> SavedResearchSession:
        timestamp = _iso_now()
        saved_id = f"rs-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        record = self._build_record(saved_id=saved_id, payload=payload, timestamp=timestamp)
        self._path_for_id(saved_id).write_text(record.model_dump_json(indent=2) + "\n", encoding="utf-8")
        return record

    def list_sessions(self) -> list[SavedResearchSessionSummary]:
        sessions: list[SavedResearchSessionSummary] = []
        for path in sorted(self.root_dir.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                record = SavedResearchSession.model_validate(payload)
            except Exception:
                continue
            sessions.append(
                SavedResearchSessionSummary(
                    id=record.id,
                    question=record.question,
                    mode=record.mode,
                    session_id=record.session_id,
                    query_class=record.query_class,
                    follow_up_context=record.follow_up_context,
                    saved_at=record.saved_at,
                    canonical_signature=record.canonical_signature,
                )
            )

        sessions.sort(key=lambda item: item.saved_at, reverse=True)
        return sessions

    def get(self, saved_id: str) -> SavedResearchSession | None:
        path = self._path_for_id(saved_id)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return SavedResearchSession.model_validate(payload)

    def get_latest_for_session(self, session_id: str) -> SavedResearchSession | None:
        candidates = [item for item in self.list_sessions() if item.session_id == session_id]
        if not candidates:
            return None
        return self.get(candidates[0].id)

    def export_markdown(self, record: SavedResearchSession) -> str:
        trace_summary = {
            "total_events": len(record.trace_events),
            "event_types": sorted({event.type for event in record.trace_events}),
            "first_step": record.trace_events[0].step if record.trace_events else None,
            "last_step": record.trace_events[-1].step if record.trace_events else None,
        }

        lines: list[str] = [
            f"# Meridian Research Session {record.id}",
            "",
            "## Metadata",
            f"- Question: {record.question}",
            f"- Mode: {record.mode}",
            f"- Runtime Session ID: {record.session_id}",
            f"- Query Class: {record.query_class or 'unknown'}",
            f"- Follow-up Context: {record.follow_up_context or 'none'}",
            f"- Brief Created At: {record.created_at}",
            f"- Saved At: {record.saved_at}",
            f"- Canonical Signature: {record.canonical_signature}",
            "",
            "## Thesis",
            record.brief.thesis,
            "",
            "## Bull Case",
        ]

        for item in record.brief.bull_case:
            lines.append(f"- [{item.claim_id}] {item.point} ({item.source_ref})")

        lines.extend(["", "## Bear Case"])
        for item in record.brief.bear_case:
            lines.append(f"- [{item.claim_id}] {item.point} ({item.source_ref})")

        lines.extend(["", "## Key Risks"])
        for item in record.brief.key_risks:
            lines.append(f"- [{item.claim_id}] {item.risk} ({item.source_ref})")

        lines.extend(["", "## Sources"])
        for source in record.brief.sources:
            claim_refs = ", ".join(source.claim_refs) if source.claim_refs else "none"
            lines.append(f"- {source.type}:{source.id} | claims: {claim_refs} | {source.excerpt}")

        lines.extend(["", "## Signal Conflicts"])
        if record.brief.signal_conflicts:
            for conflict in record.brief.signal_conflicts:
                lines.append(f"- {conflict.conflict_id} [{conflict.severity}] {conflict.title}")
                lines.append(f"  - {conflict.summary}")
                lines.append(f"  - claims: {', '.join(conflict.claim_refs)}")
                lines.append(f"  - sources: {', '.join(conflict.source_refs)}")
        else:
            lines.append("- none")

        lines.extend(
            [
                "",
                "## Trace Summary",
                f"- Total events: {trace_summary['total_events']}",
                f"- Event types: {', '.join(trace_summary['event_types']) if trace_summary['event_types'] else 'none'}",
                f"- Step range: {trace_summary['first_step']} -> {trace_summary['last_step']}",
                "",
                "## Evidence Navigation State",
                f"- Active claim: {record.evidence_state.active_claim_id if record.evidence_state else 'none'}",
                f"- Expanded source: {record.evidence_state.expanded_source_id if record.evidence_state else 'none'}",
                "",
                "## Trace Payload",
                "```json",
                json.dumps([event.model_dump(exclude_none=True) for event in record.trace_events], indent=2),
                "```",
            ]
        )

        return "\n".join(lines) + "\n"


_STORE: ResearchSessionStore | None = None


def get_session_store() -> ResearchSessionStore:
    global _STORE
    root_dir = _default_store_dir()
    if _STORE is None or _STORE.root_dir != root_dir:
        _STORE = ResearchSessionStore(root_dir=root_dir)
    return _STORE
