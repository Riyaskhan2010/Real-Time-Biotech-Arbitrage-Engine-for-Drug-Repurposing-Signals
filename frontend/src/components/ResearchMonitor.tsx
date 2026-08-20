/**
 * ResearchMonitor
 * ===============
 * Shows the live ingestion pipeline + record feed.
 *
 * Props:
 *   compact       – compact layout for the Dashboard sidebar (default false)
 *   showRunButton – show "Run Live Ingestion" button regardless of compact mode
 *   onIngestionComplete – called after a successful/partial run so the caller
 *                         can refresh dashboard data (signals, alerts, stats, etc.)
 *
 * LIVE records are clearly labelled with an animated green "LIVE" badge.
 * DEMO records are clearly labelled with an amber "DEMO" badge.
 * Never fakes a successful ingestion — all state comes from the real backend response.
 *
 * Research decision-support tool only. Not for clinical use.
 */
import { useCallback, useEffect, useState } from 'react'
import {
  Database, Cpu, GitMerge, Layers, BarChart2,
  ChevronDown, ChevronUp, TrendingUp, TrendingDown,
  FlaskConical, RefreshCw, Play, CheckCircle2,
  AlertTriangle, Wifi, Clock, RotateCw,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { clsx } from 'clsx'
import { researchMonitorApi, ingestionApi } from '../api'
import type {
  ResearchMonitorData, ResearchMonitorRecord,
  IngestionRunOut, IngestionRunStatus,
} from '../types'
import { formatDistanceToNow, parseISO, format } from 'date-fns'

// ── Icon maps ─────────────────────────────────────────────────────────────────

const STAGE_ICONS: Record<string, LucideIcon> = {
  ingestion:                Database,
  entity_extraction:        Cpu,
  mechanism_identification: GitMerge,
  evidence_matching:        Layers,
  signal_evaluation:        BarChart2,
}

const SOURCE_COLORS: Record<string, string> = {
  pubmed:         'bg-blue-500/15   text-blue-400   border-blue-500/25',
  biorxiv:        'bg-amber-500/15  text-amber-400  border-amber-500/25',
  medrxiv:        'bg-orange-500/15 text-orange-400 border-orange-500/25',
  clinicaltrials: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/25',
  default:        'bg-slate-500/15  text-slate-400  border-slate-500/25',
}

// ── LIVE / DEMO badge ─────────────────────────────────────────────────────────

function DataModeBadge({ mode }: { mode: string }) {
  if (mode === 'live') {
    return (
      <span className="flex items-center gap-1 text-[9px] px-1.5 py-0.5 rounded border border-emerald-500/40 bg-emerald-500/10 text-emerald-400 font-semibold uppercase tracking-wide">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shrink-0" />
        LIVE
      </span>
    )
  }
  return (
    <span className="text-[9px] px-1.5 py-0.5 rounded border border-amber-500/30 bg-amber-500/10 text-amber-400 font-semibold uppercase tracking-wide">
      DEMO
    </span>
  )
}

// ── Record row ────────────────────────────────────────────────────────────────

function RecordRow({ record }: { record: ResearchMonitorRecord }) {
  const [expanded, setExpanded] = useState(false)
  const mode        = (record as any).data_mode ?? 'demo'
  const sourceKey   = (record.source_type ?? record.source ?? '').toLowerCase()
  const sourceColor = SOURCE_COLORS[sourceKey] ?? SOURCE_COLORS.default
  const timeAgo     = record.ingested_at
    ? formatDistanceToNow(parseISO(record.ingested_at), { addSuffix: true })
    : null

  return (
    <div className={clsx(
      'rounded-xl border overflow-hidden',
      mode === 'live' ? 'border-emerald-800/40 bg-emerald-950/20' : 'border-slate-800 bg-surface-800',
    )}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-start gap-3 p-4 text-left hover:bg-slate-800/40 transition-colors"
      >
        {/* Source label */}
        <div className="shrink-0 pt-0.5">
          <div className={clsx('text-[10px] px-2 py-0.5 rounded-full border font-medium', sourceColor)}>
            {record.source}
          </div>
        </div>

        <div className="flex-1 min-w-0">
          {/* Status row */}
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <DataModeBadge mode={mode} />
            <span className="text-[10px] text-slate-600">{record.id}</span>
            <span className={clsx(
              'text-[10px] px-2 py-0.5 rounded-full border',
              record.pipeline_status === 'complete'
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
            )}>
              {record.pipeline_stage.replace(/_/g, ' ')}
            </span>
            {timeAgo && <span className="text-[10px] text-slate-600 ml-auto">{timeAgo}</span>}
          </div>

          <p className="text-xs font-medium text-slate-200 leading-snug">{record.title}</p>
          <p className="text-[11px] text-slate-500 mt-1">{record.evaluation_result}</p>

          {/* Matched signals */}
          {record.matched_signals?.length > 0 && (
            <div className="flex gap-2 mt-1.5 flex-wrap">
              {record.matched_signals.map((m, i) => (
                <div key={i} className="flex items-center gap-1 text-[10px]">
                  <span className="text-slate-500">{m.drug} → {m.disease}</span>
                  {m.score_delta !== 0 && (
                    <span className={clsx(
                      'flex items-center gap-0.5 font-medium',
                      m.score_delta > 0 ? 'text-emerald-400' : 'text-rose-400'
                    )}>
                      {m.score_delta > 0 ? <TrendingUp size={9} /> : <TrendingDown size={9} />}
                      {m.score_delta > 0 ? '+' : ''}{m.score_delta}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="shrink-0 text-slate-600">
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </button>

      {/* Expanded entities */}
      {expanded && (
        <div className="border-t border-slate-800 px-4 pb-4 pt-3 bg-surface-900/30 space-y-3">
          <p className="text-[11px] text-slate-500 font-semibold">Extracted Entities</p>
          <div className="grid grid-cols-2 gap-2 text-[11px]">
            {record.extracted_entities.drugs?.length > 0 && (
              <div>
                <span className="text-slate-500">Drugs: </span>
                <span className="text-brand-300">{record.extracted_entities.drugs.join(', ')}</span>
              </div>
            )}
            {record.extracted_entities.diseases?.length > 0 && (
              <div>
                <span className="text-slate-500">Diseases: </span>
                <span className="text-purple-300">{record.extracted_entities.diseases.join(', ')}</span>
              </div>
            )}
            {record.extracted_entities.mechanisms?.length > 0 && (
              <div>
                <span className="text-slate-500">Mechanisms: </span>
                <span className="text-amber-300">{record.extracted_entities.mechanisms.join(', ')}</span>
              </div>
            )}
            {record.extracted_entities.targets?.length > 0 && (
              <div>
                <span className="text-slate-500">Targets: </span>
                <span className="text-rose-300">{record.extracted_entities.targets.join(', ')}</span>
              </div>
            )}
          </div>
          {/* Real record: show source ID fields if available */}
          {mode === 'live' && (
            <div className="text-[10px] text-slate-600 space-y-0.5 pt-1 border-t border-slate-800/60 mt-2">
              {(record as any).pmid  && <p>PMID: {(record as any).pmid}</p>}
              {(record as any).doi   && <p>DOI: {(record as any).doi}</p>}
              {(record as any).nct_id && <p>NCT: {(record as any).nct_id}</p>}
              {(record as any).source_url && (
                <p>
                  <a href={(record as any).source_url} target="_blank" rel="noopener noreferrer"
                    className="text-brand-400 hover:text-brand-300 transition-colors">
                    View source ↗
                  </a>
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Last run status strip ─────────────────────────────────────────────────────

function LastRunStrip({ run }: { run: IngestionRunStatus }) {
  const timeAgo = run.finished_at
    ? formatDistanceToNow(parseISO(run.finished_at), { addSuffix: true })
    : null

  const statusMeta = {
    complete: { color: 'text-emerald-400', label: 'Completed' },
    partial:  { color: 'text-amber-400',   label: 'Completed with warnings' },
    failed:   { color: 'text-rose-400',    label: 'Failed' },
    running:  { color: 'text-brand-400',   label: 'Running…' },
    pending:  { color: 'text-slate-400',   label: 'Pending' },
  }[run.status] ?? { color: 'text-slate-400', label: run.status }

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 px-3 py-2 rounded-lg bg-slate-800/40 border border-slate-700/40 text-[11px]">
      <div className="flex items-center gap-1.5">
        <Clock size={10} className="text-slate-500" />
        <span className="text-slate-500">Last run:</span>
        <span className="text-slate-300">{timeAgo ?? '—'}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <span className="text-slate-500">Status:</span>
        <span className={clsx('font-medium', statusMeta.color)}>{statusMeta.label}</span>
      </div>
      {run.total_new > 0 && (
        <span className="text-emerald-400">+{run.total_new} new records</span>
      )}
      {run.signals_updated > 0 && (
        <span className="text-brand-400">{run.signals_updated} signal{run.signals_updated !== 1 ? 's' : ''} updated</span>
      )}
      {run.signals_created > 0 && (
        <span className="text-purple-400">{run.signals_created} novel signal{run.signals_created !== 1 ? 's' : ''}</span>
      )}
    </div>
  )
}

// ── Run Ingestion panel ───────────────────────────────────────────────────────

type RunPhase = 'idle' | 'running' | 'done' | 'partial' | 'error'

interface RunIngestionPanelProps {
  onComplete: () => void
  compact?: boolean
}

function RunIngestionPanel({ onComplete, compact = false }: RunIngestionPanelProps) {
  const [phase,  setPhase]  = useState<RunPhase>('idle')
  const [result, setResult] = useState<IngestionRunOut | null>(null)
  const [errMsg, setErrMsg] = useState<string | null>(null)

  const handleRun = async () => {
    setPhase('running')
    setResult(null)
    setErrMsg(null)
    try {
      const run = await ingestionApi.run()
      const resolved: RunPhase =
        run.status === 'complete' ? 'done'
        : run.status === 'partial' ? 'partial'
        : run.status === 'failed'  ? 'error'
        : 'done'
      setPhase(resolved)
      setResult(run)
      onComplete()
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? err?.message ?? 'Ingestion failed'
      setPhase('error')
      setErrMsg(msg)
    }
  }

  // Button label per spec
  const btnLabel =
    phase === 'running' ? 'Ingesting…'
    : phase === 'error'   ? 'Retry Ingestion'
    : phase === 'partial' ? 'Run Live Ingestion'
    : 'Run Live Ingestion'

  const btnClass = clsx(
    'flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all',
    phase === 'running'
      ? 'bg-brand-700/50 text-brand-400 cursor-not-allowed'
      : phase === 'error'
      ? 'bg-rose-700/60 hover:bg-rose-600/70 text-white'
      : 'bg-brand-600 hover:bg-brand-500 text-white shadow-sm shadow-brand-900/40',
  )

  return (
    <div className="space-y-3">
      {/* Run button */}
      <button onClick={handleRun} disabled={phase === 'running'} className={btnClass}>
        {phase === 'running'
          ? <RefreshCw size={14} className="animate-spin" />
          : phase === 'error'
          ? <RotateCw size={14} />
          : <Play size={14} />
        }
        {btnLabel}
      </button>

      {/* Running hint */}
      {phase === 'running' && (
        <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg border border-brand-500/25 bg-brand-500/8 text-[11px] text-brand-300">
          <RefreshCw size={11} className="animate-spin shrink-0 mt-0.5" />
          <span>
            Ingesting research from PubMed, bioRxiv, medRxiv, ClinicalTrials.gov.
            This takes 5–30 seconds. If one source times out the others continue.
            Demo data is unaffected.
          </span>
        </div>
      )}

      {/* Result card */}
      {result && (phase === 'done' || phase === 'partial' || phase === 'error') && (
        <div className={clsx(
          'rounded-xl border p-4 space-y-3 text-xs',
          phase === 'error'   ? 'border-rose-500/30 bg-rose-500/8'
          : phase === 'partial' ? 'border-amber-500/30 bg-amber-500/8'
          : 'border-emerald-500/30 bg-emerald-500/8',
        )}>
          {/* Header row */}
          <div className="flex items-center gap-2">
            {phase === 'error'
              ? <AlertTriangle size={14} className="text-rose-400" />
              : phase === 'partial'
              ? <AlertTriangle size={14} className="text-amber-400" />
              : <CheckCircle2 size={14} className="text-emerald-400" />
            }
            <p className={clsx('font-semibold',
              phase === 'error'   ? 'text-rose-300'
              : phase === 'partial' ? 'text-amber-300'
              : 'text-emerald-300'
            )}>
              {phase === 'error'   ? 'Live ingestion failed'
               : phase === 'partial' ? 'Completed with some source errors'
               : 'Live ingestion completed successfully'}
            </p>
          </div>

          {/* Summary text from backend */}
          <p className="text-slate-400 leading-relaxed">{result.summary}</p>

          {/* Metric counters — only for non-failed runs */}
          {phase !== 'error' && (
            <div className="grid grid-cols-3 gap-2">
              {[
                { label: 'New Records',    value: result.total_new,        color: 'text-emerald-400' },
                { label: 'Signals Updated',value: result.signals_updated,  color: 'text-brand-400'   },
                { label: 'Novel Signals',  value: result.signals_created,  color: 'text-purple-400'  },
              ].map(({ label, value, color }) => (
                <div key={label} className="rounded-lg bg-slate-800/50 border border-slate-700/40 px-3 py-2 text-center">
                  <p className={clsx('text-lg font-bold tabular-nums', color)}>{value}</p>
                  <p className="text-[10px] text-slate-500">{label}</p>
                </div>
              ))}
            </div>
          )}

          {/* Per-source breakdown */}
          {result.source_results?.length > 0 && !compact && (
            <div className="space-y-1.5">
              <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wide">
                Per-source results
              </p>
              {result.source_results.map((sr: any) => {
                const dot =
                  sr.status === 'connected' ? 'bg-emerald-400'
                  : sr.status === 'empty'   ? 'bg-slate-500'
                  : sr.status === 'timeout' ? 'bg-amber-400'
                  : 'bg-rose-400'
                const detail =
                  sr.status === 'connected' || sr.status === 'empty'
                    ? `${sr.records_new} new · ${sr.records_duplicate} dup · ${sr.elapsed_seconds.toFixed(1)}s`
                  : sr.status === 'timeout'
                    ? `Timeout after ${sr.elapsed_seconds.toFixed(1)}s — other sources continued`
                  : `Error — ${sr.errors?.[0] ?? 'unknown'}`
                const statusLabel =
                  sr.status === 'connected' ? 'Connected'
                  : sr.status === 'empty'   ? 'Connected (no new records)'
                  : sr.status === 'timeout' ? 'Timeout'
                  : sr.status === 'error'   ? 'Error'
                  : sr.status

                return (
                  <div key={sr.source} className="flex items-center gap-2 text-[11px]">
                    <div className={clsx('w-2 h-2 rounded-full shrink-0', dot)} />
                    <span className="text-slate-400 w-28 shrink-0 capitalize">{sr.source}</span>
                    <span className={clsx(
                      'shrink-0 text-[10px] font-medium mr-2',
                      sr.status === 'connected' || sr.status === 'empty' ? 'text-emerald-400'
                      : sr.status === 'timeout' ? 'text-amber-400'
                      : 'text-rose-400'
                    )}>{statusLabel}</span>
                    <span className="text-slate-500 truncate">{detail}</span>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* Pure error (no result object) */}
      {phase === 'error' && !result && (
        <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg border border-rose-500/30 bg-rose-500/8 text-[11px] text-rose-300">
          <AlertTriangle size={11} className="shrink-0 mt-0.5" />
          <span>
            {errMsg?.includes('already in progress')
              ? 'An ingestion run is already in progress. Please wait.'
              : `Ingestion error: ${errMsg}. Demo data is unaffected.`}
          </span>
        </div>
      )}
    </div>
  )
}

// ── Main exported component ───────────────────────────────────────────────────

interface ResearchMonitorProps {
  compact?: boolean
  /** Show the Run Live Ingestion button even in compact mode (for Dashboard) */
  showRunButton?: boolean
  /** Called after ingestion completes so parent can refresh other data */
  onIngestionComplete?: () => void
}

export function ResearchMonitor({
  compact = false,
  showRunButton = false,
  onIngestionComplete,
}: ResearchMonitorProps) {
  const [data,    setData]    = useState<ResearchMonitorData | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastRun, setLastRun] = useState<IngestionRunStatus | null>(null)

  const loadMonitor = useCallback(() => {
    setLoading(true)
    researchMonitorApi.get()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const loadLastRun = useCallback(() => {
    ingestionApi.latest()
      .then(run => setLastRun(run))
      .catch(() => {})
  }, [])

  useEffect(() => {
    loadMonitor()
    loadLastRun()
  }, [loadMonitor, loadLastRun])

  const handleIngestionComplete = useCallback(() => {
    // Refresh monitor records + last-run strip
    loadMonitor()
    loadLastRun()
    // Propagate up to Dashboard so it can reload stats/signals/alerts
    onIngestionComplete?.()
  }, [loadMonitor, loadLastRun, onIngestionComplete])

  if (loading) return (
    <div className="flex items-center gap-2 text-xs text-slate-500 py-4">
      <RefreshCw size={12} className="animate-spin" /> Loading research monitor…
    </div>
  )

  const hasLive   = (data as any)?.has_live_data ?? false
  const liveCount = (data as any)?.live_records  ?? 0
  const demoCount = (data as any)?.demo_records  ?? 0
  const showBtn   = showRunButton || !compact

  return (
    <div className="space-y-4">
      {/* Live/Demo status banner */}
      {hasLive ? (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-emerald-500/25 bg-emerald-500/8 text-[11px] text-emerald-400">
          <Wifi size={11} className="shrink-0" />
          <span>
            <strong>{liveCount} live record{liveCount !== 1 ? 's' : ''}</strong> from real ingestion ·{' '}
            {demoCount} demo record{demoCount !== 1 ? 's' : ''}
          </span>
        </div>
      ) : (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-amber-500/20 bg-amber-500/8 text-[11px] text-amber-400">
          <FlaskConical size={11} className="shrink-0" />
          <span>
            <strong>Demo data only</strong> — Click "Run Live Ingestion" to fetch real research records.
          </span>
        </div>
      )}

      {/* Last run status */}
      {lastRun && <LastRunStrip run={lastRun} />}

      {/* Run button — shown in compact mode if showRunButton=true */}
      {showBtn && (
        <RunIngestionPanel
          onComplete={handleIngestionComplete}
          compact={compact}
        />
      )}

      {/* Pipeline stages (full mode only) */}
      {!compact && (data?.pipeline_stages?.length ?? 0) > 0 && data && (
        <div>
          <p className="text-[11px] text-slate-500 font-semibold mb-2 uppercase tracking-wide">
            Ingestion Pipeline Stages
          </p>
          <div className="flex flex-wrap gap-1.5">
            {data.pipeline_stages.map((stage, i) => {
              const Icon = STAGE_ICONS[stage.stage] ?? Database
              return (
                <div key={stage.stage} className="flex items-center gap-1.5 text-[11px] text-slate-400">
                  <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800/60 border border-slate-700/50">
                    <Icon size={10} /><span>{stage.label}</span>
                  </div>
                  {i < data.pipeline_stages.length - 1 && (
                    <span className="text-slate-700">→</span>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Recent records */}
      {data && (
        <div>
          {!compact && (
            <div className="flex items-center justify-between mb-2">
              <p className="text-[11px] text-slate-500 font-semibold uppercase tracking-wide">
                Recent Records ({data.total_records})
              </p>
              <button
                onClick={() => { loadMonitor(); loadLastRun() }}
                className="flex items-center gap-1 text-[11px] text-brand-400 hover:text-brand-300 transition-colors"
              >
                <RefreshCw size={10} /> Refresh
              </button>
            </div>
          )}
          <div className="space-y-2">
            {(compact ? data.recent_records.slice(0, 3) : data.recent_records).map((record) => (
              <RecordRow key={record.id} record={record} />
            ))}
          </div>
        </div>
      )}

      {/* Integration points (full mode only) */}
      {!compact && (data?.integration_points?.length ?? 0) > 0 && data && (
        <div>
          <p className="text-[11px] text-slate-500 font-semibold mb-2 uppercase tracking-wide">
            Live Source Integration
          </p>
          <div className="grid grid-cols-2 gap-2">
            {data.integration_points.map((ip) => (
              <div key={ip.source} className="flex items-center justify-between px-3 py-2 rounded-lg bg-slate-800/50 border border-slate-700/50 text-xs">
                <span className="text-slate-300">{ip.source}</span>
                <span className={clsx(
                  'text-[10px] px-1.5 py-0.5 rounded border',
                  ip.status === 'active'
                    ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
                    : 'bg-slate-700/50 text-slate-500 border-slate-600/40'
                )}>
                  {ip.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
