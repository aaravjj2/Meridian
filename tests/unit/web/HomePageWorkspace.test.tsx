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
  provenance_summary: {
    source_count: 3,
    freshness_counts: {
      fresh: 1,
      aging: 2,
      stale: 0,
      unknown: 0,
    },
  },
  snapshot_summary: {
    snapshot_count: 3,
    snapshot_kind_counts: {
      fixture: 3,
      cache: 0,
      live_capture: 0,
      derived: 0,
      unknown: 0,
    },
    cache_lineage_counts: {
      fixture: 3,
      cache: 0,
      fresh_pull: 0,
      derived: 0,
      unknown: 0,
    },
    snapshot_checksum_coverage: 3,
  },
  created_at: '2026-04-03T10:00:00Z',
  trace_steps: [0, 1, 2],
} as const

const savedSummary = {
  id: 'rs-saved-001',
  question: 'Saved macro question',
  mode: 'demo',
  session_id: 'sess-saved-thread',
  label: 'Saved label one',
  query_class: 'macro_outlook',
  follow_up_context: 'Follow-up to prior question: Prior saved question',
  archived: false,
  archived_at: null,
  saved_at: '2026-04-03T10:05:00Z',
  updated_at: '2026-04-03T10:05:00Z',
  canonical_signature: 'abc123',
  evaluation_passed: true,
  evaluation_signature: 'eval-abc123',
  snapshot_kind_counts: {
    fixture: 3,
    cache: 0,
    live_capture: 0,
    derived: 0,
    unknown: 0,
  },
  snapshot_signature: 'snap-sig-abc123',
} as const

const savedSummaryTwo = {
  id: 'rs-saved-002',
  question: 'Second saved macro question',
  mode: 'demo',
  session_id: 'sess-saved-thread-2',
  label: 'Saved label two',
  query_class: 'event_probability',
  follow_up_context: null,
  archived: false,
  archived_at: null,
  saved_at: '2026-04-03T10:06:00Z',
  updated_at: '2026-04-03T10:06:00Z',
  canonical_signature: 'def456',
  evaluation_passed: true,
  evaluation_signature: 'eval-def456',
  snapshot_kind_counts: {
    fixture: 3,
    cache: 0,
    live_capture: 0,
    derived: 0,
    unknown: 0,
  },
  snapshot_signature: 'snap-sig-def456',
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
  evaluation: {
    version: 'phase-7',
    deterministic_signature: 'eval-abc123',
    passed: true,
    checks: [
      {
        check_id: 'claim_source_coverage',
        passed: true,
        detail: 'all linked',
        value: '7/7',
      },
    ],
    metrics: { source_count: 3 },
  },
  created_at: '2026-04-03T10:00:00Z',
  updated_at: '2026-04-03T10:05:00Z',
} as const

const savedRecordTwo = {
  ...savedSummaryTwo,
  brief: {
    ...briefFixture,
    question: 'Second saved macro question',
    query_class: 'event_probability',
    thesis: 'Second saved thesis',
    follow_up_context: null,
    confidence: 4,
    created_at: '2026-04-03T10:06:00Z',
  },
  trace_events: [
    {
      type: 'tool_call',
      step: 0,
      ts: '2026-04-03T10:06:00Z',
      tool: 'fred_fetch',
      args: { series_id: 'CPIAUCSL' },
    },
    {
      type: 'complete',
      step: 1,
      ts: '2026-04-03T10:06:02Z',
      brief: {
        ...briefFixture,
        question: 'Second saved macro question',
        query_class: 'event_probability',
        thesis: 'Second saved thesis',
        follow_up_context: null,
        confidence: 4,
        created_at: '2026-04-03T10:06:00Z',
      },
      query_class: 'event_probability',
      session_context_used: true,
      duration_ms: 850,
    },
  ],
  evidence_state: {
    active_claim_id: 'bull-2-disinflation-progress',
    expanded_source_id: 'fred:CPIAUCSL',
  },
  evaluation: {
    version: 'phase-7',
    deterministic_signature: 'eval-def456',
    passed: true,
    checks: [
      {
        check_id: 'claim_source_coverage',
        passed: true,
        detail: 'all linked',
        value: '7/7',
      },
    ],
    metrics: { source_count: 3 },
  },
  created_at: '2026-04-03T10:06:00Z',
  updated_at: '2026-04-03T10:06:00Z',
} as const

