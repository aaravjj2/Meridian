'use client'

import type { ScreenerContract } from './types'

type ScreenerTableProps = {
  contracts: ScreenerContract[]
  onSelect: (contract: ScreenerContract) => void
}

function stars(confidence: number): string {
  const value = Math.max(1, Math.min(5, confidence))
  return '★'.repeat(value) + '☆'.repeat(5 - value)
}

export default function ScreenerTable({ contracts, onSelect }: ScreenerTableProps) {
  return (
    <table className="screener-table" data-testid="screener-table">
      <thead>
        <tr>
          <th scope="col">Rank</th>
          <th scope="col">Contract</th>
          <th scope="col">Platform</th>
          <th scope="col">Category</th>
          <th scope="col">Market %</th>
          <th scope="col">Model %</th>
          <th scope="col">Gap</th>
          <th scope="col">Confidence</th>
          <th scope="col">Resolution</th>
          <th scope="col">Updated</th>
        </tr>
      </thead>
      <tbody>
        {contracts.map((item, index) => {
          const marketPct = Math.round(item.market_prob * 100)
          const modelPct = Math.round(item.model_prob * 100)
          const gap = Math.round((item.model_prob - item.market_prob) * 100)
          const gapClass = gap >= 0 ? 'gap-up' : 'gap-down'
          const arrow = gap >= 0 ? '↑' : '↓'

          return (
            <tr
              key={item.market_id}
              data-testid={`screener-row-${item.market_id}`}
              onClick={() => onSelect(item)}
              className="screener-row"
              tabIndex={0}
              onKeyDown={(event) => {
                if (event.key === 'Enter') onSelect(item)
              }}
            >
              <td data-testid={`screener-rank-${item.market_id}`}>{index + 1}</td>
              <td>{item.title}</td>
              <td>
                <span className={item.platform === 'kalshi' ? 'platform-kalshi' : 'platform-polymarket'}>
                  {item.platform}
                </span>
              </td>
              <td>{item.category}</td>
              <td>{marketPct}%</td>
              <td>{modelPct}%</td>
              <td className={gapClass} data-testid={`screener-dislocation-${item.market_id}`}>
                {arrow} {Math.abs(gap)}pp
              </td>
              <td>{stars(item.confidence)}</td>
              <td>{item.resolution_date}</td>
              <td>{new Date(item.scored_at).toLocaleDateString()}</td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
