export type TraceEvent = {
  type: 'tool_call' | 'tool_result' | 'reasoning' | 'brief_delta' | 'complete' | 'error' | 'reflection'
  step: number
  ts: string
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

export type BriefPoint = {
  point: string
  source_ref: string
}

export type RiskPoint = {
  risk: string
  source_ref: string
}

export type SourceItem = {
  type: 'fred' | 'edgar' | 'news' | 'market'
  id: string
  excerpt: string
}

export type ResearchBrief = {
  question: string
  thesis: string
  bull_case: BriefPoint[]
  bear_case: BriefPoint[]
  key_risks: RiskPoint[]
  confidence: number
  confidence_rationale: string
  sources: SourceItem[]
  created_at: string
  trace_steps: number[]
}
