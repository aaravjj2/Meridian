import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { HttpResponse, http } from 'msw'

import ScreenerPage from '@/app/screener/page'
import { server } from './setup'

const screenerPayload = {
  contracts: [
    {
      market_id: 'pm-fed-cut-june-2026',
      platform: 'polymarket',
      category: 'fed_policy',
      title: 'Fed cut',
      resolution_date: '2026-06-30',
      market_prob: 0.67,
      model_prob: 0.41,
      dislocation: 0.26,
      direction: 'market_overpriced',
      explanation: 'A',
      confidence: 2,
      scored_at: '2026-04-02T00:00:00Z',
    },
    {
      market_id: 'KXFEDCUT-H1-2026',
      platform: 'kalshi',
      category: 'fed_policy',
      title: 'Kalshi cut',
      resolution_date: '2026-06-30',
      market_prob: 0.64,
      model_prob: 0.45,
      dislocation: 0.19,
      direction: 'market_overpriced',
      explanation: 'B',
      confidence: 5,
      scored_at: '2026-04-02T00:00:00Z',
    },
    {
      market_id: 'pm-recession-2026',
      platform: 'polymarket',
      category: 'recession',
      title: 'Recession',
      resolution_date: '2026-12-31',
      market_prob: 0.33,
      model_prob: 0.48,
      dislocation: 0.15,
      direction: 'market_underpriced',
      explanation: 'C',
      confidence: 1,
      scored_at: '2026-04-02T00:00:00Z',
    },
    {
      market_id: 'KXREC-2026',
      platform: 'kalshi',
      category: 'recession',
      title: 'Kalshi recession',
      resolution_date: '2026-12-31',
      market_prob: 0.29,
      model_prob: 0.43,
      dislocation: 0.14,
      direction: 'market_underpriced',
      explanation: 'D',
      confidence: 4,
      scored_at: '2026-04-02T00:00:00Z',
    },
    {
      market_id: 'pm-cpi-over-3-q2-2026',
      platform: 'polymarket',
      category: 'inflation',
      title: 'CPI',
      resolution_date: '2026-07-15',
      market_prob: 0.44,
      model_prob: 0.37,
      dislocation: 0.07,
      direction: 'market_overpriced',
      explanation: 'E',
      confidence: 3,
      scored_at: '2026-04-02T00:00:00Z',
    },
  ],
  scored_at: '2026-04-02T00:00:00Z',
  count: 5,
}

describe('Screener page', () => {
  it('sorts, filters, and opens drawer', async () => {
    server.use(
      http.get('/api/v1/screener', () => HttpResponse.json(screenerPayload)),
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
          updated_at: '2026-04-02T00:00:00Z',
        })
      )
    )

    const { container } = render(<ScreenerPage />)

    await screen.findByTestId('screener-table')
    await screen.findByTestId('screener-row-pm-fed-cut-june-2026')

    const beforeSort = container.querySelector('[data-testid^="screener-row-"]')?.getAttribute('data-testid')

    fireEvent.click(screen.getByTestId('sort-confidence'))

    await waitFor(() => {
      const afterSort = container.querySelector('[data-testid^="screener-row-"]')?.getAttribute('data-testid')
      expect(afterSort).not.toBe(beforeSort)
    })

    fireEvent.change(screen.getByTestId('filter-platform'), { target: { value: 'kalshi' } })

    await waitFor(() => {
      expect(container.querySelector('[data-testid="screener-row-pm-fed-cut-june-2026"]')).toBeNull()
      expect(container.querySelector('[data-testid="screener-row-KXFEDCUT-H1-2026"]')).toBeTruthy()
    })

    const firstKalshiRow = container.querySelector('[data-testid^="screener-row-KX"]') as HTMLElement
    fireEvent.click(firstKalshiRow)

    const rowTestId = firstKalshiRow.getAttribute('data-testid') ?? ''
    const id = rowTestId.replace('screener-row-', '')

    expect(await screen.findByTestId(`screener-drawer-${id}`)).toBeInTheDocument()
    expect(screen.getByTestId('screener-drawer-explanation')).toHaveTextContent('B')
  })
})
