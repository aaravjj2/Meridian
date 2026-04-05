# Meridian Schemas

## CanonicalMarket

- `id: str`
- `platform: "kalshi" | "polymarket"`
- `title: str`
- `category: str`
- `resolution_date: str (ISO)`
- `market_probability: float [0, 1]`
- `volume_usd: float`
- `open_interest: float`
- `last_updated: str (ISO)`
- `history: list[DataPoint]`

## ResearchTemplateDefinition

- `id: "macro_outlook" | "event_probability_interpretation" | "ticker_macro_framing" | "thesis_change_compare"`
- `title: str`
- `description: str`
- `framing: str`
- `query_class_default: "macro_outlook" | "event_probability" | "ticker_macro"`
- `emphasis: list[str]`
- `evaluation_expectations: list[str]`

## ResearchBrief

- `question: str`
- `template_id: "macro_outlook" | "event_probability_interpretation" | "ticker_macro_framing" | "thesis_change_compare" | null`
- `template_title: str | null`
- `thesis: str`
- `bull_case: list[{ claim_id, point, source_ref }]` (3-5)
- `bear_case: list[{ claim_id, point, source_ref }]` (2-5)
- `key_risks: list[{ claim_id, risk, source_ref }]` (>=2)
- `confidence: int [1, 5]`
- `confidence_rationale: str`
- `sources: list[{ type, id, excerpt, claim_refs?, preview?, provenance? }]`
- `signal_conflicts: list[{ conflict_id, title, summary, severity, claim_refs, source_refs }]`
- `provenance_summary: dict | null` (captured_at, mode, source_count, state_label_counts, freshness_counts)
- `snapshot_summary: dict | null` (snapshot_count, state_label_counts, snapshot_kind_counts, cache_lineage_counts, freshness_by_snapshot_kind, timing_summary, snapshot_checksum_coverage)
- `created_at: str (ISO)`
- `trace_steps: list[int]`

Validation notes:

- `claim_id` values are unique across bull/bear/risk sections.
- Every claim must be linked from at least one `sources[].claim_refs` entry.
- `signal_conflicts[].claim_refs` must reference valid `claim_id` values.
- `signal_conflicts[].source_refs` uses `type:id` format (example: `fred:T10Y2Y`).

## SnapshotProvenance

- `snapshot_id: str`
- `snapshot_kind: "fixture" | "cache" | "live_capture" | "derived" | "unknown"`
- `dataset: str` (source dataset label, e.g. `fred:T10Y2Y`)
- `dataset_version: str | null` (fixture/snapshot version label)
- `generated_at: str | null`
- `cached_at: str | null`
- `fetched_at: str | null`
- `checksum_sha256: str | null`
- `deterministic: bool`

Snapshot meaning guidance:

- `fixture`: deterministic fixture-backed snapshot (demo-safe)
- `cache`: replayed from cached snapshot state
- `live_capture`: fetched through a fresher pull path
- `derived`: computed/derived from upstream snapshots
- `unknown`: metadata insufficient; should be treated as degraded provenance

## SourceProvenance

- `source_ref: str` (`type:id`)
- `tool_name: str`
- `mode: "demo" | "live"`
- `state_label: "fixture" | "cached" | "live" | "derived" | "unknown"`
- `cache_lineage: "fixture" | "cache" | "fresh_pull" | "derived" | "unknown"`
- `observed_at: str | null`
- `captured_at: str`
- `freshness: "fresh" | "aging" | "stale" | "unknown"`
- `freshness_hours: float | null`
- `deterministic: bool`
- `snapshot: SnapshotProvenance | null`

## ResearchEvaluationReport

- `version: str` (currently `phase-7`)
- `deterministic_signature: str` (SHA256 over stable evaluation projection)
- `passed: bool`
- `checks: list[{ check_id, passed, detail, value? }]`
- `metrics: dict[str, Any]`

Phase 7 snapshot-aware checks include:

- `snapshot_metadata_complete`
- `snapshot_source_consistency`
- `cache_lineage_visibility`
- `bundle_snapshot_provenance_ready`

