from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from meridian.normalisation.schemas import (
    ResearchBrief,
    ResearchEvaluationCheck,
    ResearchEvaluationReport,
    SnapshotProvenance,
    SourceProvenance,
)
from meridian.settings import ROOT_DIR


QueryClass = Literal["macro_outlook", "event_probability", "ticker_macro"]

FRESHNESS_POLICY_VERSION = "wave10-v1"
FRESHNESS_POLICY_RULES: dict[str, dict[str, Any]] = {
    "fred": {"max_age_hours": 24 * 180, "warn_age_hours": 24 * 30},
    "market": {"max_age_hours": 24 * 3, "warn_age_hours": 24},
    "news": {"max_age_hours": 24 * 2, "warn_age_hours": 12},
    "edgar": {"max_age_hours": 24 * 45, "warn_age_hours": 24 * 15},
}
DEFAULT_FRESHNESS_POLICY = {"max_age_hours": 24 * 30, "warn_age_hours": 24 * 7}


def _iso_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _freshness_from_hours(hours: float | None) -> Literal["fresh", "aging", "stale", "unknown"]:
    if hours is None:
        return "unknown"
    if hours <= 24 * 7:
        return "fresh"
    if hours <= 24 * 180:
        return "aging"
    return "stale"


def _normalize_snapshot_kind(value: Any) -> Literal["fixture", "cache", "live_capture", "derived", "unknown"]:
    candidate = str(value or "").strip().lower()
    if candidate in {"fixture", "cache", "live_capture", "derived", "unknown"}:
        return candidate
    return "unknown"


def _cache_lineage_from_snapshot_kind(
    snapshot_kind: str,
) -> Literal["fixture", "cache", "fresh_pull", "derived", "unknown"]:
    if snapshot_kind == "fixture":
        return "fixture"
    if snapshot_kind == "cache":
        return "cache"
    if snapshot_kind == "live_capture":
        return "fresh_pull"
    if snapshot_kind == "derived":
        return "derived"
    return "unknown"


