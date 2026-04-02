import React from 'react'
import { render, screen } from '@testing-library/react'

import ResearchPanel from '@/components/Terminal/ResearchPanel'

const brief = {
  question: 'q',
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
  sources: [
    { type: 'fred', id: 'T10Y2Y', excerpt: 'x' },
    { type: 'fred', id: 'CPIAUCSL', excerpt: 'y' },
    { type: 'market', id: 'KXFEDCUT-H1-2026', excerpt: 'z' },
  ],
  created_at: '2026-04-02T00:00:00Z',
  trace_steps: [0],
} as const

describe('ResearchPanel', () => {
  it('renders complete brief sections and confidence meter', () => {
    render(<ResearchPanel status="complete" brief={brief} errorMessage="" />)

    expect(screen.getByTestId('brief-complete')).toBeInTheDocument()
    expect(screen.getByTestId('thesis-summary')).toHaveTextContent('Macro thesis text')
    expect(screen.getByTestId('bull-case')).toBeInTheDocument()
    expect(screen.getByTestId('bear-case')).toBeInTheDocument()
    expect(screen.getByTestId('confidence-meter')).toHaveTextContent('3 / 5')
  })
})
