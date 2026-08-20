import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface Props {
  high: number
  medium: number
  low: number
}

const COLORS = ['#10b981', '#f59e0b', '#f43f5e']

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload?.length) {
    return (
      <div className="bg-surface-800 border border-slate-700 rounded-lg px-3 py-2 text-xs shadow-xl">
        <p style={{ color: payload[0].payload.fill }} className="font-semibold">{payload[0].name}</p>
        <p className="text-slate-300">{payload[0].value} signal{payload[0].value !== 1 ? 's' : ''}</p>
      </div>
    )
  }
  return null
}

export function ConfidenceDistributionChart({ high, medium, low }: Props) {
  const data = [
    { name: 'High', value: high },
    { name: 'Medium', value: medium },
    { name: 'Low', value: low },
  ].filter((d) => d.value > 0)

  if (data.length === 0) return (
    <p className="text-xs text-slate-500 text-center py-8">No signals available</p>
  )

  return (
    <ResponsiveContainer width="100%" height={180}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={46}
          outerRadius={68}
          paddingAngle={3}
          dataKey="value"
          strokeWidth={0}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: 11, color: '#94a3b8', paddingTop: 8 }}
          iconType="circle"
          iconSize={7}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}
