import '@testing-library/jest-dom/vitest'

import { afterAll, afterEach, beforeAll } from 'vitest'
import { vi } from 'vitest'
import { HttpResponse, http } from 'msw'
import { setupServer } from 'msw/node'

export const server = setupServer(
  http.get('/api/v1/research/templates', () =>
    HttpResponse.json({
      templates: [
        {
          id: 'macro_outlook',
          title: 'Macro outlook',
          description: 'Baseline macro framing',
          framing: 'Macro first',
          query_class_default: 'macro_outlook',
          emphasis: ['Cycle and regime interpretation'],
          evaluation_expectations: ['At least one macro signal conflict is surfaced'],
        },
        {
          id: 'event_probability_interpretation',
          title: 'Event probability interpretation',
          description: 'Event odds framing',
          framing: 'Odds first',
          query_class_default: 'event_probability',
          emphasis: ['Cross-venue probability consistency'],
          evaluation_expectations: ['Confidence rationale discusses timing risk'],
        },
        {
          id: 'ticker_macro_framing',
          title: 'Ticker + macro framing',
          description: 'Ticker and macro combined framing',
          framing: 'Bottom-up plus top-down',
          query_class_default: 'ticker_macro',
          emphasis: ['Fundamental versus macro tension'],
          evaluation_expectations: ['Conflicts capture bottom-up vs top-down tension'],
        },
        {
          id: 'thesis_change_compare',
          title: 'Compare old vs new thesis',
          description: 'Delta-oriented thesis updates',
          framing: 'Prior-vs-current comparison',
          query_class_default: 'macro_outlook',
          emphasis: ['Prior-vs-current thesis deltas'],
          evaluation_expectations: ['Follow-up context present when available'],
        },
      ],
      count: 4,
    })
  )
)

class ResizeObserverMock {
  observe() {
    return undefined
  }

  unobserve() {
    return undefined
  }

  disconnect() {
    return undefined
  }
}

vi.stubGlobal('ResizeObserver', ResizeObserverMock)
Object.defineProperty(window.HTMLElement.prototype, 'scrollIntoView', {
  configurable: true,
  value: vi.fn(),
})

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'bypass' })
})

afterEach(() => {
  server.resetHandlers()
})

afterAll(() => {
  server.close()
})
