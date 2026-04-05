from __future__ import annotations

from datetime import datetime
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class DataPoint(BaseModel):
    date: str
    value: float


def _slugify_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


class CanonicalMarket(BaseModel):
    id: str
    platform: Literal["kalshi", "polymarket"]
    title: str
    category: str
    resolution_date: str
    market_probability: float = Field(ge=0.0, le=1.0)
    volume_usd: float = Field(ge=0.0)
    open_interest: float = Field(ge=0.0)
    last_updated: str
    history: list[DataPoint] = Field(default_factory=list)


class ClaimBase(BaseModel):
    claim_id: str
    source_ref: str

    @field_validator("claim_id")
    @classmethod
    def ensure_claim_id(cls, value: str) -> str:
        claim_id = value.strip()
        if not claim_id:
            raise ValueError("claim_id must be non-empty")
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,63}", claim_id):
            raise ValueError("claim_id must use lowercase letters, numbers, '_' or '-'")
        return claim_id

    @field_validator("source_ref")
    @classmethod
    def ensure_source_ref(cls, value: str) -> str:
        if ":" not in value:
            raise ValueError("source_ref must follow tool_name:id format")
        return value


class BriefPoint(ClaimBase):
    point: str


class RiskPoint(ClaimBase):
    risk: str


class SnapshotProvenance(BaseModel):
    snapshot_id: str
    snapshot_kind: Literal["fixture", "cache", "live_capture", "derived", "unknown"] = "unknown"
    dataset: str
    dataset_version: str | None = None
    generated_at: str | None = None
    cached_at: str | None = None
    fetched_at: str | None = None
    checksum_sha256: str | None = None
    deterministic: bool = False


class SourceProvenance(BaseModel):
    source_ref: str
    tool_name: str
    mode: Literal["demo", "live"]
    state_label: Literal["fixture", "cached", "live", "derived", "unknown"] = "unknown"
    cache_lineage: Literal["fixture", "cache", "fresh_pull", "derived", "unknown"] = "unknown"
    observed_at: str | None = None
    captured_at: str
    freshness: Literal["fresh", "aging", "stale", "unknown"] = "unknown"
    freshness_hours: float | None = None
    deterministic: bool = False
    snapshot: SnapshotProvenance | None = None


class SourceRef(BaseModel):
    type: Literal["fred", "edgar", "news", "market"]
    id: str
    excerpt: str
    claim_refs: list[str] = Field(default_factory=list)
    preview: dict[str, Any] | None = None
    provenance: SourceProvenance | None = None


ResearchTemplateId = Literal[
    "macro_outlook",
    "event_probability_interpretation",
    "ticker_macro_framing",
    "thesis_change_compare",
]


class ResearchTemplateDefinition(BaseModel):
    id: ResearchTemplateId
    title: str
    description: str
    framing: str
    query_class_default: Literal["macro_outlook", "event_probability", "ticker_macro"]
    emphasis: list[str] = Field(default_factory=list)
    evaluation_expectations: list[str] = Field(default_factory=list)


class ResearchEvaluationCheck(BaseModel):
    check_id: str
    passed: bool
    detail: str
    value: float | int | str | None = None


class ResearchEvaluationReport(BaseModel):
    version: str = "phase-7"
    deterministic_signature: str
    passed: bool
    checks: list[ResearchEvaluationCheck] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


class ResearchEvaluationDashboardFailureType(BaseModel):
    check_id: str
    count: int = Field(ge=0)


class ResearchEvaluationDashboardSession(BaseModel):
    id: str
    saved_at: str
    query_class: Literal["macro_outlook", "event_probability", "ticker_macro"] | None = None
    template_id: ResearchTemplateId | None = None
    template_title: str | None = None
    evaluation_passed: bool
    evaluation_signature: str | None = None
    failed_checks: list[str] = Field(default_factory=list)
    provenance_gap_count: int = Field(ge=0)
    stale_source_count: int = Field(ge=0)
    claim_linking_gap_count: int = Field(ge=0)