const collectionSummary = {
  id: 'coll-20260403110000-abcd1234',
  title: 'Macro Notebook',
  summary: 'Session thread',
  session_count: 1,
  created_at: '2026-04-03T11:00:00Z',
  updated_at: '2026-04-03T11:00:00Z',
  collection_signature: 'collection-sig-001',
} as const

const collectionDetail = {
  collection: {
    id: collectionSummary.id,
    title: collectionSummary.title,
    summary: collectionSummary.summary,
    notes: 'Initial notes',
    session_ids: [savedSummary.id],
    created_at: collectionSummary.created_at,
    updated_at: collectionSummary.updated_at,
    collection_signature: collectionSummary.collection_signature,
  },
  timeline_signature: 'timeline-sig-collection-001',
  timeline: [
    {
      session_id: savedSummary.id,
      exists: true,
      label: savedSummary.label,
      question: savedSummary.question,
      query_class: savedSummary.query_class,
      saved_at: savedSummary.saved_at,
      evaluation_passed: true,
      snapshot_signature: savedSummary.snapshot_signature,
      archived: false,
      thesis_state: {
        thesis: briefFixture.thesis,
        confidence: briefFixture.confidence,
        claim_ids: [
          'bull-1-inversion-easing',
          'bull-2-disinflation-progress',
          'bull-3-easing-pricing-support',
          'bear-1-inversion-still-warning',
          'bear-2-credit-stress-elevated',
          'risk-1-policy-repricing',
          'risk-2-inflation-surprise',
        ],
        claim_count: 7,
        freshness_policy_violation_count: 0,
        freshness_policy_warning_count: 0,
        conflict_ids: ['conflict-curve-interpretation'],
        conflict_count: 1,
        evaluation_passed: true,
        evaluation_signature: 'eval-abc123',
      },
      thesis_delta: {
        previous_session_id: null,
        thesis_changed: false,
        confidence_changed: false,
        claims_changed: false,
        claim_ids_added: [],
        claim_ids_removed: [],
        freshness_policy_changed: false,
        freshness_policy_violation_delta: 0,
        freshness_policy_warning_delta: 0,
        conflicts_changed: false,
        conflict_ids_added: [],
        conflict_ids_removed: [],
        evaluation_changed: false,
        evaluation_passed_changed: false,
        evaluation_signature_before: null,
        evaluation_signature_after: 'eval-abc123',
        delta_signature: 'delta-sig-baseline',
      },
    },
  ],
  missing_session_count: 0,
} as const

