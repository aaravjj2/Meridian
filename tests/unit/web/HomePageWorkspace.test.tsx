import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'

import HomePage from '../../../apps/web/app/page'
import { server } from './setup'

const briefFixture = {
  question: 'Saved macro question',
  query_class: 'macro_outlook',
  follow_up_context: 'Follow-up to prior question: Prior saved question',
  thesis: 'Saved thesis',
  bull_case: [
    { claim_id: 'bull-1-inversion-easing', point: 'Bull one', source_ref: 'fred_fetch:T10Y2Y' },
    { claim_id: 'bull-2-disinflation-progress', point: 'Bull two', source_ref: 'fred_fetch:CPIAUCSL' },
    { claim_id: 'bull-3-easing-pricing-support', point: 'Bull three', source_ref: 'prediction_market_fetch:KXFEDCUT-H1-2026' },
  ],
  bear_case: [
    { claim_id: 'bear-1-inversion-still-warning', point: 'Bear one', source_ref: 'fred_fetch:T10Y2Y' },
    { claim_id: 'bear-2-credit-stress-elevated', point: 'Bear two', source_ref: 'fred_fetch:BAMLH0A0HYM2' },
  ],
  key_risks: [
    { claim_id: 'risk-1-policy-repricing', risk: 'Risk one', source_ref: 'news_fetch:fed-rate-decision' },
    { claim_id: 'risk-2-inflation-surprise', risk: 'Risk two', source_ref: 'fred_fetch:CPIAUCSL' },
  ],
  confidence: 3,
  confidence_rationale: 'Mixed saved confidence',
  methodology_summary: 'Saved methodology',
  sources: [
    {
      type: 'fred',
      id: 'T10Y2Y',
      excerpt: 'Curve excerpt',
      claim_refs: ['bull-1-inversion-easing', 'bear-1-inversion-still-warning'],
      preview: {
        kind: 'fred_series',
        latest: -0.21,
        points: [
          { date: '2025-12-01', value: -0.35 },
          { date: '2026-01-01', value: -0.29 },
          { date: '2026-02-01', value: -0.21 },
        ],
      },
    },
    {
      type: 'fred',
      id: 'CPIAUCSL',
      excerpt: 'Inflation excerpt',
      claim_refs: ['bull-2-disinflation-progress', 'risk-2-inflation-surprise'],
    },
    {
      type: 'market',
      id: 'KXFEDCUT-H1-2026',
      excerpt: 'Market excerpt',
      claim_refs: ['bull-3-easing-pricing-support'],
      preview: {
        kind: 'market_contract',
        market_prob: 0.64,
      },
    },
  ],
  signal_conflicts: [
    {
      conflict_id: 'conflict-curve-interpretation',
      title: 'Curve split',
      summary: 'Saved conflict summary',
      severity: 'medium',
      claim_refs: ['bull-1-inversion-easing', 'bear-1-inversion-still-warning'],
      source_refs: ['fred:T10Y2Y'],
    },
  ],
  created_at: '2026-04-03T10:00:00Z',
  trace_steps: [0, 1, 2],
} as const

const savedSummary = {
  id: 'rs-saved-001',
  question: 'Saved macro question',
  mode: 'demo',
  session_id: 'sess-saved-thread',
  query_class: 'macro_outlook',
  follow_up_context: 'Follow-up to prior question: Prior saved question',
  saved_at: '2026-04-03T10:05:00Z',
  canonical_signature: 'abc123',
} as const

const savedRecord = {
  ...savedSummary,
  brief: briefFixture,
  trace_events: [
    {
      type: 'tool_call',
      step: 0,
      ts: '2026-04-03T10:00:00Z',
      tool: 'fred_fetch',
      args: { series_id: 'T10Y2Y' },
    },
    {
      type: 'complete',
      step: 1,
      ts: '2026-04-03T10:00:02Z',
      brief: briefFixture,
      query_class: 'macro_outlook',
      session_context_used: true,
      duration_ms: 900,
    },
  ],
  evidence_state: {
    active_claim_id: 'bull-1-inversion-easing',
    expanded_source_id: 'fred:T10Y2Y',
  },
  created_at: '2026-04-03T10:00:00Z',
  updated_at: '2026-04-03T10:05:00Z',
} as const

