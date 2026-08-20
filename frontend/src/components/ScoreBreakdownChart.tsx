import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  ResponsiveContainer, Tooltip,
} from 'recharts'
import type { ScoreBreakdown } from '../types'

interface Props {
  breakdown: ScoreBreakdown
}

const MAX: Record<string, number> = {
  independent_sources: 30,
  recency_score: 25,
  clinical_trial_support: 20,
  mechanism_alignment: 25,
}

const LABELS: Record<string, string> = {
  independent_sources: 'Sources',
  recency_score: 'Recency',
  clinical_trial_support: 'Trial Support',
  mechanism_alignment: 'Mechanism',
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload?.length) {
    return (
      <div className="bg-surface-800 border border-slate-700 rounded-lg px-3 py-2 text-xs shadow-xl">
        <p className="text-slate-300 font-medium">{payload[0]?.payload?.subject}</p>
        <p className="text-brand-400">Score: {payload[0]?.value?.toFixed(0)}%</p>
      </div>
    )
  }
  return null
}

export function ScoreBreakdownChart({ breakdown }: Props) {
  const data = Object.entries(MAX)
    .map(([key, max]) => ({
      subject: LABELS[key] ?? key,
      value: Math.round(((breakdown[key as keyof ScoreBreakdown] as number) / max) * 100),
      fullMark: 100,
    }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <RadarChart cx="50%" cy="50%" outerRadius={80} data={data}>
        <PolarGrid stroke="#1e2130" />
        <PolarAngleAxis
          dataKey="subject"
          tick={{ fill: '#64748b', fontSize: 10 }}
        />
        <Radar
          name="Score"
          dataKey="value"
          stroke="#6366f1"
          fill="#6366f1"
          fillOpacity={0.25}
          strokeWidth={2}
          dot={{ r: 3, fill: '#6366f1', strokeWidth: 0 }}
        />
        <Tooltip content={<CustomTooltip />} />
      </RadarChart>
    </ResponsiveContainer>
  )
}
