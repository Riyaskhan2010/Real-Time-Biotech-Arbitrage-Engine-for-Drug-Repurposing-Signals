/**
 * EvidenceScoreBreakdown
 * ======================
 * Transparent 5-factor scoring table.
 * Explicitly labelled as "Experimental Research Prioritization Score".
 * Never presented as clinical probability.
 */
import { BookOpen, FlaskConical, GitMerge, Layers, Clock, Info } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { clsx } from 'clsx'
import type { EnrichedScoreBreakdown } from '../types'

interface Props {
  breakdown: EnrichedScoreBreakdown
  className?: string
}

const FACTOR_META: Record<string, {
  icon: LucideIcon
  color: string
  description: string
}> = {
  research_evidence: {
    icon: BookOpen,
    color: 'text-blue-400',
    description: 'Published research papers, preprints, and review articles',
  },
  clinical_evidence: {
    icon: FlaskConical,
    color: 'text-emerald-400',
    description: 'Registered clinical trials and clinical study records',
  },
  mechanism_match: {
    icon: GitMerge,
    color: 'text-purple-400',
    description: 'Degree of target/pathway overlap between drug and disease',
  },
  independent_sources: {
    icon: Layers,
    color: 'text-amber-400',
    description: 'Number of independent sources corroborating the association',
  },
  recency: {
    icon: Clock,
    color: 'text-rose-400',
    description: 'Proportion of evidence published after 2020',
  },
}

function scorePct(score: number, max: number) {
  return max > 0 ? Math.min((score / max) * 100, 100) : 0
}

function barColor(pct: number) {
  if (pct >= 80) return 'bg-emerald-500'
  if (pct >= 50) return 'bg-amber-500'
  return 'bg-rose-500'
}

export function EvidenceScoreBreakdown({ breakdown, className }: Props) {
  const factors = [
    'research_evidence',
    'clinical_evidence',
    'mechanism_match',
    'independent_sources',
    'recency',
  ] as const

  const total = breakdown.total

  return (
    <div className={clsx('space-y-4', className)}>
      {/* Label */}
      <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg bg-brand-500/8 border border-brand-500/20">
        <Info size={13} className="text-brand-400 shrink-0 mt-0.5" />
        <div>
          <p className="text-xs font-semibold text-brand-300">
            Experimental Research Prioritization Score
          </p>
          <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
            This score reflects evidence volume and diversity — not clinical efficacy or treatment probability.
            It is a research-prioritization heuristic to help researchers focus attention.
            Requires expert validation before any further use.
          </p>
        </div>
      </div>

      {/* Factor rows */}
      <div className="space-y-3">
        {factors.map((key) => {
          const factor = breakdown[key]
          if (!factor) return null
          const meta   = FACTOR_META[key]
          const pct    = scorePct(factor.score, factor.max)
          const Icon   = meta?.icon ?? BookOpen

          return (
            <div key={key} className="group">
              <div className="flex items-center gap-3 mb-1.5">
                {/* Icon + label */}
                <div className="flex items-center gap-2 w-40 shrink-0">
                  <Icon size={13} className={clsx(meta?.color ?? 'text-slate-400')} />
                  <span className="text-xs text-slate-300 font-medium">{factor.label}</span>
                </div>

                {/* Bar */}
                <div className="flex-1 h-2 rounded-full bg-slate-700/60">
                  <div
                    className={clsx('h-2 rounded-full transition-all duration-500', barColor(pct))}
                    style={{ width: `${pct}%` }}
                  />
                </div>

                {/* Score / max */}
                <div className="flex items-center gap-1 w-16 shrink-0 justify-end">
                  <span className="text-sm font-bold tabular-nums text-slate-200">{factor.score}</span>
                  <span className="text-xs text-slate-600">/ {factor.max}</span>
                </div>

                {/* Item count */}
                {factor.items !== null && factor.items !== undefined && (
                  <span className="text-[10px] text-slate-600 w-16 shrink-0 text-right">
                    ({factor.items} item{factor.items !== 1 ? 's' : ''})
                  </span>
                )}
              </div>

              {/* Hover description */}
              <p className="text-[10px] text-slate-600 pl-[calc(10rem+0.5rem)] leading-relaxed hidden group-hover:block">
                {meta?.description}
              </p>
            </div>
          )
        })}
      </div>

      {/* Divider */}
      <div className="border-t border-slate-700/60 pt-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-slate-300">Total</span>
            <span className="text-[10px] text-slate-500">(Experimental Research Prioritization Score)</span>
          </div>
          <div className="flex items-baseline gap-1">
            <span className={clsx(
              'text-3xl font-bold tabular-nums',
              total.score >= 75 ? 'text-emerald-400' :
              total.score >= 55 ? 'text-amber-400'   : 'text-rose-400'
            )}>
              {total.score}
            </span>
            <span className="text-slate-500 text-sm">/ {total.max}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