const threadTimelineSingle = {
  thread_session_id: savedSummary.session_id,
  timeline_signature: 'thread-timeline-sig-001',
  timeline: collectionDetail.timeline,
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
      }),
      http.get('/api/v1/collections', () => HttpResponse.json({ collections: [], count: 0 }))
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
      http.get('/api/v1/research/sessions/:savedId/timeline', () => HttpResponse.json(threadTimelineSingle)),
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
      }),
      http.get('/api/v1/collections', () => HttpResponse.json({ collections: [], count: 0 }))
    )

    render(<HomePage />)

    expect(await screen.findByTestId('workspace-item-0')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-evaluation-0')).toHaveTextContent('Eval PASS')
    expect(screen.getByTestId('workspace-export-current-json')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-export-current-markdown')).toBeInTheDocument()

    fireEvent.click(screen.getByTestId('workspace-reopen-0'))

    expect(await screen.findByTestId('brief-complete')).toBeInTheDocument()
    expect(await screen.findByTestId('workspace-thread-signature')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-thread-timeline-item-0')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-thread-delta-0')).toBeInTheDocument()
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

  it('supports compare and integrity workspace actions', async () => {
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
      http.get('/api/v1/research/sessions', ({ request }) => {
        const url = new URL(request.url)
        if (url.searchParams.get('search') === 'Second') {
          return HttpResponse.json({ sessions: [savedSummaryTwo], count: 1 })
        }
        return HttpResponse.json({ sessions: [savedSummary, savedSummaryTwo], count: 2 })
      }),
      http.get('/api/v1/research/sessions/compare', () =>
        HttpResponse.json({
          left_id: savedSummary.id,
          right_id: savedSummaryTwo.id,
          signature_match: false,
          metadata_diffs: [
            { field: 'query_class', left: 'macro_outlook', right: 'event_probability', changed: true },
          ],
          claim_diffs: {
            bull_added: ['bull-2-disinflation-progress'],
            bull_removed: ['bull-1-inversion-easing'],
          },
          source_diffs: {
            sources_added: ['fred:CPIAUCSL'],
            sources_removed: ['fred:T10Y2Y'],
          },
          snapshot_drift: {
            left_snapshot_signature: 'snap-sig-abc123',
            right_snapshot_signature: 'snap-sig-def456',
            snapshot_signature_changed: true,
            left_evaluation_signature: 'eval-abc123',
            right_evaluation_signature: 'eval-def456',
            evaluation_signature_changed: true,
            source_set_changed: true,
            source_set_delta_count: 2,
            sources_added: ['fred:CPIAUCSL'],
            sources_removed: ['fred:T10Y2Y'],
            snapshot_ids_changed: [
              {
                source_ref: 'fred:T10Y2Y',
                left_snapshot_id: 'snap-left-123',
                right_snapshot_id: 'snap-right-987',
                left_snapshot_kind: 'fixture',
                right_snapshot_kind: 'cache',
              },
            ],
            freshness_changed: [
              {
                source_ref: 'fred:T10Y2Y',
                left_freshness: 'fresh',
                right_freshness: 'aging',
                left_freshness_hours: 12,
                right_freshness_hours: 72,
              },
            ],
            drift_signature: 'drift-sig-123',
          },
          conflict_diffs: {
            resolved: [],
            unchanged: [
              {
                conflict_id: 'conflict-curve-interpretation',
                title: 'Curve interpretation split',
                state: 'unchanged',
                left_severity: 'medium',
                right_severity: 'medium',
                claim_refs_added: [],
                claim_refs_removed: [],
                source_refs_added: [],
                source_refs_removed: [],
                claim_delta: false,
                source_delta: false,
                snapshot_delta: true,
              },
            ],
            worsened: [
              {
                conflict_id: 'conflict-inflation-tail-risk',
                title: 'Inflation tail risk re-pricing',
                state: 'worsened',
                left_severity: 'medium',
                right_severity: 'high',
                claim_refs_added: ['risk-2-inflation-surprise'],
                claim_refs_removed: [],
                source_refs_added: ['fred:CPIAUCSL'],
                source_refs_removed: [],
                claim_delta: true,
                source_delta: true,
                snapshot_delta: true,
              },
            ],
            drift_signature: 'conflict-drift-sig-987',
          },
          trace_diffs: {
            left_event_count: 2,
            right_event_count: 2,
            event_count_delta: 0,
            event_type_deltas: { complete: 0, tool_call: 0 },
            left_step_range: [0, 1],
            right_step_range: [0, 1],
          },
          summary: {
            changed_fields: ['query_class'],
            total_changed_fields: 1,
            total_claim_changes: 2,
            total_source_changes: 2,
            thesis_changed: true,
            confidence_changed: true,
            signature_match: false,
            snapshot_id_changes: 1,
            freshness_changes: 1,
            source_set_changed: true,
            evaluation_signature_changed: true,
            snapshot_drift_signature: 'drift-sig-123',
            resolved_conflict_count: 0,
            unchanged_conflict_count: 1,
            worsened_conflict_count: 1,
            conflict_drift_signature: 'conflict-drift-sig-987',
          },
        })
      ),
      http.post('/api/v1/research/sessions/:savedId/recapture', ({ params }) =>
        HttpResponse.json({
          saved: {
            ...savedRecord,
            id: 'rs-recapture-003',
            label: 'Saved label one [recapture]',
            updated_at: '2026-04-03T10:20:00Z',
          },
          lineage: {
            source_session_id: String(params.savedId),
            recaptured_session_id: 'rs-recapture-003',
            recapture_mode: 'demo_pseudo_refresh',
            before_snapshot_signature: 'snap-sig-abc123',
            after_snapshot_signature: 'snap-sig-recapture-003',
            snapshot_id_changes: 3,
            source_set_changes: 0,
            transition_count: 3,
            transitions: [
              {
                source_ref: 'fred:T10Y2Y',
                before_snapshot_id: 'snap-old-001',
                after_snapshot_id: 'snap-new-001',
                before_cache_lineage: 'fixture',
                after_cache_lineage: 'derived',
              },
            ],
            generated_at: '2026-04-03T10:20:00Z',
          },
        })
      ),
      http.get('/api/v1/research/sessions/:savedId/integrity', ({ params }) =>
        HttpResponse.json({
          id: params.savedId,
          signature_valid: true,
          canonical_signature: 'sig',
          recomputed_signature: 'sig',
          trace_event_count: 2,
          trace_step_order_valid: true,
          trace_step_unique: true,
          evidence_state_valid: true,
          provenance_complete: true,
          freshness_valid: true,
          freshness_policy_valid: true,
          freshness_policy_violation_count: 0,
          snapshot_complete: true,
          snapshot_consistent: true,
          snapshot_summary_present: true,
          snapshot_checksum_complete: true,
          evaluation_present: true,
          evaluation_valid: true,
          evaluation_signature: 'eval-abc123',
          bundle_snapshot_signature: 'snap-sig-abc123',
          issues: [],
          checked_at: '2026-04-03T10:10:00Z',
          provenance: {},
        })
      ),
      http.get('/api/v1/research/sessions/integrity', () =>
        HttpResponse.json({
          reports: [
            {
              id: savedSummary.id,
              signature_valid: true,
              canonical_signature: 'sig-a',
              recomputed_signature: 'sig-a',
              trace_event_count: 2,
              trace_step_order_valid: true,
              trace_step_unique: true,
              evidence_state_valid: true,
              provenance_complete: true,
              freshness_valid: true,
              freshness_policy_valid: true,
              freshness_policy_violation_count: 0,
              snapshot_complete: true,
              snapshot_consistent: true,
              snapshot_summary_present: true,
              snapshot_checksum_complete: true,
              evaluation_present: true,
              evaluation_valid: true,
              evaluation_signature: 'eval-abc123',
              bundle_snapshot_signature: 'snap-sig-abc123',
              issues: [],
              checked_at: '2026-04-03T10:10:00Z',
              provenance: {},
            },
            {
              id: savedSummaryTwo.id,
              signature_valid: true,
              canonical_signature: 'sig-b',
              recomputed_signature: 'sig-b',
              trace_event_count: 2,
              trace_step_order_valid: true,
              trace_step_unique: true,
              evidence_state_valid: true,
              provenance_complete: true,
              freshness_valid: true,
              freshness_policy_valid: true,
              freshness_policy_violation_count: 0,
              snapshot_complete: true,
              snapshot_consistent: true,
              snapshot_summary_present: true,
              snapshot_checksum_complete: true,
              evaluation_present: true,
              evaluation_valid: true,
              evaluation_signature: 'eval-def456',
              bundle_snapshot_signature: 'snap-sig-def456',
              issues: [],
              checked_at: '2026-04-03T10:10:00Z',
              provenance: {},
            },
          ],
          count: 2,
          healthy_count: 2,
          issue_count: 0,
        })
      ),
      http.get('/api/v1/research/sessions/:savedId', ({ params }) => {
        if (params.savedId === savedSummaryTwo.id) {
          return HttpResponse.json(savedRecordTwo)
        }
        return HttpResponse.json(savedRecord)
      }),
      http.get('/api/v1/research/sessions/:savedId/timeline', ({ params }) => {
        if (params.savedId === savedSummaryTwo.id) {
          return HttpResponse.json({
            thread_session_id: savedSummaryTwo.session_id,
            timeline_signature: 'thread-timeline-sig-compare-2',
            timeline: [
              collectionDetail.timeline[0],
              {
                ...collectionDetail.timeline[0],
                session_id: savedSummaryTwo.id,
                label: savedSummaryTwo.label,
                question: savedSummaryTwo.question,
                query_class: savedSummaryTwo.query_class,
                saved_at: savedSummaryTwo.saved_at,
                snapshot_signature: savedSummaryTwo.snapshot_signature,
                thesis_state: {
                  ...collectionDetail.timeline[0].thesis_state,
                  thesis: savedRecordTwo.brief.thesis,
                  confidence: savedRecordTwo.brief.confidence,
                  evaluation_signature: 'eval-def456',
                },
                thesis_delta: {
                  ...collectionDetail.timeline[0].thesis_delta,
                  previous_session_id: savedSummary.id,
                  thesis_changed: true,
                  confidence_changed: true,
                  evaluation_changed: true,
                  evaluation_signature_before: 'eval-abc123',
                  evaluation_signature_after: 'eval-def456',
                  delta_signature: 'delta-sig-thread-2',
                },
              },
            ],
          })
        }
        return HttpResponse.json(threadTimelineSingle)
      }),
      http.get('/api/v1/collections', () => HttpResponse.json({ collections: [], count: 0 }))
    )

    render(<HomePage />)

    expect(await screen.findByTestId('workspace-item-0')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-snapshot-0')).toBeInTheDocument()

    fireEvent.change(screen.getByTestId('workspace-compare-left'), {
      target: { value: savedSummary.id },
    })
    fireEvent.change(screen.getByTestId('workspace-compare-right'), {
      target: { value: savedSummaryTwo.id },
    })
    fireEvent.click(screen.getByTestId('workspace-compare-run'))

    expect(await screen.findByTestId('workspace-compare-result')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-compare-signature')).toHaveTextContent('different')
    expect(screen.getByTestId('workspace-compare-drift-panel')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-compare-drift-evaluation-signature')).toHaveTextContent('yes')
    expect(screen.getByTestId('workspace-compare-drift-source-set')).toHaveTextContent('yes')
    expect(screen.getByTestId('workspace-compare-snapshot-id-change-0')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-compare-freshness-change-0')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-compare-conflict-panel')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-compare-conflict-worsened-count')).toHaveTextContent('1')
    expect(screen.getByTestId('workspace-compare-conflict-item-0')).toBeInTheDocument()

    fireEvent.click(screen.getByTestId('workspace-recapture-0'))
    expect(await screen.findByTestId('workspace-recapture-lineage')).toBeInTheDocument()
    expect(await screen.findByTestId('workspace-thread-signature')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-thread-timeline-item-0')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-recapture-mode')).toHaveTextContent('demo_pseudo_refresh')
    expect(screen.getByTestId('workspace-recapture-snapshot-id-changes')).toHaveTextContent('3')
    expect(screen.getByTestId('workspace-recapture-transition-0')).toBeInTheDocument()

    fireEvent.click(screen.getByTestId('workspace-verify-0'))
    expect(await screen.findByTestId('workspace-integrity-report')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-integrity-provenance')).toHaveTextContent('complete')
    expect(screen.getByTestId('workspace-integrity-freshness-policy')).toHaveTextContent('compliant')
    expect(screen.getByTestId('workspace-integrity-snapshot')).toHaveTextContent('complete + consistent')
    expect(screen.getByTestId('workspace-integrity-evaluation')).toHaveTextContent('valid')

    fireEvent.click(screen.getByTestId('workspace-integrity-run-all'))
    expect(await screen.findByTestId('workspace-integrity-overview')).toHaveTextContent('Checked 2 sessions')

    fireEvent.change(screen.getByTestId('workspace-search-input'), {
      target: { value: 'Second' },
    })
    await waitFor(() => {
      expect(screen.getByText('Second saved macro question')).toBeInTheDocument()
    })
  })

  it('supports collection create, timeline management, reorder, and reopen actions', async () => {
    const sessionById: Record<string, any> = {
      [savedSummary.id]: savedSummary,
      [savedSummaryTwo.id]: savedSummaryTwo,
    }
    const fullRecordById: Record<string, any> = {
      [savedSummary.id]: savedRecord,
      [savedSummaryTwo.id]: savedRecordTwo,
    }

    let detail: any = {
      ...collectionDetail,
      collection: {
        ...collectionDetail.collection,
        session_ids: [],
      },
      timeline: [],
      missing_session_count: 0,
    }
    let listPayload: Array<any> = []
    let patchCalls = 0
    let reorderCalls = 0

    const syncListFromDetail = () => {
      listPayload = [
        {
          ...collectionSummary,
          id: detail.collection.id,
          title: detail.collection.title,
          summary: detail.collection.summary,
          session_count: detail.collection.session_ids.length,
          updated_at: detail.collection.updated_at,
          collection_signature: detail.collection.collection_signature,
        },
      ]
    }

    const rebuildTimeline = () => {
      detail = {
        ...detail,
        timeline_signature: `timeline-sig-${detail.collection.session_ids.join('-') || 'empty'}`,
        timeline: detail.collection.session_ids.map((sessionId: string, idx: number) => {
          const record = fullRecordById[sessionId]
          const previousSessionId = idx > 0 ? detail.collection.session_ids[idx - 1] : null
          return {
            session_id: sessionId,
            exists: true,
            label: sessionById[sessionId].label ?? null,
            question: sessionById[sessionId].question,
            query_class: sessionById[sessionId].query_class,
            saved_at: sessionById[sessionId].saved_at,
            evaluation_passed: true,
            snapshot_signature: sessionById[sessionId].snapshot_signature ?? null,
            archived: false,
            thesis_state: {
              thesis: record.brief.thesis,
              confidence: record.brief.confidence,
              claim_ids: [
                'bull-1-inversion-easing',
                'bull-2-disinflation-progress',
                'bull-3-easing-pricing-support',
                'bear-1-inversion-still-warning',
                'bear-2-credit-stress-elevated',
                'risk-1-policy-repricing',
                'risk-2-inflation-surprise',
              ],
              claim_count: 7,
              freshness_policy_violation_count: 0,
              freshness_policy_warning_count: 0,
              conflict_ids: ['conflict-curve-interpretation'],
              conflict_count: 1,
              evaluation_passed: true,
              evaluation_signature: record.evaluation.deterministic_signature,
            },
            thesis_delta: {
              previous_session_id: previousSessionId,
              thesis_changed: idx > 0,
              confidence_changed: idx > 0,
              claims_changed: false,
              claim_ids_added: [],
              claim_ids_removed: [],
              freshness_policy_changed: false,
              freshness_policy_violation_delta: 0,
              freshness_policy_warning_delta: 0,
              conflicts_changed: false,
              conflict_ids_added: [],
              conflict_ids_removed: [],
              evaluation_changed: idx > 0,
              evaluation_passed_changed: false,
              evaluation_signature_before:
                idx > 0 ? fullRecordById[previousSessionId as string].evaluation.deterministic_signature : null,
              evaluation_signature_after: record.evaluation.deterministic_signature,
              delta_signature: `delta-sig-${sessionId}-${idx}`,
            },
          }
        }),
      }
    }

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
      http.get('/api/v1/research/sessions', () => HttpResponse.json({ sessions: [savedSummary, savedSummaryTwo], count: 2 })),
      http.get('/api/v1/research/sessions/:savedId', ({ params }) => {
        return HttpResponse.json(fullRecordById[String(params.savedId)])
      }),
      http.get('/api/v1/research/sessions/:savedId/timeline', ({ params }) => {
        const savedId = String(params.savedId)
        const summary = sessionById[savedId] ?? savedSummary
        const record = fullRecordById[savedId] ?? savedRecord
        return HttpResponse.json({
          thread_session_id: summary.session_id,
          timeline_signature: `thread-timeline-${summary.session_id}`,
          timeline: [
            {
              session_id: savedId,
              exists: true,
              label: summary.label,
              question: summary.question,
              query_class: summary.query_class,
              saved_at: summary.saved_at,
              evaluation_passed: true,
              snapshot_signature: summary.snapshot_signature,
              archived: false,
              thesis_state: {
                thesis: record.brief.thesis,
                confidence: record.brief.confidence,
                claim_ids: [
                  'bull-1-inversion-easing',
                  'bull-2-disinflation-progress',
                  'bull-3-easing-pricing-support',
                  'bear-1-inversion-still-warning',
                  'bear-2-credit-stress-elevated',
                  'risk-1-policy-repricing',
                  'risk-2-inflation-surprise',
                ],
                claim_count: 7,
                freshness_policy_violation_count: 0,
                freshness_policy_warning_count: 0,
                conflict_ids: ['conflict-curve-interpretation'],
                conflict_count: 1,
                evaluation_passed: true,
                evaluation_signature: record.evaluation.deterministic_signature,
              },
              thesis_delta: {
                previous_session_id: null,
                thesis_changed: false,
                confidence_changed: false,
                claims_changed: false,
                claim_ids_added: [],
                claim_ids_removed: [],
                freshness_policy_changed: false,
                freshness_policy_violation_delta: 0,
                freshness_policy_warning_delta: 0,
                conflicts_changed: false,
                conflict_ids_added: [],
                conflict_ids_removed: [],
                evaluation_changed: false,
                evaluation_passed_changed: false,
                evaluation_signature_before: null,
                evaluation_signature_after: record.evaluation.deterministic_signature,
                delta_signature: `delta-${savedId}`,
              },
            },
          ],
        })
      }),
      http.get('/api/v1/collections', () => HttpResponse.json({ collections: listPayload, count: listPayload.length })),
      http.post('/api/v1/collections', async ({ request }) => {
        const body = (await request.json()) as { title: string; summary?: string; notes?: string }
        detail = {
          ...detail,
          collection: {
            ...detail.collection,
            id: 'coll-20260403113000-zz001122',
            title: body.title,
            summary: body.summary ?? null,
            notes: body.notes ?? null,
            session_ids: [],
            updated_at: '2026-04-03T11:30:00Z',
            collection_signature: 'collection-sig-created',
          },
          timeline: [],
          missing_session_count: 0,
        }
        syncListFromDetail()
        return HttpResponse.json(detail)
      }),
      http.get('/api/v1/collections/:collectionId', () => HttpResponse.json(detail)),
      http.patch('/api/v1/collections/:collectionId', async ({ request }) => {
        patchCalls += 1
        const body = (await request.json()) as { title?: string; summary?: string | null; notes?: string | null }
        detail = {
          ...detail,
          collection: {
            ...detail.collection,
            title: body.title ?? detail.collection.title,
            summary: body.summary ?? null,
            notes: body.notes ?? null,
            updated_at: '2026-04-03T11:31:00Z',
            collection_signature: 'collection-sig-updated',
          },
        }
        syncListFromDetail()
        return HttpResponse.json(detail)
      }),
      http.post('/api/v1/collections/:collectionId/sessions', async ({ request }) => {
        const body = (await request.json()) as { session_id: string; position?: number }
        const next = [...detail.collection.session_ids]
        if (!next.includes(body.session_id)) {
          if (typeof body.position === 'number' && body.position >= 0 && body.position <= next.length) {
            next.splice(body.position, 0, body.session_id)
          } else {
            next.push(body.session_id)
          }
        }
        detail = {
          ...detail,
          collection: {
            ...detail.collection,
            session_ids: next,
            updated_at: '2026-04-03T11:32:00Z',
            collection_signature: `collection-sig-${next.join('-')}`,
          },
        }
        rebuildTimeline()
        syncListFromDetail()
        return HttpResponse.json(detail)
      }),
      http.delete('/api/v1/collections/:collectionId/sessions/:sessionId', ({ params }) => {
        detail = {
          ...detail,
          collection: {
            ...detail.collection,
            session_ids: detail.collection.session_ids.filter(
              (sessionId: string) => sessionId !== String(params.sessionId)
            ),
            updated_at: '2026-04-03T11:33:00Z',
            collection_signature: 'collection-sig-removed',
          },
        }
        rebuildTimeline()
        syncListFromDetail()
        return HttpResponse.json(detail)
      }),
      http.put('/api/v1/collections/:collectionId/sessions/reorder', async ({ request }) => {
        reorderCalls += 1
        const body = (await request.json()) as { session_ids: string[] }
        detail = {
          ...detail,
          collection: {
            ...detail.collection,
            session_ids: body.session_ids,
            updated_at: '2026-04-03T11:34:00Z',
            collection_signature: `collection-sig-${body.session_ids.join('-')}`,
          },
        }
        rebuildTimeline()
        syncListFromDetail()
        return HttpResponse.json(detail)
      }),
      http.get('/api/v1/collections/:collectionId/bundle', ({ params }) => {
        return HttpResponse.json(
          {
            bundle_version: 'wave14-v2',
            bundle_kind: 'collection',
            manifest: {
              collection_id: params.collectionId,
              deterministic_signature: 'bundle-collection-signature',
            },
            files: {
              collection_json: {
                id: params.collectionId,
              },
            },
          },
          {
            headers: {
              'content-disposition': `attachment; filename=${String(params.collectionId)}.bundle.json`,
            },
          }
        )
      })
    )

    render(<HomePage />)

    expect(await screen.findByTestId('workspace-collections-empty')).toBeInTheDocument()

    fireEvent.change(screen.getByTestId('workspace-collection-create-title'), {
      target: { value: 'Macro Notebook' },
    })
    fireEvent.change(screen.getByTestId('workspace-collection-create-summary'), {
      target: { value: 'Threaded sessions' },
    })
    fireEvent.click(screen.getByTestId('workspace-collection-create-submit'))

    expect(await screen.findByTestId('workspace-collection-detail')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-collection-timeline-empty')).toBeInTheDocument()

    fireEvent.change(screen.getByTestId('workspace-collection-edit-notes'), {
      target: { value: 'Updated notes for this notebook' },
    })
    fireEvent.click(screen.getByTestId('workspace-collection-save'))
    await waitFor(() => {
      expect(patchCalls).toBe(1)
    })

    fireEvent.click(screen.getByTestId('workspace-reopen-0'))
    expect(await screen.findByTestId('brief-complete')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('workspace-collection-add-active-session'))
    expect(await screen.findByTestId('workspace-collection-timeline-item-0')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-collection-timeline-signature')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-collection-thesis-0')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-collection-delta-0')).toBeInTheDocument()

    fireEvent.click(screen.getByTestId('workspace-reopen-1'))
    expect(await screen.findByTestId('brief-complete')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('workspace-collection-add-active-session'))
    expect(await screen.findByTestId('workspace-collection-timeline-item-1')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-collection-delta-1')).toBeInTheDocument()

    fireEvent.click(screen.getByTestId('workspace-collection-move-up-1'))
    await waitFor(() => {
      expect(reorderCalls).toBe(1)
    })

    fireEvent.click(screen.getByTestId('workspace-collection-reopen-0'))
    expect(await screen.findByTestId('brief-complete')).toBeInTheDocument()
    expect(await screen.findByTestId('workspace-thread-signature')).toBeInTheDocument()
    expect(screen.getByTestId('workspace-thread-timeline-item-0')).toBeInTheDocument()

    fireEvent.click(screen.getByTestId('workspace-collection-export-bundle'))
    await waitFor(() => {
      expect(screen.getByTestId('workspace-status')).toHaveTextContent('Exported collection')
    })

    fireEvent.click(screen.getByTestId('workspace-collection-remove-0'))
    await waitFor(() => {
      expect(screen.getByTestId('workspace-collection-timeline-item-0')).toBeInTheDocument()
    })
  })
})
