'use client'

import { useEffect, useMemo, useState } from 'react'

type RegimeDimensions = {
  growth: string
  inflation: string
  monetary: string
  credit: string
  labor: string
}

type RegimePayload = {
  dimensions: RegimeDimensions
  narrative: string
  updated_at: string
}

const DEFAULT_REGIME: RegimePayload = {
  dimensions: {
    growth: 'EXPANSION',
    inflation: 'ELEVATED',
    monetary: 'RESTRICTIVE',
    credit: 'CAUTION',
    labor: 'TIGHT',
  },
  narrative: 'Fallback demo regime loaded locally.',
  updated_at: '2026-04-02T00:00:00Z',
}

function statusClass(value: string): string {
  const v = value.toUpperCase()
  if (v.includes('EXPANSION') || v.includes('TIGHT') || v.includes('HEALTHY')) return 'dot-green'
  if (v.includes('CAUTION') || v.includes('ELEVATED') || v.includes('RESTRICTIVE') || v.includes('NEUTRAL')) {
    return 'dot-amber'
  }
  if (v.includes('STRESS') || v.includes('SOFTENING') || v.includes('WEAK')) return 'dot-red'
  return 'dot-amber'
}

export default function RegimeDashboard() {
  const [regime, setRegime] = useState<RegimePayload>(DEFAULT_REGIME)
  const [state, setState] = useState<'loading' | 'error' | 'complete'>('loading')

  useEffect(() => {
    let active = true

    async function loadRegime() {
      try {
        const response = await fetch('/api/v1/regime')
        if (!response.ok) {
          throw new Error('Regime request failed')
        }
        const payload = (await response.json()) as RegimePayload
        if (!active) return
        setRegime(payload)
        setState('complete')
      } catch {
        if (!active) return
        setRegime(DEFAULT_REGIME)
        setState('error')
      }
    }

    loadRegime()
    return () => {
      active = false
    }
  }, [])

  const items = useMemo(
    () => [
      { dim: 'growth', label: 'GROWTH', value: regime.dimensions.growth, testId: 'regime-growth' },
      { dim: 'inflation', label: 'INFLATION', value: regime.dimensions.inflation, testId: 'regime-inflation' },
      { dim: 'monetary', label: 'MONETARY', value: regime.dimensions.monetary, testId: 'regime-monetary' },
      { dim: 'credit', label: 'CREDIT', value: regime.dimensions.credit, testId: 'regime-credit' },
      { dim: 'labor', label: 'LABOR', value: regime.dimensions.labor, testId: 'regime-labor' },
    ],
    [regime]
  )

  return (
    <section className="regime-strip" data-testid="regime-strip" aria-live="polite">
      {items.map((item, index) => (
        <div className="regime-pill" key={item.dim} data-testid={item.testId}>
          <span className="regime-label">{item.label}</span>
          <span className="regime-value" data-testid={`regime-${item.dim}-value`}>
            {item.value}
          </span>
          <span
            className={`regime-dot ${statusClass(item.value)}`}
            data-testid={`regime-${item.dim}-dot`}
            aria-label={`${item.label} status`}
          />
          {index < items.length - 1 ? <span className="regime-separator">|</span> : null}
        </div>
      ))}
      {state === 'loading' ? <span className="regime-meta">Loading...</span> : null}
      {state === 'error' ? <span className="regime-meta">Fallback data</span> : null}
    </section>
  )
}
