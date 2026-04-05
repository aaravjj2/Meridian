'use client'

import { useCallback, useEffect, useState } from 'react'

import { createParser } from 'eventsource-parser'

import RegimeDashboard from '@/components/RegimeDashboard/RegimeDashboard'
import QueryInput from '@/components/Terminal/QueryInput'
import ResearchPanel from '@/components/Terminal/ResearchPanel'
import SplitPane from '@/components/Terminal/SplitPane'
import TracePanel from '@/components/Terminal/TracePanel'
import WorkspacePanel from '@/components/Terminal/WorkspacePanel'
import type {
  EvidenceNavigationState,
  ResearchCollection,
  ResearchCollectionSummary,
  ResearchEvaluationDashboard,
  ResearchEvaluationReport,
  ResearchRegressionPackRun,
  ResearchRegressionPackSummary,
  ResearchBrief,
  ResearchReviewChecklist,
  ResearchTemplateDefinition,
  ResearchTemplateId,
  SessionRecaptureLineage,
  SessionRecaptureResult,
  SessionComparison,
  SessionIntegrityReport,
  SavedResearchSession,
  SavedResearchSessionSummary,
  ResearchThreadTimelineDetail,
  TraceEvent,
} from '@/components/Terminal/types'

type SaveResearchSessionRequest = {
  question: string
  mode: 'demo' | 'live'
  session_id: string
  label?: string | null
  template_id?: ResearchTemplateId | null
  brief: ResearchBrief
  trace_events: TraceEvent[]
  evidence_state: EvidenceNavigationState | null
  evaluation?: ResearchEvaluationReport | null
}

type ListSavedSessionsOptions = {
  search?: string
  includeArchived?: boolean
  queryClass?: ResearchBrief['query_class'] | 'all'
}

const FALLBACK_EVENTS: TraceEvent[] = [
  {
    type: 'tool_call',
    step: 0,
    tool: 'fred_fetch',
    args: { series_id: 'T10Y2Y' },
    ts: '2026-04-02T00:00:00Z',
  },
  {
    type: 'tool_result',
    step: 1,
    tool: 'fred_fetch',
    preview: [
      ['2025-12-15', -0.35],
      ['2026-01-15', -0.29],
      ['2026-02-15', -0.21],
    ],
    ts: '2026-04-02T00:00:01Z',
  },
  {
    type: 'reasoning',
    step: 2,
    text: 'Yield curve inversion is easing but remains a cautionary macro signal.',
    ts: '2026-04-02T00:00:02Z',
  },
  {
    type: 'reflection',
    step: 3,
    ts: '2026-04-02T00:00:03Z',
    content: {
      step: 3,
      tools_used: ['fred_fetch', 'news_fetch'],
      message: 'Fallback reflection checkpoint confirms deterministic local replay path.',
    },
  },
  {
    type: 'tool_call',
    step: 4,
    tool: 'news_fetch',
    args: { topic: 'fed rate decision recession', days_back: 7 },
    ts: '2026-04-02T00:00:04Z',
  },
  {
    type: 'tool_result',
    step: 5,
    tool: 'news_fetch',
    preview: [['articles', 2]],
    ts: '2026-04-02T00:00:05Z',
  },
  {
    type: 'reasoning',
    step: 6,
    text: 'Fallback replay complete with deterministic local trace.',
    ts: '2026-04-02T00:00:06Z',
  },
  {
    type: 'complete',
    step: 7,
    ts: '2026-04-02T00:00:07Z',
  },
]

const FALLBACK_RESEARCH_TEMPLATES: ResearchTemplateDefinition[] = [
  {
    id: 'macro_outlook',
    title: 'Macro outlook',
    description: 'Build a balanced macro baseline with explicit bull, bear, and risk structure.',
    framing: 'Start from cycle position, inflation trend, and policy stance before sizing risk.',
    query_class_default: 'macro_outlook',
    emphasis: ['Cycle and regime interpretation', 'Cross-check inflation, growth, and credit', 'Translate evidence into scenario odds'],
    evaluation_expectations: ['At least one macro signal conflict is surfaced', 'Freshness and snapshot provenance checks pass'],
  },
  {
    id: 'event_probability_interpretation',
    title: 'Event probability interpretation',
    description: 'Interpret market-implied event odds against macro evidence and policy context.',
    framing: 'Start from priced probabilities, then test whether macro inputs justify that pricing.',
    query_class_default: 'event_probability',
    emphasis: ['Cross-venue probability consistency', 'Macro validation of priced odds', 'Repricing and communication tail risks'],
    evaluation_expectations: ['Event-odds claims map to market sources', 'Confidence rationale discusses timing risk'],
  },
  {
    id: 'ticker_macro_framing',
    title: 'Ticker + macro framing',
    description: 'Blend single-name or sector positioning with macro and credit regime overlays.',
    framing: 'Combine bottom-up fundamental context with top-down macro risk budgeting.',
    query_class_default: 'ticker_macro',
    emphasis: ['Fundamental versus macro tension', 'Credit and policy sensitivity', 'Positioning risk controls'],
    evaluation_expectations: ['Thesis references both ticker and macro evidence', 'Conflict section captures bottom-up vs top-down tension'],
  },
  {
    id: 'thesis_change_compare',
    title: 'Compare old vs new thesis',
    description: 'Update or challenge a prior thesis and make deltas explicit for auditability.',
    framing: 'Anchor on prior thesis context, then highlight what changed and why.',
    query_class_default: 'macro_outlook',
    emphasis: ['Prior-vs-current thesis deltas', 'Evidence that changed confidence', 'Explicit conflict and risk updates'],
    evaluation_expectations: ['Follow-up context is present when available', 'Delta-oriented reasoning is reflected in thesis narrative'],
  },
]

function classifyQuery(question: string): ResearchBrief['query_class'] {
  const lowered = question.toLowerCase()
  const upper = question.toUpperCase()
  const tickerTokens = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'META', 'GOOGL', 'XLF', 'XLK', 'XLE', 'SMH']

  if (tickerTokens.some((token) => upper.includes(token)) || lowered.includes('ticker') || lowered.includes('sector')) {
    return 'ticker_macro'
  }
  if (
    lowered.includes('probability') ||
    lowered.includes('odds') ||
    lowered.includes('chance') ||
    lowered.includes('implied') ||
    lowered.includes('priced')
  ) {
    return 'event_probability'
  }
  return 'macro_outlook'
}

