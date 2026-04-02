'use client'

import { useMemo, useState } from 'react'

import SeriesChart from '../Charts/SeriesChart'
import type { ResearchBrief } from './types'

type ResearchPanelProps = {
  status: 'empty' | 'loading' | 'error' | 'complete'
  brief: ResearchBrief | null
  errorMessage: string
}

function sourceBadgeClass(type: string): string {
  if (type === 'fred') return 'source-badge source-badge-fred'
  if (type === 'edgar') return 'source-badge source-badge-edgar'
  if (type === 'news') return 'source-badge source-badge-news'
  return 'source-badge source-badge-market'
}

const SAMPLE_SERIES = [
  { date: '2025-11-01', value: -0.38 },
  { date: '2025-12-01', value: -0.35 },
  { date: '2026-01-01', value: -0.29 },
  { date: '2026-02-01', value: -0.21 },
]

export default function ResearchPanel({ status, brief, errorMessage }: ResearchPanelProps) {
  const [expandedSource, setExpandedSource] = useState<string | null>(null)

  const confidenceSegments = useMemo(() => {
    const value = brief?.confidence ?? 0
    return Array.from({ length: 5 }).map((_, idx) => idx < value)
  }, [brief])

  if (status === 'empty') {
    return (
      <div className="brief-state brief-empty" data-testid="brief-empty">
        <div className="cursor">▋</div>
        <p>Ask a question to begin research.</p>
        <p className="brief-sub">GLM-5.1 will fetch live macro data and synthesize a brief.</p>
      </div>
    )
  }

  if (status === 'loading') {
    return (
      <div className="brief-state" data-testid="brief-loading" role="status" aria-live="polite">
        <div className="skeleton skeleton-line" />
        <div className="skeleton skeleton-line short" />
        <div className="skeleton skeleton-line short2" />
        <div className="skeleton skeleton-line" />
        <div className="skeleton skeleton-line short" />
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="brief-state brief-error" data-testid="brief-error">
        <p>{errorMessage || 'Research request failed.'}</p>
        <button type="button" className="retry-btn">
          Retry
        </button>
      </div>
    )
  }

  if (!brief) {
    return null
  }

  return (
    <div className="brief-complete" data-testid="brief-complete">
      <section className="thesis-block" data-testid="thesis-summary">
        <span className="block-label">THESIS</span>
        <p>{brief.thesis}</p>
      </section>

      <section className="brief-section" data-testid="bull-case">
        <span className="block-label bull">BULL CASE</span>
        {brief.bull_case.map((item, idx) => (
          <p key={item.source_ref} data-testid={`bull-case-item-${idx}`}>
            <span className="point-symbol bull-symbol">▸</span>
            {item.point}
            <span className="source-pill">[{item.source_ref}]</span>
          </p>
        ))}
      </section>

      <section className="brief-section" data-testid="bear-case">
        <span className="block-label bear">BEAR CASE</span>
        {brief.bear_case.map((item, idx) => (
          <p key={item.source_ref} data-testid={`bear-case-item-${idx}`}>
            <span className="point-symbol bear-symbol">▸</span>
            {item.point}
            <span className="source-pill">[{item.source_ref}]</span>
          </p>
        ))}
      </section>

      <section className="brief-section" data-testid="key-risks">
        <span className="block-label risk">KEY RISKS</span>
        {brief.key_risks.map((item, idx) => (
          <p key={item.source_ref} data-testid={`key-risks-item-${idx}`}>
            <span className="point-symbol risk-symbol">⚠</span>
            {item.risk}
            <span className="source-pill">[{item.source_ref}]</span>
          </p>
        ))}
      </section>

      <section className="brief-section" data-testid="confidence-meter">
        <span className="block-label">CONFIDENCE</span>
        <div className="confidence-row">
          <div className="confidence-segments">
            {confidenceSegments.map((filled, idx) => (
              <span key={idx} className={filled ? 'conf-segment conf-filled' : 'conf-segment'} />
            ))}
          </div>
          <span>{brief.confidence} / 5</span>
        </div>
      </section>

      <section className="brief-section" data-testid="source-list">
        <span className="block-label">SOURCES</span>
        {brief.sources.map((source, idx) => {
          const expanded = expandedSource === source.id
          return (
            <div key={`${source.type}-${source.id}`}>
              <button
                type="button"
                className="source-row"
                data-testid={`source-item-${idx}`}
                onClick={() => setExpandedSource(expanded ? null : source.id)}
              >
                <span className={sourceBadgeClass(source.type)}>{source.type.toUpperCase()}</span>
                <span className="source-id">{source.id}</span>
                <span className="source-excerpt">{source.excerpt}</span>
              </button>
              {expanded && source.type === 'fred' ? <SeriesChart id={source.id} data={SAMPLE_SERIES} /> : null}
            </div>
          )
        })}
      </section>
    </div>
  )
}
