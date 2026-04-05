export type TraceEvent = {
  type: 'tool_call' | 'tool_result' | 'reasoning' | 'brief_delta' | 'complete' | 'error' | 'reflection'
  step: number
  ts: string
  session_id?: string
  followup?: boolean
  query_class?: ResearchBrief['query_class']
  template_id?: ResearchTemplateId
  session_context_used?: boolean
  tool?: string
  args?: Record<string, unknown>
  preview?: unknown[]
  text?: string
  section?: string
  brief?: ResearchBrief
  duration_ms?: number
  message?: string
  evaluation?: ResearchEvaluationReport
  provenance?: Record<string, unknown>
  snapshot?: Record<string, unknown>
  content?: {
    step?: number
    tools_used?: string[] | string
    message?: string
    [key: string]: unknown
  }
}

export type ResearchTemplateId =
  | 'macro_outlook'
  | 'event_probability_interpretation'
  | 'ticker_macro_framing'
  | 'thesis_change_compare'

export type ResearchTemplateDefinition = {
  id: ResearchTemplateId
  title: string
  description: string
  framing: string
  query_class_default: NonNullable<ResearchBrief['query_class']>
  emphasis: string[]
  evaluation_expectations: string[]
}

export type SourcePreview = {
  kind?: string
  points?: Array<{ date: string; value: number }>
  [key: string]: unknown
}

export type SnapshotProvenance = {
  snapshot_id: string
  snapshot_kind: 'fixture' | 'cache' | 'live_capture' | 'derived' | 'unknown'
  dataset: string
  dataset_version?: string | null
  generated_at?: string | null
  cached_at?: string | null
  fetched_at?: string | null
  checksum_sha256?: string | null
  deterministic: boolean
}

export type SourceProvenance = {
  source_ref: string
  tool_name: string
  mode: 'demo' | 'live'
  state_label: 'fixture' | 'cached' | 'live' | 'derived' | 'unknown'
  cache_lineage: 'fixture' | 'cache' | 'fresh_pull' | 'derived' | 'unknown'
  observed_at?: string | null
  captured_at: string
  freshness: 'fresh' | 'aging' | 'stale' | 'unknown'
  freshness_hours?: number | null
  deterministic: boolean
  snapshot?: SnapshotProvenance | null
}

export type ResearchEvaluationCheck = {
  check_id: string
  passed: boolean
  detail: string
  value?: number | string | null
}

export type ResearchEvaluationReport = {
  version: string
  deterministic_signature: string
  passed: boolean
  checks: ResearchEvaluationCheck[]
  metrics: Record<string, unknown>
}

export type ResearchEvaluationDashboardFailureType = {
  check_id: string
  count: number
}

export type ResearchEvaluationDashboardSession = {
  id: string
  saved_at: string
  query_class?: ResearchBrief['query_class']
  template_id?: ResearchTemplateId | null
  template_title?: string | null
  evaluation_passed: boolean
  evaluation_signature?: string | null
  failed_checks: string[]
  provenance_gap_count: number
  stale_source_count: number
  claim_linking_gap_count: number
}

export type ResearchEvaluationDashboard = {
  generated_at: string
  session_count: number
  passed_count: number
  failed_count: number
  pass_rate: number
  provenance_gap_session_count: number
  provenance_gap_total_count: number
  stale_source_session_count: number
  stale_source_total_count: number
  claim_linking_gap_session_count: number
  claim_linking_gap_total_count: number
  common_failure_types: ResearchEvaluationDashboardFailureType[]
  template_usage: Record<string, number>
  sessions: ResearchEvaluationDashboardSession[]
  deterministic_signature: string
  ready_for_export: boolean
  filters: Record<string, unknown>
}

export type BriefPoint = {
  claim_id: string
  point: string
  source_ref: string
}

export type RiskPoint = {
  claim_id: string
  risk: string
  source_ref: string
}

export type SourceItem = {
  type: 'fred' | 'edgar' | 'news' | 'market'
  id: string
  excerpt: string
  claim_refs?: string[]
  preview?: SourcePreview
  provenance?: SourceProvenance
}

export type SignalConflict = {
  conflict_id: string
  title: string
  summary: string
  severity: 'low' | 'medium' | 'high'
  claim_refs: string[]
  source_refs: string[]
}

export type EvidenceNavigationState = {
  active_claim_id: string | null
  expanded_source_id: string | null
}

