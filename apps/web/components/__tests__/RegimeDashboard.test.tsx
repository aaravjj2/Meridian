import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import RegimeDashboard from '../RegimeDashboard/RegimeDashboard'

describe('RegimeDashboard', () => {
  let mockFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    // Stub fetch globally for happy-dom
    mockFetch = vi.fn()
    vi.stubGlobal('fetch', mockFetch)

    // Default successful response
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        dimensions: {
          growth: 'EXPANSION',
          inflation: 'ELEVATED',
          monetary: 'RESTRICTIVE',
          credit: 'CAUTION',
          labor: 'TIGHT',
        },
        narrative: 'Test narrative',
        updated_at: '2025-04-01T00:00:00Z',
      }),
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('renders in loading state initially', () => {
    render(<RegimeDashboard />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders all 5 regime dimensions', async () => {
    render(<RegimeDashboard />)

    await waitFor(
      () => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
      },
      { timeout: 5000 }
    )

    expect(screen.getByTestId('regime-growth')).toBeInTheDocument()
    expect(screen.getByTestId('regime-inflation')).toBeInTheDocument()
    expect(screen.getByTestId('regime-monetary')).toBeInTheDocument()
    expect(screen.getByTestId('regime-credit')).toBeInTheDocument()
    expect(screen.getByTestId('regime-labor')).toBeInTheDocument()
  })

  it('displays correct regime values', async () => {
    render(<RegimeDashboard />)

    await waitFor(
      () => {
        expect(screen.getByTestId('regime-growth-value')).toHaveTextContent('EXPANSION')
        expect(screen.getByTestId('regime-inflation-value')).toHaveTextContent('ELEVATED')
        expect(screen.getByTestId('regime-monetary-value')).toHaveTextContent('RESTRICTIVE')
        expect(screen.getByTestId('regime-credit-value')).toHaveTextContent('CAUTION')
        expect(screen.getByTestId('regime-labor-value')).toHaveTextContent('TIGHT')
      },
      { timeout: 5000 }
    )
  })

  it('applies correct status dot classes', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        dimensions: {
          growth: 'EXPANSION', // green
          inflation: 'ELEVATED', // amber
          monetary: 'RESTRICTIVE', // amber
          credit: 'STRESS', // red
          labor: 'TIGHT', // green
        },
        narrative: 'Test narrative',
        updated_at: '2025-04-01T00:00:00Z',
      }),
    })

    render(<RegimeDashboard />)

    await waitFor(
      () => {
        expect(screen.getByTestId('regime-growth-dot')).toHaveClass('dot-green')
        expect(screen.getByTestId('regime-inflation-dot')).toHaveClass('dot-amber')
        expect(screen.getByTestId('regime-monetary-dot')).toHaveClass('dot-amber')
        expect(screen.getByTestId('regime-credit-dot')).toHaveClass('dot-red')
        expect(screen.getByTestId('regime-labor-dot')).toHaveClass('dot-green')
      },
      { timeout: 5000 }
    )
  })

  it('fetches regime data from correct endpoint', () => {
    render(<RegimeDashboard />)
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/regime')
  })

  it('handles fetch error gracefully', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'))

    render(<RegimeDashboard />)

    await waitFor(
      () => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
      },
      { timeout: 5000 }
    )

    expect(screen.getByText('Fallback data')).toBeInTheDocument()

    // Should show default regime
    expect(screen.getByTestId('regime-growth-value')).toHaveTextContent('EXPANSION')
  })

  it('uses default regime when API returns non-ok response', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      json: async () => ({}),
    })

    render(<RegimeDashboard />)

    await waitFor(
      () => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
      },
      { timeout: 5000 }
    )

    expect(screen.getByText('Fallback data')).toBeInTheDocument()
  })

  it('renders separators between dimensions', async () => {
    render(<RegimeDashboard />)

    await waitFor(
      () => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
      },
      { timeout: 5000 }
    )

    // Should have 4 separators for 5 items
    const separators = screen.getAllByText('|')
    expect(separators).toHaveLength(4)
  })

  it('has correct accessibility attributes', async () => {
    render(<RegimeDashboard />)

    await waitFor(
      () => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
      },
      { timeout: 5000 }
    )

    const regimeStrip = screen.getByTestId('regime-strip')
    expect(regimeStrip).toHaveAttribute('aria-live', 'polite')

    const dots = screen.getAllByTestId(/-dot$/)
    dots.forEach(dot => {
      expect(dot).toHaveAttribute('aria-label')
    })
  })
})