function fallbackBrief(
  question: string,
  priorQuestion: string | null,
  template: ResearchTemplateDefinition
): ResearchBrief {
  const queryClass = template.query_class_default ?? classifyQuery(question)
  return {
    question,
    query_class: queryClass,
    template_id: template.id,
    template_title: template.title,
    follow_up_context: priorQuestion ? `Follow-up to prior question: ${priorQuestion}` : null,
    thesis:
      queryClass === 'event_probability'
        ? 'Fallback event-probability interpretation suggests current pricing leans toward easing but remains sensitive to inflation surprises.'
        : queryClass === 'ticker_macro'
          ? 'Fallback ticker-plus-macro framing favors quality exposure with explicit risk controls tied to credit and growth signals.'
          : 'Fallback macro outlook indicates a late-cycle mix: easing inflation trend versus persistent inversion and credit caution.',
    bull_case: [
      {
        claim_id: 'bull-1-disinflation-progress',
        point: 'Disinflation progress supports policy flexibility in baseline scenarios.',
        source_ref: 'fred_fetch:CPIAUCSL',
      },
      {
        claim_id: 'bull-2-event-pricing-supports-easing',
        point: 'Event-pricing data indicates easing expectations remain active.',
        source_ref: 'prediction_market_fetch:KXFEDCUT-H1-2026',
      },
      {
        claim_id: 'bull-3-growth-absorption-capacity',
        point: 'Risk assets can remain supported if growth deceleration stays orderly.',
        source_ref: 'fred_fetch:GDPC1',
      },
    ],
    bear_case: [
      {
        claim_id: 'bear-1-curve-inversion-warning',
        point: 'Curve inversion still signals lagged downside growth risk.',
        source_ref: 'fred_fetch:T10Y2Y',
      },
      {
        claim_id: 'bear-2-credit-spread-caution',
        point: 'Credit spreads remain above low-stress ranges.',
        source_ref: 'fred_fetch:BAMLH0A0HYM2',
      },
    ],
    key_risks: [
      {
        claim_id: 'risk-1-inflation-reacceleration',
        risk: 'Inflation re-acceleration can delay easing and tighten conditions.',
        source_ref: 'fred_fetch:CPIAUCSL',
      },
      {
        claim_id: 'risk-2-policy-communication-shock',
        risk: 'Policy communication shocks can reprice event probabilities rapidly.',
        source_ref: 'news_fetch:fed-rate-decision',
      },
    ],
    confidence: 3,
    confidence_rationale: 'Fallback mode provides deterministic but reduced-depth synthesis.',
    methodology_summary: 'Deterministic fallback replay using fixture-backed macro and event context.',
    sources: [
      {
        type: 'fred',
        id: 'T10Y2Y',
        excerpt: 'Curve inversion has moderated from recent lows.',
        claim_refs: ['bear-1-curve-inversion-warning'],
        preview: {
          kind: 'fred_series',
          series_id: 'T10Y2Y',
          latest: -0.21,
          delta_lookback: 0.14,
          points: [
            { date: '2025-11-01', value: -0.38 },
            { date: '2025-12-01', value: -0.35 },
            { date: '2026-01-01', value: -0.29 },
            { date: '2026-02-01', value: -0.21 },
          ],
        },
      },
      {
        type: 'fred',
        id: 'CPIAUCSL',
        excerpt: 'Inflation index remains elevated but trend has eased.',
        claim_refs: ['bull-1-disinflation-progress', 'risk-1-inflation-reacceleration'],
        preview: {
          kind: 'fred_series',
          series_id: 'CPIAUCSL',
          latest: 318.211,
          delta_lookback: 0.756,
          points: [
            { date: '2025-11-01', value: 317.455 },
            { date: '2026-01-01', value: 317.902 },
            { date: '2026-02-01', value: 318.211 },
          ],
        },
      },
      {
        type: 'market',
        id: 'KXFEDCUT-H1-2026',
        excerpt: 'Kalshi cut-probability remains elevated in mid-2026 contracts.',
        claim_refs: ['bull-2-event-pricing-supports-easing'],
        preview: {
          kind: 'market_contract',
          platform: 'kalshi',
          market_prob: 0.64,
          model_prob: 0.45,
          dislocation: 0.19,
        },
      },
      {
        type: 'fred',
        id: 'GDPC1',
        excerpt: 'Real GDP has remained positive, supporting orderly slowdown scenarios.',
        claim_refs: ['bull-3-growth-absorption-capacity'],
        preview: {
          kind: 'fred_series',
          series_id: 'GDPC1',
          latest: 23201.58,
          delta_lookback: 148.24,
          points: [
            { date: '2025-07-01', value: 22995.11 },
            { date: '2025-10-01', value: 23053.34 },
            { date: '2026-01-01', value: 23124.17 },
            { date: '2026-04-01', value: 23201.58 },
          ],
        },
      },
      {
        type: 'fred',
        id: 'BAMLH0A0HYM2',
        excerpt: 'High-yield spreads remain above benign-cycle lows.',
        claim_refs: ['bear-2-credit-spread-caution'],
        preview: {
          kind: 'fred_series',
          series_id: 'BAMLH0A0HYM2',
          latest: 3.72,
          delta_lookback: -0.18,
          points: [
            { date: '2025-11-01', value: 3.9 },
            { date: '2025-12-01', value: 3.85 },
            { date: '2026-01-01', value: 3.79 },
            { date: '2026-02-01', value: 3.72 },
          ],
        },
      },
      {
        type: 'news',
        id: 'fed-rate-decision',
        excerpt: 'Recent coverage highlights data-dependent easing with recession hedging.',
        claim_refs: ['risk-2-policy-communication-shock'],
        preview: {
          kind: 'news_digest',
          topic: 'fed-rate-decision',
          headlines: ['Fed signals data-dependent easing path', 'Bond market prices faster cuts after dovish remarks'],
        },
      },
    ],
    signal_conflicts: [
      {
        conflict_id: 'conflict-curve-improving-vs-risky',
        title: 'Curve Improvement Versus Residual Inversion Risk',
        summary: 'The inversion has improved from extremes while still signaling caution for lagged growth outcomes.',
        severity: 'medium',
        claim_refs: ['bull-3-growth-absorption-capacity', 'bear-1-curve-inversion-warning'],
        source_refs: ['fred:T10Y2Y', 'fred:GDPC1'],
      },
      {
        conflict_id: 'conflict-disinflation-vs-tail-risk',
        title: 'Disinflation Baseline Versus Inflation Tail Risk',
        summary: 'Cooling inflation supports easing assumptions, yet tail risk remains non-trivial in policy-sensitive windows.',
        severity: 'high',
        claim_refs: ['bull-1-disinflation-progress', 'risk-1-inflation-reacceleration'],
        source_refs: ['fred:CPIAUCSL'],
      },
    ],
    created_at: '2026-04-02T00:00:09Z',
    trace_steps: [0, 1, 2, 3, 4, 5, 6, 7],
  }
}

async function streamResearch(
  question: string,
  sessionId: string | null,
  templateId: ResearchTemplateId,
  onEvent: (step: TraceEvent) => void
): Promise<void> {
  const response = await fetch('/api/v1/research', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, mode: 'demo', session_id: sessionId ?? undefined, template_id: templateId }),
  })

  if (!response.ok) {
    throw new Error(`Research endpoint failed: ${response.status}`)
  }

  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('text/event-stream')) {
    throw new Error('Research endpoint returned non-SSE content')
  }

  if (!response.body) {
    throw new Error('No response body from research endpoint')
  }

  let parsedEvents = 0

  const parser = createParser({
    onEvent(event) {
      parsedEvents += 1
      const parsed = JSON.parse(event.data) as TraceEvent
      onEvent(parsed)
    },
  })

  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    parser.feed(decoder.decode(value, { stream: true }))
  }

  if (parsedEvents === 0) {
    throw new Error('Research stream produced zero events')
  }
}

async function listSavedSessions(options?: ListSavedSessionsOptions): Promise<SavedResearchSessionSummary[]> {
  const params = new URLSearchParams()
  if (options?.search?.trim()) {
    params.set('search', options.search.trim())
  }
  if (options?.includeArchived) {
    params.set('include_archived', 'true')
  }
  if (options?.queryClass && options.queryClass !== 'all') {
    params.set('query_class', options.queryClass)
  }
  const query = params.toString()
  const response = await fetch(`/api/v1/research/sessions${query ? `?${query}` : ''}`)
  if (!response.ok) {
    throw new Error(`Failed to list saved sessions: ${response.status}`)
  }
  const payload = (await response.json()) as { sessions?: SavedResearchSessionSummary[] }
  return payload.sessions ?? []
}

async function listResearchTemplates(): Promise<ResearchTemplateDefinition[]> {
  const response = await fetch('/api/v1/research/templates')
  if (!response.ok) {
    throw new Error(`Failed to load research templates: ${response.status}`)
  }
  const payload = (await response.json()) as { templates?: ResearchTemplateDefinition[] }
  return payload.templates ?? []
}

async function saveSession(payload: SaveResearchSessionRequest): Promise<SavedResearchSession> {
  const response = await fetch('/api/v1/research/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(`Failed to save session: ${response.status}`)
  }
  return (await response.json()) as SavedResearchSession
}

async function getSavedSession(savedId: string): Promise<SavedResearchSession> {
  const response = await fetch(`/api/v1/research/sessions/${encodeURIComponent(savedId)}`)
  if (!response.ok) {
    throw new Error(`Failed to load saved session: ${response.status}`)
  }
  return (await response.json()) as SavedResearchSession
}

async function renameSavedSession(savedId: string, label: string | null): Promise<SavedResearchSession> {
  const response = await fetch(`/api/v1/research/sessions/${encodeURIComponent(savedId)}/rename`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ label }),
  })
  if (!response.ok) {
    throw new Error(`Failed to rename session: ${response.status}`)
  }
  return (await response.json()) as SavedResearchSession
}

async function archiveSavedSession(savedId: string, archived: boolean): Promise<SavedResearchSession> {
  const response = await fetch(`/api/v1/research/sessions/${encodeURIComponent(savedId)}/archive`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ archived }),
  })
  if (!response.ok) {
    throw new Error(`Failed to update archive status: ${response.status}`)
  }
  return (await response.json()) as SavedResearchSession
}

