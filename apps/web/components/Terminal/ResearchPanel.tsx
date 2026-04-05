'use client'

import { useEffect, useMemo, useState } from 'react'

import SeriesChart from '../Charts/SeriesChart'
import type {
  EvidenceNavigationState,
  ResearchBrief,
  ResearchEvaluationReport,
  SourceItem,
} from './types'

type ResearchPanelProps = {
  status: 'empty' | 'loading' | 'error' | 'complete'
  brief: ResearchBrief | null
  evaluation?: ResearchEvaluationReport | null
  errorMessage: string
  initialEvidenceState?: EvidenceNavigationState | null
  evidenceHydrationKey?: number
  onEvidenceStateChange?: (state: EvidenceNavigationState) => void
}

function sourceBadgeClass(type: string): string {
  if (type === 'fred') return 'source-badge source-badge-fred'
  if (type === 'edgar') return 'source-badge source-badge-edgar'
  if (type === 'news') return 'source-badge source-badge-news'
  return 'source-badge source-badge-market'
}

function freshnessBadgeClass(freshness: string): string {
  if (freshness === 'fresh') return 'freshness-badge freshness-badge-fresh'
  if (freshness === 'aging') return 'freshness-badge freshness-badge-aging'
  if (freshness === 'stale') return 'freshness-badge freshness-badge-stale'
  return 'freshness-badge freshness-badge-unknown'
}

function snapshotKindBadgeClass(snapshotKind: string): string {
  if (snapshotKind === 'fixture') return 'snapshot-badge snapshot-badge-fixture'
  if (snapshotKind === 'cache') return 'snapshot-badge snapshot-badge-cache'
  if (snapshotKind === 'live_capture') return 'snapshot-badge snapshot-badge-live'
  if (snapshotKind === 'derived') return 'snapshot-badge snapshot-badge-derived'
  return 'snapshot-badge snapshot-badge-unknown'
}

function stateLabelBadgeClass(stateLabel: string): string {
  if (stateLabel === 'fixture') return 'snapshot-badge snapshot-badge-fixture'
  if (stateLabel === 'cached') return 'snapshot-badge snapshot-badge-cache'
  if (stateLabel === 'live') return 'snapshot-badge snapshot-badge-live'
  if (stateLabel === 'derived') return 'snapshot-badge snapshot-badge-derived'
  return 'snapshot-badge snapshot-badge-unknown'
}

const SAMPLE_SERIES = [
  { date: '2025-11-01', value: -0.38 },
  { date: '2025-12-01', value: -0.35 },
  { date: '2026-01-01', value: -0.29 },
  { date: '2026-02-01', value: -0.21 },
]

function queryClassLabel(queryClass: ResearchBrief['query_class']): string {
  if (queryClass === 'event_probability') return 'EVENT PROBABILITY'
  if (queryClass === 'ticker_macro') return 'TICKER + MACRO'
  return 'MACRO OUTLOOK'
}

function formatPreviewValue(value: unknown): string {
  if (value === null || value === undefined) return 'n/a'
  if (typeof value === 'number') return Number.isInteger(value) ? String(value) : value.toFixed(4)
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return `${value.length} items`
  if (typeof value === 'object') return 'object'
  return String(value)
}

function extractSeriesPoints(source: SourceItem): Array<{ date: string; value: number }> {
  const maybePoints = source.preview?.points
  if (!Array.isArray(maybePoints)) return SAMPLE_SERIES

  const parsed = maybePoints
    .map((point) => {
      if (!point || typeof point !== 'object') return null
      const date = (point as { date?: unknown }).date
      const value = (point as { value?: unknown }).value
      if (typeof date !== 'string' || typeof value !== 'number') return null
      return { date, value }
    })
    .filter((item): item is { date: string; value: number } => item !== null)

  return parsed.length >= 2 ? parsed : SAMPLE_SERIES
}

function sourceKey(source: SourceItem): string {
  return `${source.type}:${source.id}`
}

function claimTestToken(claimId: string): string {
  return claimId.replace(/[^a-zA-Z0-9_-]+/g, '-')
}

type ClaimRecord = {
  claim_id: string
  text: string
  source_ref: string
  section: 'bull_case' | 'bear_case' | 'key_risks'
}

