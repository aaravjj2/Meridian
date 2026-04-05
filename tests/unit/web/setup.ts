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
  ),
  http.get('/api/v1/research/sessions/regression/packs', () =>
    HttpResponse.json({
      packs: [],
      count: 0,
    })
  ),
  http.post('/api/v1/research/sessions/regression/packs', async ({ request }) => {
    const body = (await request.json()) as { title?: string; description?: string | null; session_ids?: string[] }
    return HttpResponse.json({
      id: 'rpack-20260405000000-default0001',
      title: body.title ?? 'Regression Pack',
      description: body.description ?? null,
      session_count: Array.isArray(body.session_ids) ? body.session_ids.length : 0,
      created_at: '2026-04-05T00:00:00Z',
      updated_at: '2026-04-05T00:00:00Z',
      pack_signature: 'rpack-sig-default-001',
    })
  }),
  http.delete('/api/v1/research/sessions/regression/packs/:packId', ({ params }) =>
    HttpResponse.json({ deleted: true, id: params.packId })
  ),
  http.post('/api/v1/research/sessions/regression/packs/:packId/run', ({ params }) =>
    HttpResponse.json({
      pack_id: params.packId,
      generated_at: '2026-04-05T00:00:10Z',
      session_count: 0,
      compared_count: 0,
      changed_count: 0,
      unchanged_count: 0,
      thesis_drift_count: 0,
      claim_drift_count: 0,
      provenance_drift_count: 0,
      evaluation_drift_count: 0,
      bundle_drift_count: 0,
      deterministic_signature: 'rpack-run-sig-default-001',
      drifts: [],
    })
  ),
  http.get('/api/v1/research/sessions/regression/packs/:packId/run/export', ({ params }) =>
    HttpResponse.json(
      {
        pack_id: params.packId,
        generated_at: '2026-04-05T00:00:10Z',
        session_count: 0,
        compared_count: 0,
        changed_count: 0,
        unchanged_count: 0,
        thesis_drift_count: 0,
        claim_drift_count: 0,
        provenance_drift_count: 0,
        evaluation_drift_count: 0,
        bundle_drift_count: 0,
        deterministic_signature: 'rpack-run-sig-default-001',
        drifts: [],
      },
      {
        headers: {
          'content-disposition': `attachment; filename=workspace-regression-pack-${String(params.packId)}.json`,
        },
      }
    )
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