describe('HomePage workspace persistence', () => {
  it('renders workspace loading and empty states', async () => {
    server.use(
      http.get('/api/v1/regime', () =>
        HttpResponse.json({
          dimensions: {
            growth: 'EXPANSION',
            inflation: 'ELEVATED',
            monetary: 'RESTRICTIVE',
            credit: 'CAUTION',
            labor: 'TIGHT',
          },
          narrative: 'n',
          updated_at: '2026-04-03T10:00:00Z',
        })
      ),
      http.get('/api/v1/research/sessions', async () => {
        await new Promise((resolve) => setTimeout(resolve, 20))
        return HttpResponse.json({ sessions: [], count: 0 })
      })
    )

    render(<HomePage />)

    expect(screen.getByTestId('workspace-loading')).toBeInTheDocument()
    expect(await screen.findByTestId('workspace-empty')).toBeInTheDocument()
  })

  it('reopens saved session, then saves and exports from completed state', async () => {
    let saveCalls = 0
    const exportFormats: string[] = []

    server.use(
      http.get('/api/v1/regime', () =>
        HttpResponse.json({
          dimensions: {
            growth: 'EXPANSION',
            inflation: 'ELEVATED',
            monetary: 'RESTRICTIVE',
            credit: 'CAUTION',
            labor: 'TIGHT',
          },
          narrative: 'n',
          updated_at: '2026-04-03T10:00:00Z',
        })
      ),
      http.get('/api/v1/research/sessions', () => HttpResponse.json({ sessions: [savedSummary], count: 1 })),
      http.get('/api/v1/research/sessions/:savedId', ({ params }) => {
        if (params.savedId !== savedSummary.id) {
          return HttpResponse.json({ detail: 'not found' }, { status: 404 })
        }
        return HttpResponse.json(savedRecord)
      }),
      http.post('/api/v1/research/sessions', async ({ request }) => {
        saveCalls += 1
        const body = (await request.json()) as Record<string, unknown>
        return HttpResponse.json({
          ...savedRecord,
          id: 'rs-saved-copy',
          session_id: body.session_id,
          question: body.question,
          brief: body.brief,
          trace_events: body.trace_events,
          evidence_state: body.evidence_state,
          canonical_signature: 'copy-signature',
          saved_at: '2026-04-03T10:06:00Z',
          updated_at: '2026-04-03T10:06:00Z',
        })
      }),
      http.get('/api/v1/research/sessions/:savedId/export', ({ request }) => {
        const format = new URL(request.url).searchParams.get('format') ?? 'json'
        exportFormats.push(format)
        if (format === 'markdown') {
          return HttpResponse.text('# saved markdown\n', {
            headers: {
              'content-type': 'text/markdown; charset=utf-8',
              'content-disposition': 'attachment; filename=rs-saved-copy.md',
            },
          })
        }
        return HttpResponse.json(savedRecord, {
          headers: {
            'content-disposition': 'attachment; filename=rs-saved-copy.json',
          },
        })
      })
    )

    render(<HomePage />)

    expect(await screen.findByTestId('workspace-item-0')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-export-current-json')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-export-current-markdown')).toBeInTheDocument()

    fireEvent.click(screen.getByTestId('workspace-reopen-0'))

    expect(await screen.findByTestId('brief-complete')).toBeInTheDocument()
    expect(screen.getByTestId('trace-step-0')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('claim-link-bull-1-inversion-easing'))
    expect(screen.getByTestId('evidence-drilldown')).toBeInTheDocument()
    expect(screen.getByTestId('active-claim-id')).toHaveTextContent('bull-1-inversion-easing')

    fireEvent.click(screen.getByTestId('save-session-button'))
    await waitFor(() => {
      expect(saveCalls).toBe(1)
    })

    fireEvent.click(screen.getByTestId('workspace-export-current-json'))
    await waitFor(() => {
      expect(exportFormats).toContain('json')
    })

    fireEvent.click(screen.getByTestId('workspace-export-current-markdown'))
    await waitFor(() => {
      expect(exportFormats).toContain('markdown')
    })

    expect(screen.getByTestId('workspace-status')).toBeInTheDocument()
  })
})