Wave 10 freshness policy check includes:

- `freshness_policy_compliance`

## ResearchEvaluationDashboard

- `generated_at: str (ISO)`
- `session_count: int`
- `passed_count: int`
- `failed_count: int`
- `pass_rate: float` (`0.0..1.0`)
- `provenance_gap_session_count: int`
- `provenance_gap_total_count: int`
- `stale_source_session_count: int`
- `stale_source_total_count: int`
- `claim_linking_gap_session_count: int`
- `claim_linking_gap_total_count: int`
- `common_failure_types: list[{ check_id, count }]`
- `template_usage: dict[str, int]`
- `sessions: list[ResearchEvaluationDashboardSession]`
- `deterministic_signature: str`
- `ready_for_export: bool`
- `filters: { search, include_archived, query_class }`

Builder semantics:

- deterministic workspace-level quality monitoring over saved sessions
- captures recurring failure modes by check id
- tracks provenance, stale-source, and claim-linking gap incidence
- marks when aggregate quality is clean enough for JSON export

## ResearchEvaluationDashboardSession

- `id: str`
- `saved_at: str (ISO)`
- `query_class: "macro_outlook" | "event_probability" | "ticker_macro" | null`
- `template_id: ResearchTemplateId | null`
- `template_title: str | null`
- `evaluation_passed: bool`
- `evaluation_signature: str | null`
- `failed_checks: list[str]`
- `provenance_gap_count: int`
- `stale_source_count: int`
- `claim_linking_gap_count: int`

## ResearchRegressionPack

- `id: str` (must start with `rpack-`)
- `title: str` (1..120 chars, trimmed)
- `description: str | null` (trimmed, max 500)
- `session_ids: list[str]` (ordered saved-session ids)
- `created_at: str (ISO)`
- `updated_at: str (ISO)`
- `pack_signature: str` (deterministic SHA256 over title/description/session_ids)

## ResearchRegressionPackSummary

- `id: str`
- `title: str`
- `description: str | null`
- `session_count: int`
- `created_at: str (ISO)`
- `updated_at: str (ISO)`
- `pack_signature: str`

## CreateRegressionPackRequest

- `title: str` (required, trimmed, non-empty)
- `description: str | null` (optional)
- `session_ids: list[str]` (required, min length 1)

## ResearchRegressionSessionDrift

- `saved_id: str`
- `question: str`
- `template_id: ResearchTemplateId | null`
- `signature_before: str`
- `signature_after: str`
- `signature_changed: bool`
- `thesis_changed: bool`
- `confidence_changed: bool`
- `claim_ids_added: list[str]`
- `claim_ids_removed: list[str]`
- `provenance_signature_before: str`
- `provenance_signature_after: str`
- `provenance_changed: bool`
- `evaluation_signature_before: str | null`
- `evaluation_signature_after: str | null`
- `evaluation_changed: bool`
- `evaluation_passed_before: bool | null`
- `evaluation_passed_after: bool | null`
- `bundle_snapshot_signature_before: str | null`
- `bundle_snapshot_signature_after: str | null`
- `bundle_snapshot_changed: bool`
- `drift_signature: str`

## ResearchRegressionPackRun

- `pack_id: str`
- `generated_at: str (ISO)`
- `session_count: int`
- `compared_count: int`
- `changed_count: int`
- `unchanged_count: int`
- `thesis_drift_count: int`
- `claim_drift_count: int`
- `provenance_drift_count: int`
- `evaluation_drift_count: int`
- `bundle_drift_count: int`
- `deterministic_signature: str`
- `drifts: list[ResearchRegressionSessionDrift]`

Semantics:

- `session_count`: configured pack size
- `compared_count`: sessions successfully replayed and compared
- `changed_count`: sessions with any meaningful drift (`signature|thesis|confidence|claims|provenance|evaluation|bundle`)
- `deterministic_signature`: stable hash over run projection for audit replay

## ResearchReviewChecklist

