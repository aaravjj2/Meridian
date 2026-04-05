'use client'

import type { DerivedIndicator } from './types'

type DerivedIndicatorPanelProps = {
  indicators: DerivedIndicator[]
}

export default function DerivedIndicatorPanel({ indicators }: DerivedIndicatorPanelProps) {
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
    }
    return labels[kind] || kind
  }

  return (
    <div className="mt-4 border-t border-gray-200 dark:border-gray-700 pt-4" data-testid="derived-indicator-panel">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3" data-testid="derived-indicators-title">
        Derived Indicators
      </h3>
      <div className="space-y-2">
        {indicators.map((indicator) => (
          <div
            key={indicator.indicator_id}
            className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700"
            data-testid={`derived-indicator-${indicator.indicator_id}`}
          >
            <div className="flex items-center justify-between mb-1">
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
            {indicator.reasoning && (
              <div className="text-xs text-gray-600 dark:text-gray-400" data-testid={`derived-indicator-${indicator.indicator_id}-reasoning`}>
                {indicator.reasoning}
              </div>
            )}
            {indicator.source_refs && indicator.source_refs.length > 0 && (
              <div className="mt-2 text-xs">
                <span className="text-gray-500 dark:text-gray-500">Sources: </span>
                <span className="text-gray-600 dark:text-gray-400" data-testid={`derived-indicator-${indicator.indicator_id}-sources`}>
                  {indicator.source_refs.slice(0, 3).join(', ')}
                  {indicator.source_refs.length > 3 && ` (+${indicator.source_refs.length - 3} more)`}
                </span>
              </div>
            )}
            {indicator.snapshot_kind && (
              <div className="mt-1 text-xs">
                <span className="text-gray-500 dark:text-gray-500">Computed from: </span>
                <span className="text-gray-600 dark:text-gray-400" data-testid={`derived-indicator-${indicator.indicator_id}-snapshot-kind`}>
                  {indicator.snapshot_kind}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
