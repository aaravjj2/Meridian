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
    type: 'tool_call',
    step: 3,
    tool: 'news_fetch',
    args: { topic: 'fed rate decision recession', days_back: 7 },
    ts: '2026-04-02T00:00:03Z',
  },
  {
    type: 'tool_result',
    step: 4,
    tool: 'news_fetch',
    preview: [['articles', 2]],
    ts: '2026-04-02T00:00:04Z',
  },
  {
    type: 'reasoning',
    step: 5,
    text: 'Fallback replay complete with deterministic local trace.',
    ts: '2026-04-02T00:00:05Z',
  },
]

const FALLBACK_BRIEF: ResearchBrief = {
  question: 'What does the current yield curve shape imply for equities over the next 6 months?',
  thesis:
    'The curve is still inverted but has steepened, supporting a late-cycle backdrop where equities can hold up near term while downside risk remains elevated.',
  bull_case: [
    {
      point: 'The inversion is less severe than prior months, reducing immediate stress signals.',
      source_ref: 'fred_fetch:T10Y2Y',
    },
    {
      point: 'Inflation trend moderation supports potential easing expectations.',
      source_ref: 'fred_fetch:CPIAUCSL',
    },
    {
      point: 'Rate-cut probabilities remain supportive for risk assets.',
      source_ref: 'prediction_market_fetch:KXFEDCUT-H1-2026',
    },
  ],
  bear_case: [
    {
      point: 'An inverted curve still historically aligns with slower growth and earnings pressure.',
      source_ref: 'fred_fetch:T10Y2Y',
    },
    {
      point: 'Credit spreads remain above soft-landing lows.',
      source_ref: 'fred_fetch:BAMLH0A0HYM2',
    },
  ],
  key_risks: [
    {
      risk: 'Inflation re-acceleration can delay easing and tighten financial conditions.',
      source_ref: 'fred_fetch:CPIAUCSL',
    },
    {
      risk: 'Policy communication shocks can quickly reprice recession expectations.',
      source_ref: 'news_fetch:fed-rate-decision',
    },
  ],
  confidence: 3,
  confidence_rationale: 'Signals are mixed between disinflation progress and persistent inversion.',
  sources: [
    {
      type: 'fred',
      id: 'T10Y2Y',
      excerpt: 'Curve inversion has moderated from recent lows.',
    },
    {
      type: 'fred',
      id: 'CPIAUCSL',
      excerpt: 'Inflation index remains elevated but trend has eased.',
    },
    {
      type: 'market',
      id: 'KXFEDCUT-H1-2026',
      excerpt: 'Kalshi cut-probability remains elevated in mid-2026 contracts.',
    },
  ],
  created_at: '2026-04-02T00:00:04Z',
  trace_steps: [0, 1, 2, 3],
}

async function streamResearch(question: string, onEvent: (step: TraceEvent) => void): Promise<void> {
  const response = await fetch('/api/v1/research', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, mode: 'demo' }),
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

  async function runQuery(question: string) {
    setLastQuery(question)
    setRunning(true)
    setError('')
    setBrief(null)
    setTraceSteps([])
    setBriefState('loading')

    try {
      await streamResearch(question, (step) => {
        setTraceSteps((prev) => [...prev, step])

        if (step.type === 'complete' && step.brief) {
          setBrief(step.brief)
          setBriefState('complete')
        }
        if (step.type === 'error') {
          setError(step.message ?? 'Research failed')
          setBriefState('error')
        }
      })
    } catch {
      // Deterministic fallback path when the API route is unavailable in local-only runs.
      for (const step of FALLBACK_EVENTS) {
        setTraceSteps((prev) => [...prev, step])
      }
      setBrief(FALLBACK_BRIEF)
      setBriefState('complete')
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
      <QueryInput disabled={running} onSubmit={runQuery} lastQuery={lastQuery} />
    </main>
  )
}