async function deleteSavedSession(savedId: string): Promise<void> {
  const response = await fetch(`/api/v1/research/sessions/${encodeURIComponent(savedId)}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error(`Failed to delete session: ${response.status}`)
  }
}

async function compareSavedSessions(leftId: string, rightId: string): Promise<SessionComparison> {
  const params = new URLSearchParams({ left_id: leftId, right_id: rightId })
  const response = await fetch(`/api/v1/research/sessions/compare?${params.toString()}`)
  if (!response.ok) {
    throw new Error(`Failed to compare sessions: ${response.status}`)
  }
  return (await response.json()) as SessionComparison
}

async function recaptureSavedSession(savedId: string): Promise<SessionRecaptureResult> {
  const response = await fetch(`/api/v1/research/sessions/${encodeURIComponent(savedId)}/recapture`, {
    method: 'POST',
  })
  if (!response.ok) {
    throw new Error(`Failed to recapture session: ${response.status}`)
  }
  return (await response.json()) as SessionRecaptureResult
}

async function getSavedSessionIntegrity(savedId: string): Promise<SessionIntegrityReport> {
  const response = await fetch(`/api/v1/research/sessions/${encodeURIComponent(savedId)}/integrity`)
  if (!response.ok) {
    throw new Error(`Failed to verify integrity: ${response.status}`)
  }
  return (await response.json()) as SessionIntegrityReport
}

async function getSavedSessionReview(savedId: string): Promise<ResearchReviewChecklist> {
  const response = await fetch(`/api/v1/research/sessions/${encodeURIComponent(savedId)}/review`)
  if (!response.ok) {
    throw new Error(`Failed to run guided review: ${response.status}`)
  }
  return (await response.json()) as ResearchReviewChecklist
}

async function getWorkspaceIntegrity(options?: { search?: string; includeArchived?: boolean }): Promise<SessionIntegrityReport[]> {
  const params = new URLSearchParams()
  if (options?.search?.trim()) {
    params.set('search', options.search.trim())
  }
  if (options?.includeArchived !== false) {
    params.set('include_archived', 'true')
  }
  const query = params.toString()
  const response = await fetch(`/api/v1/research/sessions/integrity${query ? `?${query}` : ''}`)
  if (!response.ok) {
    throw new Error(`Failed to verify workspace integrity: ${response.status}`)
  }
  const payload = (await response.json()) as { reports?: SessionIntegrityReport[] }
  return payload.reports ?? []
}

async function getWorkspaceEvaluationDashboard(options?: ListSavedSessionsOptions): Promise<ResearchEvaluationDashboard> {
  const params = new URLSearchParams()
  if (options?.search?.trim()) {
    params.set('search', options.search.trim())
  }
  if (options?.includeArchived) {
    params.set('include_archived', 'true')
  }
  if (options?.queryClass && options.queryClass !== 'all') {
    params.set('query_class', options.queryClass)
  }
  const query = params.toString()
  const response = await fetch(`/api/v1/research/sessions/evaluation/dashboard${query ? `?${query}` : ''}`)
  if (!response.ok) {
    throw new Error(`Failed to build evaluation dashboard: ${response.status}`)
  }
  return (await response.json()) as ResearchEvaluationDashboard
}

async function exportWorkspaceEvaluationDashboard(options?: ListSavedSessionsOptions): Promise<Response> {
  const params = new URLSearchParams()
  if (options?.search?.trim()) {
    params.set('search', options.search.trim())
  }
  if (options?.includeArchived) {
    params.set('include_archived', 'true')
  }
  if (options?.queryClass && options.queryClass !== 'all') {
    params.set('query_class', options.queryClass)
  }
  const query = params.toString()
  const response = await fetch(`/api/v1/research/sessions/evaluation/dashboard/export${query ? `?${query}` : ''}`)
  if (!response.ok) {
    throw new Error(`Failed to export evaluation dashboard: ${response.status}`)
  }
  return response
}

async function listRegressionPacks(): Promise<ResearchRegressionPackSummary[]> {
  const response = await fetch('/api/v1/research/sessions/regression/packs')
  if (!response.ok) {
    throw new Error(`Failed to list regression packs: ${response.status}`)
  }
  const payload = (await response.json()) as { packs?: ResearchRegressionPackSummary[] }
  return payload.packs ?? []
}

async function createRegressionPack(payload: {
  title: string
  description?: string | null
  session_ids: string[]
}): Promise<ResearchRegressionPackSummary> {
  const response = await fetch('/api/v1/research/sessions/regression/packs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(`Failed to create regression pack: ${response.status}`)
  }
  return (await response.json()) as ResearchRegressionPackSummary
}

async function deleteRegressionPack(packId: string): Promise<void> {
  const response = await fetch(`/api/v1/research/sessions/regression/packs/${encodeURIComponent(packId)}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error(`Failed to delete regression pack: ${response.status}`)
  }
}

async function runRegressionPack(packId: string): Promise<ResearchRegressionPackRun> {
  const response = await fetch(`/api/v1/research/sessions/regression/packs/${encodeURIComponent(packId)}/run`, {
    method: 'POST',
  })
  if (!response.ok) {
    throw new Error(`Failed to run regression pack: ${response.status}`)
  }
  return (await response.json()) as ResearchRegressionPackRun
}

async function exportRegressionPackRun(packId: string): Promise<Response> {
  const response = await fetch(
    `/api/v1/research/sessions/regression/packs/${encodeURIComponent(packId)}/run/export`
  )
  if (!response.ok) {
    throw new Error(`Failed to export regression pack run: ${response.status}`)
  }
  return response
}

type CollectionDetailResponse = {
  collection: Omit<ResearchCollection, 'timeline' | 'missing_session_count' | 'timeline_signature'>
  timeline?: ResearchCollection['timeline']
  missing_session_count?: number
  timeline_signature?: string
}

function normalizeCollectionDetail(payload: CollectionDetailResponse | ResearchCollection): ResearchCollection {
  if ('collection' in payload) {
    return {
      ...payload.collection,
      timeline: payload.timeline ?? [],
      missing_session_count: payload.missing_session_count ?? 0,
      timeline_signature: payload.timeline_signature ?? '',
    }
  }
  return {
    ...payload,
    timeline_signature: payload.timeline_signature ?? '',
  }
}

async function getThreadTimeline(savedId: string): Promise<ResearchThreadTimelineDetail> {
  const response = await fetch(`/api/v1/research/sessions/${encodeURIComponent(savedId)}/timeline`)
  if (!response.ok) {
    throw new Error(`Failed to load timeline: ${response.status}`)
  }
  return (await response.json()) as ResearchThreadTimelineDetail
}

async function listCollections(): Promise<ResearchCollectionSummary[]> {
  const response = await fetch('/api/v1/collections')
  if (!response.ok) {
    throw new Error(`Failed to list collections: ${response.status}`)
  }
  const payload = (await response.json()) as { collections?: ResearchCollectionSummary[] }
  return payload.collections ?? []
}

async function createCollection(payload: {
  title: string
  summary?: string | null
  notes?: string | null
}): Promise<ResearchCollection> {
  const response = await fetch('/api/v1/collections', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(`Failed to create collection: ${response.status}`)
  }
  return normalizeCollectionDetail((await response.json()) as CollectionDetailResponse | ResearchCollection)
}

async function getCollection(collectionId: string): Promise<ResearchCollection> {
  const response = await fetch(`/api/v1/collections/${encodeURIComponent(collectionId)}`)
  if (!response.ok) {
    throw new Error(`Failed to load collection: ${response.status}`)
  }
  return normalizeCollectionDetail((await response.json()) as CollectionDetailResponse | ResearchCollection)
}

async function updateCollection(
  collectionId: string,
  payload: { title?: string; summary?: string | null; notes?: string | null }
): Promise<ResearchCollection> {
  const response = await fetch(`/api/v1/collections/${encodeURIComponent(collectionId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(`Failed to update collection: ${response.status}`)
  }
  return normalizeCollectionDetail((await response.json()) as CollectionDetailResponse | ResearchCollection)
}

async function addSessionToCollection(
  collectionId: string,
  payload: { session_id: string; position?: number }
): Promise<ResearchCollection> {
  const response = await fetch(`/api/v1/collections/${encodeURIComponent(collectionId)}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(`Failed to add session to collection: ${response.status}`)
  }
  return normalizeCollectionDetail((await response.json()) as CollectionDetailResponse | ResearchCollection)
}