def _preview_timestamp(preview: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        raw = preview.get(key)
        if isinstance(raw, str) and raw.strip():
            if "T" in raw:
                return raw
            return f"{raw}T00:00:00Z"
    return None


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
    label: str | None = Field(default=None, max_length=120)
    brief: ResearchBrief
    trace_events: list[SavedTraceEvent] = Field(default_factory=list)
    evidence_state: EvidenceNavigationState | None = None
    evaluation: ResearchEvaluationReport | None = None

    @field_validator("label")
    @classmethod
    def normalize_label(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class SavedResearchSession(BaseModel):
    id: str
    question: str
    mode: Literal["demo", "live"]
    session_id: str
    label: str | None = None
    query_class: QueryClass | None = None
    follow_up_context: str | None = None
    brief: ResearchBrief
    trace_events: list[SavedTraceEvent] = Field(default_factory=list)
    evidence_state: EvidenceNavigationState | None = None
    evaluation: ResearchEvaluationReport | None = None
    archived: bool = False
    archived_at: str | None = None
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
    label: str | None = None
    query_class: QueryClass | None = None
    follow_up_context: str | None = None
    archived: bool = False
    archived_at: str | None = None
    saved_at: str
    updated_at: str
    canonical_signature: str
    evaluation_passed: bool | None = None
    evaluation_signature: str | None = None
    snapshot_kind_counts: dict[str, int] | None = None
    snapshot_signature: str | None = None


class SnapshotIdDrift(BaseModel):
    source_ref: str
    left_snapshot_id: str | None = None
    right_snapshot_id: str | None = None
    left_snapshot_kind: str | None = None
    right_snapshot_kind: str | None = None


class FreshnessDrift(BaseModel):
    source_ref: str
    left_freshness: str | None = None
    right_freshness: str | None = None
    left_freshness_hours: float | None = None
    right_freshness_hours: float | None = None


class SnapshotDriftReport(BaseModel):
    left_snapshot_signature: str
    right_snapshot_signature: str
    snapshot_signature_changed: bool
    left_evaluation_signature: str | None = None
    right_evaluation_signature: str | None = None
    evaluation_signature_changed: bool
    source_set_changed: bool
    source_set_delta_count: int
    sources_added: list[str] = Field(default_factory=list)
    sources_removed: list[str] = Field(default_factory=list)
    snapshot_ids_changed: list[SnapshotIdDrift] = Field(default_factory=list)
    freshness_changed: list[FreshnessDrift] = Field(default_factory=list)
    drift_signature: str


class SessionComparison(BaseModel):
    left_id: str
    right_id: str
    signature_match: bool
    metadata_diffs: list[dict[str, Any]] = Field(default_factory=list)
    claim_diffs: dict[str, list[str]] = Field(default_factory=dict)
    source_diffs: dict[str, list[str]] = Field(default_factory=dict)
    snapshot_drift: SnapshotDriftReport
    trace_diffs: dict[str, Any] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)


class RecaptureSnapshotTransition(BaseModel):
    source_ref: str
    before_snapshot_id: str | None = None
    after_snapshot_id: str | None = None
    before_cache_lineage: str | None = None
    after_cache_lineage: str | None = None


class SessionRecaptureLineage(BaseModel):
    source_session_id: str
    recaptured_session_id: str
    recapture_mode: Literal["demo_pseudo_refresh", "live_refresh"]
    before_snapshot_signature: str
    after_snapshot_signature: str
    snapshot_id_changes: int
    source_set_changes: int
    transition_count: int
    transitions: list[RecaptureSnapshotTransition] = Field(default_factory=list)
    generated_at: str


class SessionRecaptureResult(BaseModel):
    saved: SavedResearchSession
    lineage: SessionRecaptureLineage


class SessionIntegrityReport(BaseModel):
    id: str
    signature_valid: bool
    canonical_signature: str
    recomputed_signature: str
    trace_event_count: int
    trace_step_order_valid: bool
    trace_step_unique: bool
    evidence_state_valid: bool
    provenance_complete: bool
    freshness_valid: bool
    freshness_policy_valid: bool
    freshness_policy_violation_count: int
    snapshot_complete: bool
    snapshot_consistent: bool
    snapshot_summary_present: bool
    snapshot_checksum_complete: bool
    evaluation_present: bool
    evaluation_valid: bool
    evaluation_signature: str | None = None
    bundle_snapshot_signature: str | None = None
    issues: list[str] = Field(default_factory=list)
    checked_at: str
    provenance: dict[str, Any] = Field(default_factory=dict)


class ResearchSessionStore:
    def __init__(self, root_dir: Path | None = None) -> None:
        self.root_dir = root_dir or _default_store_dir()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _path_for_id(self, saved_id: str) -> Path:
        return self.root_dir / f"{saved_id}.json"

    def _canonical_trace_events(self, events: list[SavedTraceEvent]) -> list[dict[str, Any]]:
        canonical_events: list[dict[str, Any]] = []
        for event in events:
            event_payload = event.model_dump(exclude_none=True)
            event_payload.pop("session_id", None)
            event_payload.pop("followup", None)
            event_payload.pop("duration_ms", None)
            canonical_events.append(event_payload)
        return canonical_events

    def _canonical_payload(
        self,
        question: str,
        mode: Literal["demo", "live"],
        brief: ResearchBrief,
        trace_events: list[SavedTraceEvent],
        evidence_state: EvidenceNavigationState | None,
        evaluation: ResearchEvaluationReport | None,
    ) -> dict[str, Any]:
        return {
            "question": question,
            "mode": mode,
            "query_class": brief.query_class,
            "follow_up_context": brief.follow_up_context,
            "brief": brief.model_dump(),
            "trace_events": self._canonical_trace_events(trace_events),
            "evidence_state": evidence_state.model_dump(exclude_none=True) if evidence_state else None,
            "evaluation": evaluation.model_dump(exclude_none=True) if evaluation else None,
        }

    def _hash_canonical_payload(self, canonical_payload: dict[str, Any]) -> str:
        encoded = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _compute_signature(self, payload: SaveResearchSessionRequest) -> str:
        canonical_payload = self._canonical_payload(
            question=payload.question,
            mode=payload.mode,
            brief=payload.brief,
            trace_events=payload.trace_events,
            evidence_state=payload.evidence_state,
            evaluation=payload.evaluation,
        )
        return self._hash_canonical_payload(canonical_payload)

    def _compute_signature_for_record(self, record: SavedResearchSession) -> str:
        canonical_payload = self._canonical_payload(
            question=record.question,
            mode=record.mode,
            brief=record.brief,
            trace_events=record.trace_events,
            evidence_state=record.evidence_state,
            evaluation=record.evaluation,
        )
        return self._hash_canonical_payload(canonical_payload)

    def _derive_observed_at(self, source: Any) -> str | None:
        preview = source.preview or {}
        points = preview.get("points") if isinstance(preview, dict) else None
        if isinstance(points, list) and points:
            last_point = points[-1]
            if isinstance(last_point, dict):
                date_value = last_point.get("date")
                if isinstance(date_value, str) and date_value.strip():
                    if "T" in date_value:
                        return date_value
                    return f"{date_value}T00:00:00Z"

        if not isinstance(preview, dict):
            return None

        for key in ["last_updated", "updated_at", "as_of", "timestamp", "scored_at", "filed_date"]:
            value = preview.get(key)
            if isinstance(value, str) and value.strip():
                if "T" in value:
                    return value
                return f"{value}T00:00:00Z"
        return None

    def _source_tool_name(self, source_type: str) -> str:
        mapping = {
            "fred": "fred_fetch",
            "market": "prediction_market_fetch",
            "news": "news_fetch",
            "edgar": "edgar_fetch",
        }
        return mapping.get(source_type, "unknown")

    def _snapshot_kind_for_source(
        self,
        source: Any,
        mode: Literal["demo", "live"],
        existing_snapshot: dict[str, Any],
    ) -> Literal["fixture", "cache", "live_capture", "derived", "unknown"]:
        explicit = _normalize_snapshot_kind(existing_snapshot.get("snapshot_kind"))
        if explicit != "unknown":
            return explicit

        preview = source.preview or {}
        hinted = _normalize_snapshot_kind(preview.get("snapshot_kind") or preview.get("snapshot_source"))
        if hinted != "unknown":
            return hinted

        if mode == "demo":
            return "fixture"

        if any(
            key in preview
            for key in ["cached_at", "cache_timestamp", "cache_key", "cache_hit", "cache_snapshot_id"]
        ):
            return "cache"
        if any(key in preview for key in ["derived_from", "computed_from", "calculation", "model_version"]):
            return "derived"
        if mode == "live":
            return "live_capture"
        return "unknown"

    def _snapshot_dataset_label(self, source: Any) -> str:
        preview = source.preview or {}
        if source.type == "fred":
            return f"fred:{str(preview.get('series_id') or source.id)}"
        if source.type == "market":
            platform = str(preview.get("platform") or "market")
            return f"{platform}:{source.id}"
        if source.type == "edgar":
            return f"edgar:{str(preview.get('cik') or source.id)}"
        if source.type == "news":
            return f"news:{str(preview.get('topic') or source.id)}"
        return f"{source.type}:{source.id}"

    def _snapshot_projection(self, brief: ResearchBrief) -> list[dict[str, Any]]:
        projection: list[dict[str, Any]] = []
        for source in brief.sources:
            source_ref = f"{source.type}:{source.id}"
            snapshot = source.provenance.snapshot if source.provenance else None
            projection.append(
                {
                    "source_ref": source_ref,
                    "cache_lineage": source.provenance.cache_lineage if source.provenance else "unknown",
                    "snapshot": snapshot.model_dump(exclude_none=True) if snapshot else None,
                }
            )
        return projection

    def _snapshot_signature(self, brief: ResearchBrief) -> str:
        payload = {
            "snapshot_summary": brief.snapshot_summary,
            "sources": self._snapshot_projection(brief),
        }
        return self._hash_canonical_payload(payload)

    def _source_snapshot_index(self, brief: ResearchBrief) -> dict[str, dict[str, Any]]:
        index: dict[str, dict[str, Any]] = {}
        for source in brief.sources:
            source_ref = f"{source.type}:{source.id}"
            provenance = source.provenance
            snapshot = provenance.snapshot if provenance else None
            index[source_ref] = {
                "snapshot_id": snapshot.snapshot_id if snapshot else None,
                "snapshot_kind": snapshot.snapshot_kind if snapshot else None,
                "cache_lineage": provenance.cache_lineage if provenance else "unknown",
                "freshness": provenance.freshness if provenance else "unknown",
                "freshness_hours": provenance.freshness_hours if provenance else None,
            }
        return index

    def _compute_freshness(self, observed_at: str | None, captured_at: str) -> tuple[str, float | None]:
        observed_dt = _parse_iso(observed_at)
        captured_dt = _parse_iso(captured_at)
        if observed_dt is None or captured_dt is None:
            return "unknown", None

        age_hours = max(0.0, (captured_dt - observed_dt).total_seconds() / 3600)
        return _freshness_from_hours(age_hours), round(age_hours, 2)

    def _advance_iso(self, value: str | None, *, fallback: str | None = None, hours: int = 24) -> str | None:
        parsed = _parse_iso(value) or _parse_iso(fallback)
        if parsed is None:
            return None
        return (parsed + timedelta(hours=hours)).isoformat().replace("+00:00", "Z")

    def _freshness_policy_summary(self, brief: ResearchBrief) -> dict[str, Any]:
        evaluations: list[dict[str, Any]] = []
        violations: list[dict[str, Any]] = []
        warning_count = 0

        for source in brief.sources:
            source_ref = f"{source.type}:{source.id}"
            provenance = source.provenance
            freshness = provenance.freshness if provenance else "unknown"
            freshness_hours = provenance.freshness_hours if provenance else None
            rule = FRESHNESS_POLICY_RULES.get(source.type, DEFAULT_FRESHNESS_POLICY)
            max_age_hours = float(rule["max_age_hours"])
            warn_age_hours = float(rule["warn_age_hours"])

            violation = (
                freshness == "unknown"
                or freshness == "stale"
                or (freshness_hours is not None and freshness_hours > max_age_hours)
            )
            warning = (
                not violation
                and freshness_hours is not None
                and freshness_hours > warn_age_hours
            )
            if warning:
                warning_count += 1

            evaluation = {
                "source_ref": source_ref,
                "source_type": source.type,
                "freshness": freshness,
                "freshness_hours": freshness_hours,
                "max_age_hours": max_age_hours,
                "warn_age_hours": warn_age_hours,
                "violation": violation,
                "warning": warning,
            }
            evaluations.append(evaluation)
            if violation:
                violations.append(evaluation)

        return {
            "version": FRESHNESS_POLICY_VERSION,
            "rules": FRESHNESS_POLICY_RULES,
            "evaluations": evaluations,
            "violations": violations,
            "violation_count": len(violations),
            "warning_count": warning_count,
        }

    def _enrich_brief_provenance(self, brief: ResearchBrief, mode: Literal["demo", "live"]) -> ResearchBrief:
        enriched = brief.model_copy(deep=True)
        captured_at = enriched.created_at or _iso_now()
        freshness_counts: Counter[str] = Counter()
        snapshot_kind_counts: Counter[str] = Counter()
        cache_lineage_counts: Counter[str] = Counter()
        freshness_by_snapshot_kind: dict[str, Counter[str]] = {
            "fixture": Counter(),
            "cache": Counter(),
            "live_capture": Counter(),
            "derived": Counter(),
            "unknown": Counter(),
        }
        observed_candidates: list[datetime] = []
        snapshot_checksum_coverage = 0

        for source in enriched.sources:
            source_ref = f"{source.type}:{source.id}"
            preview = source.preview or {}
            existing = source.provenance.model_dump(exclude_none=True) if source.provenance else {}
            existing_snapshot = existing.get("snapshot") if isinstance(existing.get("snapshot"), dict) else {}
            observed_at = str(existing.get("observed_at") or self._derive_observed_at(source) or captured_at)
            freshness, freshness_hours = self._compute_freshness(observed_at=observed_at, captured_at=captured_at)
            mode_value = str(existing.get("mode") or mode)
            if mode_value not in {"demo", "live"}:
                mode_value = mode
            freshness_value = str(existing.get("freshness") or freshness)
            if freshness_value not in {"fresh", "aging", "stale", "unknown"}:
                freshness_value = freshness
            snapshot_kind = self._snapshot_kind_for_source(
                source=source,
                mode=mode_value,
                existing_snapshot=existing_snapshot,
            )
            cache_lineage = str(existing.get("cache_lineage") or _cache_lineage_from_snapshot_kind(snapshot_kind))
            if cache_lineage not in {"fixture", "cache", "fresh_pull", "derived", "unknown"}:
                cache_lineage = _cache_lineage_from_snapshot_kind(snapshot_kind)

            dataset = str(existing_snapshot.get("dataset") or self._snapshot_dataset_label(source))
            dataset_version = existing_snapshot.get("dataset_version") or preview.get("dataset_version")
            if mode == "demo" and not dataset_version:
                dataset_version = "demo-fixture-v1"

            generated_at = existing_snapshot.get("generated_at") or _preview_timestamp(
                preview,
                ["generated_at", "snapshot_generated_at", "as_of", "last_updated", "updated_at", "filed_date"],
            )
            cached_at = existing_snapshot.get("cached_at") or _preview_timestamp(
                preview,
                ["cached_at", "cache_timestamp", "cache_as_of"],
            )
            fetched_at = existing_snapshot.get("fetched_at") or _preview_timestamp(
                preview,
                ["fetched_at", "retrieved_at"],
            )

            if snapshot_kind == "fixture":
                generated_at = generated_at or observed_at
            elif snapshot_kind == "cache":
                cached_at = cached_at or observed_at
            elif snapshot_kind == "live_capture":
                fetched_at = fetched_at or captured_at
            elif snapshot_kind == "derived":
                generated_at = generated_at or captured_at

            snapshot_signature_payload = {
                "source_ref": source_ref,
                "snapshot_kind": snapshot_kind,
                "dataset": dataset,
                "dataset_version": dataset_version,
                "generated_at": generated_at,
                "cached_at": cached_at,
                "fetched_at": fetched_at,
                "preview_kind": preview.get("kind"),
                "mode": mode_value,
            }
            checksum_sha256 = str(
                existing_snapshot.get("checksum_sha256") or self._hash_canonical_payload(snapshot_signature_payload)
            )
            snapshot_id = str(existing_snapshot.get("snapshot_id") or f"snap-{checksum_sha256[:12]}")
            deterministic_snapshot = bool(existing_snapshot.get("deterministic", mode == "demo"))

            if observed_at:
                parsed = _parse_iso(observed_at)
                if parsed is not None:
                    observed_candidates.append(parsed)

            source.provenance = SourceProvenance(
                source_ref=source_ref,
                tool_name=str(existing.get("tool_name") or self._source_tool_name(source.type)),
                mode=mode_value,
                cache_lineage=cache_lineage,
                observed_at=observed_at,
                captured_at=str(existing.get("captured_at") or captured_at),
                freshness=freshness_value,
                freshness_hours=existing.get("freshness_hours", freshness_hours),
                deterministic=bool(existing.get("deterministic", mode == "demo")),
                snapshot=SnapshotProvenance(
                    snapshot_id=snapshot_id,
                    snapshot_kind=snapshot_kind,
                    dataset=dataset,
                    dataset_version=(str(dataset_version) if dataset_version is not None else None),
                    generated_at=(str(generated_at) if generated_at is not None else None),
                    cached_at=(str(cached_at) if cached_at is not None else None),
                    fetched_at=(str(fetched_at) if fetched_at is not None else None),
                    checksum_sha256=checksum_sha256,
                    deterministic=deterministic_snapshot,
                ),
            )
            freshness_counts[source.provenance.freshness] += 1
            snapshot_kind_counts[snapshot_kind] += 1
            cache_lineage_counts[cache_lineage] += 1
            freshness_by_snapshot_kind[snapshot_kind][source.provenance.freshness] += 1
            if checksum_sha256:
                snapshot_checksum_coverage += 1

        oldest_observed_at = (
            min(observed_candidates).isoformat().replace("+00:00", "Z") if observed_candidates else None
        )
        enriched.provenance_summary = {
            "captured_at": captured_at,
            "mode": mode,
            "deterministic": mode == "demo",
            "source_count": len(enriched.sources),
            "freshness_counts": {
                "fresh": freshness_counts.get("fresh", 0),
                "aging": freshness_counts.get("aging", 0),
                "stale": freshness_counts.get("stale", 0),
                "unknown": freshness_counts.get("unknown", 0),
            },
            "oldest_observed_at": oldest_observed_at,
        }
        enriched.snapshot_summary = {
            "captured_at": captured_at,
            "mode": mode,
            "deterministic": mode == "demo",
            "snapshot_count": len(enriched.sources),
            "snapshot_kind_counts": {
                "fixture": snapshot_kind_counts.get("fixture", 0),
                "cache": snapshot_kind_counts.get("cache", 0),
                "live_capture": snapshot_kind_counts.get("live_capture", 0),
                "derived": snapshot_kind_counts.get("derived", 0),
                "unknown": snapshot_kind_counts.get("unknown", 0),
            },
            "cache_lineage_counts": {
                "fixture": cache_lineage_counts.get("fixture", 0),
                "cache": cache_lineage_counts.get("cache", 0),
                "fresh_pull": cache_lineage_counts.get("fresh_pull", 0),
                "derived": cache_lineage_counts.get("derived", 0),
                "unknown": cache_lineage_counts.get("unknown", 0),
            },
            "freshness_by_snapshot_kind": {
                kind: {
                    "fresh": counters.get("fresh", 0),
                    "aging": counters.get("aging", 0),
                    "stale": counters.get("stale", 0),
                    "unknown": counters.get("unknown", 0),
                }
                for kind, counters in freshness_by_snapshot_kind.items()
            },
            "snapshot_checksum_coverage": snapshot_checksum_coverage,
        }
        return enriched

    def _claim_ids(self, brief: ResearchBrief) -> set[str]:
        return {
            *[item.claim_id for item in brief.bull_case],
            *[item.claim_id for item in brief.bear_case],
            *[item.claim_id for item in brief.key_risks],
        }

    def _build_evaluation(
        self,
        brief: ResearchBrief,
        trace_events: list[SavedTraceEvent],
        mode: Literal["demo", "live"],
    ) -> ResearchEvaluationReport:
        claim_ids = self._claim_ids(brief)
        source_refs = [f"{source.type}:{source.id}" for source in brief.sources]
        source_claim_refs = {
            claim_ref
            for source in brief.sources
            for claim_ref in source.claim_refs
        }

        trace_steps = [event.step for event in trace_events]
        trace_step_order_valid = all(
            previous <= current for previous, current in zip(trace_steps, trace_steps[1:])
        )
        trace_step_unique = len(trace_steps) == len(set(trace_steps))

        missing_provenance = [
            f"{source.type}:{source.id}" for source in brief.sources if source.provenance is None
        ]
        stale_count = sum(
            1
            for source in brief.sources
            if source.provenance is not None and source.provenance.freshness == "stale"
        )
        unknown_count = sum(
            1
            for source in brief.sources
            if source.provenance is not None and source.provenance.freshness == "unknown"
        )
        deterministic_sources = sum(
            1
            for source in brief.sources
            if source.provenance is not None and source.provenance.deterministic
        )
        snapshot_records = [
            source.provenance.snapshot
            for source in brief.sources
            if source.provenance is not None
        ]
        snapshot_kind_counts: Counter[str] = Counter(
            snapshot.snapshot_kind
            for snapshot in snapshot_records
            if snapshot is not None
        )
        snapshot_complete = all(
            snapshot is not None
            and bool(snapshot.snapshot_id.strip())
            and bool(snapshot.dataset.strip())
            and snapshot.snapshot_kind != "unknown"
            for snapshot in snapshot_records
        )
        snapshot_consistent = all(
            source.provenance is not None
            and source.provenance.snapshot is not None
            and (
                source.provenance.mode != "demo"
                or source.provenance.snapshot.snapshot_kind in {"fixture", "derived"}
            )
            for source in brief.sources
        )
        snapshot_summary = brief.snapshot_summary if isinstance(brief.snapshot_summary, dict) else {}
        snapshot_summary_present = bool(snapshot_summary)
        cache_lineage_counts = (
            snapshot_summary.get("cache_lineage_counts")
            if isinstance(snapshot_summary.get("cache_lineage_counts"), dict)
            else {}
        )
        cache_lineage_visible = (
            snapshot_summary_present
            and isinstance(cache_lineage_counts, dict)
            and sum(
                int(cache_lineage_counts.get(key, 0))
                for key in ["fixture", "cache", "fresh_pull", "derived", "unknown"]
            )
            == len(brief.sources)
        )
        snapshot_checksum_complete = all(
            snapshot is not None and bool((snapshot.checksum_sha256 or "").strip())
            for snapshot in snapshot_records
        )
        bundle_snapshot_ready = (
            snapshot_complete
            and snapshot_consistent
            and cache_lineage_visible
            and snapshot_summary_present
            and snapshot_checksum_complete
        )
        freshness_policy = self._freshness_policy_summary(brief)
        freshness_policy_violations = freshness_policy["violations"]
        freshness_policy_passed = freshness_policy["violation_count"] == 0

        checks = [
            ResearchEvaluationCheck(
                check_id="claim_source_coverage",
                passed=claim_ids.issubset(source_claim_refs),
                detail="Every claim_id is linked by at least one source claim_ref.",
                value=f"{len(source_claim_refs)}/{len(claim_ids)}",
            ),
            ResearchEvaluationCheck(
                check_id="provenance_attached",
                passed=len(missing_provenance) == 0,
                detail="Every source includes provenance metadata.",
                value=len(brief.sources) - len(missing_provenance),
            ),
            ResearchEvaluationCheck(
                check_id="trace_step_order",
                passed=trace_step_order_valid and trace_step_unique,
                detail="Trace steps are monotonic and unique.",
                value=len(trace_steps),
            ),
            ResearchEvaluationCheck(
                check_id="freshness_visibility",
                passed=unknown_count == 0,
                detail="Every source has a resolved freshness state.",
                value=len(brief.sources) - unknown_count,
            ),
            ResearchEvaluationCheck(
                check_id="freshness_policy_compliance",
                passed=freshness_policy_passed,
                detail="Source freshness is within policy thresholds by source type.",
                value=freshness_policy["violation_count"],
            ),
            ResearchEvaluationCheck(
                check_id="deterministic_mode_alignment",
                passed=(mode != "demo") or (deterministic_sources == len(brief.sources)),
                detail="Demo mode sources should all be deterministic.",
                value=deterministic_sources,
            ),
            ResearchEvaluationCheck(
                check_id="snapshot_metadata_complete",
                passed=snapshot_complete,
                detail="Every source includes snapshot id, kind, and dataset metadata.",
                value=len(snapshot_records),
            ),
            ResearchEvaluationCheck(
                check_id="snapshot_source_consistency",
                passed=snapshot_consistent,
                detail="Snapshot labels are consistent with source mode and lineage semantics.",
                value=len(brief.sources),
            ),
            ResearchEvaluationCheck(
                check_id="cache_lineage_visibility",
                passed=cache_lineage_visible,
                detail="Snapshot summary exposes cache lineage coverage for all sources.",
                value=sum(
                    int(cache_lineage_counts.get(key, 0))
                    for key in ["fixture", "cache", "fresh_pull", "derived", "unknown"]
                ),
            ),
            ResearchEvaluationCheck(
                check_id="bundle_snapshot_provenance_ready",
                passed=bundle_snapshot_ready,
                detail="Snapshot checksum coverage is complete for offline bundle auditing.",
                value=sum(
                    1
                    for snapshot in snapshot_records
                    if snapshot is not None and bool((snapshot.checksum_sha256 or "").strip())
                ),
            ),
        ]

        signature_payload = {
            "mode": mode,
            "query_class": brief.query_class,
            "claim_ids": sorted(claim_ids),
            "source_refs": sorted(source_refs),
            "source_freshness": {
                f"{source.type}:{source.id}": (
                    source.provenance.freshness if source.provenance else "unknown"
                )
                for source in brief.sources
            },
            "source_snapshot_kind": {
                f"{source.type}:{source.id}": (
                    source.provenance.snapshot.snapshot_kind
                    if source.provenance and source.provenance.snapshot
                    else "unknown"
                )
                for source in brief.sources
            },
            "source_cache_lineage": {
                f"{source.type}:{source.id}": (
                    source.provenance.cache_lineage if source.provenance else "unknown"
                )
                for source in brief.sources
            },
            "freshness_policy": {
                "version": freshness_policy["version"],
                "violation_count": freshness_policy["violation_count"],
                "warning_count": freshness_policy["warning_count"],
                "violations": [
                    {
                        "source_ref": item["source_ref"],
                        "freshness": item["freshness"],
                    }
                    for item in freshness_policy_violations
                ],
            },
            "snapshot_summary": brief.snapshot_summary,
            "trace_steps": trace_steps,
            "trace_types": [event.type for event in trace_events],
        }
        deterministic_signature = self._hash_canonical_payload(signature_payload)

        metrics = {
            "claim_count": len(claim_ids),
            "source_count": len(brief.sources),
            "trace_event_count": len(trace_events),
            "stale_source_count": stale_count,
            "unknown_source_count": unknown_count,
            "freshness_policy_version": freshness_policy["version"],
            "freshness_policy_violation_count": freshness_policy["violation_count"],
            "freshness_policy_warning_count": freshness_policy["warning_count"],
            "freshness_policy_violations": [
                f"{item['source_ref']} ({item['freshness']})"
                for item in freshness_policy_violations
            ],
            "deterministic_source_count": deterministic_sources,
            "snapshot_count": len(snapshot_records),
            "fixture_snapshot_count": snapshot_kind_counts.get("fixture", 0),
            "cache_snapshot_count": snapshot_kind_counts.get("cache", 0),
            "live_capture_snapshot_count": snapshot_kind_counts.get("live_capture", 0),
            "derived_snapshot_count": snapshot_kind_counts.get("derived", 0),
            "unknown_snapshot_count": snapshot_kind_counts.get("unknown", 0),
            "snapshot_checksum_coverage": sum(
                1
                for snapshot in snapshot_records
                if snapshot is not None and bool((snapshot.checksum_sha256 or "").strip())
            ),
        }

        return ResearchEvaluationReport(
            deterministic_signature=deterministic_signature,
            passed=all(check.passed for check in checks),
            checks=checks,
            metrics=metrics,
        )

    def _build_record(self, saved_id: str, payload: SaveResearchSessionRequest, timestamp: str) -> SavedResearchSession:
        enriched_brief = self._enrich_brief_provenance(payload.brief, mode=payload.mode)
        evaluation = self._build_evaluation(
            brief=enriched_brief,
            trace_events=payload.trace_events,
            mode=payload.mode,
        )
        canonical_signature = self._hash_canonical_payload(
            self._canonical_payload(
                question=payload.question,
                mode=payload.mode,
                brief=enriched_brief,
                trace_events=payload.trace_events,
                evidence_state=payload.evidence_state,
                evaluation=evaluation,
            )
        )

        return SavedResearchSession(
            id=saved_id,
            question=payload.question,
            mode=payload.mode,
            session_id=payload.session_id,
            label=payload.label,
            query_class=enriched_brief.query_class,
            follow_up_context=enriched_brief.follow_up_context,
            brief=enriched_brief,
            trace_events=payload.trace_events,
            evidence_state=payload.evidence_state,
            evaluation=evaluation,
            archived=False,
            archived_at=None,
            created_at=enriched_brief.created_at,
            saved_at=timestamp,
            updated_at=timestamp,
            canonical_signature=canonical_signature,
        )

    def _write_record(self, record: SavedResearchSession) -> None:
        self._path_for_id(record.id).write_text(record.model_dump_json(indent=2) + "\n", encoding="utf-8")

    def _load_record(self, path: Path) -> SavedResearchSession | None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return SavedResearchSession.model_validate(payload)
        except Exception:
            return None

    def _all_records(self) -> list[SavedResearchSession]:
        records: list[SavedResearchSession] = []
        for path in sorted(self.root_dir.glob("*.json")):
            record = self._load_record(path)
            if record is not None:
                records.append(record)
        records.sort(key=lambda item: item.saved_at, reverse=True)
        return records

    def _build_summary(self, record: SavedResearchSession) -> SavedResearchSessionSummary:
        snapshot_summary = (
            record.brief.snapshot_summary
            if isinstance(record.brief.snapshot_summary, dict)
            else {}
        )
        snapshot_kind_counts = (
            snapshot_summary.get("snapshot_kind_counts")
            if isinstance(snapshot_summary.get("snapshot_kind_counts"), dict)
            else None
        )
        return SavedResearchSessionSummary(
            id=record.id,
            question=record.question,
            mode=record.mode,
            session_id=record.session_id,
            label=record.label,
            query_class=record.query_class,
            follow_up_context=record.follow_up_context,
            archived=record.archived,
            archived_at=record.archived_at,
            saved_at=record.saved_at,
            updated_at=record.updated_at,
            canonical_signature=record.canonical_signature,
            evaluation_passed=record.evaluation.passed if record.evaluation else None,
            evaluation_signature=record.evaluation.deterministic_signature if record.evaluation else None,
            snapshot_kind_counts=snapshot_kind_counts,
            snapshot_signature=self._snapshot_signature(record.brief),
        )

    def _matches_filters(
        self,
        record: SavedResearchSession,
        search: str | None,
        include_archived: bool,
        query_class: QueryClass | None,
    ) -> bool:
        if not include_archived and record.archived:
            return False
        if query_class and record.query_class != query_class:
            return False
        if search:
            token = search.strip().lower()
            if token:
                haystack = " ".join(
                    [
                        record.id,
                        record.question,
                        record.label or "",
                        record.session_id,
                        record.query_class or "",
                    ]
                ).lower()
                if token not in haystack:
                    return False
        return True

    def save(self, payload: SaveResearchSessionRequest) -> SavedResearchSession:
        timestamp = _iso_now()
        saved_id = f"rs-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        record = self._build_record(saved_id=saved_id, payload=payload, timestamp=timestamp)
        self._write_record(record)
        return record

    def recapture(self, saved_id: str) -> SessionRecaptureResult | None:
        record = self.get(saved_id)
        if record is None:
            return None

        recaptured_brief = record.brief.model_copy(deep=True)
        recapture_mode: Literal["demo_pseudo_refresh", "live_refresh"] = (
            "demo_pseudo_refresh" if record.mode == "demo" else "live_refresh"
        )
        before_snapshot_signature = self._snapshot_signature(record.brief)
        before_index = self._source_snapshot_index(record.brief)

        refreshed_created_at = self._advance_iso(record.brief.created_at, fallback=_iso_now()) or _iso_now()
        recaptured_brief.created_at = refreshed_created_at

        transition_candidates: list[RecaptureSnapshotTransition] = []
        for source in recaptured_brief.sources:
            if source.provenance is None or source.provenance.snapshot is None:
                continue

            snapshot = source.provenance.snapshot
            source_ref = source.provenance.source_ref
            before_snapshot_id = snapshot.snapshot_id
            before_cache_lineage = source.provenance.cache_lineage

            refreshed_checksum = self._hash_canonical_payload(
                {
                    "source_ref": source_ref,
                    "before_snapshot_id": before_snapshot_id,
                    "before_checksum": snapshot.checksum_sha256,
                    "recapture_mode": recapture_mode,
                    "refresh_profile": "wave9-recapture-v1",
                }
            )
            snapshot.snapshot_id = f"snap-{refreshed_checksum[:12]}"
            snapshot.checksum_sha256 = refreshed_checksum

            if record.mode == "demo":
                snapshot.snapshot_kind = "derived"
                source.provenance.cache_lineage = "derived"
                base_dataset_version = str(snapshot.dataset_version or "demo-fixture-v1")
                snapshot.dataset_version = (
                    base_dataset_version
                    if base_dataset_version.endswith("-recapture-v1")
                    else f"{base_dataset_version}-recapture-v1"
                )

            snapshot.generated_at = self._advance_iso(snapshot.generated_at, fallback=record.brief.created_at)
            snapshot.cached_at = self._advance_iso(snapshot.cached_at, fallback=record.brief.created_at)
            snapshot.fetched_at = self._advance_iso(snapshot.fetched_at, fallback=record.brief.created_at)
            source.provenance.observed_at = self._advance_iso(
                source.provenance.observed_at,
                fallback=record.brief.created_at,
            )
            source.provenance.captured_at = self._advance_iso(
                source.provenance.captured_at,
                fallback=record.brief.created_at,
            ) or source.provenance.captured_at

            transition_candidates.append(
                RecaptureSnapshotTransition(
                    source_ref=source_ref,
                    before_snapshot_id=before_snapshot_id,
                    after_snapshot_id=snapshot.snapshot_id,
                    before_cache_lineage=before_cache_lineage,
                    after_cache_lineage=source.provenance.cache_lineage,
                )
            )

        recaptured_trace_events = [event.model_copy(deep=True) for event in record.trace_events]
        next_step = recaptured_trace_events[-1].step + 1 if recaptured_trace_events else 0
        recaptured_trace_events.append(
            SavedTraceEvent(
                type="reasoning",
                step=next_step,
                ts=refreshed_created_at,
                text=(
                    f"Recaptured session {saved_id} using {recapture_mode}; "
                    "snapshot lineage refreshed without overwriting prior work."
                ),
            )
        )
        recaptured_trace_events.append(
            SavedTraceEvent(
                type="complete",
                step=next_step + 1,
                ts=refreshed_created_at,
                followup=True,
                session_id=record.session_id,
            )
        )

        next_label = ((record.label or record.question) + " [recapture]").strip()
        if len(next_label) > 120:
            next_label = next_label[:120]

        recaptured_record = self.save(
            SaveResearchSessionRequest(
                question=record.question,
                mode=record.mode,
                session_id=record.session_id,
                label=next_label,
                brief=recaptured_brief,
                trace_events=recaptured_trace_events,
                evidence_state=record.evidence_state.model_copy(deep=True) if record.evidence_state else None,
                evaluation=record.evaluation.model_copy(deep=True) if record.evaluation else None,
            )
        )

        after_snapshot_signature = self._snapshot_signature(recaptured_record.brief)
        after_index = self._source_snapshot_index(recaptured_record.brief)
        common_source_refs = sorted(set(before_index) & set(after_index))
        transition_lookup = {item.source_ref: item for item in transition_candidates}
        changed_transitions = [
            transition_lookup[source_ref]
            for source_ref in common_source_refs
            if before_index[source_ref]["snapshot_id"] != after_index[source_ref]["snapshot_id"]
            and source_ref in transition_lookup
        ]
        source_set_changes = len(set(before_index) ^ set(after_index))

        return SessionRecaptureResult(
            saved=recaptured_record,
            lineage=SessionRecaptureLineage(
                source_session_id=record.id,
                recaptured_session_id=recaptured_record.id,
                recapture_mode=recapture_mode,
                before_snapshot_signature=before_snapshot_signature,
                after_snapshot_signature=after_snapshot_signature,
                snapshot_id_changes=len(changed_transitions),
                source_set_changes=source_set_changes,
                transition_count=len(changed_transitions),
                transitions=changed_transitions,
                generated_at=_iso_now(),
            ),
        )

    def list_sessions(
        self,
        *,
        search: str | None = None,
        include_archived: bool = False,
        query_class: QueryClass | None = None,
    ) -> list[SavedResearchSessionSummary]:
        sessions: list[SavedResearchSessionSummary] = []
        for record in self._all_records():
            if not self._matches_filters(
                record=record,
                search=search,
                include_archived=include_archived,
                query_class=query_class,
            ):
                continue
            sessions.append(self._build_summary(record))

        sessions.sort(key=lambda item: item.saved_at, reverse=True)
        return sessions

    def get(self, saved_id: str) -> SavedResearchSession | None:
        path = self._path_for_id(saved_id)
        if not path.exists():
            return None
        return self._load_record(path)

    def get_latest_for_session(self, session_id: str) -> SavedResearchSession | None:
        candidates = [item for item in self.list_sessions(include_archived=True) if item.session_id == session_id]
        if not candidates:
            return None
        return self.get(candidates[0].id)

    def rename(self, saved_id: str, label: str | None) -> SavedResearchSession | None:
        record = self.get(saved_id)
        if record is None:
            return None

        normalized = label.strip() if label else ""
        record.label = normalized or None
        record.updated_at = _iso_now()
        self._write_record(record)
        return record

    def set_archived(self, saved_id: str, archived: bool) -> SavedResearchSession | None:
        record = self.get(saved_id)
        if record is None:
            return None

        if record.archived == archived:
            return record

        now = _iso_now()
        record.archived = archived
        record.archived_at = now if archived else None
        record.updated_at = now
        self._write_record(record)
        return record

    def delete(self, saved_id: str) -> bool:
        path = self._path_for_id(saved_id)
        if not path.exists():
            return False
        path.unlink()
        return True

    def compare(self, left_id: str, right_id: str) -> SessionComparison | None:
        left = self.get(left_id)
        right = self.get(right_id)
        if left is None or right is None:
            return None

        left_evaluation_signature = left.evaluation.deterministic_signature if left.evaluation else None
        right_evaluation_signature = right.evaluation.deterministic_signature if right.evaluation else None
        left_snapshot_signature = self._snapshot_signature(left.brief)
        right_snapshot_signature = self._snapshot_signature(right.brief)

        metadata_candidates: list[tuple[str, Any, Any]] = [
            ("question", left.question, right.question),
            ("label", left.label, right.label),
            ("query_class", left.query_class, right.query_class),
            ("follow_up_context", left.follow_up_context, right.follow_up_context),
            ("mode", left.mode, right.mode),
            ("archived", left.archived, right.archived),
            (
                "evaluation_signature",
                left_evaluation_signature,
                right_evaluation_signature,
            ),
            (
                "snapshot_signature",
                left_snapshot_signature,
                right_snapshot_signature,
            ),
        ]
        metadata_diffs = [
            {
                "field": field,
                "left": left_value,
                "right": right_value,
                "changed": left_value != right_value,
            }
            for field, left_value, right_value in metadata_candidates
        ]

        left_bull = {item.claim_id for item in left.brief.bull_case}
        right_bull = {item.claim_id for item in right.brief.bull_case}
        left_bear = {item.claim_id for item in left.brief.bear_case}
        right_bear = {item.claim_id for item in right.brief.bear_case}
        left_risk = {item.claim_id for item in left.brief.key_risks}
        right_risk = {item.claim_id for item in right.brief.key_risks}

        claim_diffs = {
            "bull_added": sorted(right_bull - left_bull),
            "bull_removed": sorted(left_bull - right_bull),
            "bear_added": sorted(right_bear - left_bear),
            "bear_removed": sorted(left_bear - right_bear),
            "risk_added": sorted(right_risk - left_risk),
            "risk_removed": sorted(left_risk - right_risk),
        }

        left_sources = {f"{source.type}:{source.id}" for source in left.brief.sources}
        right_sources = {f"{source.type}:{source.id}" for source in right.brief.sources}
        source_diffs = {
            "sources_added": sorted(right_sources - left_sources),
            "sources_removed": sorted(left_sources - right_sources),
        }
        source_set_delta_count = len(source_diffs["sources_added"]) + len(source_diffs["sources_removed"])

        left_snapshot_index = self._source_snapshot_index(left.brief)
        right_snapshot_index = self._source_snapshot_index(right.brief)
        shared_source_refs = sorted(set(left_snapshot_index) & set(right_snapshot_index))

        snapshot_ids_changed: list[SnapshotIdDrift] = []
        freshness_changed: list[FreshnessDrift] = []
        for source_ref in shared_source_refs:
            left_state = left_snapshot_index[source_ref]
            right_state = right_snapshot_index[source_ref]
            if left_state["snapshot_id"] != right_state["snapshot_id"]:
                snapshot_ids_changed.append(
                    SnapshotIdDrift(
                        source_ref=source_ref,
                        left_snapshot_id=left_state["snapshot_id"],
                        right_snapshot_id=right_state["snapshot_id"],
                        left_snapshot_kind=left_state["snapshot_kind"],
                        right_snapshot_kind=right_state["snapshot_kind"],
                    )
                )
            if (
                left_state["freshness"] != right_state["freshness"]
                or left_state["freshness_hours"] != right_state["freshness_hours"]
            ):
                freshness_changed.append(
                    FreshnessDrift(
                        source_ref=source_ref,
                        left_freshness=left_state["freshness"],
                        right_freshness=right_state["freshness"],
                        left_freshness_hours=left_state["freshness_hours"],
                        right_freshness_hours=right_state["freshness_hours"],
                    )
                )

        snapshot_drift_payload = {
            "left_snapshot_signature": left_snapshot_signature,
            "right_snapshot_signature": right_snapshot_signature,
            "snapshot_signature_changed": left_snapshot_signature != right_snapshot_signature,
            "left_evaluation_signature": left_evaluation_signature,
            "right_evaluation_signature": right_evaluation_signature,
            "evaluation_signature_changed": left_evaluation_signature != right_evaluation_signature,
            "source_set_changed": source_set_delta_count > 0,
            "source_set_delta_count": source_set_delta_count,
            "sources_added": source_diffs["sources_added"],
            "sources_removed": source_diffs["sources_removed"],
            "snapshot_ids_changed": [item.model_dump(exclude_none=True) for item in snapshot_ids_changed],
            "freshness_changed": [item.model_dump(exclude_none=True) for item in freshness_changed],
        }
        snapshot_drift_signature = self._hash_canonical_payload(snapshot_drift_payload)
        snapshot_drift = SnapshotDriftReport(
            left_snapshot_signature=left_snapshot_signature,
            right_snapshot_signature=right_snapshot_signature,
            snapshot_signature_changed=left_snapshot_signature != right_snapshot_signature,
            left_evaluation_signature=left_evaluation_signature,
            right_evaluation_signature=right_evaluation_signature,
            evaluation_signature_changed=left_evaluation_signature != right_evaluation_signature,
            source_set_changed=source_set_delta_count > 0,
            source_set_delta_count=source_set_delta_count,
            sources_added=source_diffs["sources_added"],
            sources_removed=source_diffs["sources_removed"],
            snapshot_ids_changed=snapshot_ids_changed,
            freshness_changed=freshness_changed,
            drift_signature=snapshot_drift_signature,
        )

        left_trace_counts = Counter(event.type for event in left.trace_events)
        right_trace_counts = Counter(event.type for event in right.trace_events)
        trace_types = sorted(set(left_trace_counts) | set(right_trace_counts))
        trace_diffs = {
            "left_event_count": len(left.trace_events),
            "right_event_count": len(right.trace_events),
            "event_count_delta": len(right.trace_events) - len(left.trace_events),
            "event_type_deltas": {
                event_type: right_trace_counts.get(event_type, 0) - left_trace_counts.get(event_type, 0)
                for event_type in trace_types
            },
            "left_step_range": [
                left.trace_events[0].step if left.trace_events else None,
                left.trace_events[-1].step if left.trace_events else None,
            ],
            "right_step_range": [
                right.trace_events[0].step if right.trace_events else None,
                right.trace_events[-1].step if right.trace_events else None,
            ],
        }

        changed_fields = [item["field"] for item in metadata_diffs if item["changed"]]
        total_claim_changes = sum(len(values) for values in claim_diffs.values())
        total_source_changes = source_set_delta_count

        summary = {
            "changed_fields": changed_fields,
            "total_changed_fields": len(changed_fields),
            "total_claim_changes": total_claim_changes,
            "total_source_changes": total_source_changes,
            "thesis_changed": left.brief.thesis != right.brief.thesis,
            "confidence_changed": left.brief.confidence != right.brief.confidence,
            "signature_match": left.canonical_signature == right.canonical_signature,
            "snapshot_id_changes": len(snapshot_ids_changed),
            "freshness_changes": len(freshness_changed),
            "source_set_changed": source_set_delta_count > 0,
            "evaluation_signature_changed": left_evaluation_signature != right_evaluation_signature,
            "snapshot_drift_signature": snapshot_drift_signature,
        }

        return SessionComparison(
            left_id=left.id,
            right_id=right.id,
            signature_match=left.canonical_signature == right.canonical_signature,
            metadata_diffs=metadata_diffs,
            claim_diffs=claim_diffs,
            source_diffs=source_diffs,
            snapshot_drift=snapshot_drift,
            trace_diffs=trace_diffs,
            summary=summary,
        )

    def _evidence_state_valid(self, record: SavedResearchSession) -> bool:
        state = record.evidence_state
        if state is None:
            return True

        claim_ids = {
            *[item.claim_id for item in record.brief.bull_case],
            *[item.claim_id for item in record.brief.bear_case],
            *[item.claim_id for item in record.brief.key_risks],
        }
        source_refs = {f"{source.type}:{source.id}" for source in record.brief.sources}

        claim_ok = state.active_claim_id is None or state.active_claim_id in claim_ids
        source_ok = state.expanded_source_id is None or state.expanded_source_id in source_refs
        return claim_ok and source_ok

    def build_integrity_report(self, record: SavedResearchSession) -> SessionIntegrityReport:
        recomputed_signature = self._compute_signature_for_record(record)
        snapshot_signature = self._snapshot_signature(record.brief)
        trace_steps = [event.step for event in record.trace_events]
        trace_step_order_valid = all(
            previous <= current for previous, current in zip(trace_steps, trace_steps[1:])
        )
        trace_step_unique = len(trace_steps) == len(set(trace_steps))
        evidence_state_valid = self._evidence_state_valid(record)

        sources_with_provenance = [source for source in record.brief.sources if source.provenance is not None]
        provenance_complete = len(sources_with_provenance) == len(record.brief.sources)
        freshness_counter = Counter(
            source.provenance.freshness
            for source in sources_with_provenance
            if source.provenance is not None
        )
        freshness_valid = freshness_counter.get("unknown", 0) == 0
        freshness_policy = self._freshness_policy_summary(record.brief)
        freshness_policy_valid = freshness_policy["violation_count"] == 0
        freshness_policy_violation_count = int(freshness_policy["violation_count"])
        snapshots = [
            source.provenance.snapshot
            for source in sources_with_provenance
            if source.provenance is not None
        ]
        snapshot_complete = len(snapshots) == len(record.brief.sources) and all(
            snapshot is not None
            and bool(snapshot.snapshot_id.strip())
            and bool(snapshot.dataset.strip())
            and snapshot.snapshot_kind != "unknown"
            for snapshot in snapshots
        )
        snapshot_consistent = all(
            source.provenance is not None
            and source.provenance.snapshot is not None
            and (
                source.provenance.mode != "demo"
                or source.provenance.snapshot.snapshot_kind in {"fixture", "derived"}
            )
            for source in record.brief.sources
        )
        snapshot_summary = record.brief.snapshot_summary if isinstance(record.brief.snapshot_summary, dict) else {}
        snapshot_summary_present = bool(snapshot_summary)
        snapshot_checksum_complete = all(
            snapshot is not None and bool((snapshot.checksum_sha256 or "").strip())
            for snapshot in snapshots
        )

        recomputed_evaluation = self._build_evaluation(
            brief=record.brief,
            trace_events=record.trace_events,
            mode=record.mode,
        )
        evaluation_present = record.evaluation is not None
        evaluation_valid = (
            evaluation_present
            and record.evaluation is not None
            and record.evaluation.deterministic_signature == recomputed_evaluation.deterministic_signature
            and record.evaluation.passed == recomputed_evaluation.passed
        )

        issues: list[str] = []
        if record.canonical_signature != recomputed_signature:
            issues.append("canonical signature mismatch")
        if not trace_step_order_valid:
            issues.append("trace steps are out of order")
        if not trace_step_unique:
            issues.append("trace steps contain duplicates")
        if not evidence_state_valid:
            issues.append("evidence navigation state references missing claim/source")
        if not provenance_complete:
            issues.append("one or more sources are missing provenance metadata")
        if not freshness_valid:
            issues.append("one or more sources have unknown freshness state")
        if not freshness_policy_valid:
            issues.append("one or more sources violate freshness policy thresholds")
        if not snapshot_complete:
            issues.append("one or more sources are missing snapshot provenance metadata")
        if not snapshot_consistent:
            issues.append("snapshot provenance is inconsistent with source mode")
        if not snapshot_summary_present:
            issues.append("snapshot summary metadata is missing")
        if not snapshot_checksum_complete:
            issues.append("snapshot checksums are incomplete")
        if not evaluation_present:
            issues.append("evaluation report is missing")
        elif not evaluation_valid:
            issues.append("evaluation deterministic signature mismatch")

        return SessionIntegrityReport(
            id=record.id,
            signature_valid=record.canonical_signature == recomputed_signature,
            canonical_signature=record.canonical_signature,
            recomputed_signature=recomputed_signature,
            trace_event_count=len(record.trace_events),
            trace_step_order_valid=trace_step_order_valid,
            trace_step_unique=trace_step_unique,
            evidence_state_valid=evidence_state_valid,
            provenance_complete=provenance_complete,
            freshness_valid=freshness_valid,
            freshness_policy_valid=freshness_policy_valid,
            freshness_policy_violation_count=freshness_policy_violation_count,
            snapshot_complete=snapshot_complete,
            snapshot_consistent=snapshot_consistent,
            snapshot_summary_present=snapshot_summary_present,
            snapshot_checksum_complete=snapshot_checksum_complete,
            evaluation_present=evaluation_present,
            evaluation_valid=evaluation_valid,
            evaluation_signature=(record.evaluation.deterministic_signature if record.evaluation else None),
            bundle_snapshot_signature=snapshot_signature,
            issues=issues,
            checked_at=_iso_now(),
            provenance={
                "mode": record.mode,
                "session_id": record.session_id,
                "query_class": record.query_class,
                "saved_at": record.saved_at,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
                "archived": record.archived,
                "freshness_counts": {
                    "fresh": freshness_counter.get("fresh", 0),
                    "aging": freshness_counter.get("aging", 0),
                    "stale": freshness_counter.get("stale", 0),
                    "unknown": freshness_counter.get("unknown", 0),
                },
                "freshness_policy": {
                    "version": freshness_policy["version"],
                    "violation_count": freshness_policy_violation_count,
                    "warning_count": int(freshness_policy["warning_count"]),
                },
                "snapshot_kind_counts": (
                    snapshot_summary.get("snapshot_kind_counts")
                    if isinstance(snapshot_summary.get("snapshot_kind_counts"), dict)
                    else {}
                ),
                "cache_lineage_counts": (
                    snapshot_summary.get("cache_lineage_counts")
                    if isinstance(snapshot_summary.get("cache_lineage_counts"), dict)
                    else {}
                ),
                "snapshot_signature": snapshot_signature,
                "evaluation_passed": record.evaluation.passed if record.evaluation else None,
            },
        )

    def verify_integrity(self, saved_id: str) -> SessionIntegrityReport | None:
        record = self.get(saved_id)
        if record is None:
            return None
        return self.build_integrity_report(record)

    def verify_integrity_all(
        self,
        *,
        search: str | None = None,
        include_archived: bool = True,
    ) -> list[SessionIntegrityReport]:
        reports: list[SessionIntegrityReport] = []
        for record in self._all_records():
            if not self._matches_filters(
                record=record,
                search=search,
                include_archived=include_archived,
                query_class=None,
            ):
                continue
            reports.append(self.build_integrity_report(record))
        return reports

    def export_bundle_payload(self, record: SavedResearchSession) -> dict[str, Any]:
        integrity = self.build_integrity_report(record)
        freshness_counts = (
            record.brief.provenance_summary.get("freshness_counts")
            if isinstance(record.brief.provenance_summary, dict)
            else None
        )
        snapshot_summary = (
            record.brief.snapshot_summary
            if isinstance(record.brief.snapshot_summary, dict)
            else None
        )
        snapshot_projection = self._snapshot_projection(record.brief)
        snapshot_signature = self._snapshot_signature(record.brief)
        return {
            "bundle_version": "phase-7",
            "exported_at": _iso_now(),
            "session": record.model_dump(),
            "integrity": integrity.model_dump(),
            "evaluation": record.evaluation.model_dump() if record.evaluation else None,
            "snapshot_provenance": {
                "summary": snapshot_summary,
                "sources": snapshot_projection,
                "signature_sha256": snapshot_signature,
            },
            "provenance": {
                "source": "meridian-workspace",
                "app_version": "0.1.0",
                "model": "glm-5.1",
                "mode": record.mode,
                "freshness_counts": freshness_counts,
                "snapshot_kind_counts": (
                    snapshot_summary.get("snapshot_kind_counts")
                    if isinstance(snapshot_summary, dict)
                    else None
                ),
                "cache_lineage_counts": (
                    snapshot_summary.get("cache_lineage_counts")
                    if isinstance(snapshot_summary, dict)
                    else None
                ),
                "snapshot_signature": snapshot_signature,
                "evaluation_signature": (
                    record.evaluation.deterministic_signature if record.evaluation else None
                ),
            },
        }

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
            f"- Label: {record.label or 'none'}",
            f"- Mode: {record.mode}",
            f"- Runtime Session ID: {record.session_id}",
            f"- Query Class: {record.query_class or 'unknown'}",
            f"- Follow-up Context: {record.follow_up_context or 'none'}",
            f"- Archived: {record.archived}",
            f"- Archived At: {record.archived_at or 'n/a'}",
            f"- Brief Created At: {record.created_at}",
            f"- Saved At: {record.saved_at}",
            f"- Updated At: {record.updated_at}",
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
            freshness = source.provenance.freshness if source.provenance else "unknown"
            observed_at = source.provenance.observed_at if source.provenance else "n/a"
            snapshot_kind = (
                source.provenance.snapshot.snapshot_kind
                if source.provenance and source.provenance.snapshot
                else "unknown"
            )
            snapshot_id = (
                source.provenance.snapshot.snapshot_id
                if source.provenance and source.provenance.snapshot
                else "n/a"
            )
            cache_lineage = source.provenance.cache_lineage if source.provenance else "unknown"
            lines.append(
                f"- {source.type}:{source.id} | claims: {claim_refs} | freshness: {freshness} | cache_lineage: {cache_lineage} | snapshot_kind: {snapshot_kind} | snapshot_id: {snapshot_id} | observed_at: {observed_at} | {source.excerpt}"
            )

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
                "## Provenance Summary",
            ]
        )
        if isinstance(record.brief.provenance_summary, dict) and record.brief.provenance_summary:
            for key, value in record.brief.provenance_summary.items():
                lines.append(f"- {key}: {value}")
        else:
            lines.append("- none")

        lines.extend(["", "## Snapshot Summary"])
        if isinstance(record.brief.snapshot_summary, dict) and record.brief.snapshot_summary:
            for key, value in record.brief.snapshot_summary.items():
                lines.append(f"- {key}: {value}")
            lines.append(f"- snapshot_signature: {self._snapshot_signature(record.brief)}")
        else:
            lines.append("- none")

        lines.extend(
            [
                "",
                "## Evaluation",
            ]
        )
        if record.evaluation:
            lines.append(f"- Version: {record.evaluation.version}")
            lines.append(f"- Passed: {record.evaluation.passed}")
            lines.append(f"- Deterministic signature: {record.evaluation.deterministic_signature}")
            lines.append("- Checks:")
            for check in record.evaluation.checks:
                lines.append(
                    f"  - {check.check_id}: {'pass' if check.passed else 'fail'} ({check.value}) - {check.detail}"
                )
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
