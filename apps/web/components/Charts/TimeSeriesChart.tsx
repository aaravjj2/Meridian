'use client'

import { useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
  ReferenceLine,
} from 'recharts'

type DataPoint = {
  date: string
  value: number
}

interface TimeSeriesChartProps {
  data: DataPoint[]
  title?: string
  color?: string
  showArea?: boolean
  threshold?: number
  thresholdLabel?: string
  className?: string
}

const DEFAULT_COLOR = '#3a8abd'

export default function TimeSeriesChart({
  data,
  title,
  color = DEFAULT_COLOR,
  showArea = true,
  threshold,
  thresholdLabel,
  className,
}: TimeSeriesChartProps) {
  const chartData = useMemo(() => {
    return data.map((d) => ({
      ...d,
      date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    }))
  }, [data])

  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: any[] }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-date">{payload[0].payload.date}</p>
          <p className="tooltip-value">
            <span style={{ color }} className="tooltip-indicator" />
            {payload[0].value?.toFixed(2)}
          </p>
        </div>
      )
    }
    return null
  }

  const ChartComponent = showArea ? AreaChart : LineChart

  return (
    <div className={`timeseries-chart ${className || ''}`}>
      {title && <h4 className="chart-title">{title}</h4>}
      <ResponsiveContainer width="100%" height={200}>
        <ChartComponent data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2a38" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#8899aa', fontSize: 11 }}
            stroke="#2a3a4c"
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#8899aa', fontSize: 11 }}
            stroke="#2a3a4c"
            tickLine={false}
            domain={['auto', 'auto']}
          />
          <Tooltip content={<CustomTooltip />} />
          {threshold && (
            <ReferenceLine
              y={threshold}
              stroke={threshold > (data[data.length - 1]?.value || 0) ? '#22c55e' : '#ef4444'}
              strokeDasharray="3 3"
              label={{
                value: thresholdLabel || 'Threshold',
                fill: threshold > (data[data.length - 1]?.value || 0) ? '#22c55e' : '#ef4444',
                fontSize: 10,
              }}
            />
          )}
          {showArea ? (
            <Area
              type="monotone"
              dataKey="value"
              stroke={color}
              fill={color}
              fillOpacity={0.2}
              strokeWidth={2}
              animationBegin={0}
              animationDuration={1000}
              dot={false}
            />
          ) : (
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              animationBegin={0}
              animationDuration={1000}
              dot={false}
              activeDot={{ r: 4, stroke: color, strokeWidth: 2 }}
            />
          )}
        </ChartComponent>
      </ResponsiveContainer>
    </div>
  )
}

// Multi-series time series chart
interface MultiSeriesTimeSeriesChartProps {
  data: Array<{ date: string; [key: string]: string | number }>
  series: Array<{ key: string; name: string; color: string }>
  title?: string
  className?: string
}

export function MultiSeriesTimeSeriesChart({
  data,
  series,
  title,
  className,
}: MultiSeriesTimeSeriesChartProps) {
  const chartData = useMemo(() => {
    return data.map((d) => ({
      ...d,
      date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    }))
  }, [data])

  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: any[] }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip multi-series">
          <p className="tooltip-date">{payload[0].payload.date}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="tooltip-value">
              <span
                style={{ backgroundColor: entry.color }}
                className="tooltip-indicator"
              />
              {entry.name}: {entry.value?.toFixed(2)}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <div className={`timeseries-chart multi-series ${className || ''}`}>
      {title && <h4 className="chart-title">{title}</h4>}
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2a38" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#8899aa', fontSize: 11 }}
            stroke="#2a3a4c"
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#8899aa', fontSize: 11 }}
            stroke="#2a3a4c"
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          {series.map((s) => (
            <Line
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.name}
              stroke={s.color}
              strokeWidth={2}
              animationBegin={0}
              animationDuration={1000}
              dot={false}
              activeDot={{ r: 4, stroke: s.color, strokeWidth: 2 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

// Gauge chart for single metric
interface GaugeChartProps {
  value: number
  min: number
  max: number
  title?: string
  color?: string
  thresholds?: Array<{ value: number; color: string; label: string }>
  className?: string
}

export function GaugeChart({
  value,
  min,
  max,
  title,
  color = DEFAULT_COLOR,
  thresholds,
  className,
}: GaugeChartProps) {
  const percentage = useMemo(() => {
    return ((value - min) / (max - min)) * 100
  }, [value, min, max])

  const strokeColor = useMemo(() => {
    if (thresholds) {
      for (const t of thresholds) {
        if (value <= t.value) {
          return t.color
        }
      }
    }
    return color
  }, [value, thresholds, color])

  return (
    <div className={`gauge-chart ${className || ''}`}>
      {title && <h4 className="chart-title">{title}</h4>}
      <div className="gauge-container">
        <svg viewBox="0 0 200 120" className="gauge-svg">
          {/* Background arc */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="#1e2a38"
            strokeWidth="20"
            strokeLinecap="round"
          />
          {/* Value arc */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke={strokeColor}
            strokeWidth="20"
            strokeLinecap="round"
            strokeDasharray={`${(percentage / 100) * 251.2} 251.2`}
            className="gauge-value-arc"
            style={{ transition: 'stroke-dasharray 1s ease-out' }}
          />
          {/* Value text */}
          <text x="100" y="85" textAnchor="middle" className="gauge-value-text">
            {value.toFixed(1)}
          </text>
          <text x="100" y="105" textAnchor="middle" className="gauge-label-text">
            {title || ''}
          </text>
        </svg>
        {thresholds && (
          <div className="gauge-legend">
            {thresholds.map((t, i) => (
              <div key={i} className="gauge-legend-item">
                <span className="legend-dot" style={{ backgroundColor: t.color }} />
                <span className="legend-label">{t.label}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
