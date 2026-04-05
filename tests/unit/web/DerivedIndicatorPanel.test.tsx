import { render, screen } from '@testing-library/react'

import DerivedIndicatorPanel from '@/components/Terminal/DerivedIndicatorPanel'
import type { DerivedIndicator } from '@/components/Terminal/types'

describe('DerivedIndicatorPanel', () => {
  const mockIndicators: DerivedIndicator[] = [
    {
      indicator_id: 'ind-roc-fred-test123',
      title: 'FRED Rate of Change',
      value: 5.2,
      unit: '%',
      display_hint: 'percentage_change_from_previous_period',
      computation_kind: 'rate_of_change',
      source_refs: ['fred:test123'],
      snapshot_id: 'snap-test123',
      snapshot_kind: 'fixture',
      computation_timestamp: '2026-04-05T00:00:00Z',
      observed_at: '2026-04-05T00:00:00Z',
      deterministic: true,
      reasoning: 'Rate of change computed from 2.50 to 2.63 over most recent period (significant movement)',
      deterministic_signature: 'test-sig-123',
    },
    {
      indicator_id: 'ind-spread-claims-abc',
      title: 'Claim Spread Indicator',
      value: 0.33,
      unit: 'ratio',
      display_hint: 'absolute_difference_normalized_by_total_claims',
      computation_kind: 'spread',
      source_refs: ['news:source1', 'news:source2'],
      snapshot_id: null,
      snapshot_kind: 'derived',
      computation_timestamp: '2026-04-05T00:00:00Z',
      observed_at: null,
      deterministic: true,
      reasoning: 'Claim spread: 4 bull vs 2 bear (spread of 2) (moderate imbalance)',
      deterministic_signature: 'test-sig-456',
    },
    {
      indicator_id: 'ind-freshness-aggregate-def',
      title: 'Aggregate Data Freshness',
      value: 0.5,
      unit: 'index',
      display_hint: '0=fresh, 1=aging, 2=stale',
      computation_kind: 'aggregate_freshness',
      source_refs: ['fred:GDP', 'market:BTC-USD'],
      snapshot_id: null,
      snapshot_kind: 'derived',
      computation_timestamp: '2026-04-05T00:00:00:00Z',
      observed_at: null,
      deterministic: true,
      reasoning: 'Aggregate freshness: 1 fresh, 1 aging, 0 stale out of 2 sources (good data freshness)',
      deterministic_signature: 'test-sig-789',
    },
  ]

  it('renders indicators correctly', () => {
    render(<DerivedIndicatorPanel indicators={mockIndicators} />)

    expect(screen.getByTestId('derived-indicator-panel')).toBeInTheDocument()
    expect(screen.getByTestId('derived-indicators-title')).toBeInTheDocument()
    expect(screen.getByTestId('derived-indicators-title')).toHaveTextContent('Derived Indicators')

    expect(screen.getByTestId('derived-indicator-ind-roc-fred-test123')).toBeInTheDocument()
    expect(screen.getByTestId(`derived-indicator-ind-roc-fred-test123-value`)).toBeInTheDocument()
    expect(screen.getByTestId(`derived-indicator-ind-roc-fred-test123-value`)).toHaveTextContent(/5\.2%/)

    expect(screen.getByTestId('derived-indicator-ind-spread-claims-abc')).toBeInTheDocument()
    expect(screen.getByTestId(`derived-indicator-ind-spread-claims-abc-title`)).toHaveTextContent('Claim Spread Indicator')
  })

  it('renders indicator details correctly', () => {
    render(<DerivedIndicatorPanel indicators={mockIndicators} />)

    const rocIndicator = screen.getByTestId('derived-indicator-ind-roc-fred-test123')
    expect(rocIndicator).toBeInTheDocument()

    expect(screen.getByTestId(`derived-indicator-ind-roc-fred-test123-reasoning`)).toBeInTheDocument()
    expect(screen.getByTestId(`derived-indicator-ind-roc-fred-test123-sources`)).toBeInTheDocument()
    expect(screen.getByTestId(`derived-indicator-ind-roc-fred-test123-snapshot-kind`)).toBeInTheDocument()
    expect(screen.getByTestId(`derived-indicator-ind-roc-fred-test123-snapshot-kind`)).toHaveTextContent('fixture')
  })

  it('returns null when no indicators', () => {
    const { container } = render(<DerivedIndicatorPanel indicators={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('returns null when indicators is undefined', () => {
    const { container } = render(<DerivedIndicatorPanel indicators={undefined as unknown as typeof mockIndicators} />)
    expect(container.firstChild).toBeNull()
  })

  it('displays correct number of indicators', () => {
    render(<DerivedIndicatorPanel indicators={mockIndicators} />)

    expect(screen.getByTestId('derived-indicator-panel')).toBeInTheDocument()
    expect(screen.getByTestId('derived-indicator-ind-roc-fred-test123')).toBeInTheDocument()
    expect(screen.getByTestId('derived-indicator-ind-spread-claims-abc')).toBeInTheDocument()
    expect(screen.getByTestId('derived-indicator-ind-freshness-aggregate-def')).toBeInTheDocument()
  })

  it('colors values correctly based on computation kind', () => {
    render(<DerivedIndicatorPanel indicators={mockIndicators} />)

    const rocValue = screen.getByTestId(`derived-indicator-ind-roc-fred-test123-value`)
    expect(rocValue).toHaveClass('text-green-600')

    const freshnessValue = screen.getByTestId(`derived-indicator-ind-freshness-aggregate-def-value`)
    expect(freshnessValue).toHaveClass('text-green-600')
  })
})
