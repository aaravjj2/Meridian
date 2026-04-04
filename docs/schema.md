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

## ResearchBrief

- `question: str`
- `thesis: str`
- `bull_case: list[{ claim_id, point, source_ref }]` (3-5)
- `bear_case: list[{ claim_id, point, source_ref }]` (2-5)
- `key_risks: list[{ claim_id, risk, source_ref }]` (>=2)
- `confidence: int [1, 5]`
- `confidence_rationale: str`
- `sources: list[{ type, id, excerpt, claim_refs?, preview?, provenance? }]`
- `signal_conflicts: list[{ conflict_id, title, summary, severity, claim_refs, source_refs }]`
- `provenance_summary: dict | null` (captured_at, mode, source_count, freshness_counts)
- `snapshot_summary: dict | null` (snapshot_count, snapshot_kind_counts, cache_lineage_counts, freshness_by_snapshot_kind, snapshot_checksum_coverage)
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

## SessionBundleExport

- `bundle_version: str`
- `exported_at: str (ISO)`
- `session: SavedResearchSession`
- `integrity: SessionIntegrityReport`
- `evaluation: ResearchEvaluationReport | null`
- `snapshot_provenance: { summary, sources, signature_sha256 }`
- `provenance: { source, app_version, model, mode, freshness_counts, snapshot_kind_counts, cache_lineage_counts, snapshot_signature, evaluation_signature }`

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
- `saved_at: str | null`
- `evaluation_passed: bool | null`
- `snapshot_signature: str | null`
- `archived: bool | null`

## ResearchCollectionDetail

- `collection: ResearchCollection`
- `timeline: list[ResearchCollectionTimelineEntry]`
- `missing_session_count: int`

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