class ResearchEvaluationDashboard(BaseModel):
    generated_at: str
    session_count: int = Field(ge=0)
    passed_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    pass_rate: float = Field(ge=0.0, le=1.0)
    provenance_gap_session_count: int = Field(ge=0)
    provenance_gap_total_count: int = Field(ge=0)
    stale_source_session_count: int = Field(ge=0)
    stale_source_total_count: int = Field(ge=0)
    claim_linking_gap_session_count: int = Field(ge=0)
    claim_linking_gap_total_count: int = Field(ge=0)
    common_failure_types: list[ResearchEvaluationDashboardFailureType] = Field(default_factory=list)
    template_usage: dict[str, int] = Field(default_factory=dict)
    sessions: list[ResearchEvaluationDashboardSession] = Field(default_factory=list)
    deterministic_signature: str
    ready_for_export: bool = False
    filters: dict[str, Any] = Field(default_factory=dict)


class ResearchReviewChecklistItem(BaseModel):
    check_id: str
    title: str
    passed: bool
    detail: str
    value: str | int | float | None = None


class ResearchReviewChecklist(BaseModel):
    saved_id: str | None = None
    session_id: str | None = None
    status: Literal["pass", "fail"]
    completed: bool
    passed_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    total_count: int = Field(ge=0)
    deterministic_signature: str
    generated_at: str
    summary: str
    items: list[ResearchReviewChecklistItem] = Field(default_factory=list)


class SignalConflict(BaseModel):
    conflict_id: str
    title: str
    summary: str
    severity: Literal["low", "medium", "high"] = "medium"
    claim_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)

    @field_validator("conflict_id")
    @classmethod
    def ensure_conflict_id(cls, value: str) -> str:
        conflict_id = value.strip()
        if not conflict_id:
            raise ValueError("conflict_id must be non-empty")
        return conflict_id