function SourcePreview({ source, idx }: { source: SourceItem; idx: number }) {
  const preview = source.preview ?? {}
  const entries = Object.entries(preview).filter(([key]) => key !== 'points')
  const provenance = source.provenance ?? null
  const snapshot = source.provenance?.snapshot ?? null
  const cacheLineage = source.provenance?.cache_lineage ?? 'unknown'
  const stateLabel = source.provenance?.state_label ?? 'unknown'

  const snapshotPanel = (
    <div className="source-snapshot" data-testid={`source-snapshot-${idx}`}>
      <div className="source-snapshot-row">
        <span className="source-preview-key">state label</span>
        <span className="source-preview-value" data-testid={`source-state-label-detail-${idx}`}>
          {stateLabel}
        </span>
      </div>
      <div className="source-snapshot-row">
        <span className="source-preview-key">snapshot kind</span>
        <span className="source-preview-value" data-testid={`source-snapshot-kind-${idx}`}>
          {snapshot?.snapshot_kind ?? 'unknown'}
        </span>
      </div>
      <div className="source-snapshot-row">
        <span className="source-preview-key">cache lineage</span>
        <span className="source-preview-value" data-testid={`source-cache-lineage-${idx}`}>
          {cacheLineage}
        </span>
      </div>
      <div className="source-snapshot-row">
        <span className="source-preview-key">snapshot id</span>
        <span className="source-preview-value" data-testid={`source-snapshot-id-${idx}`}>
          {snapshot?.snapshot_id ?? 'n/a'}
        </span>
      </div>
      <div className="source-snapshot-row">
        <span className="source-preview-key">dataset/version</span>
        <span className="source-preview-value" data-testid={`source-snapshot-dataset-${idx}`}>
          {snapshot?.dataset ?? 'n/a'} / {snapshot?.dataset_version ?? 'n/a'}
        </span>
      </div>
      <div className="source-snapshot-row">
        <span className="source-preview-key">checksum</span>
        <span className="source-preview-value" data-testid={`source-snapshot-checksum-${idx}`}>
          {snapshot?.checksum_sha256 ?? 'n/a'}
        </span>
      </div>
      <div className="source-snapshot-row">
        <span className="source-preview-key">generated at</span>
        <span className="source-preview-value" data-testid={`source-snapshot-generated-at-${idx}`}>
          {snapshot?.generated_at ?? 'n/a'}
        </span>
      </div>
      <div className="source-snapshot-row">
        <span className="source-preview-key">cached at</span>
        <span className="source-preview-value" data-testid={`source-snapshot-cached-at-${idx}`}>
          {snapshot?.cached_at ?? 'n/a'}
        </span>
      </div>
      <div className="source-snapshot-row">
        <span className="source-preview-key">fetched at</span>
        <span className="source-preview-value" data-testid={`source-snapshot-fetched-at-${idx}`}>
          {snapshot?.fetched_at ?? 'n/a'}
        </span>
      </div>
      <div className="source-snapshot-row">
        <span className="source-preview-key">observed/captured</span>
        <span className="source-preview-value" data-testid={`source-observed-captured-${idx}`}>
          {provenance?.observed_at ?? 'n/a'} / {provenance?.captured_at ?? 'n/a'}
        </span>
      </div>
    </div>
  )

  if (source.type === 'fred') {
    return (
      <div className="source-preview" data-testid={`source-preview-${idx}`}>
        {snapshotPanel}
        <div className="source-preview-grid">
          {entries.map(([key, value]) => (
            <div key={key} className="source-preview-kv">
              <span className="source-preview-key">{key}</span>
              <span className="source-preview-value">{formatPreviewValue(value)}</span>
            </div>
          ))}
        </div>
        <SeriesChart id={`${source.id}-${idx}`} data={extractSeriesPoints(source)} />
      </div>
    )
  }

  return (
    <div className="source-preview source-preview-generic" data-testid={`source-preview-${idx}`}>
      {snapshotPanel}
      {entries.length === 0 ? <p>No preview metadata available.</p> : null}
      {entries.map(([key, value]) => (
        <div key={key} className="source-preview-kv">
          <span className="source-preview-key">{key}</span>
          <span className="source-preview-value">{formatPreviewValue(value)}</span>
        </div>
      ))}
    </div>
  )
}

