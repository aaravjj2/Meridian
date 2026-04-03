export type TraceEvent = {
  type: 'tool_call' | 'tool_result' | 'reasoning' | 'brief_delta' | 'complete' | 'error' | 'reflection'
  step: number
  ts: string
  session_id?: string
  followup?: boolean
  query_class?: ResearchBrief['query_class']
  session_context_used?: boolean
  tool?: string
  args?: Record<string, unknown>
  preview?: unknown[]
  text?: string
  section?: string
  brief?: ResearchBrief
  duration_ms?: number
  message?: string
  content?: {
    step?: number
    tools_used?: string[] | string
    message?: string
    [key: string]: unknown
  }
}

export type SourcePreview = {
  kind?: string
  points?: Array<{ date: string; value: number }>
  [key: string]: unknown
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
}

export type SignalConflict = {
  conflict_id: string
  title: string
  summary: string
  severity: 'low' | 'medium' | 'high'
  claim_refs: string[]
  source_refs: string[]
}

export type ResearchBrief = {
  question: string
  query_class?: 'macro_outlook' | 'event_probability' | 'ticker_macro'
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
  created_at: string
  trace_steps: number[]
}
