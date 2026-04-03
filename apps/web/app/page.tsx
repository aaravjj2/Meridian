'use client'

import { useState } from 'react'

import { createParser } from 'eventsource-parser'

import RegimeDashboard from '@/components/RegimeDashboard/RegimeDashboard'
import QueryInput from '@/components/Terminal/QueryInput'
import ResearchPanel from '@/components/Terminal/ResearchPanel'
import SplitPane from '@/components/Terminal/SplitPane'
import TracePanel from '@/components/Terminal/TracePanel'
import type { ResearchBrief, TraceEvent } from '@/components/Terminal/types'

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

function fallbackBrief(question: string, priorQuestion: string | null): ResearchBrief {
  const queryClass = classifyQuery(question)
  return {
    question,
    query_class: queryClass,
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
  onEvent: (step: TraceEvent) => void
): Promise<void> {
  const response = await fetch('/api/v1/research', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, mode: 'demo', session_id: sessionId ?? undefined }),
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

  async function runQuery(question: string) {
    const priorQuestion = queryHistory.length > 0 ? queryHistory[queryHistory.length - 1] : null

    setLastQuery(question)
    setRunning(true)
    setError('')
    setBrief(null)
    setTraceSteps([])
    setBriefState('loading')

    let resolvedSessionId = sessionId
    let sessionFollowUp = false

    try {
      await streamResearch(question, sessionId, (step) => {
        setTraceSteps((prev) => [...prev, step])
        if (step.session_id) {
          resolvedSessionId = step.session_id
        }
        if (step.followup) {
          sessionFollowUp = true
        }

        if (step.type === 'complete' && step.brief) {
          setBrief(step.brief)
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
      const fallback = fallbackBrief(question, priorQuestion)
      setBrief(fallback)
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
        left={<ResearchPanel status={briefState} brief={brief} errorMessage={error} />}
        right={<TracePanel steps={traceSteps} />}
      />
      <QueryInput
        disabled={running}
        onSubmit={runQuery}
        lastQuery={lastQuery}
        sessionId={sessionId}
        followUpHint={followUpHint}
      />
    </main>
  )
}
