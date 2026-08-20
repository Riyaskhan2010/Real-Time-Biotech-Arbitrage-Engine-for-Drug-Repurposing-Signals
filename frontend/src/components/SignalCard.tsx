import { useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { ConfidenceBadge } from './ui/Badge'
import { ScoreBar } from './ui/ScoreBar'
import type { SignalListItem } from '../types'
import { formatDistanceToNow, parseISO } from 'date-fns'
import { clsx } from 'clsx'

interface Props {
  signal: SignalListItem
  compact?: boolean
}

const SOURCE_COLORS: Record<string, string> = {
  pubmed:         'bg-blue-400',
  europepmc:      'bg-teal-500',
  uniprot:        'bg-violet-500',
  elsevier:       'bg-orange-400',
  biorxiv:        'bg-amber-400',
  medrxiv:        'bg-rose-400',
  clinicaltrials: 'bg-green-500',
}

export function SignalCard({ signal, compact = false }: Props) {
  const navigate   = useNavigate()
  const timeAgo    = signal.detected_at
    ? formatDistanceToNow(parseISO(signal.detected_at), { addSuffix: true })
    : null
  const hasLive    = (signal.live_evidence_count ?? 0) > 0
  const liveCount  = signal.live_evidence_count ?? 0
  const unique     = signal.unique_evidence_count ?? signal.source_count
  const sources    = (signal.source_names ?? []).filter(s => s !== 'demo').slice(0, 5)

  return (
    <article
      role="button"
      tabIndex={0}
      onClick={() => navigate(`/signals/${signal.id}`)}
      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') navigate(`/signals/${signal.id}`) }}
      className={clsx(
        'group ui-card p-4 cursor-pointer hover:border-navy-300 hover:shadow-card-md transition-all',
        'flex flex-col gap-3'
      )}
      aria-label={`Signal: ${signal.drug_name ?? ''} to ${signal.disease_name ?? ''}, score ${signal.evidence_score.toFixed(0)}`}
    >
      {/* Badges + time */}
      <div className="flex items-start justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          <ConfidenceBadge level={signal.confidence_level} />
          {signal.is_novel && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-violet-50 text-violet-700 border border-violet-200">
              Novel
            </span>
          )}
          {hasLive && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-green-50 text-green-700 border border-green-200 uppercase tracking-wide">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 pulse-green shrink-0" aria-hidden="true" />
              Live
            </span>
          )}
        </div>
        {timeAgo && (
          <time className="text-[10px] text-slate-400 shrink-0" dateTime={signal.detected_at ?? ''}>
            {timeAgo}
          </time>
        )}
      </div>

      {/* Drug → Disease */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="inline-flex items-center px-2.5 py-1 rounded-lg bg-navy-50 border border-navy-200 text-[12px] font-semibold text-navy-800">
          {signal.drug_name ?? `Drug #${signal.drug_id}`}
        </span>
        <ArrowRight size={13} className="text-slate-400 shrink-0" aria-hidden="true" />
        <span className="inline-flex items-center px-2.5 py-1 rounded-lg bg-violet-50 border border-violet-200 text-[12px] font-semibold text-violet-800">
          {signal.disease_name ?? `Disease #${signal.disease_id}`}
        </span>
      </div>

      {/* Optional mechanism snippet */}
      {!compact && signal.biological_mechanism && (
        <p className="text-[12px] text-slate-500 leading-relaxed line-clamp-2">{signal.biological_mechanism}</p>
      )}

      {/* Score */}
      <ScoreBar score={signal.evidence_score} size="sm" />

      {/* Source dots */}
      {sources.length > 0 && (
        <div className="flex items-center gap-1.5 flex-wrap" aria-label="Contributing sources">
          {sources.map(src => (
            <span key={src} className="flex items-center gap-1 text-[10px] text-slate-500">
              <span className={clsx('w-2 h-2 rounded-full shrink-0', SOURCE_COLORS[src] ?? 'bg-slate-400')} aria-hidden="true" />
              {src}
            </span>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-1 border-t border-slate-100">
        <div className="flex items-center gap-3 text-[11px] text-slate-500">
          <span>{unique ?? 0} evidence record{unique !== 1 ? 's' : ''}</span>
          {hasLive && liveCount > 0 && (
            <span className="text-green-600">{liveCount} live</span>
          )}
        </div>
        <ArrowRight size={13} className="text-slate-300 group-hover:text-navy-500 transition-colors" aria-hidden="true" />
      </div>
    </article>
  )
}
