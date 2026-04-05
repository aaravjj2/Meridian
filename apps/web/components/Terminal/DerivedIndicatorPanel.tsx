'use client'

import { useState, useMemo } from 'react'
import type { DerivedIndicator } from './types'

type DerivedIndicatorPanelProps = {
  indicators: DerivedIndicator[]
}

type FilterKind = 'all' | DerivedIndicator['computation_kind']
type SortBy = 'value' | 'kind' | 'title'

export default function DerivedIndicatorPanel({ indicators }: DerivedIndicatorPanelProps) {
  const [filterKind, setFilterKind] = useState<FilterKind>('all')
  const [sortBy, setSortBy] = useState<SortBy>('value')
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())

  if (!indicators || indicators.length === 0) {
    return null
  }

  const formatValue = (indicator: DerivedIndicator): string => {
    const { value, unit } = indicator
    if (unit === '%') {
      return `${value.toFixed(1)}%`
    }
    if (unit === 'ratio') {
      return value.toFixed(2)
    }
    if (unit === 'index') {
      return value.toFixed(2)
    }
    if (unit === 'coef') {
      return value.toFixed(2)
    }
    return value.toFixed(2)
  }

  const getValueColor = (indicator: DerivedIndicator): string => {
    const { computation_kind, value } = indicator

    if (computation_kind === 'rate_of_change') {
      if (value > 0) return 'text-green-600 dark:text-green-400'
      if (value < 0) return 'text-red-600 dark:text-red-400'
      return 'text-gray-600 dark:text-gray-400'
    }

    if (computation_kind === 'aggregate_freshness') {
      if (value <= 0.5) return 'text-green-600 dark:text-green-400'
      if (value <= 1.0) return 'text-yellow-600 dark:text-yellow-400'
      return 'text-red-600 dark:text-red-400'
    }

    if (computation_kind === 'spread' && value > 0.3) {
      return 'text-orange-600 dark:text-orange-400'
    }

    if (computation_kind === 'volatility') {
      if (value > 20) return 'text-red-600 dark:text-red-400'
      if (value > 10) return 'text-yellow-600 dark:text-yellow-400'
      return 'text-green-600 dark:text-green-400'
    }

    if (computation_kind === 'momentum') {
      if (value > 2) return 'text-green-600 dark:text-green-400'
      if (value > 0.5) return 'text-green-500 dark:text-green-400'
      if (value < -2) return 'text-red-600 dark:text-red-400'
      if (value < -0.5) return 'text-red-500 dark:text-red-400'
      return 'text-gray-600 dark:text-gray-400'
    }

    if (computation_kind === 'correlation') {
      if (value > 0.7) return 'text-green-600 dark:text-green-400'
      if (value < -0.7) return 'text-red-600 dark:text-red-400'
      return 'text-gray-600 dark:text-gray-400'
    }

    return 'text-gray-700 dark:text-gray-300'
  }

  const getKindLabel = (kind: string): string => {
    const labels: Record<string, string> = {
      rate_of_change: 'Rate of Change',
      spread: 'Spread Analysis',
      delta: 'Delta',
      trend_bucket: 'Trend',
      aggregate_freshness: 'Data Freshness',
      conflict_pressure: 'Conflict Pressure',
      helper_summary: 'Summary',
      volatility: 'Volatility',
      momentum: 'Momentum',
      correlation: 'Correlation',
    }
    return labels[kind] || kind
  }

  const toggleExpanded = (id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const filteredAndSortedIndicators = useMemo(() => {
    let filtered = filterKind === 'all'
      ? indicators
      : indicators.filter(ind => ind.computation_kind === filterKind)

    return [...filtered].sort((a, b) => {
      if (sortBy === 'value') {
        return Math.abs(b.value) - Math.abs(a.value)
      }
      if (sortBy === 'kind') {
        return a.computation_kind.localeCompare(b.computation_kind)
      }
      return a.title.localeCompare(b.title)
    })
  }, [indicators, filterKind, sortBy])

  const kindOptions = Array.from(new Set(indicators.map(ind => ind.computation_kind)))

  return (
    <div className="mt-4 border-t border-gray-200 dark:border-gray-700 pt-4" data-testid="derived-indicator-panel">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300" data-testid="derived-indicators-title">
          Derived Indicators
        </h3>
        <div className="flex items-center gap-2">
          <select
            value={filterKind}
            onChange={(e) => setFilterKind(e.target.value as FilterKind)}
            className="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
            data-testid="derived-indicators-filter"
          >
            <option value="all">All Types</option>
            {kindOptions.map(kind => (
              <option key={kind} value={kind}>{getKindLabel(kind)}</option>
            ))}
          </select>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortBy)}
            className="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
            data-testid="derived-indicators-sort"
          >
            <option value="value">Sort by Value</option>
            <option value="kind">Sort by Type</option>
            <option value="title">Sort by Title</option>
          </select>
        </div>
      </div>
      {filteredAndSortedIndicators.length === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400 italic">No indicators match the selected filter.</p>
      ) : (
        <div className="space-y-2">
          {filteredAndSortedIndicators.map((indicator) => (
            <div
              key={indicator.indicator_id}
              className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700"
              data-testid={`derived-indicator-${indicator.indicator_id}`}
            >
              <div
                className="flex items-center justify-between mb-1 cursor-pointer"
                onClick={() => toggleExpanded(indicator.indicator_id)}
                data-testid={`derived-indicator-${indicator.indicator_id}-header`}
              >
                <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                  {getKindLabel(indicator.computation_kind)}
                </span>
                <span className={`text-sm font-bold ${getValueColor(indicator)}`} data-testid={`derived-indicator-${indicator.indicator_id}-value`}>
                  {formatValue(indicator)}
                  {indicator.unit && <span className="text-xs text-gray-500 ml-1">{indicator.unit}</span>}
                </span>
              </div>
              <div className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-1" data-testid={`derived-indicator-${indicator.indicator_id}-title`}>
                {indicator.title}
              </div>
              {expandedIds.has(indicator.indicator_id) && indicator.reasoning && (
                <div className="text-xs text-gray-600 dark:text-gray-400 mb-2" data-testid={`derived-indicator-${indicator.indicator_id}-reasoning`}>
                  {indicator.reasoning}
                </div>
              )}
              {expandedIds.has(indicator.indicator_id) && indicator.source_refs && indicator.source_refs.length > 0 && (
                <div className="text-xs">
                  <span className="text-gray-500 dark:text-gray-500">Sources: </span>
                  <span className="text-gray-600 dark:text-gray-400" data-testid={`derived-indicator-${indicator.indicator_id}-sources`}>
                    {indicator.source_refs.slice(0, 3).join(', ')}
                    {indicator.source_refs.length > 3 && ` (+${indicator.source_refs.length - 3} more)`}
                  </span>
                </div>
              )}
              {expandedIds.has(indicator.indicator_id) && indicator.snapshot_kind && (
                <div className="mt-1 text-xs">
                  <span className="text-gray-500 dark:text-gray-500">Computed from: </span>
                  <span className="text-gray-600 dark:text-gray-400" data-testid={`derived-indicator-${indicator.indicator_id}-snapshot-kind`}>
                    {indicator.snapshot_kind}
                  </span>
                </div>
              )}
              {!expandedIds.has(indicator.indicator_id) && indicator.reasoning && (
                <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {indicator.reasoning}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
