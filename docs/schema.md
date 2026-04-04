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
- `created_at: str (ISO)`
- `trace_steps: list[int]`

Validation notes:

- `claim_id` values are unique across bull/bear/risk sections.
- Every claim must be linked from at least one `sources[].claim_refs` entry.
- `signal_conflicts[].claim_refs` must reference valid `claim_id` values.
- `signal_conflicts[].source_refs` uses `type:id` format (example: `fred:T10Y2Y`).

## SourceProvenance

- `source_ref: str` (`type:id`)
- `tool_name: str`
- `mode: "demo" | "live"`
- `observed_at: str | null`
- `captured_at: str`
- `freshness: "fresh" | "aging" | "stale" | "unknown"`
- `freshness_hours: float | null`
- `deterministic: bool`

## ResearchEvaluationReport

- `version: str` (currently `phase-6`)
- `deterministic_signature: str` (SHA256 over stable evaluation projection)
- `passed: bool`
- `checks: list[{ check_id, passed, detail, value? }]`
- `metrics: dict[str, Any]`

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
- `trace_diffs: { left_event_count, right_event_count, event_count_delta, event_type_deltas, left_step_range, right_step_range }`
- `summary: { changed_fields, total_changed_fields, total_claim_changes, total_source_changes, thesis_changed, confidence_changed, signature_match }`

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
- `evaluation_present: bool`
- `evaluation_valid: bool`
- `evaluation_signature: str | null`
- `issues: list[str]`
- `checked_at: str (ISO)`
- `provenance: dict[str, Any]`

## SessionBundleExport

- `bundle_version: str`
- `exported_at: str (ISO)`
- `session: SavedResearchSession`
- `integrity: SessionIntegrityReport`
- `evaluation: ResearchEvaluationReport | null`
- `provenance: { source, app_version, model, mode, freshness_counts, evaluation_signature }`

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