export type ResearchBrief = {
  question: string
  query_class?: 'macro_outlook' | 'event_probability' | 'ticker_macro'
  template_id?: ResearchTemplateId
  template_title?: string | null
  follow_up_context?: string | null
  thesis: string
  bull_case: BriefPoint[]
  bear_case: BriefPoint[]
  key_risks: RiskPoint[]
  confidence: number
  confidence_rationale: string
  methodology_summary?: string | null
  sources: SourceItem[]
  signal_conflicts?: SignalConflict[]
  provenance_summary?: Record<string, unknown> | null
  snapshot_summary?: Record<string, unknown> | null
  created_at: string
  trace_steps: number[]
}

export type SavedResearchSessionSummary = {
  id: string
  question: string
  mode: 'demo' | 'live'
  session_id: string
  label?: string | null
  query_class?: ResearchBrief['query_class']
  template_id?: ResearchTemplateId | null
  template_title?: string | null
  follow_up_context?: string | null
  archived?: boolean
  archived_at?: string | null
  saved_at: string
  updated_at?: string
  canonical_signature: string
  evaluation_passed?: boolean | null
  evaluation_signature?: string | null
  snapshot_kind_counts?: Record<string, number> | null
  cache_lineage_counts?: Record<string, number> | null
  state_label_counts?: Record<string, number> | null
  latest_fetched_at?: string | null
  latest_cached_at?: string | null
  latest_generated_at?: string | null
  snapshot_signature?: string | null
}

export type SavedResearchSession = SavedResearchSessionSummary & {
  brief: ResearchBrief
  trace_events: TraceEvent[]
  evidence_state?: EvidenceNavigationState | null
  evaluation?: ResearchEvaluationReport | null
  archived?: boolean
  archived_at?: string | null
  created_at: string
  updated_at: string
}

export type ResearchCollectionSummary = {
  id: string
  title: string
  summary?: string | null
  session_count: number
  created_at: string
  updated_at: string
  collection_signature: string
}

export type ResearchThesisStateSnapshot = {
  thesis: string
  confidence: number
  claim_ids: string[]
  claim_count: number
  freshness_policy_violation_count: number
  freshness_policy_warning_count: number
  conflict_ids: string[]
  conflict_count: number
  evaluation_passed?: boolean | null
  evaluation_signature?: string | null
}

export type ResearchThesisDelta = {
  previous_session_id?: string | null
  thesis_changed: boolean
  confidence_changed: boolean
  claims_changed: boolean
  claim_ids_added: string[]
  claim_ids_removed: string[]
  freshness_policy_changed: boolean
  freshness_policy_violation_delta: number
  freshness_policy_warning_delta: number
  conflicts_changed: boolean
  conflict_ids_added: string[]
  conflict_ids_removed: string[]
  evaluation_changed: boolean
  evaluation_passed_changed: boolean
  evaluation_signature_before?: string | null
  evaluation_signature_after?: string | null
  delta_signature: string
}

export type ResearchCollectionTimelineEntry = {
  session_id: string
  exists: boolean
  label?: string | null
  question?: string | null
  query_class?: ResearchBrief['query_class']
  template_id?: ResearchTemplateId | null
  template_title?: string | null
  saved_at?: string | null
  evaluation_passed?: boolean | null
  snapshot_signature?: string | null
  archived?: boolean | null
  thesis_state?: ResearchThesisStateSnapshot | null
  thesis_delta?: ResearchThesisDelta | null
}

export type ResearchCollection = {
  id: string
  title: string
  summary?: string | null
  notes?: string | null
  session_ids: string[]
  created_at: string
  updated_at: string
  collection_signature: string
  timeline: ResearchCollectionTimelineEntry[]
  missing_session_count: number
  timeline_signature: string
}

export type ResearchThreadTimelineDetail = {
  thread_session_id: string
  timeline: ResearchCollectionTimelineEntry[]
  timeline_signature: string
}

export type SessionRecaptureLineage = {
  source_session_id: string
  recaptured_session_id: string
  recapture_mode: 'demo_pseudo_refresh' | 'live_refresh'
  before_snapshot_signature: string
  after_snapshot_signature: string
  snapshot_id_changes: number
  source_set_changes: number
  transition_count: number
  transitions: Array<{
    source_ref: string
    before_snapshot_id?: string | null
    after_snapshot_id?: string | null
    before_cache_lineage?: string | null
    after_cache_lineage?: string | null
  }>
  generated_at: string
}