async function removeSessionFromCollection(collectionId: string, sessionId: string): Promise<ResearchCollection> {
  const response = await fetch(
    `/api/v1/collections/${encodeURIComponent(collectionId)}/sessions/${encodeURIComponent(sessionId)}`,
    {
      method: 'DELETE',
    }
  )
  if (!response.ok) {
    throw new Error(`Failed to remove session from collection: ${response.status}`)
  }
  return normalizeCollectionDetail((await response.json()) as CollectionDetailResponse | ResearchCollection)
}

async function reorderCollectionSessions(collectionId: string, sessionIds: string[]): Promise<ResearchCollection> {
  const response = await fetch(`/api/v1/collections/${encodeURIComponent(collectionId)}/sessions/reorder`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_ids: sessionIds }),
  })
  if (!response.ok) {
    throw new Error(`Failed to reorder collection sessions: ${response.status}`)
  }
  return normalizeCollectionDetail((await response.json()) as CollectionDetailResponse | ResearchCollection)
}

async function exportSavedSession(savedId: string, format: 'json' | 'markdown'): Promise<Response> {
  const response = await fetch(`/api/v1/research/sessions/${encodeURIComponent(savedId)}/export?format=${format}`)
  if (!response.ok) {
    throw new Error(`Failed to export session: ${response.status}`)
  }
  return response
}

async function exportSavedBundle(savedId: string): Promise<Response> {
  const response = await fetch(`/api/v1/research/sessions/${encodeURIComponent(savedId)}/bundle`)
  if (!response.ok) {
    throw new Error(`Failed to export bundle: ${response.status}`)
  }
  return response
}

async function exportCollectionBundle(collectionId: string): Promise<Response> {
  const response = await fetch(`/api/v1/collections/${encodeURIComponent(collectionId)}/bundle`)
  if (!response.ok) {
    throw new Error(`Failed to export collection bundle: ${response.status}`)
  }
  return response
}

