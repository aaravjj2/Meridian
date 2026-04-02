'use client'

import { useEffect, useMemo, useState } from 'react'

import RegimeDashboard from '@/components/RegimeDashboard/RegimeDashboard'
import ScreenerDrawer from '@/components/Screener/ScreenerDrawer'
import ScreenerTable from '@/components/Screener/ScreenerTable'
import type { ScreenerContract } from '@/components/Screener/types'

type ScreenerResponse = {
  contracts: ScreenerContract[]
  scored_at: string
  count: number
}

const FALLBACK_CONTRACTS: ScreenerContract[] = [
  {
    market_id: 'pm-fed-cut-june-2026',
    platform: 'polymarket',
    category: 'fed_policy',
    title: 'Fed cuts rates by at least 50bps before July 2026',
    resolution_date: '2026-06-30',
    market_prob: 0.67,
    model_prob: 0.41,
    dislocation: 0.26,
    direction: 'market_overpriced',
    explanation: 'Model probability differs by 26.0pp from market-implied odds.',
    confidence: 4,
    scored_at: '2026-04-02T00:00:00Z',
  },
  {
    market_id: 'KXFEDCUT-H1-2026',
    platform: 'kalshi',
    category: 'fed_policy',
    title: 'Will the Fed cut rates by 50bps by June 2026?',
    resolution_date: '2026-06-30',
    market_prob: 0.64,
    model_prob: 0.45,
    dislocation: 0.19,
    direction: 'market_overpriced',
    explanation: 'Model probability differs by 19.0pp from market-implied odds.',
    confidence: 4,
    scored_at: '2026-04-02T00:00:00Z',
  },
  {
    market_id: 'pm-recession-2026',
    platform: 'polymarket',
    category: 'recession',
    title: 'US recession starts in 2026',
    resolution_date: '2026-12-31',
    market_prob: 0.33,
    model_prob: 0.48,
    dislocation: 0.15,
    direction: 'market_underpriced',
    explanation: 'Model probability differs by 15.0pp from market-implied odds.',
    confidence: 3,
    scored_at: '2026-04-02T00:00:00Z',
  },
  {
    market_id: 'KXREC-2026',
    platform: 'kalshi',
    category: 'recession',
    title: 'Will the NBER declare recession starting in 2026?',
    resolution_date: '2026-12-31',
    market_prob: 0.29,
    model_prob: 0.43,
    dislocation: 0.14,
    direction: 'market_underpriced',
    explanation: 'Model probability differs by 14.0pp from market-implied odds.',
    confidence: 3,
    scored_at: '2026-04-02T00:00:00Z',
  },
  {
    market_id: 'pm-cpi-over-3-q2-2026',
    platform: 'polymarket',
    category: 'inflation',
    title: 'CPI YoY above 3% in Q2 2026',
    resolution_date: '2026-07-15',
    market_prob: 0.44,
    model_prob: 0.37,
    dislocation: 0.07,
    direction: 'market_overpriced',
    explanation: 'Model probability differs by 7.0pp from market-implied odds.',
    confidence: 2,
    scored_at: '2026-04-02T00:00:00Z',
  },
]

export default function ScreenerPage() {
  const [contracts, setContracts] = useState<ScreenerContract[]>([])
  const [status, setStatus] = useState<'loading' | 'error' | 'complete'>('loading')
  const [sortBy, setSortBy] = useState<'dislocation' | 'confidence' | 'resolution'>('dislocation')
  const [platform, setPlatform] = useState<'all' | 'kalshi' | 'polymarket'>('all')
  const [category, setCategory] = useState<string>('all')
  const [minDislocation, setMinDislocation] = useState(0)
  const [selected, setSelected] = useState<ScreenerContract | null>(null)

  useEffect(() => {
    let active = true

    async function load() {
      try {
        const response = await fetch('/api/v1/screener')
        if (!response.ok) {
          throw new Error('Screener fetch failed')
        }
        const payload = (await response.json()) as ScreenerResponse
        if (!active) return
        setContracts(payload.contracts)
        setStatus('complete')
      } catch {
        if (!active) return
        setContracts(FALLBACK_CONTRACTS)
        setStatus('error')
      }
    }

    load()
    return () => {
      active = false
    }
  }, [])

  const categories = useMemo(() => {
    const values = new Set<string>()
    contracts.forEach((item) => values.add(item.category))
    return ['all', ...Array.from(values)]
  }, [contracts])

  const filtered = useMemo(() => {
    let rows = [...contracts]

    if (platform !== 'all') {
      rows = rows.filter((item) => item.platform === platform)
    }
    if (category !== 'all') {
      rows = rows.filter((item) => item.category === category)
    }
    rows = rows.filter((item) => item.dislocation >= minDislocation / 100)

    if (sortBy === 'dislocation') {
      rows.sort((a, b) => b.dislocation - a.dislocation)
    }
    if (sortBy === 'confidence') {
      rows.sort((a, b) => b.confidence - a.confidence || a.dislocation - b.dislocation)
    }
    if (sortBy === 'resolution') {
      rows.sort((a, b) => a.resolution_date.localeCompare(b.resolution_date))
    }

    return rows
  }, [contracts, sortBy, platform, category, minDislocation])

  return (
    <main className="screener-page" data-testid="screener-page">
      <RegimeDashboard />

      <section className="screener-header-row">
        <div>
          <h1>MISPRICING SCREENER</h1>
          <p>Kalshi × Polymarket × FRED</p>
        </div>
        <p>{filtered.length} contracts</p>
      </section>

      <section className="screener-filters">
        <button type="button" data-testid="sort-dislocation" onClick={() => setSortBy('dislocation')}>
          Sort Dislocation
        </button>
        <button type="button" data-testid="sort-confidence" onClick={() => setSortBy('confidence')}>
          Sort Confidence
        </button>
        <button type="button" data-testid="sort-resolution" onClick={() => setSortBy('resolution')}>
          Sort Resolution
        </button>

        <select
          data-testid="filter-platform"
          value={platform}
          onChange={(event) => setPlatform(event.target.value as 'all' | 'kalshi' | 'polymarket')}
        >
          <option value="all">All Platforms</option>
          <option value="kalshi">Kalshi</option>
          <option value="polymarket">Polymarket</option>
        </select>

        <select data-testid="filter-category" value={category} onChange={(event) => setCategory(event.target.value)}>
          {categories.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>

        <input
          data-testid="filter-min-dislocation"
          type="range"
          min={0}
          max={40}
          value={minDislocation}
          onChange={(event) => setMinDislocation(Number(event.target.value))}
        />
      </section>

      {status === 'loading' ? <div className="panel-message">Loading screener...</div> : null}
      {status === 'error' ? <div className="panel-message">Showing fallback snapshot.</div> : null}

      <ScreenerTable contracts={filtered} onSelect={setSelected} />
      <ScreenerDrawer contract={selected} onClose={() => setSelected(null)} />
    </main>
  )
}
