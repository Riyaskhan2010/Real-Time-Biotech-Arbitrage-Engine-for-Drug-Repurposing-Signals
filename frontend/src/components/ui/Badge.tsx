import { clsx } from 'clsx'

type Variant = 'high' | 'medium' | 'low' | 'info' | 'novel' | 'default' | 'demo'

interface BadgeProps {
  variant?: Variant
  children: React.ReactNode
  className?: string
}

// Light-background badge variants
const VARIANT_CLS: Record<Variant, string> = {
  high:    'bg-emerald-50  text-emerald-800 border border-emerald-200',
  medium:  'bg-amber-50    text-amber-800   border border-amber-200',
  low:     'bg-slate-50    text-slate-700   border border-slate-200',
  info:    'bg-blue-50     text-blue-800    border border-blue-200',
  novel:   'bg-violet-50   text-violet-800  border border-violet-200',
  demo:    'bg-slate-50    text-slate-600   border border-slate-200',
  default: 'bg-slate-50    text-slate-700   border border-slate-200',
}

export function Badge({ variant = 'default', children, className }: BadgeProps) {
  return (
    <span className={clsx(
      'inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium',
      VARIANT_CLS[variant],
      className
    )}>
      {children}
    </span>
  )
}

export function ConfidenceBadge({ level }: { level: string }) {
  const variant = level === 'high' ? 'high' : level === 'medium' ? 'medium' : 'low'
  const label   = level.charAt(0).toUpperCase() + level.slice(1)
  return <Badge variant={variant}>{label} Confidence</Badge>
}