export default function ResearchPanel({
  status,
  brief,
  evaluation,
  errorMessage,
  initialEvidenceState,
  evidenceHydrationKey,
  onEvidenceStateChange,
}: ResearchPanelProps) {
  const [expandedSource, setExpandedSource] = useState<string | null>(null)
  const [activeClaimId, setActiveClaimId] = useState<string | null>(null)

  const confidenceSegments = useMemo(() => {
    const value = brief?.confidence ?? 0
    return Array.from({ length: 5 }).map((_, idx) => idx < value)
  }, [brief])

  const claimRecords = useMemo<ClaimRecord[]>(() => {
    if (!brief) return []

    const bullClaims = brief.bull_case.map((item) => ({
      claim_id: item.claim_id,
      text: item.point,
      source_ref: item.source_ref,
      section: 'bull_case' as const,
    }))
    const bearClaims = brief.bear_case.map((item) => ({
      claim_id: item.claim_id,
      text: item.point,
      source_ref: item.source_ref,
      section: 'bear_case' as const,
    }))
    const riskClaims = brief.key_risks.map((item) => ({
      claim_id: item.claim_id,
      text: item.risk,
      source_ref: item.source_ref,
      section: 'key_risks' as const,
    }))

    return [...bullClaims, ...bearClaims, ...riskClaims]
  }, [brief])

  const claimLookup = useMemo(() => {
    const lookup = new Map<string, ClaimRecord>()
    for (const claim of claimRecords) {
      lookup.set(claim.claim_id, claim)
    }
    return lookup
  }, [claimRecords])

  const claimToSourceKeys = useMemo(() => {
    const mapping = new Map<string, string[]>()
    if (!brief) return mapping

    for (const source of brief.sources) {
      const key = sourceKey(source)
      for (const claimRef of source.claim_refs ?? []) {
        const linked = mapping.get(claimRef) ?? []
        if (!linked.includes(key)) {
          linked.push(key)
          mapping.set(claimRef, linked)
        }
      }
    }

    return mapping
  }, [brief])

  const activeClaim = activeClaimId ? claimLookup.get(activeClaimId) ?? null : null
  const activeClaimSources = useMemo(() => {
    if (!brief || !activeClaimId) return [] as SourceItem[]
    const linkedSourceKeys = new Set(claimToSourceKeys.get(activeClaimId) ?? [])
    return brief.sources.filter((source) => linkedSourceKeys.has(sourceKey(source)))
  }, [brief, activeClaimId, claimToSourceKeys])

  useEffect(() => {
    setExpandedSource(initialEvidenceState?.expanded_source_id ?? null)
    setActiveClaimId(initialEvidenceState?.active_claim_id ?? null)
  }, [brief?.created_at, brief?.question, evidenceHydrationKey])

  useEffect(() => {
    onEvidenceStateChange?.({
      active_claim_id: activeClaimId,
      expanded_source_id: expandedSource,
    })
  }, [activeClaimId, expandedSource, onEvidenceStateChange])

  function focusClaim(claimId: string): void {
    setActiveClaimId(claimId)
    const linked = claimToSourceKeys.get(claimId)
    if (linked && linked.length > 0) {
      setExpandedSource(linked[0])
    }
  }

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

  const provenanceSummary =
    brief.provenance_summary && typeof brief.provenance_summary === 'object' ? brief.provenance_summary : null
  const freshnessCounts =
    provenanceSummary && typeof provenanceSummary.freshness_counts === 'object'
      ? (provenanceSummary.freshness_counts as Record<string, unknown>)
      : null
  const snapshotSummary =
    brief.snapshot_summary && typeof brief.snapshot_summary === 'object' ? brief.snapshot_summary : null
  const snapshotKindCounts =
    snapshotSummary && typeof snapshotSummary.snapshot_kind_counts === 'object'
      ? (snapshotSummary.snapshot_kind_counts as Record<string, unknown>)
      : null
  const cacheLineageCounts =
    snapshotSummary && typeof snapshotSummary.cache_lineage_counts === 'object'
      ? (snapshotSummary.cache_lineage_counts as Record<string, unknown>)
      : null
  const freshnessPolicyViolations =
    evaluation && Array.isArray(evaluation.metrics?.freshness_policy_violations)
      ? (evaluation.metrics.freshness_policy_violations as string[])
      : []

  return (
    <div className="brief-complete" data-testid="brief-complete">
      <section className="brief-meta" data-testid="brief-meta">
        <span className="block-label">QUERY CLASS</span>
        <p data-testid="brief-query-class">{queryClassLabel(brief.query_class)}</p>
        {brief.template_title ? (
          <p data-testid="brief-template-title">Template: {brief.template_title}</p>
        ) : null}
        <p className="brief-question" data-testid="brief-question">
          {brief.question}
        </p>
      </section>

      {brief.follow_up_context ? (
        <section className="brief-context" data-testid="brief-followup-context">
          <span className="block-label">FOLLOW-UP CONTEXT</span>
          <p>{brief.follow_up_context}</p>
        </section>
      ) : null}

      <section className="thesis-block" data-testid="thesis-summary">
        <span className="block-label">THESIS</span>
        <p>{brief.thesis}</p>
      </section>

      <section className="brief-section" data-testid="bull-case">
        <span className="block-label bull">BULL CASE</span>
        {brief.bull_case.map((item, idx) => (
          <button
            key={item.claim_id}
            type="button"
            className={activeClaimId === item.claim_id ? 'claim-row claim-row-active' : 'claim-row'}
            data-testid={`claim-link-${claimTestToken(item.claim_id)}`}
            onClick={() => focusClaim(item.claim_id)}
          >
            <span className="point-symbol bull-symbol">▸</span>
            <span className="claim-text" data-testid={`bull-case-item-${idx}`}>
              {item.point}
            </span>
            <span className="source-pill">[{item.source_ref}]</span>
          </button>
        ))}
      </section>

      <section className="brief-section" data-testid="bear-case">
        <span className="block-label bear">BEAR CASE</span>
        {brief.bear_case.map((item, idx) => (
          <button
            key={item.claim_id}
            type="button"
            className={activeClaimId === item.claim_id ? 'claim-row claim-row-active' : 'claim-row'}
            data-testid={`claim-link-${claimTestToken(item.claim_id)}`}
            onClick={() => focusClaim(item.claim_id)}
          >
            <span className="point-symbol bear-symbol">▸</span>
            <span className="claim-text" data-testid={`bear-case-item-${idx}`}>
              {item.point}
            </span>
            <span className="source-pill">[{item.source_ref}]</span>
          </button>
        ))}
      </section>

      <section className="brief-section" data-testid="key-risks">
        <span className="block-label risk">KEY RISKS</span>
        {brief.key_risks.map((item, idx) => (
          <button
            key={item.claim_id}
            type="button"
            className={activeClaimId === item.claim_id ? 'claim-row claim-row-active' : 'claim-row'}
            data-testid={`claim-link-${claimTestToken(item.claim_id)}`}
            onClick={() => focusClaim(item.claim_id)}
          >
            <span className="point-symbol risk-symbol">⚠</span>
            <span className="claim-text" data-testid={`key-risks-item-${idx}`}>
              {item.risk}
            </span>
            <span className="source-pill">[{item.source_ref}]</span>
          </button>
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
        <p className="confidence-rationale" data-testid="confidence-rationale">
          {brief.confidence_rationale}
        </p>
      </section>

      {brief.methodology_summary ? (
        <section className="brief-section" data-testid="methodology-summary">
          <span className="block-label">METHODOLOGY</span>
          <p>{brief.methodology_summary}</p>
        </section>
      ) : null}

      {provenanceSummary ? (
        <section className="brief-section" data-testid="provenance-summary">
          <span className="block-label">PROVENANCE</span>
          <p data-testid="provenance-captured-at">Captured at: {String(provenanceSummary.captured_at ?? 'n/a')}</p>
          <p data-testid="provenance-source-count">Sources tracked: {String(provenanceSummary.source_count ?? brief.sources.length)}</p>
          {freshnessCounts ? (
            <div className="provenance-freshness-grid" data-testid="provenance-freshness-grid">
              <span data-testid="provenance-freshness-fresh">Fresh: {String(freshnessCounts.fresh ?? 0)}</span>
              <span data-testid="provenance-freshness-aging">Aging: {String(freshnessCounts.aging ?? 0)}</span>
              <span data-testid="provenance-freshness-stale">Stale: {String(freshnessCounts.stale ?? 0)}</span>
              <span data-testid="provenance-freshness-unknown">Unknown: {String(freshnessCounts.unknown ?? 0)}</span>
            </div>
          ) : null}
        </section>
      ) : null}

      {snapshotSummary ? (
        <section className="brief-section" data-testid="snapshot-summary">
          <span className="block-label">SNAPSHOTS</span>
          <p data-testid="snapshot-count">Snapshots tracked: {String(snapshotSummary.snapshot_count ?? brief.sources.length)}</p>
          {snapshotKindCounts ? (
            <div className="provenance-freshness-grid" data-testid="snapshot-kind-grid">
              <span data-testid="snapshot-kind-fixture">Fixture: {String(snapshotKindCounts.fixture ?? 0)}</span>
              <span data-testid="snapshot-kind-cache">Cache: {String(snapshotKindCounts.cache ?? 0)}</span>
              <span data-testid="snapshot-kind-live">Live: {String(snapshotKindCounts.live_capture ?? 0)}</span>
              <span data-testid="snapshot-kind-derived">Derived: {String(snapshotKindCounts.derived ?? 0)}</span>
            </div>
          ) : null}
          {cacheLineageCounts ? (
            <div className="provenance-freshness-grid" data-testid="snapshot-lineage-grid">
              <span data-testid="snapshot-lineage-fixture">Fixture lineage: {String(cacheLineageCounts.fixture ?? 0)}</span>
              <span data-testid="snapshot-lineage-cache">Cache lineage: {String(cacheLineageCounts.cache ?? 0)}</span>
              <span data-testid="snapshot-lineage-fresh">Fresh pulls: {String(cacheLineageCounts.fresh_pull ?? 0)}</span>
              <span data-testid="snapshot-lineage-derived">Derived lineage: {String(cacheLineageCounts.derived ?? 0)}</span>
            </div>
          ) : null}
          <p data-testid="snapshot-checksum-coverage">
            Snapshot checksum coverage: {String(snapshotSummary.snapshot_checksum_coverage ?? 0)}
          </p>
        </section>
      ) : null}

      {evaluation ? (
        <section className="brief-section" data-testid="evaluation-report">
          <span className="block-label">EVALUATION</span>
          <p data-testid="evaluation-status">Status: {evaluation.passed ? 'PASS' : 'FAIL'}</p>
          <p className="evaluation-signature" data-testid="evaluation-signature">
            Signature: {evaluation.deterministic_signature}
          </p>
          <div className="evaluation-checks">
            {evaluation.checks.map((check, idx) => (
              <div
                key={`${check.check_id}-${idx}`}
                className={check.passed ? 'evaluation-check evaluation-check-pass' : 'evaluation-check evaluation-check-fail'}
                data-testid={`evaluation-check-${idx}`}
              >
                <strong>{check.check_id}</strong>
                <span>{check.detail}</span>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {freshnessPolicyViolations.length > 0 ? (
        <section className="brief-section" data-testid="policy-warning-panel">
          <span className="block-label">FRESHNESS POLICY WARNINGS</span>
          <p data-testid="policy-warning-count">Violations: {freshnessPolicyViolations.length}</p>
          <div className="evaluation-checks">
            {freshnessPolicyViolations.slice(0, 6).map((violation, idx) => (
              <div
                key={`${violation}-${idx}`}
                className="evaluation-check evaluation-check-fail"
                data-testid={`policy-warning-item-${idx}`}
              >
                {violation}
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {brief.signal_conflicts && brief.signal_conflicts.length > 0 ? (
        <section className="brief-section" data-testid="signal-conflicts">
          <span className="block-label">SIGNAL CONFLICTS</span>
          {brief.signal_conflicts.map((conflict, idx) => (
            <article key={conflict.conflict_id} className="signal-conflict" data-testid={`signal-conflict-${idx}`}>
              <div className="signal-conflict-header">
                <strong>{conflict.title}</strong>
                <span className={`signal-conflict-severity signal-conflict-severity-${conflict.severity}`}>{conflict.severity.toUpperCase()}</span>
              </div>
              <p>{conflict.summary}</p>
              {conflict.claim_refs.length > 0 ? (
                <div className="signal-conflict-claims">
                  Claims:
                  {conflict.claim_refs.map((claimRef, claimIdx) => (
                    <button
                      key={`${conflict.conflict_id}-${claimRef}`}
                      type="button"
                      className={activeClaimId === claimRef ? 'inline-claim-link inline-claim-link-active' : 'inline-claim-link'}
                      data-testid={`signal-conflict-claim-${idx}-${claimIdx}`}
                      onClick={() => focusClaim(claimRef)}
                    >
                      {claimRef}
                    </button>
                  ))}
                </div>
              ) : null}
              {conflict.source_refs.length > 0 ? (
                <div className="signal-conflict-sources" data-testid={`signal-conflict-sources-${idx}`}>
                  Sources: {conflict.source_refs.join(', ')}
                </div>
              ) : null}
            </article>
          ))}
        </section>
      ) : null}

      {activeClaim ? (
        <section className="brief-section" data-testid="evidence-drilldown">
          <span className="block-label">EVIDENCE DRILL-DOWN</span>
          <p data-testid="active-claim-id">Active claim: {activeClaim.claim_id}</p>
          <p>{activeClaim.text}</p>
          <p>
            Linked sources: {activeClaimSources.length > 0 ? activeClaimSources.map((source) => sourceKey(source)).join(', ') : 'none'}
          </p>
        </section>
      ) : null}

      <section className="brief-section" data-testid="session-lineage">
        <span className="block-label">LINEAGE</span>
        <p>
          Trace steps referenced: {brief.trace_steps.length > 0 ? `${brief.trace_steps[0]}-${brief.trace_steps[brief.trace_steps.length - 1]}` : 'none'}
        </p>
      </section>

      <section className="brief-section" data-testid="source-list">
        <span className="block-label">SOURCES</span>
        {brief.sources.map((source, idx) => {
          const sourceIdentifier = sourceKey(source)
          const expanded = expandedSource === sourceIdentifier
          const sourceLinkedToActiveClaim = activeClaimId ? (source.claim_refs ?? []).includes(activeClaimId) : false
          return (
            <div key={sourceIdentifier}>
              <button
                type="button"
                className={
                  sourceLinkedToActiveClaim ? 'source-row source-row-linked-claim' : 'source-row'
                }
                data-testid={`source-item-${idx}`}
                aria-expanded={expanded}
                data-preview-kind={source.preview?.kind ?? 'none'}
                onClick={() => setExpandedSource(expanded ? null : sourceIdentifier)}
              >
                <span className={sourceBadgeClass(source.type)}>{source.type.toUpperCase()}</span>
                <span className="source-id">{source.id}</span>
                <span className="source-excerpt">{source.excerpt}</span>
                <span
                  className={freshnessBadgeClass(source.provenance?.freshness ?? 'unknown')}
                  data-testid={`source-freshness-${idx}`}
                >
                  {(source.provenance?.freshness ?? 'unknown').toUpperCase()}
                </span>
                <span
                  className={stateLabelBadgeClass(source.provenance?.state_label ?? 'unknown')}
                  data-testid={`source-state-label-${idx}`}
                >
                  {(source.provenance?.state_label ?? 'unknown').toUpperCase()}
                </span>
                <span
                  className={snapshotKindBadgeClass(source.provenance?.snapshot?.snapshot_kind ?? 'unknown')}
                  data-testid={`source-snapshot-kind-badge-${idx}`}
                >
                  {(source.provenance?.snapshot?.snapshot_kind ?? 'unknown').toUpperCase()}
                </span>
              </button>
              {source.claim_refs && source.claim_refs.length > 0 ? (
                <div className="source-claims" data-testid={`source-claims-${idx}`}>
                  Claims:
                  {source.claim_refs.map((claimRef, claimIdx) => (
                    <button
                      key={`${sourceIdentifier}-${claimRef}`}
                      type="button"
                      className={activeClaimId === claimRef ? 'inline-claim-link inline-claim-link-active' : 'inline-claim-link'}
                      data-testid={`source-claim-ref-${idx}-${claimIdx}`}
                      onClick={() => focusClaim(claimRef)}
                    >
                      {claimRef}
                    </button>
                  ))}
                </div>
              ) : null}
              {expanded ? <SourcePreview source={source} idx={idx} /> : null}
            </div>
          )
        })}
      </section>
    </div>
  )
}
