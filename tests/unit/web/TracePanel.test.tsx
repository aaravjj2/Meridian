import React from 'react'
import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'

import TracePanel from '@/components/Terminal/TracePanel'


describe('TracePanel', () => {
  it('renders empty state and tool call row', () => {
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
        ]}
      />
    )

    expect(screen.getByTestId('trace-step-0')).toBeInTheDocument()
    expect(screen.getByTestId('trace-tool-call-0')).toBeInTheDocument()
    expect(scrollSpy).toHaveBeenCalled()
  })
})
