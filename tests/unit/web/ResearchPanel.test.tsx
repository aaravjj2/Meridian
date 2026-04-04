import React from 'react'
import { fireEvent, render, screen } from '@testing-library/react'

import ResearchPanel from '@/components/Terminal/ResearchPanel'

const brief = {
  question: 'What does the current yield curve imply for equities?',
  query_class: 'macro_outlook',
  follow_up_context: 'Follow-up to prior question: How should I think about recession odds?',
  thesis: 'Macro thesis text',
  bull_case: [
    { claim_id: 'bull-1-inversion-easing', point: 'Bull one', source_ref: 'fred_fetch:T10Y2Y' },
    { claim_id: 'bull-2-disinflation-progress', point: 'Bull two', source_ref: 'fred_fetch:CPIAUCSL' },
    {
      claim_id: 'bull-3-easing-pricing-support',
      point: 'Bull three',
      source_ref: 'prediction_market_fetch:KXFEDCUT-H1-2026',
    },
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
  confidence_rationale: 'mixed',
  methodology_summary: 'Cross-source synthesis',
  sources: [
    {
      type: 'fred',
      id: 'T10Y2Y',
      excerpt: 'x',
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
      excerpt: 'y',
      claim_refs: ['bull-2-disinflation-progress', 'risk-2-inflation-surprise'],
    },
    {
      type: 'market',
      id: 'KXFEDCUT-H1-2026',
      excerpt: 'z',
      claim_refs: ['bull-3-easing-pricing-support'],
      preview: { kind: 'market_contract', market_prob: 0.64, dislocation: 0.19 },
    },
  ],
  signal_conflicts: [
    {
      conflict_id: 'conflict-curve-interpretation',
      title: 'Curve interpretation split',
      summary: 'The same curve data can be interpreted as improving but still cautionary.',
      severity: 'medium',
      claim_refs: ['bull-1-inversion-easing', 'bear-1-inversion-still-warning'],
      source_refs: ['fred:T10Y2Y'],
    },
  ],
  created_at: '2026-04-02T00:00:00Z',
  trace_steps: [0, 1, 2, 3],
} satisfies NonNullable<React.ComponentProps<typeof ResearchPanel>['brief']>

describe('ResearchPanel', () => {
  it('renders complete brief sections, supports claim navigation, and shows conflict context', () => {
    render(<ResearchPanel status="complete" brief={brief} errorMessage="" />)

    expect(screen.getByTestId('brief-complete')).toBeInTheDocument()
    expect(screen.getByTestId('brief-query-class')).toHaveTextContent('MACRO OUTLOOK')
    expect(screen.getByTestId('brief-followup-context')).toBeInTheDocument()
    expect(screen.getByTestId('thesis-summary')).toHaveTextContent('Macro thesis text')
    expect(screen.getByTestId('bull-case')).toBeInTheDocument()
    expect(screen.getByTestId('bear-case')).toBeInTheDocument()
    expect(screen.getByTestId('confidence-meter')).toHaveTextContent('3 / 5')
    expect(screen.getByTestId('confidence-rationale')).toHaveTextContent('mixed')
    expect(screen.getByTestId('methodology-summary')).toHaveTextContent('Cross-source synthesis')
    expect(screen.getByTestId('signal-conflicts')).toBeInTheDocument()

    fireEvent.click(screen.getByTestId('claim-link-bull-1-inversion-easing'))
    expect(screen.getByTestId('evidence-drilldown')).toBeInTheDocument()
    expect(screen.getByTestId('active-claim-id')).toHaveTextContent('bull-1-inversion-easing')
    expect(screen.getByTestId('source-preview-0')).toBeInTheDocument()
    expect(screen.getByTestId('source-claims-0')).toHaveTextContent('bull-1-inversion-easing')

    fireEvent.click(screen.getByTestId('signal-conflict-claim-0-1'))
    expect(screen.getByTestId('active-claim-id')).toHaveTextContent('bear-1-inversion-still-warning')
  })

  it.each([
    ['event_probability', 'EVENT PROBABILITY'],
    ['ticker_macro', 'TICKER + MACRO'],
  ] as const)('renders stable brief structure for %s query class', (queryClass, label) => {
    render(
      <ResearchPanel
        status="complete"
        brief={{
          ...brief,
          query_class: queryClass,
          question: `Synthetic ${queryClass} question`,
          follow_up_context: null,
        }}
        errorMessage=""
      />
    )

    expect(screen.getByTestId('brief-query-class')).toHaveTextContent(label)
    expect(screen.getByTestId('thesis-summary')).toBeInTheDocument()
    expect(screen.getByTestId('bull-case-item-0')).toBeInTheDocument()
    expect(screen.getByTestId('bear-case-item-0')).toBeInTheDocument()
    expect(screen.getByTestId('key-risks-item-0')).toBeInTheDocument()
  })

  it('renders provenance and evaluation sections when available', () => {
    render(
      <ResearchPanel
        status="complete"
        brief={{
          ...brief,
          provenance_summary: {
            captured_at: '2026-04-02T00:00:00Z',
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
          sources: brief.sources.map((source) => ({
            ...source,
            provenance: {
              source_ref: `${source.type}:${source.id}`,
              tool_name: source.type === 'market' ? 'prediction_market_fetch' : 'fred_fetch',
              mode: 'demo',
              cache_lineage: 'fixture',
              observed_at: '2026-03-01T00:00:00Z',
              captured_at: '2026-04-02T00:00:00Z',
              freshness: 'aging',
              freshness_hours: 120,
              deterministic: true,
              snapshot: {
                snapshot_id: `snap-${source.id}`,
                snapshot_kind: 'fixture',
                dataset: `${source.type}:${source.id}`,
                dataset_version: 'demo-fixture-v1',
                generated_at: '2026-03-01T00:00:00Z',
                checksum_sha256: `checksum-${source.id}`,
                deterministic: true,
              },
            },
          })),
        }}
        evaluation={{
          version: 'phase-7',
          deterministic_signature: 'sig-123',
          passed: true,
          checks: [
            {
              check_id: 'claim_source_coverage',
              passed: true,
              detail: 'All claims are linked',
              value: '7/7',
            },
          ],
          metrics: {
            source_count: 3,
            freshness_policy_violations: ['news:fed-rate-decision (stale)'],
          },
        }}
        errorMessage=""
      />
    )

    expect(screen.getByTestId('provenance-summary')).toBeInTheDocument()
    expect(screen.getByTestId('snapshot-summary')).toBeInTheDocument()
    expect(screen.getByTestId('snapshot-kind-fixture')).toHaveTextContent('Fixture: 3')
    expect(screen.getByTestId('evaluation-report')).toBeInTheDocument()
    expect(screen.getByTestId('evaluation-signature')).toHaveTextContent('sig-123')
    expect(screen.getByTestId('policy-warning-panel')).toBeInTheDocument()
    expect(screen.getByTestId('policy-warning-item-0')).toHaveTextContent('news:fed-rate-decision (stale)')
    expect(screen.getByTestId('source-freshness-0')).toHaveTextContent('AGING')
    expect(screen.getByTestId('source-snapshot-kind-badge-0')).toHaveTextContent('FIXTURE')

    fireEvent.click(screen.getByTestId('source-item-0'))
    expect(screen.getByTestId('source-snapshot-id-0')).toHaveTextContent('snap-T10Y2Y')
    expect(screen.getByTestId('source-cache-lineage-0')).toHaveTextContent('fixture')
  })
})
