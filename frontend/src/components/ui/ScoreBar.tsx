import { clsx } from 'clsx'

interface ScoreBarProps {
  score: number   // 0–100
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  className?: string
}

function getBarColor(score: number) {
  if (score >= 75) return 'bg-emerald-500'
  if (score >= 55) return 'bg-amber-500'
  return 'bg-rose-400'
}

function getTextColor(score: number) {
  if (score >= 75) return 'text-emerald-600'
  if (score >= 55) return 'text-amber-600'
  return 'text-rose-500'
}

const HEIGHT: Record<string, string> = { sm: 'h-1', md: 'h-1.5', lg: 'h-2' }

export function ScoreBar({ score, size = 'md', showLabel = true, className }: ScoreBarProps) {
  return (
    <div className={clsx('w-full', className)}>
      {showLabel && (
        <div className="flex items-center justify-between mb-1">
          <span className="text-[11px] text-slate-500">Evidence Score</span>
          <span className={clsx('text-[13px] font-bold tabular-nums', getTextColor(score))}>
            {score.toFixed(0)}<span className="text-slate-400 font-normal text-[11px]">/100</span>
          </span>
        </div>
      )}
      <div className={clsx('w-full rounded-full bg-slate-200', HEIGHT[size])}>
        <div
          className={clsx('rounded-full transition-all duration-500', HEIGHT[size], getBarColor(score))}
          style={{ width: `${Math.min(score, 100)}%` }}
          role="progressbar"
          aria-valuenow={score}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  )
}

export function ScoreCircle({ score }: { score: number }) {
  const border = score >= 75 ? 'border-emerald-400' : score >= 55 ? 'border-amber-400' : 'border-rose-400'
  const bg     = score >= 75 ? 'bg-emerald-50'      : score >= 55 ? 'bg-amber-50'      : 'bg-rose-50'
  return (
    <div className={clsx('flex flex-col items-center justify-center w-20 h-20 rounded-full border-2', border, bg)}>
      <span className={clsx('text-2xl font-bold tabular-nums', getTextColor(score))}>
        {score.toFixed(0)}
      </span>
      <span className="text-[10px] text-slate-400">/ 100</span>
    </div>
  )
}