class ResearchBrief(BaseModel):
    question: str
    query_class: Literal["macro_outlook", "event_probability", "ticker_macro"] | None = None
    template_id: ResearchTemplateId | None = None
    template_title: str | None = None
    follow_up_context: str | None = None
    thesis: str
    bull_case: list[BriefPoint]
    bear_case: list[BriefPoint]
    key_risks: list[RiskPoint]
    confidence: int = Field(ge=1, le=5)
    confidence_rationale: str
    methodology_summary: str | None = None
    sources: list[SourceRef]
    signal_conflicts: list[SignalConflict] = Field(default_factory=list)
    provenance_summary: dict[str, Any] | None = None
    snapshot_summary: dict[str, Any] | None = None
    created_at: str
    trace_steps: list[int] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_claim_references(cls, payload: Any) -> Any:
        if not isinstance(payload, dict):
            return payload

        section_map = (("bull_case", "bull"), ("bear_case", "bear"), ("key_risks", "risk"))
        legacy_to_claim: dict[str, str] = {}
        source_to_claims: dict[str, list[str]] = {}

        for section_name, prefix in section_map:
            items = payload.get(section_name, [])
            if not isinstance(items, list):
                continue

            for idx, item in enumerate(items):
                if not isinstance(item, dict):
                    continue

                source_ref = str(item.get("source_ref", "")).strip()
                source_token = ""
                if ":" in source_ref:
                    source_token = source_ref.split(":", 1)[1]

                existing_claim_id = str(item.get("claim_id", "")).strip()
                if existing_claim_id:
                    claim_id = existing_claim_id
                else:
                    suffix = _slugify_token(source_token)[:24] if source_token else ""
                    if not suffix:
                        suffix = f"{idx + 1:02d}"
                    claim_id = f"{prefix}-{idx + 1}-{suffix}"
                    item["claim_id"] = claim_id

                legacy_to_claim[f"{section_name}[{idx}]"] = claim_id

                if source_token:
                    source_to_claims.setdefault(source_token, [])
                    if claim_id not in source_to_claims[source_token]:
                        source_to_claims[source_token].append(claim_id)

        sources = payload.get("sources", [])
        if isinstance(sources, list):
            for source in sources:
                if not isinstance(source, dict):
                    continue

                refs = source.get("claim_refs", [])
                normalized_refs: list[str] = []
                if isinstance(refs, list):
                    for ref in refs:
                        ref_text = str(ref).strip()
                        if not ref_text:
                            continue
                        normalized_refs.append(legacy_to_claim.get(ref_text, ref_text))

                source_id = str(source.get("id", "")).strip()
                if not normalized_refs and source_id in source_to_claims:
                    normalized_refs = list(source_to_claims[source_id])

                deduped_refs: list[str] = []
                seen_refs: set[str] = set()
                for claim_ref in normalized_refs:
                    if claim_ref in seen_refs:
                        continue
                    deduped_refs.append(claim_ref)
                    seen_refs.add(claim_ref)

                source["claim_refs"] = deduped_refs

        conflicts = payload.get("signal_conflicts")
        if isinstance(conflicts, list):
            for idx, conflict in enumerate(conflicts):
                if not isinstance(conflict, dict):
                    continue
                if not str(conflict.get("conflict_id", "")).strip():
                    conflict["conflict_id"] = f"conflict-{idx + 1}"
                claim_refs = conflict.get("claim_refs", [])
                if isinstance(claim_refs, list):
                    conflict["claim_refs"] = [legacy_to_claim.get(str(ref), str(ref)) for ref in claim_refs if str(ref).strip()]

        return payload

    @model_validator(mode="after")
    def enforce_case_lengths(self) -> "ResearchBrief":
        if not 3 <= len(self.bull_case) <= 5:
            raise ValueError("bull_case must contain 3-5 items")
        if not 2 <= len(self.bear_case) <= 5:
            raise ValueError("bear_case must contain 2-5 items")
        if len(self.key_risks) < 2:
            raise ValueError("key_risks must contain at least 2 items")

        claim_points: list[ClaimBase] = [*self.bull_case, *self.bear_case, *self.key_risks]
        claim_ids = [item.claim_id for item in claim_points]
        if len(set(claim_ids)) != len(claim_ids):
            raise ValueError("claim_id values must be unique across bull, bear, and risk sections")

        claim_id_set = set(claim_ids)
        claim_coverage = {claim_id: 0 for claim_id in claim_ids}
        source_refs = {f"{source.type}:{source.id}" for source in self.sources}

        for source in self.sources:
            for claim_ref in source.claim_refs:
                if claim_ref not in claim_id_set:
                    raise ValueError(f"source {source.type}:{source.id} references unknown claim_id: {claim_ref}")
                claim_coverage[claim_ref] += 1

        unlinked_claims = [claim_id for claim_id, count in claim_coverage.items() if count == 0]
        if unlinked_claims:
            raise ValueError(f"every claim must map to at least one source via claim_refs: {unlinked_claims}")

        for conflict in self.signal_conflicts:
            if len(conflict.claim_refs) < 2:
                raise ValueError("signal_conflicts entries must reference at least 2 claims")
            unknown_claims = [claim_ref for claim_ref in conflict.claim_refs if claim_ref not in claim_id_set]
            if unknown_claims:
                raise ValueError(
                    f"signal_conflict {conflict.conflict_id} references unknown claim_ids: {unknown_claims}"
                )
            unknown_sources = [source_ref for source_ref in conflict.source_refs if source_ref not in source_refs]
            if unknown_sources:
                raise ValueError(
                    f"signal_conflict {conflict.conflict_id} references unknown source_refs: {unknown_sources}"
                )

        return self


class TraceStep(BaseModel):
    step_index: int = Field(ge=0)
    type: Literal["tool_call", "tool_result", "reasoning", "brief_delta", "complete", "error", "reflection"]
    tool_name: str | None = None
    tool_args: dict | None = None
    content: str | dict | list | None = None
    timestamp: str

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value


