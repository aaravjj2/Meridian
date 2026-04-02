'use client'

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

type Point = {
  date: string
  value: number
}

type SeriesChartProps = {
  id: string
  data: Point[]
}

export default function SeriesChart({ id, data }: SeriesChartProps) {
  const isE2E =
    process.env.PLAYWRIGHT === 'true' ||
    (typeof document !== 'undefined' && document.body.dataset.e2e === 'true')

  return (
    <div className="series-chart-wrap" data-testid={`series-chart-${id}`} aria-label={`Series chart for ${id}`}>
      <ResponsiveContainer width="100%" height={120}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="var(--border-subtle)" />
          <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
          <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} width={40} />
          <Tooltip
            contentStyle={{
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-default)',
              color: 'var(--text-primary)',
            }}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="var(--accent)"
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={!isE2E}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
