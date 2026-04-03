import React from 'react'
import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'

import TracePanel from '@/components/Terminal/TracePanel'


describe('TracePanel', () => {
  it('renders empty state and grouped trace progression', () => {
    const scrollSpy = vi.fn()
    Object.defineProperty(window.HTMLElement.prototype, 'scrollIntoView', {
      configurable: true,
      value: scrollSpy,
    })

    const { rerender } = render(<TracePanel steps={[]} />)
    expect(screen.getByText('Awaiting query…')).toBeInTheDocument()

    rerender(
      <TracePanel
        steps={[
          {
            type: 'tool_call',
            step: 0,
            ts: '2026-04-02T00:00:00Z',
            tool: 'fred_fetch',
            args: { series_id: 'T10Y2Y' },
          },
          {
            type: 'tool_result',
            step: 1,
            ts: '2026-04-02T00:00:01Z',
            tool: 'fred_fetch',
            preview: [['2026-02-01', -0.21]],
          },
          {
            type: 'reasoning',
            step: 2,
            ts: '2026-04-02T00:00:02Z',
            text: 'Signal synthesis in progress',
          },
          {
            type: 'brief_delta',
            step: 3,
            ts: '2026-04-02T00:00:03Z',
            section: 'thesis',
            text: 'Draft thesis line',
          },
          {
            type: 'complete',
            step: 4,
            ts: '2026-04-02T00:00:04Z',
            duration_ms: 12000,
          },
        ]}
      />
    )

    expect(screen.getByTestId('trace-step-0')).toBeInTheDocument()
    expect(screen.getByTestId('trace-tool-call-0')).toBeInTheDocument()
    expect(screen.getByTestId('trace-group-evidence-0')).toBeInTheDocument()
    expect(screen.getByTestId('trace-group-analysis-2')).toBeInTheDocument()
    expect(screen.getByTestId('trace-group-synthesis-3')).toBeInTheDocument()
    expect(screen.getByTestId('trace-group-outcome-4')).toBeInTheDocument()
    expect(screen.getByTestId('trace-complete')).toHaveTextContent('RESEARCH COMPLETE')
    expect(scrollSpy).toHaveBeenCalled()
  })
})