class MispricingScore(BaseModel):
    market_id: str
    market_prob: float = Field(ge=0.0, le=1.0)
    model_prob: float = Field(ge=0.0, le=1.0)
    dislocation: float = Field(ge=0.0, le=1.0)
    direction: Literal["market_overpriced", "market_underpriced"]
    explanation: str
    confidence: int = Field(ge=1, le=5)
    scored_at: str


class ResearchCollection(BaseModel):
    id: str
    title: str = Field(min_length=1, max_length=120)
    summary: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=2000)
    session_ids: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    collection_signature: str

    @field_validator("id")
    @classmethod
    def ensure_id(cls, value: str) -> str:
        collection_id = value.strip()
        if not collection_id.startswith("coll-"):
            raise ValueError("id must start with 'coll-'")
        return collection_id

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title must be non-empty")
        return cleaned

    @field_validator("summary", "notes")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ResearchCollectionSummary(BaseModel):
    id: str
    title: str
    summary: str | None = None
    session_count: int
    created_at: str
    updated_at: str
    collection_signature: str


class ResearchRegressionPack(BaseModel):
    id: str
    title: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    session_ids: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    pack_signature: str

    @field_validator("id")
    @classmethod
    def ensure_id(cls, value: str) -> str:
        pack_id = value.strip()
        if not pack_id.startswith("rpack-"):
            raise ValueError("id must start with 'rpack-'")
        return pack_id

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title must be non-empty")
        return cleaned

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ResearchRegressionPackSummary(BaseModel):
    id: str
    title: str
    description: str | None = None
    session_count: int
    created_at: str
    updated_at: str
    pack_signature: str


class CreateRegressionPackRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    session_ids: list[str] = Field(min_length=1)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title must be non-empty")
        return cleaned

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ResearchRegressionSessionDrift(BaseModel):
    saved_id: str
    question: str
    template_id: ResearchTemplateId | None = None
    signature_before: str
    signature_after: str
    signature_changed: bool
    thesis_changed: bool
    confidence_changed: bool
    claim_ids_added: list[str] = Field(default_factory=list)
    claim_ids_removed: list[str] = Field(default_factory=list)
    provenance_signature_before: str
    provenance_signature_after: str
    provenance_changed: bool
    evaluation_signature_before: str | None = None
    evaluation_signature_after: str | None = None
    evaluation_changed: bool
    evaluation_passed_before: bool | None = None
    evaluation_passed_after: bool | None = None
    bundle_snapshot_signature_before: str | None = None
    bundle_snapshot_signature_after: str | None = None
    bundle_snapshot_changed: bool = False
    drift_signature: str


class ResearchRegressionPackRun(BaseModel):
    pack_id: str
    generated_at: str
    session_count: int = Field(ge=0)
    compared_count: int = Field(ge=0)
    changed_count: int = Field(ge=0)
    unchanged_count: int = Field(ge=0)
    thesis_drift_count: int = Field(ge=0)
    claim_drift_count: int = Field(ge=0)
    provenance_drift_count: int = Field(ge=0)
    evaluation_drift_count: int = Field(ge=0)
    bundle_drift_count: int = Field(ge=0)
    deterministic_signature: str
    drifts: list[ResearchRegressionSessionDrift] = Field(default_factory=list)


class CreateCollectionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    summary: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title must be non-empty")
        return cleaned

    @field_validator("summary", "notes")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class UpdateCollectionRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    summary: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title must be non-empty")
        return cleaned

    @field_validator("summary", "notes")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class AddSessionToCollectionRequest(BaseModel):
    session_id: str = Field(min_length=4)
    position: int | None = Field(default=None, ge=0)


class ReorderCollectionSessionsRequest(BaseModel):
    session_ids: list[str] = Field(min_length=1)