- `saved_id: str | null`
- `session_id: str | null`
- `status: "pass" | "fail"`
- `completed: bool`
- `passed_count: int`
- `failed_count: int`
- `total_count: int`
- `deterministic_signature: str`
- `generated_at: str (ISO)`
- `summary: str`
- `items: list[ResearchReviewChecklistItem]`

Checklist item shape:

- `check_id: str`
- `title: str`
- `passed: bool`
- `detail: str`
- `value: str | int | float | null`

Wave 16 guided-review check ids:

- `claim_source_coverage`
- `conflict_linkage`
- `freshness_acceptability`
- `provenance_completeness`
- `evaluation_pass_fail`
- `template_metadata`
- `snapshot_completeness`

## TraceStep

- `step_index: int`
- `type: tool_call | tool_result | reasoning | brief_delta | complete | error`
- `tool_name?: str`
- `tool_args?: dict`
- `content?: str | dict | list`
- `timestamp: str (ISO)`

## SavedResearchSession

- `id: str` (stable saved-session identifier)
- `question: str`
- `mode: "demo" | "live"`
- `session_id: str` (runtime research-thread id used for follow-ups)
- `label: str | null` (operator-managed display label)
- `query_class: "macro_outlook" | "event_probability" | "ticker_macro" | null`
- `template_id: "macro_outlook" | "event_probability_interpretation" | "ticker_macro_framing" | "thesis_change_compare" | null`
- `template_title: str | null`
- `follow_up_context: str | null`
- `brief: ResearchBrief`
- `trace_events: list[SavedTraceEvent]`
- `evidence_state: { active_claim_id, expanded_source_id } | null`
- `evaluation: ResearchEvaluationReport | null`
- `archived: bool`
- `archived_at: str | null`
- `created_at: str (ISO)`
- `saved_at: str (ISO)`
- `updated_at: str (ISO)`
- `canonical_signature: str` (SHA256 of canonical content for deterministic audit checks)

Canonical signature notes:

- Canonical hashing intentionally excludes mutable management metadata (`label`, `archived`, `archived_at`, `updated_at`) so analytical payload integrity remains stable.

## SessionComparison

- `left_id: str`
- `right_id: str`
- `signature_match: bool`
- `metadata_diffs: list[{ field, left, right, changed }]`
- `claim_diffs: { bull_added, bull_removed, bear_added, bear_removed, risk_added, risk_removed }`
- `source_diffs: { sources_added, sources_removed }`
- `snapshot_drift: SnapshotDriftReport`
- `conflict_diffs: ConflictDriftReport`
- `trace_diffs: { left_event_count, right_event_count, event_count_delta, event_type_deltas, left_step_range, right_step_range }`
- `summary: { changed_fields, total_changed_fields, total_claim_changes, total_source_changes, thesis_changed, confidence_changed, signature_match, snapshot_id_changes, freshness_changes, source_set_changed, evaluation_signature_changed, snapshot_drift_signature, resolved_conflict_count, unchanged_conflict_count, worsened_conflict_count, conflict_drift_signature }`

## ConflictDriftItem

- `conflict_id: str`
- `title: str`
- `state: "resolved" | "unchanged" | "worsened"`
- `left_severity: str | null`
- `right_severity: str | null`
- `claim_refs_added: list[str]`
- `claim_refs_removed: list[str]`
- `source_refs_added: list[str]`
- `source_refs_removed: list[str]`
- `claim_delta: bool`
- `source_delta: bool`
- `snapshot_delta: bool`

## ConflictDriftReport

- `resolved: list[ConflictDriftItem]`
- `unchanged: list[ConflictDriftItem]`
- `worsened: list[ConflictDriftItem]`
- `drift_signature: str`

## SnapshotDriftReport

- `left_snapshot_signature: str`
- `right_snapshot_signature: str`
- `snapshot_signature_changed: bool`
- `left_evaluation_signature: str | null`
- `right_evaluation_signature: str | null`
- `evaluation_signature_changed: bool`
- `source_set_changed: bool`
- `source_set_delta_count: int`
- `sources_added: list[str]`
- `sources_removed: list[str]`
- `snapshot_ids_changed: list[SnapshotIdDrift]`
- `freshness_changed: list[FreshnessDrift]`
- `drift_signature: str`