export type SessionRecaptureResult = {
  saved: SavedResearchSession
  lineage: SessionRecaptureLineage
}

export type SessionComparison = {
  left_id: string
  right_id: string
  signature_match: boolean
  metadata_diffs: Array<{
    field: string
    left: unknown
    right: unknown
    changed: boolean
  }>
  claim_diffs: Record<string, string[]>
  source_diffs: Record<string, string[]>
  snapshot_drift: {
    left_snapshot_signature: string
    right_snapshot_signature: string
    snapshot_signature_changed: boolean
    left_evaluation_signature?: string | null
    right_evaluation_signature?: string | null
    evaluation_signature_changed: boolean
    source_set_changed: boolean
    source_set_delta_count: number
    sources_added: string[]
    sources_removed: string[]
    snapshot_ids_changed: Array<{
      source_ref: string
      left_snapshot_id?: string | null
      right_snapshot_id?: string | null
      left_snapshot_kind?: string | null
      right_snapshot_kind?: string | null
    }>
    freshness_changed: Array<{
      source_ref: string
      left_freshness?: string | null
      right_freshness?: string | null
      left_freshness_hours?: number | null
      right_freshness_hours?: number | null
    }>
    drift_signature: string
  }
  conflict_diffs: {
    resolved: Array<{
      conflict_id: string
      title: string
      state: 'resolved' | 'unchanged' | 'worsened'
      left_severity?: string | null
      right_severity?: string | null
      claim_refs_added: string[]
      claim_refs_removed: string[]
      source_refs_added: string[]
      source_refs_removed: string[]
      claim_delta: boolean
      source_delta: boolean
      snapshot_delta: boolean
    }>
    unchanged: Array<{
      conflict_id: string
      title: string
      state: 'resolved' | 'unchanged' | 'worsened'
      left_severity?: string | null
      right_severity?: string | null
      claim_refs_added: string[]
      claim_refs_removed: string[]
      source_refs_added: string[]
      source_refs_removed: string[]
      claim_delta: boolean
      source_delta: boolean
      snapshot_delta: boolean
    }>
    worsened: Array<{
      conflict_id: string
      title: string
      state: 'resolved' | 'unchanged' | 'worsened'
      left_severity?: string | null
      right_severity?: string | null
      claim_refs_added: string[]
      claim_refs_removed: string[]
      source_refs_added: string[]
      source_refs_removed: string[]
      claim_delta: boolean
      source_delta: boolean
      snapshot_delta: boolean
    }>
    drift_signature: string
  }
  trace_diffs: {
    left_event_count: number
    right_event_count: number
    event_count_delta: number
    event_type_deltas: Record<string, number>
    left_step_range: Array<number | null>
    right_step_range: Array<number | null>
  }
  summary: {
    changed_fields: string[]
    total_changed_fields: number
    total_claim_changes: number
    total_source_changes: number
    thesis_changed: boolean
    confidence_changed: boolean
    signature_match: boolean
    snapshot_id_changes: number
    freshness_changes: number
    source_set_changed: boolean
    evaluation_signature_changed: boolean
    snapshot_drift_signature: string
    resolved_conflict_count: number
    unchanged_conflict_count: number
    worsened_conflict_count: number
    conflict_drift_signature: string
  }
}

export type SessionIntegrityReport = {
  id: string
  signature_valid: boolean
  canonical_signature: string
  recomputed_signature: string
  trace_event_count: number
  trace_step_order_valid: boolean
  trace_step_unique: boolean
  evidence_state_valid: boolean
  provenance_complete: boolean
  freshness_valid: boolean
  freshness_policy_valid: boolean
  freshness_policy_violation_count: number
  snapshot_complete: boolean
  snapshot_consistent: boolean
  snapshot_summary_present: boolean
  snapshot_checksum_complete: boolean
  evaluation_present: boolean
  evaluation_valid: boolean
  evaluation_signature?: string | null
  bundle_snapshot_signature?: string | null
  issues: string[]
  checked_at: string
  provenance: Record<string, unknown>
}

export type ResearchReviewChecklistItem = {
  check_id: string
  title: string
  passed: boolean
  detail: string
  value?: string | number | null
}

export type ResearchReviewChecklist = {
  saved_id?: string | null
  session_id?: string | null
  status: 'pass' | 'fail'
  completed: boolean
  passed_count: number
  failed_count: number
  total_count: number
  deterministic_signature: string
  generated_at: string
  summary: string
  items: ResearchReviewChecklistItem[]
}