function triggerDownload(response: Response, content: Blob): void {
  if (typeof document === 'undefined' || typeof URL === 'undefined' || typeof URL.createObjectURL !== 'function') {
    return
  }

  const disposition = response.headers.get('content-disposition') ?? ''
  const filenameMatch = disposition.match(/filename=([^;]+)/i)
  const fallbackName = response.headers.get('content-type')?.includes('markdown') ? 'meridian-session.md' : 'meridian-session.json'
  const filename = filenameMatch ? filenameMatch[1].replace(/"/g, '') : fallbackName

  const objectUrl = URL.createObjectURL(content)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = filename
  anchor.style.display = 'none'
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(objectUrl)
}

const EMPTY_EVIDENCE_STATE: EvidenceNavigationState = {
  active_claim_id: null,
  expanded_source_id: null,
}

export default function HomePage() {
  const [traceSteps, setTraceSteps] = useState<TraceEvent[]>([])
  const [briefState, setBriefState] = useState<'empty' | 'loading' | 'error' | 'complete'>('empty')
  const [brief, setBrief] = useState<ResearchBrief | null>(null)
  const [error, setError] = useState('')
  const [running, setRunning] = useState(false)
  const [lastQuery, setLastQuery] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [queryHistory, setQueryHistory] = useState<string[]>([])
  const [followUpHint, setFollowUpHint] = useState<string | null>(null)
  const [historyState, setHistoryState] = useState<'loading' | 'ready' | 'error'>('loading')
  const [historyError, setHistoryError] = useState('')
  const [savedSessions, setSavedSessions] = useState<SavedResearchSessionSummary[]>([])
  const [activeSavedSessionId, setActiveSavedSessionId] = useState<string | null>(null)
  const [saveBusy, setSaveBusy] = useState(false)
  const [exportBusy, setExportBusy] = useState(false)
  const [mutationBusy, setMutationBusy] = useState(false)
  const [recaptureBusy, setRecaptureBusy] = useState(false)
  const [comparisonBusy, setComparisonBusy] = useState(false)
  const [integrityBusy, setIntegrityBusy] = useState(false)
  const [workspaceStatus, setWorkspaceStatus] = useState<string | null>(null)
  const [workspaceSearch, setWorkspaceSearch] = useState('')
  const [includeArchived, setIncludeArchived] = useState(false)
  const [queryClassFilter, setQueryClassFilter] = useState<ResearchBrief['query_class'] | 'all'>('all')
  const [comparisonResult, setComparisonResult] = useState<SessionComparison | null>(null)
  const [recaptureLineage, setRecaptureLineage] = useState<SessionRecaptureLineage | null>(null)
  const [integrityReport, setIntegrityReport] = useState<SessionIntegrityReport | null>(null)
  const [integrityOverview, setIntegrityOverview] = useState<{ count: number; issueCount: number } | null>(null)
  const [reviewBusy, setReviewBusy] = useState(false)
  const [reviewChecklist, setReviewChecklist] = useState<ResearchReviewChecklist | null>(null)
  const [evaluationDashboardBusy, setEvaluationDashboardBusy] = useState(false)
  const [evaluationDashboard, setEvaluationDashboard] = useState<ResearchEvaluationDashboard | null>(null)
  const [regressionPackBusy, setRegressionPackBusy] = useState(false)
  const [regressionPacks, setRegressionPacks] = useState<ResearchRegressionPackSummary[]>([])
  const [activeRegressionPackId, setActiveRegressionPackId] = useState<string | null>(null)
  const [regressionRun, setRegressionRun] = useState<ResearchRegressionPackRun | null>(null)
  const [collectionsState, setCollectionsState] = useState<'loading' | 'ready' | 'error'>('loading')
  const [collectionsError, setCollectionsError] = useState('')
  const [collections, setCollections] = useState<ResearchCollectionSummary[]>([])
  const [activeCollection, setActiveCollection] = useState<ResearchCollection | null>(null)
  const [collectionBusy, setCollectionBusy] = useState(false)
  const [threadTimelineState, setThreadTimelineState] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle')
  const [threadTimelineError, setThreadTimelineError] = useState('')
  const [threadTimeline, setThreadTimeline] = useState<ResearchThreadTimelineDetail | null>(null)
  const [evidenceState, setEvidenceState] = useState<EvidenceNavigationState>(EMPTY_EVIDENCE_STATE)
  const [evaluation, setEvaluation] = useState<ResearchEvaluationReport | null>(null)
  const [evidenceHydrationKey, setEvidenceHydrationKey] = useState(0)
  const [templateState, setTemplateState] = useState<'loading' | 'ready' | 'error'>('loading')
  const [templateError, setTemplateError] = useState('')
  const [researchTemplates, setResearchTemplates] = useState<ResearchTemplateDefinition[]>(FALLBACK_RESEARCH_TEMPLATES)
  const [selectedTemplateId, setSelectedTemplateId] = useState<ResearchTemplateId>('macro_outlook')

  const activeTemplate = researchTemplates.find((item) => item.id === selectedTemplateId) ?? FALLBACK_RESEARCH_TEMPLATES[0]

  const canSaveCurrent = briefState === 'complete' && !!brief && traceSteps.length > 0 && !running
  const canExportCurrent = canSaveCurrent || !!activeSavedSessionId
  const activeCollectionId = activeCollection?.id ?? null

  const handleEvidenceStateChange = useCallback((state: EvidenceNavigationState) => {
    setEvidenceState((previous) => {
      // Ignore transient empty updates so reopened evidence state remains stable.
      if (
        previous.active_claim_id &&
        !state.active_claim_id &&
        !state.expanded_source_id
      ) {
        return previous
      }
      if (
        previous.active_claim_id === state.active_claim_id &&
        previous.expanded_source_id === state.expanded_source_id
      ) {
        return previous
      }
      return state
    })
  }, [])

  const loadWorkspaceSessions = useCallback(async () => {
    setHistoryState('loading')
    setHistoryError('')
    try {
      const sessions = await listSavedSessions({
        search: workspaceSearch,
        includeArchived,
        queryClass: queryClassFilter,
      })
      setSavedSessions(sessions)
      setActiveSavedSessionId((previous) => {
        if (!previous) {
          return previous
        }
        return sessions.some((item) => item.id === previous) ? previous : null
      })
      setHistoryState('ready')
    } catch (loadError) {
      setHistoryState('error')
      setHistoryError(loadError instanceof Error ? loadError.message : 'Failed to load saved sessions')
    }
  }, [workspaceSearch, includeArchived, queryClassFilter])

  useEffect(() => {
    void loadWorkspaceSessions()
  }, [loadWorkspaceSessions])

  useEffect(() => {
    setEvaluationDashboard(null)
  }, [workspaceSearch, includeArchived, queryClassFilter])

  const refreshRegressionPacks = useCallback(
    async (preferredPackId?: string | null) => {
      setRegressionPackBusy(true)
      try {
        const packs = await listRegressionPacks()
        setRegressionPacks(packs)
        setActiveRegressionPackId((previous) => {
          if (preferredPackId !== undefined) {
            return packs.some((pack) => pack.id === preferredPackId) ? preferredPackId : packs[0]?.id ?? null
          }
          if (previous && packs.some((pack) => pack.id === previous)) {
            return previous
          }
          return packs[0]?.id ?? null
        })
      } catch (loadError) {
        setWorkspaceStatus(loadError instanceof Error ? loadError.message : 'Failed to load regression packs')
      } finally {
        setRegressionPackBusy(false)
      }
    },
    []
  )

  useEffect(() => {
    void refreshRegressionPacks()
  }, [refreshRegressionPacks])

  useEffect(() => {
    let active = true

    async function loadTemplates() {
      setTemplateState('loading')
      setTemplateError('')
      try {
        const templates = await listResearchTemplates()
        if (!active) {
          return
        }
        if (templates.length > 0) {
          setResearchTemplates(templates)
          setSelectedTemplateId((previous) => {
            return templates.some((item) => item.id === previous) ? previous : templates[0].id
          })
        }
        setTemplateState('ready')
      } catch (templatesError) {
        if (!active) {
          return
        }
        setResearchTemplates(FALLBACK_RESEARCH_TEMPLATES)
        setTemplateState('error')
        setTemplateError(templatesError instanceof Error ? templatesError.message : 'Failed to load templates')
      }
    }

    void loadTemplates()
    return () => {
      active = false
    }
  }, [])

  const collectionSummaryFromDetail = useCallback(
    (collection: ResearchCollection): ResearchCollectionSummary => ({
      id: collection.id,
      title: collection.title,
      summary: collection.summary,
      session_count: collection.session_ids.length,
      created_at: collection.created_at,
      updated_at: collection.updated_at,
      collection_signature: collection.collection_signature,
    }),
    []
  )

  const upsertCollectionSummary = useCallback(
    (collection: ResearchCollection) => {
      const summary = collectionSummaryFromDetail(collection)
      setCollections((previous) => {
        const others = previous.filter((item) => item.id !== summary.id)
        return [summary, ...others].sort((left, right) => right.updated_at.localeCompare(left.updated_at))
      })
    },
    [collectionSummaryFromDetail]
  )

  const refreshCollections = useCallback(
    async (preferredCollectionId?: string | null) => {
      setCollectionsState('loading')
      setCollectionsError('')
      try {
        const listed = await listCollections()
        setCollections(listed)

        const candidateId =
          preferredCollectionId !== undefined
            ? preferredCollectionId
            : activeCollectionId && listed.some((item) => item.id === activeCollectionId)
              ? activeCollectionId
              : listed[0]?.id ?? null

        if (!candidateId) {
          setActiveCollection(null)
          setCollectionsState('ready')
          return
        }

        const detail = await getCollection(candidateId)
        setActiveCollection(detail)
        setCollectionsState('ready')
      } catch (collectionError) {
        setCollectionsState('error')
        setCollectionsError(collectionError instanceof Error ? collectionError.message : 'Failed to load collections')
      }
    },
    [activeCollectionId]
  )

  useEffect(() => {
    void refreshCollections()
  }, [refreshCollections])

  const refreshThreadTimeline = useCallback(async (savedId: string | null) => {
    if (!savedId) {
      setThreadTimeline(null)
      setThreadTimelineError('')
      setThreadTimelineState('idle')
      return
    }

    setThreadTimelineState('loading')
    setThreadTimelineError('')
    try {
      const detail = await getThreadTimeline(savedId)
      setThreadTimeline(detail)
      setThreadTimelineState('ready')
    } catch (timelineError) {
      setThreadTimeline(null)
      setThreadTimelineState('error')
      setThreadTimelineError(timelineError instanceof Error ? timelineError.message : 'Failed to load timeline')
    }
  }, [])

  useEffect(() => {
    void refreshThreadTimeline(activeSavedSessionId)
  }, [activeSavedSessionId, refreshThreadTimeline])

  const createCollectionByPayload = useCallback(
    async (payload: { title: string; summary?: string | null; notes?: string | null }) => {
      setCollectionBusy(true)
      try {
        const created = await createCollection(payload)
        upsertCollectionSummary(created)
        setActiveCollection(created)
        setCollectionsState('ready')
        setWorkspaceStatus(`Created collection ${created.id}`)
      } catch (collectionError) {
        setWorkspaceStatus(collectionError instanceof Error ? collectionError.message : 'Failed to create collection')
      } finally {
        setCollectionBusy(false)
      }
    },
    [upsertCollectionSummary]
  )

  const openCollectionById = useCallback(async (collectionId: string) => {
    setCollectionBusy(true)
    try {
      const detail = await getCollection(collectionId)
      setActiveCollection(detail)
      setWorkspaceStatus(`Opened collection ${detail.id}`)
    } catch (collectionError) {
      setWorkspaceStatus(collectionError instanceof Error ? collectionError.message : 'Failed to open collection')
    } finally {
      setCollectionBusy(false)
    }
  }, [])

  const updateCollectionById = useCallback(
    async (collectionId: string, payload: { title?: string; summary?: string | null; notes?: string | null }) => {
      setCollectionBusy(true)
      try {
        const updated = await updateCollection(collectionId, payload)
        upsertCollectionSummary(updated)
        setActiveCollection(updated)
        setWorkspaceStatus(`Updated collection ${updated.id}`)
      } catch (collectionError) {
        setWorkspaceStatus(collectionError instanceof Error ? collectionError.message : 'Failed to update collection')
      } finally {
        setCollectionBusy(false)
      }
    },
    [upsertCollectionSummary]
  )

  const addActiveSessionToCurrentCollection = useCallback(async () => {
    if (!activeCollection) {
      setWorkspaceStatus('Select a collection before adding sessions.')
      return
    }
    if (!activeSavedSessionId) {
      setWorkspaceStatus('No active saved session available to add.')
      return
    }

    setCollectionBusy(true)
    try {
      const updated = await addSessionToCollection(activeCollection.id, { session_id: activeSavedSessionId })
      upsertCollectionSummary(updated)
      setActiveCollection(updated)
      setWorkspaceStatus(`Added ${activeSavedSessionId} to ${updated.title}`)
    } catch (collectionError) {
      setWorkspaceStatus(collectionError instanceof Error ? collectionError.message : 'Failed to add session to collection')
    } finally {
      setCollectionBusy(false)
    }
  }, [activeCollection, activeSavedSessionId, upsertCollectionSummary])

  const removeSessionFromCurrentCollection = useCallback(
    async (sessionIdToRemove: string) => {
      if (!activeCollection) {
        return
      }
      setCollectionBusy(true)
      try {
        const updated = await removeSessionFromCollection(activeCollection.id, sessionIdToRemove)
        upsertCollectionSummary(updated)
        setActiveCollection(updated)
        setWorkspaceStatus(`Removed ${sessionIdToRemove} from ${updated.title}`)
      } catch (collectionError) {
        setWorkspaceStatus(collectionError instanceof Error ? collectionError.message : 'Failed to remove session')
      } finally {
        setCollectionBusy(false)
      }
    },
    [activeCollection, upsertCollectionSummary]
  )

  const reorderSessionInCurrentCollection = useCallback(
    async (sessionIdToMove: string, direction: 'up' | 'down') => {
      if (!activeCollection) {
        return
      }
      const currentOrder = [...activeCollection.session_ids]
      const currentIndex = currentOrder.indexOf(sessionIdToMove)
      if (currentIndex === -1) {
        return
      }
      const targetIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1
      if (targetIndex < 0 || targetIndex >= currentOrder.length) {
        return
      }

      ;[currentOrder[currentIndex], currentOrder[targetIndex]] = [
        currentOrder[targetIndex],
        currentOrder[currentIndex],
      ]

      setCollectionBusy(true)
      try {
        const updated = await reorderCollectionSessions(activeCollection.id, currentOrder)
        upsertCollectionSummary(updated)
        setActiveCollection(updated)
        setWorkspaceStatus(`Reordered collection ${updated.title}`)
      } catch (collectionError) {
        setWorkspaceStatus(collectionError instanceof Error ? collectionError.message : 'Failed to reorder collection')
      } finally {
        setCollectionBusy(false)
      }
    },
    [activeCollection, upsertCollectionSummary]
  )

  const saveCurrentSession = useCallback(
    async (options?: { silent?: boolean }): Promise<SavedResearchSession | null> => {
      if (!brief || !canSaveCurrent) {
        if (!options?.silent) {
          setWorkspaceStatus('Run research to completion before saving.')
        }
        return null
      }

      setSaveBusy(true)
      try {
        const payload: SaveResearchSessionRequest = {
          question: brief.question || lastQuery,
          mode: 'demo',
          session_id: sessionId ?? 'local-demo',
          template_id: brief.template_id ?? selectedTemplateId,
          brief,
          trace_events: traceSteps,
          evidence_state: evidenceState,
          evaluation,
        }

        const saved = await saveSession(payload)
        await loadWorkspaceSessions()
        setActiveSavedSessionId(saved.id)
        setSessionId(saved.session_id)
        setComparisonResult(null)
        setRecaptureLineage(null)
        setIntegrityReport(null)
        setIntegrityOverview(null)
        setReviewChecklist(null)
        setEvaluationDashboard(null)
        if (saved.follow_up_context) {
          setFollowUpHint(saved.follow_up_context)
        }
        if (!options?.silent) {
          setWorkspaceStatus(`Saved session ${saved.id}`)
        }
        return saved
      } catch (saveError) {
        setWorkspaceStatus(saveError instanceof Error ? saveError.message : 'Failed to save session')
        return null
      } finally {
        setSaveBusy(false)
      }
    },
    [brief, canSaveCurrent, evaluation, evidenceState, lastQuery, loadWorkspaceSessions, selectedTemplateId, sessionId, traceSteps]
  )

  const reopenSession = useCallback(async (savedId: string) => {
    setWorkspaceStatus(null)
    try {
      const saved = await getSavedSession(savedId)
      setBrief(saved.brief)
      setBriefState('complete')
      setTraceSteps(saved.trace_events)
      setError('')
      setRunning(false)
      setLastQuery(saved.question)
      setSessionId(saved.session_id)
      setQueryHistory((previous) => [...previous, saved.question].slice(-6))
      setFollowUpHint(saved.follow_up_context ?? null)
      setEvidenceState(saved.evidence_state ?? EMPTY_EVIDENCE_STATE)
      setEvaluation(saved.evaluation ?? null)
      if (saved.brief.template_id) {
        setSelectedTemplateId(saved.brief.template_id)
      }
      setEvidenceHydrationKey((previous) => previous + 1)
      setActiveSavedSessionId(saved.id)
      setComparisonResult(null)
      setRecaptureLineage(null)
      setIntegrityReport(null)
      setIntegrityOverview(null)
      setReviewChecklist(null)
      setEvaluationDashboard(null)
      setWorkspaceStatus(`Reopened session ${saved.id}`)
    } catch (reopenError) {
      setWorkspaceStatus(reopenError instanceof Error ? reopenError.message : 'Failed to reopen session')
    }
  }, [])

  const exportSessionById = useCallback(async (savedId: string, format: 'json' | 'markdown') => {
    setExportBusy(true)
    try {
      const response = await exportSavedSession(savedId, format)
      const blob = await response.blob()
      triggerDownload(response, blob)
      setWorkspaceStatus(`Exported ${savedId} as ${format}`)
    } catch (exportError) {
      setWorkspaceStatus(exportError instanceof Error ? exportError.message : 'Export failed')
    } finally {
      setExportBusy(false)
    }
  }, [])

  const exportCurrentSession = useCallback(
    async (format: 'json' | 'markdown') => {
      let exportTarget = activeSavedSessionId
      if (!exportTarget) {
        const saved = await saveCurrentSession({ silent: true })
        if (!saved) {
          setWorkspaceStatus('Unable to export: no completed session is available.')
          return
        }
        exportTarget = saved.id
      }
      await exportSessionById(exportTarget, format)
    },
    [activeSavedSessionId, exportSessionById, saveCurrentSession]
  )

  const exportBundleById = useCallback(async (savedId: string) => {
    setExportBusy(true)
    try {
      const response = await exportSavedBundle(savedId)
      const blob = await response.blob()
      triggerDownload(response, blob)
      setWorkspaceStatus(`Exported ${savedId} as bundle`)
    } catch (exportError) {
      setWorkspaceStatus(exportError instanceof Error ? exportError.message : 'Bundle export failed')
    } finally {
      setExportBusy(false)
    }
  }, [])

  const exportCurrentBundle = useCallback(async () => {
    let exportTarget = activeSavedSessionId
    if (!exportTarget) {
      const saved = await saveCurrentSession({ silent: true })
      if (!saved) {
        setWorkspaceStatus('Unable to export bundle: no completed session is available.')
        return
      }
      exportTarget = saved.id
    }
    await exportBundleById(exportTarget)
  }, [activeSavedSessionId, exportBundleById, saveCurrentSession])

  const exportActiveCollectionBundle = useCallback(async () => {
    if (!activeCollection) {
      setWorkspaceStatus('Select a collection before exporting bundle.')
      return
    }

    setExportBusy(true)
    try {
      const response = await exportCollectionBundle(activeCollection.id)
      const blob = await response.blob()
      triggerDownload(response, blob)
      setWorkspaceStatus(`Exported collection ${activeCollection.id} as bundle`)
    } catch (exportError) {
      setWorkspaceStatus(exportError instanceof Error ? exportError.message : 'Collection bundle export failed')
    } finally {
      setExportBusy(false)
    }
  }, [activeCollection])

  const renameSessionById = useCallback(
    async (savedId: string, nextLabel: string | null) => {
      setMutationBusy(true)
      try {
        const renamed = await renameSavedSession(savedId, nextLabel)
        await loadWorkspaceSessions()
        setWorkspaceStatus(`Renamed session ${renamed.id}`)
      } catch (renameError) {
        setWorkspaceStatus(renameError instanceof Error ? renameError.message : 'Rename failed')
      } finally {
        setMutationBusy(false)
      }
    },
    [loadWorkspaceSessions]
  )

  const setArchivedById = useCallback(
    async (savedId: string, archived: boolean) => {
      setMutationBusy(true)
      try {
        const updated = await archiveSavedSession(savedId, archived)
        await loadWorkspaceSessions()
        if (!includeArchived && archived && activeSavedSessionId === savedId) {
          setActiveSavedSessionId(null)
        }
        setWorkspaceStatus(archived ? `Archived session ${updated.id}` : `Unarchived session ${updated.id}`)
      } catch (archiveError) {
        setWorkspaceStatus(archiveError instanceof Error ? archiveError.message : 'Archive update failed')
      } finally {
        setMutationBusy(false)
      }
    },
    [activeSavedSessionId, includeArchived, loadWorkspaceSessions]
  )

  const deleteSessionById = useCallback(
    async (savedId: string) => {
      setMutationBusy(true)
      try {
        await deleteSavedSession(savedId)
        await loadWorkspaceSessions()
        if (activeSavedSessionId === savedId) {
          setActiveSavedSessionId(null)
        }
        setWorkspaceStatus(`Deleted session ${savedId}`)
      } catch (deleteError) {
        setWorkspaceStatus(deleteError instanceof Error ? deleteError.message : 'Delete failed')
      } finally {
        setMutationBusy(false)
      }
    },
    [activeSavedSessionId, loadWorkspaceSessions]
  )

  const recaptureSessionById = useCallback(
    async (savedId: string) => {
      setRecaptureBusy(true)
      try {
        const recaptured = await recaptureSavedSession(savedId)
        await loadWorkspaceSessions()
        setActiveSavedSessionId(recaptured.saved.id)
        setBrief(recaptured.saved.brief)
        setBriefState('complete')
        setTraceSteps(recaptured.saved.trace_events)
        setSessionId(recaptured.saved.session_id)
        setEvaluation(recaptured.saved.evaluation ?? null)
        setEvidenceState(recaptured.saved.evidence_state ?? EMPTY_EVIDENCE_STATE)
        setEvidenceHydrationKey((previous) => previous + 1)
        setRecaptureLineage(recaptured.lineage)
        setComparisonResult(null)
        setIntegrityReport(null)
        setIntegrityOverview(null)
        setReviewChecklist(null)
        setEvaluationDashboard(null)
        setWorkspaceStatus(`Recaptured ${savedId} -> ${recaptured.saved.id}`)
      } catch (recaptureError) {
        setWorkspaceStatus(recaptureError instanceof Error ? recaptureError.message : 'Recapture failed')
      } finally {
        setRecaptureBusy(false)
      }
    },
    [loadWorkspaceSessions]
  )

  const compareSessionsById = useCallback(async (leftId: string, rightId: string) => {
    if (!leftId || !rightId) {
      setWorkspaceStatus('Select two sessions before comparing.')
      return
    }
    if (leftId === rightId) {
      setWorkspaceStatus('Select two different sessions to compare.')
      return
    }

    setComparisonBusy(true)
    try {
      const comparison = await compareSavedSessions(leftId, rightId)
      setComparisonResult(comparison)
      setWorkspaceStatus(`Compared ${leftId} vs ${rightId}`)
    } catch (compareError) {
      setWorkspaceStatus(compareError instanceof Error ? compareError.message : 'Compare failed')
    } finally {
      setComparisonBusy(false)
    }
  }, [])

  const verifySessionIntegrityById = useCallback(async (savedId: string) => {
    setIntegrityBusy(true)
    try {
      const report = await getSavedSessionIntegrity(savedId)
      setIntegrityReport(report)
      setIntegrityOverview(null)
      if (report.signature_valid && report.issues.length === 0) {
        setWorkspaceStatus(`Integrity check passed for ${savedId}`)
      } else {
        setWorkspaceStatus(`Integrity issues for ${savedId}: ${report.issues.join('; ') || 'unknown issue'}`)
      }
    } catch (integrityError) {
      setWorkspaceStatus(integrityError instanceof Error ? integrityError.message : 'Integrity check failed')
    } finally {
      setIntegrityBusy(false)
    }
  }, [])

  const verifyWorkspaceIntegrity = useCallback(async () => {
    setIntegrityBusy(true)
    try {
      const reports = await getWorkspaceIntegrity({ search: workspaceSearch, includeArchived })
      const issueCount = reports.filter((item) => !item.signature_valid || item.issues.length > 0).length
      setIntegrityOverview({ count: reports.length, issueCount })
      setIntegrityReport(null)
      if (issueCount === 0) {
        setWorkspaceStatus(`Workspace integrity passed for ${reports.length} sessions`)
      } else {
        setWorkspaceStatus(`Workspace integrity found issues in ${issueCount}/${reports.length} sessions`)
      }
    } catch (integrityError) {
      setWorkspaceStatus(integrityError instanceof Error ? integrityError.message : 'Workspace integrity check failed')
    } finally {
      setIntegrityBusy(false)
    }
  }, [includeArchived, workspaceSearch])

  const reviewSessionById = useCallback(async (savedId: string) => {
    setReviewBusy(true)
    try {
      const checklist = await getSavedSessionReview(savedId)
      setReviewChecklist(checklist)
      setWorkspaceStatus(checklist.summary)
    } catch (reviewError) {
      setWorkspaceStatus(reviewError instanceof Error ? reviewError.message : 'Guided review failed')
    } finally {
      setReviewBusy(false)
    }
  }, [])

  const runWorkspaceEvaluationDashboard = useCallback(async () => {
    setEvaluationDashboardBusy(true)
    try {
      const dashboard = await getWorkspaceEvaluationDashboard({
        search: workspaceSearch,
        includeArchived,
        queryClass: queryClassFilter,
      })
      setEvaluationDashboard(dashboard)
      setWorkspaceStatus(
        `Dashboard ready: ${dashboard.passed_count}/${dashboard.session_count} sessions passing` +
          ` (${(dashboard.pass_rate * 100).toFixed(1)}%)`
      )
    } catch (dashboardError) {
      setWorkspaceStatus(dashboardError instanceof Error ? dashboardError.message : 'Evaluation dashboard failed')
    } finally {
      setEvaluationDashboardBusy(false)
    }
  }, [includeArchived, queryClassFilter, workspaceSearch])

  const exportWorkspaceEvaluationSummary = useCallback(async () => {
    setEvaluationDashboardBusy(true)
    try {
      const response = await exportWorkspaceEvaluationDashboard({
        search: workspaceSearch,
        includeArchived,
        queryClass: queryClassFilter,
      })
      const blob = await response.blob()
      triggerDownload(response, blob)
      setWorkspaceStatus('Exported workspace evaluation dashboard summary')
    } catch (dashboardError) {
      setWorkspaceStatus(
        dashboardError instanceof Error ? dashboardError.message : 'Evaluation dashboard export failed'
      )
    } finally {
      setEvaluationDashboardBusy(false)
    }
  }, [includeArchived, queryClassFilter, workspaceSearch])

  const createRegressionPackFromVisibleSessions = useCallback(
    async (payload: { title: string; description?: string | null }) => {
      const maxPackSessions = 12
      const sessionIds = savedSessions.slice(0, maxPackSessions).map((item) => item.id)
      if (sessionIds.length === 0) {
        setWorkspaceStatus('No visible sessions to include in a regression pack.')
        return
      }

      setRegressionPackBusy(true)
      try {
        const created = await createRegressionPack({
          title: payload.title,
          description: payload.description,
          session_ids: sessionIds,
        })
        await refreshRegressionPacks(created.id)
        setRegressionRun(null)
        const skippedCount = Math.max(0, savedSessions.length - sessionIds.length)
        setWorkspaceStatus(
          skippedCount > 0
            ? `Created regression pack ${created.id} from ${sessionIds.length} sessions (${skippedCount} skipped)`
            : `Created regression pack ${created.id}`
        )
      } catch (packError) {
        setWorkspaceStatus(packError instanceof Error ? packError.message : 'Failed to create regression pack')
      } finally {
        setRegressionPackBusy(false)
      }
    },
    [refreshRegressionPacks, savedSessions]
  )

  const deleteRegressionPackById = useCallback(
    async (packId: string) => {
      setRegressionPackBusy(true)
      try {
        await deleteRegressionPack(packId)
        await refreshRegressionPacks()
        setRegressionRun(null)
        setWorkspaceStatus(`Deleted regression pack ${packId}`)
      } catch (packError) {
        setWorkspaceStatus(packError instanceof Error ? packError.message : 'Failed to delete regression pack')
      } finally {
        setRegressionPackBusy(false)
      }
    },
    [refreshRegressionPacks]
  )

  const runRegressionPackById = useCallback(async (packId: string) => {
    setRegressionPackBusy(true)
    try {
      const result = await runRegressionPack(packId)
      setRegressionRun(result)
      setWorkspaceStatus(
        `Regression run complete: ${result.changed_count}/${result.compared_count} sessions changed`
      )
    } catch (packError) {
      setWorkspaceStatus(packError instanceof Error ? packError.message : 'Failed to run regression pack')
    } finally {
      setRegressionPackBusy(false)
    }
  }, [])

  const exportRegressionPackRunById = useCallback(async (packId: string) => {
    setRegressionPackBusy(true)
    try {
      const response = await exportRegressionPackRun(packId)
      const blob = await response.blob()
      triggerDownload(response, blob)
      setWorkspaceStatus(`Exported regression pack run ${packId}`)
    } catch (packError) {
      setWorkspaceStatus(packError instanceof Error ? packError.message : 'Failed to export regression pack run')
    } finally {
      setRegressionPackBusy(false)
    }
  }, [])

  async function runQuery(question: string) {
    const priorQuestion = queryHistory.length > 0 ? queryHistory[queryHistory.length - 1] : null

    setLastQuery(question)
    setRunning(true)
    setError('')
    setBrief(null)
    setTraceSteps([])
    setBriefState('loading')
    setActiveSavedSessionId(null)
    setRecaptureLineage(null)
    setEvidenceState(EMPTY_EVIDENCE_STATE)
    setEvaluation(null)
    setReviewChecklist(null)
    setEvaluationDashboard(null)
    setEvidenceHydrationKey((previous) => previous + 1)
    setWorkspaceStatus(null)

    let resolvedSessionId = sessionId
    let sessionFollowUp = false

    try {
      await streamResearch(question, sessionId, selectedTemplateId, (step) => {
        setTraceSteps((prev) => [...prev, step])
        if (step.session_id) {
          resolvedSessionId = step.session_id
        }
        if (step.followup) {
          sessionFollowUp = true
        }

        if (step.type === 'complete' && step.brief) {
          setBrief(step.brief)
          if (step.brief.template_id) {
            setSelectedTemplateId(step.brief.template_id)
          }
          setEvaluation(step.evaluation ?? null)
          setBriefState('complete')
          setQueryHistory((prev) => [...prev, question].slice(-6))
          if (step.brief.follow_up_context) {
            setFollowUpHint(step.brief.follow_up_context)
          } else if ((step.followup || sessionFollowUp) && priorQuestion) {
            setFollowUpHint(`Follow-up to prior question: ${priorQuestion}`)
          }
        }
        if (step.type === 'error') {
          setError(step.message ?? 'Research failed')
          setBriefState('error')
        }
      })

      if (resolvedSessionId) {
        setSessionId(resolvedSessionId)
      }
    } catch {
      // Deterministic fallback path when the API route is unavailable in local-only runs.
      for (const step of FALLBACK_EVENTS) {
        setTraceSteps((prev) => [...prev, step])
      }
      const fallback = fallbackBrief(question, priorQuestion, activeTemplate)
      setBrief(fallback)
      setEvaluation(null)
      setBriefState('complete')
      setSessionId((prev) => prev ?? 'local-demo')
      setQueryHistory((prev) => [...prev, question].slice(-6))
      if (fallback.follow_up_context) {
        setFollowUpHint(fallback.follow_up_context)
      }
    } finally {
      setRunning(false)
    }
  }

  return (
    <main className="terminal-page" data-testid="research-page">
      <RegimeDashboard />
      <SplitPane
        left={
          <>
            <WorkspacePanel
              historyState={historyState}
              historyError={historyError}
              sessions={savedSessions}
              activeSavedSessionId={activeSavedSessionId}
              canSaveCurrent={canSaveCurrent}
              canExportCurrent={canExportCurrent}
              saveBusy={saveBusy}
              exportBusy={exportBusy}
              mutationBusy={mutationBusy}
              recaptureBusy={recaptureBusy}
              comparisonBusy={comparisonBusy}
              integrityBusy={integrityBusy}
              reviewBusy={reviewBusy}
              evaluationDashboardBusy={evaluationDashboardBusy}
              regressionPackBusy={regressionPackBusy}
              searchValue={workspaceSearch}
              includeArchived={includeArchived}
              queryClassFilter={queryClassFilter}
              comparisonResult={comparisonResult}
              recaptureLineage={recaptureLineage}
              integrityReport={integrityReport}
              reviewChecklist={reviewChecklist}
              evaluationDashboard={evaluationDashboard}
              regressionPacks={regressionPacks}
              activeRegressionPackId={activeRegressionPackId}
              regressionRun={regressionRun}
              integrityOverview={integrityOverview}
              statusMessage={workspaceStatus}
              collectionState={collectionsState}
              collectionError={collectionsError}
              collections={collections}
              activeCollection={activeCollection}
              collectionBusy={collectionBusy}
              threadTimelineState={threadTimelineState}
              threadTimelineError={threadTimelineError}
              threadTimeline={threadTimeline}
              onSearchChange={setWorkspaceSearch}
              onToggleIncludeArchived={setIncludeArchived}
              onQueryClassFilterChange={setQueryClassFilter}
              onRefresh={() => {
                void loadWorkspaceSessions()
              }}
              onCollectionRefresh={() => {
                void refreshCollections(activeCollectionId)
              }}
              onCollectionCreate={(payload) => {
                void createCollectionByPayload(payload)
              }}
              onCollectionOpen={(collectionId) => {
                void openCollectionById(collectionId)
              }}
              onCollectionUpdate={(collectionId, payload) => {
                void updateCollectionById(collectionId, payload)
              }}
              onCollectionAddActiveSession={() => {
                void addActiveSessionToCurrentCollection()
              }}
              onCollectionExportBundle={() => {
                void exportActiveCollectionBundle()
              }}
              onCollectionRemoveSession={(sessionIdToRemove) => {
                void removeSessionFromCurrentCollection(sessionIdToRemove)
              }}
              onCollectionReorderSession={(sessionIdToMove, direction) => {
                void reorderSessionInCurrentCollection(sessionIdToMove, direction)
              }}
              onThreadTimelineRefresh={() => {
                void refreshThreadTimeline(activeSavedSessionId)
              }}
              onSaveCurrent={() => {
                void saveCurrentSession()
              }}
              onExportCurrentJson={() => {
                void exportCurrentSession('json')
              }}
              onExportCurrentMarkdown={() => {
                void exportCurrentSession('markdown')
              }}
              onExportCurrentBundle={() => {
                void exportCurrentBundle()
              }}
              onReopen={(savedId) => {
                void reopenSession(savedId)
              }}
              onExportJson={(savedId) => {
                void exportSessionById(savedId, 'json')
              }}
              onExportMarkdown={(savedId) => {
                void exportSessionById(savedId, 'markdown')
              }}
              onExportBundle={(savedId) => {
                void exportBundleById(savedId)
              }}
              onRename={(savedId, label) => {
                void renameSessionById(savedId, label)
              }}
              onArchive={(savedId, archived) => {
                void setArchivedById(savedId, archived)
              }}
              onDelete={(savedId) => {
                void deleteSessionById(savedId)
              }}
              onRecapture={(savedId) => {
                void recaptureSessionById(savedId)
              }}
              onReview={(savedId) => {
                void reviewSessionById(savedId)
              }}
              onCompare={(leftId, rightId) => {
                void compareSessionsById(leftId, rightId)
              }}
              onVerifyIntegrity={(savedId) => {
                void verifySessionIntegrityById(savedId)
              }}
              onVerifyWorkspaceIntegrity={() => {
                void verifyWorkspaceIntegrity()
              }}
              onRunEvaluationDashboard={() => {
                void runWorkspaceEvaluationDashboard()
              }}
              onExportEvaluationDashboard={() => {
                void exportWorkspaceEvaluationSummary()
              }}
              onRegressionPackSelect={setActiveRegressionPackId}
              onRegressionPackRefresh={() => {
                void refreshRegressionPacks()
              }}
              onRegressionPackCreateFromVisible={(payload) => {
                void createRegressionPackFromVisibleSessions(payload)
              }}
              onRegressionPackDelete={(packId) => {
                void deleteRegressionPackById(packId)
              }}
              onRunRegressionPack={(packId) => {
                void runRegressionPackById(packId)
              }}
              onExportRegressionPackRun={(packId) => {
                void exportRegressionPackRunById(packId)
              }}
            />
            <ResearchPanel
              status={briefState}
              brief={brief}
              evaluation={evaluation}
              errorMessage={error}
              initialEvidenceState={evidenceState}
              evidenceHydrationKey={evidenceHydrationKey}
              onEvidenceStateChange={handleEvidenceStateChange}
            />
          </>
        }
        right={<TracePanel steps={traceSteps} />}
      />
      <QueryInput
        disabled={running}
        onSubmit={runQuery}
        lastQuery={lastQuery}
        sessionId={sessionId}
        followUpHint={followUpHint}
        templates={researchTemplates}
        selectedTemplateId={selectedTemplateId}
        templateState={templateState}
        templateError={templateError}
        onTemplateChange={setSelectedTemplateId}
      />
    </main>
  )
}