## SnapshotIdDrift

- `source_ref: str`
- `left_snapshot_id: str | null`
- `right_snapshot_id: str | null`
- `left_snapshot_kind: str | null`
- `right_snapshot_kind: str | null`

## FreshnessDrift

- `source_ref: str`
- `left_freshness: str | null`
- `right_freshness: str | null`
- `left_freshness_hours: float | null`
- `right_freshness_hours: float | null`

## RecaptureSnapshotTransition

- `source_ref: str`
- `before_snapshot_id: str | null`
- `after_snapshot_id: str | null`
- `before_cache_lineage: str | null`
- `after_cache_lineage: str | null`

## SessionRecaptureLineage

- `source_session_id: str`
- `recaptured_session_id: str`
- `recapture_mode: "demo_pseudo_refresh" | "live_refresh"`
- `before_snapshot_signature: str`
- `after_snapshot_signature: str`
- `snapshot_id_changes: int`
- `source_set_changes: int`
- `transition_count: int`
- `transitions: list[RecaptureSnapshotTransition]`
- `generated_at: str (ISO)`

## SessionRecaptureResult

- `saved: SavedResearchSession`
- `lineage: SessionRecaptureLineage`

## SessionIntegrityReport

- `id: str`
- `signature_valid: bool`
- `canonical_signature: str`
- `recomputed_signature: str`
- `trace_event_count: int`
- `trace_step_order_valid: bool`
- `trace_step_unique: bool`
- `evidence_state_valid: bool`
- `provenance_complete: bool`
- `freshness_valid: bool`
- `freshness_policy_valid: bool`
- `freshness_policy_violation_count: int`
- `snapshot_complete: bool`
- `snapshot_consistent: bool`
- `snapshot_summary_present: bool`
- `snapshot_checksum_complete: bool`
- `evaluation_present: bool`
- `evaluation_valid: bool`
- `evaluation_signature: str | null`
- `bundle_snapshot_signature: str | null`
- `issues: list[str]`
- `checked_at: str (ISO)`
- `provenance: dict[str, Any]`

## SavedResearchSessionSummary (API listing)

- `snapshot_kind_counts: dict[str, int] | null`
- `cache_lineage_counts: dict[str, int] | null`
- `state_label_counts: dict[str, int] | null`
- `latest_fetched_at: str | null`
- `latest_cached_at: str | null`
- `latest_generated_at: str | null`

## SessionBundleExportV2

- `bundle_version: "wave14-v2"`
- `bundle_kind: "session"`
- `exported_at: str (ISO)`
- `manifest: SessionBundleManifest`
- `files: dict[str, Any]`

Required `files` entries:

- `session.json: SavedResearchSession`
- `trace.json: list[SavedTraceEvent]`
- `provenance.json: dict` (snapshot summary, snapshot source projection, signatures)
- `evaluation.json: ResearchEvaluationReport | { available: false }`
- `integrity.json: SessionIntegrityReport`
- `report.md: str` (markdown export payload)
- `timeline.json: ResearchThreadTimelineDetail`
- `compare.json: { available, left_id, right_id, comparison }`

`manifest` includes deterministic signatures and equality checks:

- `deterministic_signature`
- `section_signatures` (per-file SHA256)
- `inventory` (file media type + byte size + SHA256)
- `equality_checks` (session/integrity/evaluation/snapshot parity)

## CollectionBundleExportV2

- `bundle_version: "wave14-v2"`
- `bundle_kind: "collection"`
- `manifest: CollectionBundleManifest`
- `files: dict[str, Any]`

Required `files` entries:

- `collection.json: ResearchCollection`
- `timeline.json: { collection_id, timeline_signature, missing_session_count, timeline[] }`
- `sessions.json: list[session digest rows]`
- `compare.json: { pair_count, pairs[] }`
- `provenance.json: dict`
- `report.md: str`

## ResearchCollection

