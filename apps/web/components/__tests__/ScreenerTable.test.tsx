import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import ScreenerTable from '../Screener/ScreenerTable'
import type { ScreenerContract } from '../Screener/types'

const mockContracts: ScreenerContract[] = [
  {
    market_id: 'kalshi-1',
    title: 'Fed Rate Cut in June',
    platform: 'kalshi',
    category: 'Monetary Policy',
    market_prob: 0.25,
    model_prob: 0.45,
    dislocation: 0.20,
    direction: 'market_underpriced',
    explanation: 'Model suggests higher probability of rate cut',
    confidence: 4,
    resolution_date: '2025-06-30',
    scored_at: '2025-04-01T12:00:00Z',
  },
  {
    market_id: 'poly-1',
    title: 'Recession in 2025',
    platform: 'polymarket',
    category: 'Macroeconomics',
    market_prob: 0.35,
    model_prob: 0.55,
    dislocation: 0.20,
    direction: 'market_underpriced',
    explanation: 'Model indicates higher recession risk',
    confidence: 3,
    resolution_date: '2025-12-31',
    scored_at: '2025-04-01T12:00:00Z',
  },
]

describe('ScreenerTable', () => {
  it('renders table with headers', () => {
    render(<ScreenerTable contracts={mockContracts} onSelect={vi.fn()} />)

    expect(screen.getByRole('columnheader', { name: 'Rank' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Contract' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Platform' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Category' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Market %' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Model %' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Gap' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Confidence' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Resolution' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Updated' })).toBeInTheDocument()
  })

  it('renders all contract rows', () => {
    render(<ScreenerTable contracts={mockContracts} onSelect={vi.fn()} />)

    expect(screen.getByText('Fed Rate Cut in June')).toBeInTheDocument()
    expect(screen.getByText('Recession in 2025')).toBeInTheDocument()
  })

  it('renders correct platform styling', () => {
    render(<ScreenerTable contracts={mockContracts} onSelect={vi.fn()} />)

    const kalshiPlatform = screen.getByText('kalshi')
    expect(kalshiPlatform).toHaveClass('platform-kalshi')

    const polymarketPlatform = screen.getByText('polymarket')
    expect(polymarketPlatform).toHaveClass('platform-polymarket')
  })

  it('calculates and displays percentages correctly', () => {
    render(<ScreenerTable contracts={mockContracts} onSelect={vi.fn()} />)

    // First contract: 25% market, 45% model
    expect(screen.getByText('25%')).toBeInTheDocument()
    expect(screen.getByText('45%')).toBeInTheDocument()
  })

  it('calculates and displays gap with correct direction', () => {
    render(<ScreenerTable contracts={mockContracts} onSelect={vi.fn()} />)

    // First contract: 45 - 25 = +20pp (up arrow)
    const gapCell = screen.getByTestId('screener-dislocation-kalshi-1')
    expect(gapCell.textContent).toContain('↑')
    expect(gapCell.textContent).toContain('20pp')
  })

  it('displays confidence as stars', () => {
    render(<ScreenerTable contracts={mockContracts} onSelect={vi.fn()} />)

    // Confidence 4 should show 4 stars, 1 empty star
    const rows = screen.getAllByTestId(/^screener-row-/)
    const firstRow = rows[0]

    // Check for star characters
    expect(within(firstRow as HTMLElement).getByText(/★+/)).toBeInTheDocument()
  })

  it('displays ranking correctly', () => {
    render(<ScreenerTable contracts={mockContracts} onSelect={vi.fn()} />)

    expect(screen.getByTestId('screener-rank-kalshi-1')).toHaveTextContent('1')
    expect(screen.getByTestId('screener-rank-poly-1')).toHaveTextContent('2')
  })

  it('calls onSelect when row is clicked', async () => {
    const onSelect = vi.fn()
    render(<ScreenerTable contracts={mockContracts} onSelect={onSelect} />)

    const firstRow = screen.getByTestId('screener-row-kalshi-1')
    firstRow.click()

    expect(onSelect).toHaveBeenCalledWith(mockContracts[0])
  })

  it('displays confidence as stars with correct number', () => {
    render(<ScreenerTable contracts={mockContracts} onSelect={vi.fn()} />)

    // Confidence 4 should show 4 stars, 1 empty star
    const rows = screen.getAllByTestId(/^screener-row-/)
    const firstRow = rows[0] as HTMLElement
    const starsContent = firstRow.textContent || ''
    const starCount = (starsContent.match(/★/g) || []).length
    expect(starCount).toBeGreaterThanOrEqual(4)
  })

  it('renders empty table when no contracts', () => {
    render(<ScreenerTable contracts={[]} onSelect={vi.fn()} />)

    const table = screen.getByTestId('screener-table')
    const tbody = table.querySelector('tbody')
    expect(tbody?.children).toHaveLength(0)
  })

  it('formats date correctly', () => {
    render(<ScreenerTable contracts={mockContracts} onSelect={vi.fn()} />)

    // Should show locale date string
    expect(screen.getByText(/2025-06-30/)).toBeInTheDocument()
  })

  it('applies correct gap class for positive gap', () => {
    render(<ScreenerTable contracts={mockContracts} onSelect={vi.fn()} />)

    const gapCell = screen.getByTestId('screener-dislocation-kalshi-1')
    expect(gapCell).toHaveClass('gap-up')
  })

  it('applies correct gap class for negative gap', () => {
    const contractsWithNegativeGap: ScreenerContract[] = [
      {
        ...mockContracts[0],
        market_prob: 0.45,
        model_prob: 0.25,
        dislocation: -0.20,
        direction: 'market_overpriced',
        explanation: 'Market overpriced relative to model',
      },
    ]
    render(<ScreenerTable contracts={contractsWithNegativeGap} onSelect={vi.fn()} />)

    const gapCell = screen.getByTestId('screener-dislocation-kalshi-1')
    expect(gapCell).toHaveClass('gap-down')
    expect(gapCell.textContent).toContain('↓')
  })

  it('handles large gaps correctly', () => {
    const contractsWithLargeGap: ScreenerContract[] = [
      {
        ...mockContracts[0],
        market_prob: 0.01,
        model_prob: 0.99,
        dislocation: 0.98,
        direction: 'market_underpriced',
        explanation: 'Very large gap - model much more confident',
      },
    ]
    render(<ScreenerTable contracts={contractsWithLargeGap} onSelect={vi.fn()} />)

    const gapCell = screen.getByTestId('screener-dislocation-kalshi-1')
    expect(gapCell.textContent).toContain('98pp')
  })
})
