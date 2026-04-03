import React from 'react'
import { fireEvent, render, screen } from '@testing-library/react'

import ResearchPanel from '@/components/Terminal/ResearchPanel'

const brief = {
  question: 'What does the current yield curve imply for equities?',
  query_class: 'macro_outlook',
  follow_up_context: 'Follow-up to prior question: How should I think about recession odds?',
  thesis: 'Macro thesis text',
  bull_case: [
    { point: 'Bull one', source_ref: 'fred_fetch:T10Y2Y' },
    { point: 'Bull two', source_ref: 'fred_fetch:CPIAUCSL' },
    { point: 'Bull three', source_ref: 'prediction_market_fetch:KXFEDCUT-H1-2026' },
  ],
  bear_case: [
    { point: 'Bear one', source_ref: 'fred_fetch:T10Y2Y' },
    { point: 'Bear two', source_ref: 'fred_fetch:BAMLH0A0HYM2' },
  ],
  key_risks: [
    { risk: 'Risk one', source_ref: 'news_fetch:fed-rate-decision' },
    { risk: 'Risk two', source_ref: 'fred_fetch:CPIAUCSL' },
  ],
  confidence: 3,
  confidence_rationale: 'mixed',
  methodology_summary: 'Cross-source synthesis',
  sources: [
    {
      type: 'fred',
      id: 'T10Y2Y',
      excerpt: 'x',
      claim_refs: ['bull_case[0]', 'bear_case[0]'],
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
    { type: 'fred', id: 'CPIAUCSL', excerpt: 'y', claim_refs: ['bull_case[1]'] },
    {
      type: 'market',
      id: 'KXFEDCUT-H1-2026',
      excerpt: 'z',
      claim_refs: ['bull_case[2]'],
      preview: { kind: 'market_contract', market_prob: 0.64, dislocation: 0.19 },
    },
  ],
  created_at: '2026-04-02T00:00:00Z',
  trace_steps: [0, 1, 2, 3],
} satisfies NonNullable<React.ComponentProps<typeof ResearchPanel>['brief']>

describe('ResearchPanel', () => {
  it('renders complete brief sections, follow-up context, and source previews', () => {
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

    fireEvent.click(screen.getByTestId('source-item-0'))
    expect(screen.getByTestId('source-preview-0')).toBeInTheDocument()
    expect(screen.getByTestId('source-claims-0')).toHaveTextContent('bull_case[0]')
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
})
