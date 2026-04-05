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
  http.get('/api/v1/research/sessions/:savedId/versions', () =>
    HttpResponse.json({
      versions: [],
      count: 0,
    })
  ),
  http.get('/api/v1/research/sessions/:savedId/versions/compare', () =>
    HttpResponse.json({
      left_version_id: 'bver-left',
      right_version_id: 'bver-right',
      left_saved_id: 'rs-left',
      right_saved_id: 'rs-right',
      left_brief_signature: 'left-sig',
      right_brief_signature: 'right-sig',
      thesis_changed: false,
      confidence_changed: false,
      confidence_delta: 0,
      query_class_changed: false,
      template_changed: false,
      follow_up_context_changed: false,
      methodology_changed: false,
      bull_claim_ids_added: [],
      bull_claim_ids_removed: [],
      bear_claim_ids_added: [],
      bear_claim_ids_removed: [],
      risk_claim_ids_added: [],
      risk_claim_ids_removed: [],
      source_refs_added: [],
      source_refs_removed: [],
      conflict_ids_added: [],
      conflict_ids_removed: [],
      derived_indicator_ids_added: [],
      derived_indicator_ids_removed: [],
      deterministic_signature: 'brief-version-diff-default',
    })
  ),
  http.get('/api/v1/research/sessions/:savedId/versions/:versionId', ({ params }) =>
    HttpResponse.json({
      version: {
        version_id: params.versionId,
        version_number: 1,
        saved_id: params.savedId,
        thread_session_id: 'thread-default',
        question: 'default question',
        created_at: '2026-04-05T00:00:00Z',
        saved_at: '2026-04-05T00:00:00Z',
        brief_signature: 'brief-sig-default',
        canonical_signature: 'canon-default',
      },
      brief: {
        question: 'default question',
        thesis: 'default thesis',
        bull_case: [],
        bear_case: [],
        key_risks: [],
        confidence: 3,
        confidence_rationale: 'default rationale',
        sources: [],
        created_at: '2026-04-05T00:00:00Z',
        trace_steps: [],
      },
    })
  ),
  http.get('/api/v1/research/sessions/:savedId/versions/:versionId/export', ({ params }) =>
    HttpResponse.json(
      {
        schema: 'meridian.brief_version_export.v1',
        version: {
          version_id: params.versionId,
          saved_id: params.savedId,
        },
      },
      {
        headers: {
          'content-disposition': `attachment; filename=${String(params.versionId)}.brief.json`,
        },
      }
    )
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
