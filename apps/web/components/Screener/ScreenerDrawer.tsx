'use client'

import SeriesChart from '../Charts/SeriesChart'
import type { ScreenerContract } from './types'

type ScreenerDrawerProps = {
  contract: ScreenerContract | null
  onClose: () => void
}

const SAMPLE_SERIES = [
  { date: '2025-11-01', value: -0.38 },
  { date: '2025-12-01', value: -0.35 },
  { date: '2026-01-01', value: -0.29 },
  { date: '2026-02-01', value: -0.21 },
]

export default function ScreenerDrawer({ contract, onClose }: ScreenerDrawerProps) {
  if (!contract) return null

  const gap = Math.round((contract.model_prob - contract.market_prob) * 100)
  const gapLabel = `${gap > 0 ? '+' : ''}${gap}pp`
  const stance = gap >= 0 ? 'UNDERPRICED' : 'OVERPRICED'

  return (
    <aside className="screener-drawer" data-testid={`screener-drawer-${contract.market_id}`}>
      <button type="button" className="drawer-close" aria-label="Close drawer" onClick={onClose}>
        ✕
      </button>

      <h3>{contract.title}</h3>
      <p>
        <span className="platform-pill">{contract.platform.toUpperCase()}</span>
        <span>{contract.resolution_date}</span>
      </p>

      <section className="drawer-prob-row">
        <div>
          <span className="block-label">MARKET</span>
          <strong>{Math.round(contract.market_prob * 100)}%</strong>
        </div>
        <div>
          <span className="block-label">MODEL</span>
          <strong>{Math.round(contract.model_prob * 100)}%</strong>
        </div>
      </section>

      <p className="drawer-gap">GAP {gapLabel} ({stance})</p>

      <section className="drawer-explanation" data-testid="screener-drawer-explanation">
        {contract.explanation}
      </section>

      <SeriesChart id={`${contract.market_id}-primary`} data={SAMPLE_SERIES} />
      <SeriesChart id={`${contract.market_id}-secondary`} data={SAMPLE_SERIES.map((p) => ({ ...p, value: p.value + 0.1 }))} />
    </aside>
  )
}