class ResearchThesisStateSnapshot(BaseModel):
    thesis: str
    confidence: int = Field(ge=1, le=5)
    claim_ids: list[str] = Field(default_factory=list)
    claim_count: int = Field(ge=0)
    freshness_policy_violation_count: int = Field(ge=0)
    freshness_policy_warning_count: int = Field(ge=0)
    conflict_ids: list[str] = Field(default_factory=list)
    conflict_count: int = Field(ge=0)
    evaluation_passed: bool | None = None
    evaluation_signature: str | None = None


class ResearchThesisDelta(BaseModel):
    previous_session_id: str | None = None
    thesis_changed: bool = False
    confidence_changed: bool = False
    claims_changed: bool = False
    claim_ids_added: list[str] = Field(default_factory=list)
    claim_ids_removed: list[str] = Field(default_factory=list)
    freshness_policy_changed: bool = False
    freshness_policy_violation_delta: int = 0
    freshness_policy_warning_delta: int = 0
    conflicts_changed: bool = False
    conflict_ids_added: list[str] = Field(default_factory=list)
    conflict_ids_removed: list[str] = Field(default_factory=list)
    evaluation_changed: bool = False
    evaluation_passed_changed: bool = False
    evaluation_signature_before: str | None = None
    evaluation_signature_after: str | None = None
    delta_signature: str


class ResearchCollectionTimelineEntry(BaseModel):
    session_id: str
    exists: bool
    label: str | None = None
    question: str | None = None
    query_class: Literal["macro_outlook", "event_probability", "ticker_macro"] | None = None
    template_id: ResearchTemplateId | None = None
    template_title: str | None = None
    saved_at: str | None = None
    evaluation_passed: bool | None = None
    snapshot_signature: str | None = None
    archived: bool | None = None
    thesis_state: ResearchThesisStateSnapshot | None = None
    thesis_delta: ResearchThesisDelta | None = None


class ResearchCollectionDetail(BaseModel):
    collection: ResearchCollection
    timeline: list[ResearchCollectionTimelineEntry] = Field(default_factory=list)
    missing_session_count: int = 0
    timeline_signature: str = ""


class ResearchThreadTimelineDetail(BaseModel):
    thread_session_id: str
    timeline: list[ResearchCollectionTimelineEntry] = Field(default_factory=list)
    timeline_signature: str


class BundleInventoryEntry(BaseModel):
    file: str
    media_type: str
    sha256: str
    size_bytes: int = Field(ge=0)


class SessionBundleManifest(BaseModel):
    schema_version: str = Field(alias="schema")
    bundle_kind: Literal["session"]
    generated_at: str
    saved_id: str
    thread_session_id: str
    query_class: Literal["macro_outlook", "event_probability", "ticker_macro"] | None = None
    timeline_signature: str | None = None
    compare_previous_saved_id: str | None = None
    deterministic_signature: str
    equality_checks: dict[str, bool] = Field(default_factory=dict)
    section_signatures: dict[str, str] = Field(default_factory=dict)
    inventory: list[BundleInventoryEntry] = Field(default_factory=list)


class SessionBundleExportV2(BaseModel):
    bundle_version: Literal["wave14-v2"]
    bundle_kind: Literal["session"]
    exported_at: str
    manifest: SessionBundleManifest
    files: dict[str, Any] = Field(default_factory=dict)


class CollectionBundleManifest(BaseModel):
    schema_version: str = Field(alias="schema")
    bundle_kind: Literal["collection"]
    collection_id: str
    collection_signature: str | None = None
    timeline_signature: str | None = None
    deterministic_signature: str
    equality_checks: dict[str, bool] = Field(default_factory=dict)
    section_signatures: dict[str, str] = Field(default_factory=dict)
    inventory: list[BundleInventoryEntry] = Field(default_factory=list)


class CollectionBundleExportV2(BaseModel):
    bundle_version: Literal["wave14-v2"]
    bundle_kind: Literal["collection"]
    manifest: CollectionBundleManifest
    files: dict[str, Any] = Field(default_factory=dict)
