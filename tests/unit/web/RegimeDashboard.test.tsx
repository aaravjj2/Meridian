import React from 'react'
import { render, screen } from '@testing-library/react'
import { HttpResponse, http } from 'msw'

import RegimeDashboard from '@/components/RegimeDashboard/RegimeDashboard'
import { server } from './setup'


describe('RegimeDashboard', () => {
  it('renders all five dimensions with status dots', async () => {
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
          updated_at: '2026-04-02T00:00:00Z',
        })
      )
    )

    render(<RegimeDashboard />)

    expect(await screen.findByTestId('regime-growth')).toBeInTheDocument()
    expect(screen.getByTestId('regime-inflation')).toBeInTheDocument()
    expect(screen.getByTestId('regime-monetary')).toBeInTheDocument()
    expect(screen.getByTestId('regime-credit')).toBeInTheDocument()
    expect(screen.getByTestId('regime-labor')).toBeInTheDocument()

    expect(screen.getByTestId('regime-growth-dot')).toHaveClass('dot-green')
    expect(screen.getByTestId('regime-inflation-dot')).toHaveClass('dot-amber')
  })
})
