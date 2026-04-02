'use client'

import { useMemo } from 'react'
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer, Legend } from 'recharts'

type RegimeData = {
  dimension: string
  value: number
  fullMark: number
}

interface RadarRegimeChartProps {
  growth: string
  inflation: string
  monetary: string
  credit: string
  labor: string
  className?: string
}

function dimensionScore(value: string): number {
  const v = value.toUpperCase()
  // Convert categorical values to numeric scores (0-100)
  const scores: Record<string, number> = {
    // Growth
    EXPANSION: 80,
    SLOWDOWN: 40,
    CONTRACTION: 20,

    // Inflation
    ELEVATED: 70,
    COOLING: 50,
    LOW: 30,

    // Monetary
    RESTRICTIVE: 80,
    NEUTRAL: 50,
    ACCOMMODATIVE: 20,

    // Credit
    HEALTHY: 90,
    NORMAL: 60,
    CAUTION: 40,
    STRESS: 20,

    // Labor
    TIGHT: 80,
    SOFTENING: 50,
    WEAK: 30,
  }

  for (const [key, score] of Object.entries(scores)) {
    if (v.includes(key)) {
      return score
    }
  }
  return 50 // Default neutral
}

function dimensionColor(value: string): string {
  const score = dimensionScore(value)
  if (score >= 70) return '#22c55e' // green
  if (score >= 40) return '#f59e0b' // amber
  return '#ef4444' // red
}

export default function RadarRegimeChart({ growth, inflation, monetary, credit, labor, className }: RadarRegimeChartProps) {
  const data = useMemo<RegimeData[]>(
    () => [
      { dimension: 'Growth', value: dimensionScore(growth), fullMark: 100 },
      { dimension: 'Inflation', value: dimensionScore(inflation), fullMark: 100 },
      { dimension: 'Monetary', value: dimensionScore(monetary), fullMark: 100 },
      { dimension: 'Credit', value: dimensionScore(credit), fullMark: 100 },
      { dimension: 'Labor', value: dimensionScore(labor), fullMark: 100 },
    ],
    [growth, inflation, monetary, credit, labor]
  )

  const primaryColor = useMemo(() => {
    const avgScore = data.reduce((sum, d) => sum + d.value, 0) / data.length
    if (avgScore >= 70) return '#22c55e'
    if (avgScore >= 40) return '#f59e0b'
    return '#ef4444'
  }, [data])

  return (
    <div className={`radar-chart-container ${className || ''}`}>
      <ResponsiveContainer width="100%" height={250}>
        <RadarChart data={data}>
          <PolarGrid stroke="#2a3a4c" />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fill: '#8899aa', fontSize: 11 }}
            className="radar-axis-label"
          />
          <Radar
            name="Regime Strength"
            dataKey="value"
            stroke={primaryColor}
            fill={primaryColor}
            fillOpacity={0.3}
            strokeWidth={2}
            dot={{ r: 4, fill: primaryColor }}
            animationBegin={0}
            animationDuration={800}
          />
          <Legend
            wrapperStyle={{ fontSize: '11px', color: '#8899aa' }}
            content={({ payload }) => (
              <div style={{ display: 'flex', justifyContent: 'center', gap: '16px' }}>
                {payload?.map((entry, index) => (
                  <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span
                      style={{
                        width: '10px',
                        height: '10px',
                        backgroundColor: entry.color,
                        borderRadius: '2px',
                      }}
                    />
                    <span style={{ color: '#8899aa', fontSize: '11px' }}>{entry.value}</span>
                  </div>
                ))}
              </div>
            )}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