- `id: str` (must start with `coll-`)
- `title: str` (1..120 chars, trimmed, non-empty)
- `summary: str | null` (trimmed, max 500)
- `notes: str | null` (trimmed, max 2000)
- `session_ids: list[str]` (ordered timeline of saved session ids)
- `created_at: str (ISO)`
- `updated_at: str (ISO)`
- `collection_signature: str` (deterministic SHA256 over title/summary/notes/session_ids)

## ResearchCollectionSummary

- `id: str`
- `title: str`
- `summary: str | null`
- `session_count: int`
- `created_at: str (ISO)`
- `updated_at: str (ISO)`
- `collection_signature: str`

## CreateCollectionRequest

- `title: str` (required, trimmed, non-empty)
- `summary: str | null` (optional)
- `notes: str | null` (optional)

## UpdateCollectionRequest

- `title: str | null` (optional, trimmed, non-empty when present)
- `summary: str | null` (optional)
- `notes: str | null` (optional)

## AddSessionToCollectionRequest

- `session_id: str` (saved-session id)
- `position: int | null` (optional insert index)

## ReorderCollectionSessionsRequest

- `session_ids: list[str]` (must contain exactly the current collection contents, no duplicates)

## ResearchCollectionTimelineEntry

- `session_id: str`
- `exists: bool` (false when collection references a missing deleted session)
- `label: str | null`
- `question: str | null`
- `query_class: "macro_outlook" | "event_probability" | "ticker_macro" | null`
- `template_id: "macro_outlook" | "event_probability_interpretation" | "ticker_macro_framing" | "thesis_change_compare" | null`
- `template_title: str | null`
- `saved_at: str | null`
- `evaluation_passed: bool | null`
- `snapshot_signature: str | null`
- `archived: bool | null`
- `thesis_state: ResearchThesisStateSnapshot | null`
- `thesis_delta: ResearchThesisDelta | null`

## ResearchThesisStateSnapshot

- `thesis: str`
- `confidence: int [1,5]`
- `claim_ids: list[str]`
- `claim_count: int`
- `freshness_policy_violation_count: int`
- `freshness_policy_warning_count: int`
- `conflict_ids: list[str]`
- `conflict_count: int`
- `evaluation_passed: bool | null`
- `evaluation_signature: str | null`

## ResearchThesisDelta

- `previous_session_id: str | null`
- `thesis_changed: bool`
- `confidence_changed: bool`
- `claims_changed: bool`
- `claim_ids_added: list[str]`
- `claim_ids_removed: list[str]`
- `freshness_policy_changed: bool`
- `freshness_policy_violation_delta: int`
- `freshness_policy_warning_delta: int`
- `conflicts_changed: bool`
- `conflict_ids_added: list[str]`
- `conflict_ids_removed: list[str]`
- `evaluation_changed: bool`
- `evaluation_passed_changed: bool`
- `evaluation_signature_before: str | null`
- `evaluation_signature_after: str | null`
- `delta_signature: str` (deterministic hash over stable delta payload)

## ResearchCollectionDetail

- `collection: ResearchCollection`
- `timeline: list[ResearchCollectionTimelineEntry]`
- `missing_session_count: int`
- `timeline_signature: str`

## ResearchThreadTimelineDetail

- `thread_session_id: str`
- `timeline: list[ResearchCollectionTimelineEntry]` (ordered by `saved_at` ascending)
- `timeline_signature: str`

## MispricingScore

- `market_id: str`
- `market_prob: float [0,1]`
- `model_prob: float [0,1]`
- `dislocation: float [0,1]`
- `direction: market_overpriced | market_underpriced`
- `explanation: str`
- `confidence: int [1,5]`
- `scored_at: str (ISO)`

## features.json snapshot

- `yield_curve_current`
- `yield_curve_delta_3m`
- `sahm_gap`
- `recession_signal`
- `inflation_3m_annualized_pct`
- `credit_spread`
- `credit_stress_z`
- `fed_funds`
- `monetary_regime`
- `regime_growth`
- `regime_inflation`
- `regime_monetary`
- `regime_credit`
- `regime_labor`
