/**
 * SignalDetailPage — BioArbitrage Signal Investigation
 * =====================================================
 * Fully live-data driven. Every section uses only real ingested evidence.
 * Demo records are excluded from scoring, timelines, graphs, and analysis.
 * Sections:
 *  1. Signal Overview (drug → disease, score, data_source badge)
 *  2. Live Evidence Summary (new — direct below score)
 *  3. Why This Signal? (detection reasoning)
 *  4. Source Contribution (per-source live counts + expandable records)
 *  5. Score Breakdown (5-factor, computed from live evidence)
 *  6. Evidence Timeline (live records only, real dates)
 *  7. Evidence Graph (built from live evidence nodes)
 *  8. Cross-Source Matching
 *  9. On-Demand Search (trigger live ingestion for this drug+disease)
 * 10. Source Traceability (full provenance table)
 * 11. Drug & Disease Profiles
 *
 * No hardcoded drugs, diseases, scores, or graph relationships.
 * No demo evidence mixed with live evidence.
 * Every "View Source" link opens the real original source record.
 */
import { useEffect, useRef, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Pill, Microscope, AlertTriangle, Zap,
  Brain, BarChart2, Clock, Network, Layers, BookOpen,
  FlaskConical, ExternalLink, ChevronDown, ChevronUp,
  CheckCircle2, XCircle, GitMerge, Database, Cpu,
  TrendingUp, Info, Sparkles, Target, Waypoints,
  RefreshCw, Search, Wifi, FileText, Activity,
} from 'lucide-react'
import { clsx } from 'clsx'
import { format, parseISO, formatDistanceToNow } from 'date-fns'

import { Header }           from '../components/Header'
import { Badge, ConfidenceBadge } from '../components/ui/Badge'
import { ScoreBar }         from '../components/ui/ScoreBar'
import { PageLoader }       from '../components/ui/Spinner'
import {
  signalsApi, pipelineApi, sourceBreakdownApi, liveEvidenceApi, ingestionApi,
} from '../api'
import type {
  Signal, Evidence, ExplanationFactor,
  SignalPipelineData, EnrichedScoreBreakdown,
  DetectionRationale, RelationshipGraph,
  SignalSourceBreakdown, LiveEvidenceRecord, LiveEvidenceResponse,
} from '../types'

// ─────────────────────────────────────────────────────────────────────────────
// ATOMS
// ─────────────────────────────────────────────────────────────────────────────

function Section({ id, children, className }: { id: string; children: React.ReactNode; className?: string }) {
  return (
    <section id={id} className={clsx('rounded-xl border border-slate-800 bg-[#181c27] p-5', className)}>
      {children}
    </section>
  )
}

function SectionHead({ icon, title, subtitle, badge }: {
  icon: React.ReactNode; title: string; subtitle?: string; badge?: React.ReactNode
}) {
  return (
    <div className="flex items-start gap-2 mb-4">
      <div className="shrink-0 mt-0.5">{icon}</div>
      <div className="flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <h2 className="text-sm font-semibold text-slate-100">{title}</h2>
          {badge}
        </div>
        {subtitle && <p className="text-[11px] text-slate-500 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  )
}

function Tag({ label, color = 'slate' }: {
  label: string; color?: 'brand'|'purple'|'amber'|'rose'|'emerald'|'blue'|'teal'|'slate'
}) {
  const map: Record<string, string> = {
    brand:   'bg-brand-500/10   text-brand-300   border-brand-500/25',
    purple:  'bg-purple-500/10  text-purple-300  border-purple-500/25',
    amber:   'bg-amber-500/10   text-amber-300   border-amber-500/25',
    rose:    'bg-rose-500/10    text-rose-300    border-rose-500/25',
    emerald: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/25',
    blue:    'bg-blue-500/10    text-blue-300    border-blue-500/25',
    teal:    'bg-teal-500/10    text-teal-300    border-teal-500/25',
    slate:   'bg-slate-700/40   text-slate-300   border-slate-600/30',
  }
  return <span className={clsx('inline-block px-2 py-0.5 rounded-full border text-[11px] font-medium', map[color])}>{label}</span>
}

function KV({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null
  return (
    <div className="flex items-start gap-2 text-xs">
      <span className="text-slate-500 w-28 shrink-0">{label}</span>
      <span className="text-slate-300">{value}</span>
    </div>
  )
}

/** Source colour map used across sections */
const SOURCE_COLORS: Record<string, string> = {
  pubmed:         'text-blue-400   border-blue-500/25   bg-blue-500/8',
  europepmc:      'text-teal-400   border-teal-500/25   bg-teal-500/8',
  uniprot:        'text-violet-400 border-violet-500/25 bg-violet-500/8',
  elsevier:       'text-orange-400 border-orange-500/25 bg-orange-500/8',
  biorxiv:        'text-amber-400  border-amber-500/25  bg-amber-500/8',
  medrxiv:        'text-rose-400   border-rose-500/25   bg-rose-500/8',
  clinicaltrials: 'text-emerald-400 border-emerald-500/25 bg-emerald-500/8',
  unknown:        'text-slate-400  border-slate-600/30  bg-slate-700/20',
}

const SOURCE_DOTS: Record<string, string> = {
  pubmed: 'bg-blue-400', europepmc: 'bg-teal-400', uniprot: 'bg-violet-400',
  elsevier: 'bg-orange-400', biorxiv: 'bg-amber-400', medrxiv: 'bg-rose-400',
  clinicaltrials: 'bg-emerald-400',
}

const EV_TYPE_META: Record<string, { label: string; color: string; dot: string }> = {
  research_paper:     { label: 'Research Paper',      color: 'text-blue-400',    dot: 'bg-blue-400'    },
  preprint:           { label: 'Preprint',             color: 'text-amber-400',   dot: 'bg-amber-400'   },
  clinical_trial:     { label: 'Clinical Trial',       color: 'text-emerald-400', dot: 'bg-emerald-500' },
  review_article:     { label: 'Review Article',       color: 'text-purple-400',  dot: 'bg-purple-400'  },
  meta_analysis:      { label: 'Meta-analysis',        color: 'text-violet-400',  dot: 'bg-violet-400'  },
  protein_annotation: { label: 'Protein / Target',     color: 'text-teal-400',    dot: 'bg-teal-400'    },
}

const EVIDENCE_ROLE: Record<string, string> = {
  pubmed: 'Research Evidence', europepmc: 'Research Evidence',
  elsevier: 'Research Evidence', biorxiv: 'Preprint Evidence',
  medrxiv: 'Medical Preprint', clinicaltrials: 'Clinical Evidence',
  uniprot: 'Molecular / Target Evidence',
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 1 — SIGNAL OVERVIEW
// ─────────────────────────────────────────────────────────────────────────────

function SignalOverview({ signal, liveEv }: { signal: Signal; liveEv: LiveEvidenceResponse | null }) {
  const drugName    = signal.drug?.name    ?? signal.drug_name    ?? '—'
  const diseaseName = signal.disease?.name ?? signal.disease_name ?? '—'
  const score       = signal.evidence_score
  const detectedAt  = signal.detected_at ? format(parseISO(signal.detected_at), 'dd MMM yyyy') : null
  const timeAgo     = signal.detected_at ? formatDistanceToNow(parseISO(signal.detected_at), { addSuffix: true }) : null
  const hasLive     = (liveEv?.has_live_evidence) ?? ((signal.evidence_items ?? []).some(e => !e.is_demo_data))
  const liveCount   = liveEv?.total_live_records ?? (signal.evidence_items ?? []).filter(e => !e.is_demo_data).length

  const scoreColor  = score >= 75 ? 'text-emerald-400' : score >= 55 ? 'text-amber-400' : 'text-rose-400'
  const scoreBorder = score >= 75 ? 'border-emerald-500/40' : score >= 55 ? 'border-amber-500/40' : 'border-rose-500/40'
  const scoreBg     = score >= 75 ? 'bg-emerald-500/8'  : score >= 55 ? 'bg-amber-500/8'  : 'bg-rose-500/8'

  return (
    <Section id="overview">
      <div className="flex items-center gap-2 flex-wrap mb-4">
        <ConfidenceBadge level={signal.confidence_level} />
        {signal.is_novel && <Badge variant="novel">Novel Signal</Badge>}
        {/* Live badge based on actual evidence — never show Demo for live signals */}
        {hasLive ? (
          <span className="flex items-center gap-1 text-[9px] px-1.5 py-0.5 rounded border border-emerald-500/40 bg-emerald-500/10 text-emerald-400 font-semibold uppercase tracking-wide">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shrink-0" />
            LIVE · {liveCount} evidence record{liveCount !== 1 ? 's' : ''}
          </span>
        ) : (
          <span className="text-[9px] px-1.5 py-0.5 rounded border border-slate-600/40 bg-slate-700/30 text-slate-500">
            No live evidence yet — run ingestion below
          </span>
        )}
        <span className="px-2 py-0.5 rounded-full bg-slate-700/50 border border-slate-600/30 text-[10px] text-slate-400">
          Potential Research Signal
        </span>
        {timeAgo && <span className="text-[10px] text-slate-600 ml-auto">Detected {timeAgo}</span>}
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-brand-600/10 border border-brand-500/25">
          <Pill size={16} className="text-brand-400" />
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wide">Drug</p>
            <p className="text-base font-bold text-brand-300 leading-tight">{drugName}</p>
            {signal.drug?.drug_class && <p className="text-[10px] text-brand-500/70">{signal.drug.drug_class}</p>}
          </div>
        </div>
        <div className="flex flex-col items-center">
          <div className="w-px h-3 bg-slate-700" />
          <span className="text-[10px] text-slate-600 px-2 py-0.5 rounded border border-slate-700 bg-slate-800">potential indication</span>
          <div className="w-px h-3 bg-slate-700" />
        </div>
        <div className="flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-purple-600/10 border border-purple-500/25">
          <Microscope size={16} className="text-purple-400" />
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wide">Disease</p>
            <p className="text-base font-bold text-purple-300 leading-tight">{diseaseName}</p>
            {signal.disease?.category && <p className="text-[10px] text-purple-500/70">{signal.disease.category}</p>}
          </div>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-4 mb-4">
        <div className={clsx('flex flex-col items-center justify-center rounded-xl border p-4 min-w-[110px]', scoreBorder, scoreBg)}>
          <span className={clsx('text-4xl font-black tabular-nums', scoreColor)}>{score.toFixed(0)}</span>
          <span className="text-slate-500 text-xs">&nbsp;/ 100</span>
          <span className="text-[10px] text-slate-500 mt-1 text-center leading-tight">Research Prioritization Score</span>
        </div>
        <div className="flex-1 space-y-2">
          <ScoreBar score={score} size="lg" showLabel={false} />
          <div className="flex items-start gap-1.5 px-3 py-2 rounded-lg bg-amber-500/8 border border-amber-500/20">
            <Info size={11} className="text-amber-400 shrink-0 mt-0.5" />
            <p className="text-[10px] text-amber-300/80 leading-relaxed">
              <strong>Research prioritization only — not a clinical probability.</strong>{' '}
              Score reflects research association evidence volume and diversity.
            </p>
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-500">
            {liveEv && Object.keys(liveEv.per_source_counts).length > 0 && (
              <span className="flex items-center gap-1">
                <Wifi size={10} className="text-emerald-400" />
                {Object.keys(liveEv.per_source_counts).join(', ')}
              </span>
            )}
            {detectedAt && <span>Detected: {detectedAt}</span>}
          </div>
        </div>
      </div>

      {signal.summary && (
        <p className="text-xs text-slate-400 leading-relaxed border-t border-slate-800 pt-4">{signal.summary}</p>
      )}

      <div className="flex items-start gap-2 mt-4 px-3 py-2.5 rounded-lg bg-amber-500/8 border border-amber-500/20">
        <AlertTriangle size={13} className="text-amber-400 shrink-0 mt-0.5" />
        <p className="text-[10px] text-amber-400/80 leading-relaxed">
          <strong>Research decision-support only.</strong> This is a <em>potential research signal</em> requiring
          expert validation. NOT a clinical recommendation, diagnosis, or treatment suggestion.
        </p>
      </div>
    </Section>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 2 — LIVE EVIDENCE SUMMARY (new — directly below score)
// Shows every live evidence record with full provenance, authors, DOI/PMID/NCT,
// abstract, View Source link. No demo records. If no live evidence: empty state.
// ─────────────────────────────────────────────────────────────────────────────

function LiveEvidenceCard({ rec, index }: { rec: LiveEvidenceRecord; index: number }) {
  const [open, setOpen] = useState(false)
  const meta = EV_TYPE_META[rec.evidence_type] ?? { label: rec.evidence_type.replace(/_/g, ' '), color: 'text-slate-400', dot: 'bg-slate-500' }
  const srcColor = SOURCE_COLORS[rec.source] ?? SOURCE_COLORS.unknown
  const ref = rec.doi ?? rec.pmid ?? rec.pmcid ?? rec.nct_id

  return (
    <div className={clsx('rounded-xl border overflow-hidden', open ? 'border-slate-600' : 'border-slate-700/50')}>
      <button onClick={() => setOpen(!open)}
        className="w-full flex items-start gap-3 p-4 text-left hover:bg-slate-800/40 transition-colors">
        <span className="text-[10px] text-slate-600 w-5 shrink-0 pt-0.5 tabular-nums">{index + 1}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className={clsx('text-[10px] px-2 py-0.5 rounded-full border font-semibold uppercase tracking-wide shrink-0', srcColor)}>
              {rec.source}
            </span>
            <span className={clsx('text-[10px] font-semibold', meta.color)}>{meta.label}</span>
            {rec.is_open_access && (
              <span className="text-[9px] px-1.5 py-0.5 rounded border border-teal-500/30 bg-teal-500/8 text-teal-400">Open Access</span>
            )}
            {rec.supports_mechanism && (
              <span className="text-[9px] px-1.5 py-0.5 rounded border border-purple-500/30 bg-purple-500/8 text-purple-400">Mechanism</span>
            )}
            {/* Always show LIVE badge — this endpoint only returns live records */}
            <span className="flex items-center gap-0.5 text-[9px] px-1.5 py-0.5 rounded border border-emerald-500/40 bg-emerald-500/8 text-emerald-400 font-semibold ml-auto shrink-0">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />LIVE
            </span>
          </div>
          <p className="text-xs font-medium text-slate-200 leading-snug">{rec.title}</p>
          <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1.5 text-[11px] text-slate-500">
            {rec.publication_date && <span className="flex items-center gap-1"><Clock size={9} />{rec.publication_date}</span>}
            {rec.journal && <span className="italic">{rec.journal}</span>}
            {rec.authors?.[0] && <span>{rec.authors.slice(0, 2).join(', ')}{(rec.authors?.length ?? 0) > 2 ? ' et al.' : ''}</span>}
          </div>
        </div>
        <div className="shrink-0 flex items-center gap-1">
          {open ? <ChevronUp size={13} className="text-slate-500" /> : <ChevronDown size={13} className="text-slate-500" />}
        </div>
      </button>

      {open && (
        <div className="border-t border-slate-700/50 px-4 pb-4 pt-3 space-y-3 bg-slate-900/20">
          {rec.abstract && (
            <div className="text-xs text-slate-400 leading-relaxed border-l-2 border-slate-700 pl-3 max-h-40 overflow-y-auto">
              {rec.abstract}
            </div>
          )}
          {rec.relevance_explanation && (
            <p className="text-[11px] text-slate-500 leading-relaxed">
              <span className="text-slate-400 font-medium">Signal contribution: </span>{rec.relevance_explanation}
            </p>
          )}
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 pt-1">
            {/* Identifiers */}
            {rec.pmid  && <span className="text-[10px] font-mono text-slate-500">PMID: {rec.pmid}</span>}
            {rec.pmcid && <span className="text-[10px] font-mono text-slate-500">PMCID: {rec.pmcid}</span>}
            {rec.doi   && <span className="text-[10px] font-mono text-slate-500">DOI: {rec.doi}</span>}
            {rec.nct_id && <span className="text-[10px] font-mono text-slate-500">NCT: {rec.nct_id}</span>}
            {/* View Source — only real URLs */}
            {rec.source_url && (
              <a href={rec.source_url} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1 text-[11px] text-brand-400 hover:text-brand-300 transition-colors ml-auto">
                <ExternalLink size={10} /> View Source
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function LiveEvidenceSummarySection({ liveEv, signal }: {
  liveEv: LiveEvidenceResponse | null; signal: Signal
}) {
  const [filter, setFilter] = useState<string>('all')
  const [sourceFilter, setSourceFilter] = useState<string>('all')
  const [showAll, setShowAll] = useState(false)
  const PAGE = 10

  if (!liveEv) return null

  const allRecs = liveEv.evidence
  const types   = ['all', ...Array.from(new Set(allRecs.map(r => r.evidence_type)))]
  const sources = ['all', ...Object.keys(liveEv.per_source_counts).sort()]

  const filtered = allRecs.filter(r =>
    (filter === 'all'  || r.evidence_type === filter) &&
    (sourceFilter === 'all' || r.source === sourceFilter)
  )
  const visible = showAll ? filtered : filtered.slice(0, PAGE)

  return (
    <Section id="live-evidence">
      <SectionHead
        icon={<Wifi size={15} className="text-emerald-400" />}
        title="Live Evidence Supporting This Signal"
        subtitle="Real research records fetched from connected sources — no demo data"
        badge={liveEv.has_live_evidence
          ? <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/25 text-emerald-400">{liveEv.total_live_records} live records</span>
          : undefined}
      />

      {!liveEv.has_live_evidence ? (
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-6 text-center">
          <Wifi size={24} className="text-slate-600 mx-auto mb-3" />
          <p className="text-sm text-slate-400 font-medium mb-2">No live research evidence yet</p>
          <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
            {liveEv.message}
          </p>
          <p className="text-[10px] text-slate-600 mt-3">
            Use the "Run Live Research" section below to fetch real evidence from all connected sources.
          </p>
        </div>
      ) : (
        <>
          {/* Per-source summary dots */}
          <div className="flex flex-wrap gap-2 mb-4">
            {Object.entries(liveEv.per_source_counts).map(([src, count]) => {
              const dot = SOURCE_DOTS[src] ?? 'bg-slate-500'
              const color = SOURCE_COLORS[src] ?? SOURCE_COLORS.unknown
              return (
                <span key={src}
                  className={clsx('flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-lg border cursor-pointer transition-colors',
                    sourceFilter === src ? color : 'border-slate-700/50 text-slate-400 hover:border-slate-600')}
                  onClick={() => setSourceFilter(s => s === src ? 'all' : src)}>
                  <span className={clsx('w-2 h-2 rounded-full shrink-0', dot)} />
                  {src} <span className="font-semibold">{count}</span>
                </span>
              )
            })}
          </div>

          {/* Sources without evidence */}
          {liveEv.sources_without_evidence.length > 0 && (
            <div className="mb-4 px-3 py-2 rounded-lg bg-slate-800/40 border border-slate-700/40">
              <p className="text-[11px] text-slate-500">
                No relevant live evidence found from:{' '}
                <span className="text-slate-400">{liveEv.sources_without_evidence.join(', ')}</span>
              </p>
            </div>
          )}

          {/* Type filter pills */}
          <div className="flex flex-wrap gap-1.5 mb-4">
            {types.map(t => (
              <button key={t} onClick={() => setFilter(t)}
                className={clsx('px-2.5 py-1 rounded-lg text-[11px] border transition-colors',
                  filter === t ? 'bg-brand-600/20 border-brand-500/40 text-brand-300' : 'border-slate-700/50 text-slate-500 hover:text-slate-300')}>
                {t === 'all' ? 'All types' : (EV_TYPE_META[t]?.label ?? t.replace(/_/g, ' '))}
                {t !== 'all' && ` (${liveEv.per_type_counts[t] ?? 0})`}
              </button>
            ))}
          </div>

          <div className="space-y-2">
            {visible.map((rec, i) => <LiveEvidenceCard key={rec.id} rec={rec} index={i} />)}
          </div>

          {filtered.length > PAGE && (
            <button onClick={() => setShowAll(v => !v)}
              className="mt-3 w-full text-xs text-slate-500 hover:text-slate-300 transition-colors py-2 rounded-lg border border-slate-700/50 hover:border-slate-600">
              {showAll ? 'Show less' : `Show all ${filtered.length} records`}
            </button>
          )}
        </>
      )}

      <p className="text-[10px] text-slate-600 mt-3">{liveEv.disclaimer}</p>
    </Section>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 3 — WHY THIS SIGNAL?
// ─────────────────────────────────────────────────────────────────────────────

const FLOW_STEPS = [
  { key: 'observation',  label: 'Research Observation',      icon: Database,  color: 'text-blue-400',    border: 'border-blue-500/30',    bg: 'bg-blue-500/8'    },
  { key: 'mechanism',    label: 'Mechanism Connection',      icon: GitMerge,  color: 'text-purple-400',  border: 'border-purple-500/30',  bg: 'bg-purple-500/8'  },
  { key: 'evidence',     label: 'Supporting Evidence',       icon: BookOpen,  color: 'text-amber-400',   border: 'border-amber-500/30',   bg: 'bg-amber-500/8'   },
  { key: 'confirmation', label: 'Cross-Source Confirmation', icon: Layers,    color: 'text-emerald-400', border: 'border-emerald-500/30', bg: 'bg-emerald-500/8' },
  { key: 'signal',       label: 'Signal Generated',          icon: Zap,       color: 'text-brand-400',   border: 'border-brand-500/30',   bg: 'bg-brand-500/8'   },
] as const

function WhyThisSignalSection({ signal, pipelineData, liveEv }: {
  signal: Signal; pipelineData: SignalPipelineData | null; liveEv: LiveEvidenceResponse | null
}) {
  const drugName    = signal.drug?.name    ?? signal.drug_name    ?? '—'
  const diseaseName = signal.disease?.name ?? signal.disease_name ?? '—'
  const rationale   = pipelineData?.detection_rationale ?? null
  const liveItems   = liveEv?.evidence ?? (signal.evidence_items ?? []).filter(e => !e.is_demo_data)
  const evCount     = liveItems.length
  const trialCount  = liveItems.filter(e => e.evidence_type === 'clinical_trial').length
  const sources     = Array.from(new Set(liveItems.map(e => (e as any).source || (e as any).data_source || 'unknown')))
  const strength    = evCount >= 5 ? 'strong' : evCount >= 2 ? 'moderate' : 'preliminary'

  const content = {
    observation: `${evCount} live evidence record${evCount !== 1 ? 's' : ''} co-mentioning "${drugName}" and "${diseaseName}" indexed from ${sources.length || signal.source_count} independent source${(sources.length || signal.source_count) !== 1 ? 's' : ''}.`,
    mechanism: rationale?.mechanism_summary ?? signal.biological_mechanism ?? `${drugName}'s known molecular targets overlap with pathways implicated in ${diseaseName}.`,
    evidence: `${evCount} live record${evCount !== 1 ? 's' : ''} support the association.${trialCount > 0 ? ` ${trialCount} clinical trial record${trialCount !== 1 ? 's' : ''} included.` : ' No clinical trial records currently indexed.'}`,
    confirmation: `${strength} cross-source support across ${sources.length || signal.source_count} source${(sources.length || signal.source_count) !== 1 ? 's' : ''}.${rationale?.pathway_overlap?.length ? ` Pathway overlap: ${rationale.pathway_overlap.slice(0, 3).join(', ')}.` : ''}`,
    signal: `Evidence score ${signal.evidence_score.toFixed(0)}/100 (${signal.confidence_level} confidence). Potential research signal — requires expert validation.`,
  }

  return (
    <Section id="why">
      <SectionHead icon={<Brain size={15} className="text-brand-400" />}
        title="Why This Signal?"
        subtitle={`How BioArbitrage connected ${drugName} to ${diseaseName} using live evidence`} />

      {/* Explanation factors */}
      {(signal.explanation_factors?.length ?? 0) > 0 && (
        <div className="mb-5 space-y-2">
          {signal.explanation_factors.map((f: ExplanationFactor, i: number) => {
            const styles: Record<string, string> = {
              strong: 'border-emerald-500/30 bg-emerald-500/8 text-emerald-300',
              moderate: 'border-amber-500/30 bg-amber-500/8 text-amber-300',
              weak: 'border-slate-600/30 bg-slate-700/20 text-slate-400',
              negative: 'border-rose-500/30 bg-rose-500/8 text-rose-300',
              supportive: 'border-blue-500/30 bg-blue-500/8 text-blue-300',
              complex: 'border-violet-500/30 bg-violet-500/8 text-violet-300',
            }
            return (
              <div key={i} className={clsx('flex items-start gap-3 rounded-lg border px-4 py-3', styles[f.strength] ?? styles.weak)}>
                <div className="flex-1">
                  <p className="text-xs font-semibold">{f.factor}</p>
                  <p className="text-xs mt-0.5 opacity-80 leading-relaxed">{f.detail}</p>
                </div>
                <span className="text-[9px] font-semibold uppercase tracking-wide opacity-60 shrink-0 pt-0.5">{f.strength}</span>
              </div>
            )
          })}
        </div>
      )}

      <div className="space-y-0">
        {FLOW_STEPS.map((step, i) => {
          const Icon = step.icon
          const isLast = i === FLOW_STEPS.length - 1
          return (
            <div key={step.key} className="flex gap-3">
              <div className="flex flex-col items-center shrink-0 w-8">
                <div className={clsx('flex items-center justify-center w-8 h-8 rounded-full border-2 shrink-0', step.bg, step.border)}>
                  <Icon size={13} className={step.color} />
                </div>
                {!isLast && <div className="w-px flex-1 min-h-[16px] bg-slate-700/60 my-1" />}
              </div>
              <div className={clsx('flex-1 pb-4', isLast && 'pb-0')}>
                <p className={clsx('text-[11px] font-semibold uppercase tracking-wide mb-1', step.color)}>{step.label}</p>
                <p className="text-xs text-slate-300 leading-relaxed">{content[step.key]}</p>
              </div>
            </div>
          )
        })}
      </div>

      {signal.ai_explanation && (
        <div className="mt-5 rounded-lg border border-brand-500/20 bg-brand-500/5 p-4">
          <div className="flex items-center gap-2 mb-2">
            <Brain size={12} className="text-brand-400" />
            <p className="text-[11px] font-semibold text-brand-300">AI Research Analysis</p>
            <span className="text-[9px] px-1.5 py-0.5 rounded border border-slate-600/40 bg-slate-700/50 text-slate-500">
              {pipelineData?.ai_backend ?? 'heuristic'} · based on live evidence
            </span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">{signal.ai_explanation}</p>
        </div>
      )}

      {rationale?.research_gaps && rationale.research_gaps.length > 0 && (
        <div className="mt-4 space-y-1.5">
          <p className="text-[11px] font-semibold text-rose-400 flex items-center gap-1.5"><XCircle size={11} />Research Gaps</p>
          {rationale.research_gaps.map((gap, i) => (
            <div key={i} className="flex items-start gap-2 text-xs text-slate-400">
              <span className="text-rose-500 shrink-0 mt-0.5">·</span>{gap}
            </div>
          ))}
        </div>
      )}
    </Section>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 4 — SOURCE CONTRIBUTION BREAKDOWN
// ─────────────────────────────────────────────────────────────────────────────

function SourceBreakdownSection({ breakdown }: { breakdown: SignalSourceBreakdown | null }) {
  const [expanded, setExpanded] = useState<string | null>(null)
  if (!breakdown) return null

  const sb = breakdown.source_breakdown
  // Only show sources that have live evidence — never render demo-only rows
  const sources = Object.keys(sb)
    .filter(s => s !== 'demo' && sb[s].live > 0)
    .sort((a, b) => sb[b].live - sb[a].live)
  const scoreFromEvidence = breakdown.score_breakdown_from_evidence

  return (
    <Section id="sources-breakdown">
      <SectionHead
        icon={<Layers size={15} className="text-emerald-400" />}
        title="Source Contribution"
        subtitle="Exact research sources supporting this signal — traceable to individual records"
      />

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
        {[
          { label: 'Total Records',       value: breakdown.total_evidence_records,   color: 'text-slate-300' },
          { label: 'Unique (Deduped)',    value: breakdown.unique_evidence_records,  color: 'text-brand-400' },
          { label: 'Live Records',        value: breakdown.unique_live_records,      color: 'text-emerald-400' },
          { label: 'Independent Sources', value: sources.length, color: 'text-amber-400' },
        ].map(({ label, value, color }) => (
          <div key={label} className="rounded-lg bg-slate-800/50 border border-slate-700/40 px-3 py-2 text-center">
            <p className={clsx('text-xl font-bold tabular-nums', color)}>{value}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {breakdown.duplicates_removed > 0 && (
        <div className="flex items-start gap-2 mb-4 px-3 py-2 rounded-lg bg-brand-500/8 border border-brand-500/20">
          <Info size={12} className="text-brand-400 shrink-0 mt-0.5" />
          <p className="text-[11px] text-brand-300">
            {breakdown.duplicates_removed} cross-source duplicate{breakdown.duplicates_removed !== 1 ? 's' : ''} removed.
            Same article across databases counted once for scoring; provenance preserved.
          </p>
        </div>
      )}

      <div className="mb-5 px-3 py-2.5 rounded-lg bg-slate-800/40 border border-slate-700/40">
        <p className="text-[11px] text-slate-400 leading-relaxed">{breakdown.score_explanation}</p>
      </div>

      {/* Live sources only */}
      <div className="space-y-2">
        {sources.map(src => {
          const data = sb[src]
          const isDemo = src === 'demo'
          const colorCls = SOURCE_COLORS[src] ?? SOURCE_COLORS.unknown
          const role = EVIDENCE_ROLE[src] ?? 'Research Evidence'
          const isExp = expanded === src

          return (
            <div key={src} className={clsx('rounded-xl border overflow-hidden', isDemo ? 'border-slate-800/40 opacity-50' : 'border-slate-700/50')}>
              <button onClick={() => setExpanded(isExp ? null : src)}
                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-slate-800/30 transition-colors">
                <span className={clsx('text-[10px] px-2 py-0.5 rounded-full border font-semibold uppercase tracking-wide shrink-0', colorCls)}>{src}</span>
                <span className="flex-1 text-xs font-medium text-slate-300">{role}</span>
                <div className="flex items-center gap-4 text-[11px] shrink-0">
                  {data.live > 0 && <span className="text-emerald-400 font-medium">{data.live} live</span>}
                  {isDemo && data.demo > 0 && <span className="text-slate-500 text-[10px]">{data.demo} demo (not scored)</span>}
                  <span className="text-slate-500">{data.count} total</span>
                  {isExp ? <ChevronUp size={13} className="text-slate-500" /> : <ChevronDown size={13} className="text-slate-500" />}
                </div>
              </button>

              {isExp && (
                <div className="border-t border-slate-800/60 bg-slate-900/20 px-4 pb-4 pt-3 space-y-2">
                  {/* Only live records rendered — demo records completely excluded */}
                  {data.records.filter((r: any) => !r.is_demo_data).length === 0 ? (
                    <p className="text-xs text-slate-600 py-2">No live records from this source for this signal.</p>
                  ) : (
                    data.records.filter((r: any) => !r.is_demo_data).map((rec: any) => (
                      <div key={rec.id} className="rounded-lg border border-slate-700/40 bg-slate-800/40 p-3">
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          <span className="flex items-center gap-0.5 text-[9px] px-1.5 py-0.5 rounded border border-emerald-500/40 bg-emerald-500/8 text-emerald-400 font-semibold">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />LIVE
                          </span>
                          <span className="text-[10px] text-slate-500">{rec.evidence_type?.replace(/_/g, ' ')}</span>
                          {rec.publication_date && <span className="text-[10px] text-slate-600">{rec.publication_date}</span>}
                        </div>
                        <p className="text-xs font-medium text-slate-200 leading-snug">{rec.title}</p>
                        <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1.5 text-[10px]">
                          {rec.pmid   && <span className="font-mono text-slate-500">PMID: {rec.pmid}</span>}
                          {rec.pmcid  && <span className="font-mono text-slate-500">PMCID: {rec.pmcid}</span>}
                          {rec.doi    && <span className="font-mono text-slate-500">DOI: {rec.doi}</span>}
                          {rec.nct_id && <span className="font-mono text-slate-500">NCT: {rec.nct_id}</span>}
                          {rec.source_url && (
                            <a href={rec.source_url} target="_blank" rel="noopener noreferrer"
                              className="text-brand-400 hover:text-brand-300 flex items-center gap-0.5 ml-auto">
                              <ExternalLink size={9} />View source
                            </a>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Score computed from evidence */}
      {scoreFromEvidence && (
        <div className="mt-5 rounded-xl border border-slate-700/50 bg-slate-800/30 p-4">
          <p className="text-[11px] text-slate-400 font-semibold mb-3 uppercase tracking-wide">Score From This Evidence</p>
          <div className="space-y-2">
            {(['research_evidence','clinical_evidence','mechanism_match','independent_sources','recency'] as const).map(key => {
              const factor = scoreFromEvidence[key]
              if (!factor) return null
              const pct = Math.min((factor.score / factor.max) * 100, 100)
              return (
                <div key={key} className="flex items-center gap-3">
                  <span className="text-xs text-slate-400 w-44 shrink-0">{factor.label}</span>
                  <div className="flex-1 h-1.5 rounded-full bg-slate-700/60">
                    <div className="h-1.5 rounded-full bg-brand-500 transition-all" style={{ width: `${pct}%` }} />
                  </div>
                  <span className="text-xs font-mono text-slate-300 w-16 text-right">
                    {factor.score}/{factor.max}
                    {factor.items != null && <span className="text-slate-600 text-[9px] ml-1">({factor.items})</span>}
                  </span>
                </div>
              )
            })}
          </div>
          <div className="border-t border-slate-700/60 mt-3 pt-3 flex items-center justify-between">
            <p className="text-xs text-slate-400">Total (Experimental Prioritization Score)</p>
            <p className="text-lg font-bold text-brand-400">{scoreFromEvidence.total?.score ?? '—'}<span className="text-slate-500 text-sm font-normal">/100</span></p>
          </div>
          <p className="text-[10px] text-slate-600 mt-2">Cross-source dedup applied. Demo excluded. Not clinical probability.</p>
        </div>
      )}
      <p className="text-[10px] text-slate-600 mt-3">{breakdown.disclaimer}</p>
    </Section>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 5 — SCORE BREAKDOWN
// ─────────────────────────────────────────────────────────────────────────────

const SCORE_FACTORS = [
  { key: 'research_evidence',   label: 'Research Evidence',   max: 24, icon: BookOpen,     bar: 'bg-blue-500'    },
  { key: 'clinical_evidence',   label: 'Clinical Evidence',   max: 20, icon: FlaskConical,  bar: 'bg-emerald-500' },
  { key: 'mechanism_match',     label: 'Mechanism Match',     max: 20, icon: GitMerge,      bar: 'bg-purple-500'  },
  { key: 'independent_sources', label: 'Independent Sources', max: 12, icon: Layers,        bar: 'bg-amber-500'   },
  { key: 'recency',             label: 'Recency (post-2020)', max: 8,  icon: Clock,         bar: 'bg-rose-500'    },
] as const

function ScoreBreakdownSection({ pipelineData, signal, breakdown }: {
  pipelineData: SignalPipelineData | null; signal: Signal; breakdown: SignalSourceBreakdown | null
}) {
  // Prefer the breakdown endpoint's score (computed from current evidence) over pipeline
  const enriched = breakdown?.score_breakdown_from_evidence ?? pipelineData?.enriched_score_breakdown
  const total    = signal.evidence_score

  const rows = SCORE_FACTORS.map(f => {
    const ef = enriched?.[f.key as keyof EnrichedScoreBreakdown]
    if (ef && typeof ef === 'object' && 'score' in ef) return { ...f, score: ef.score as number, items: (ef as any).items }
    return { ...f, score: 0, items: null }
  })

  return (
    <Section id="score">
      <SectionHead
        icon={<BarChart2 size={15} className="text-amber-400" />}
        title="Evidence Score Breakdown"
        badge={<span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/25 text-amber-400">Experimental Research Prioritization</span>}
      />
      <div className="flex items-start gap-2 mb-5 px-3 py-2 rounded-lg bg-slate-800/60 border border-slate-700/50">
        <Info size={11} className="text-slate-500 shrink-0 mt-0.5" />
        <p className="text-[10px] text-slate-500 leading-relaxed">
          Score computed from 5 factors using <strong className="text-slate-400">live evidence only</strong>.
          Demo records are excluded. Not clinical probability. Max 100.
        </p>
      </div>
      <div className="space-y-3">
        {rows.map(row => {
          const Icon = row.icon
          const pct  = Math.min((row.score / row.max) * 100, 100)
          return (
            <div key={row.key} className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 w-44 shrink-0">
                <Icon size={12} className="text-slate-400" />
                <span className="text-xs text-slate-300">{row.label}</span>
              </div>
              <div className="flex-1 h-2 rounded-full bg-slate-700/60">
                <div className={clsx('h-2 rounded-full transition-all duration-500', row.bar)} style={{ width: `${pct}%` }} />
              </div>
              <div className="flex items-baseline gap-1 w-20 justify-end shrink-0">
                <span className="text-sm font-bold tabular-nums text-slate-200">{row.score}</span>
                <span className="text-[10px] text-slate-500">/ {row.max}</span>
                {row.items != null && <span className="text-[9px] text-slate-600 ml-1">({row.items})</span>}
              </div>
            </div>
          )
        })}
      </div>
      <div className="border-t border-slate-700/60 mt-4 pt-4 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-200">Total</p>
          <p className="text-[10px] text-slate-500">Experimental · Live Evidence Only</p>
        </div>
        <div className="flex items-baseline gap-1">
          <span className={clsx('text-4xl font-black tabular-nums',
            total >= 75 ? 'text-emerald-400' : total >= 55 ? 'text-amber-400' : 'text-rose-400')}>{total.toFixed(0)}</span>
          <span className="text-slate-500 text-sm">/ 100</span>
        </div>
      </div>
    </Section>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 6 — EVIDENCE TIMELINE
// Live records only, sorted newest first. No demo records shown.
// ─────────────────────────────────────────────────────────────────────────────

function EvidenceTimelineItem({ ev, isLast }: { ev: LiveEvidenceRecord; isLast: boolean }) {
  const [open, setOpen] = useState(false)
  const meta = EV_TYPE_META[ev.evidence_type] ?? { label: ev.evidence_type.replace(/_/g, ' '), color: 'text-slate-400', dot: 'bg-slate-500' }

  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center shrink-0 w-4">
        <div className={clsx('w-3 h-3 rounded-full shrink-0 mt-1 ring-2 ring-[#181c27]', meta.dot)} />
        {!isLast && <div className="w-px flex-1 min-h-[20px] bg-slate-700/50 mt-1" />}
      </div>
      <div className={clsx('flex-1 rounded-xl border bg-slate-800/30 mb-4 overflow-hidden', open ? 'border-slate-600' : 'border-slate-800')}>
        <button onClick={() => setOpen(!open)}
          className="w-full flex items-start gap-3 p-4 text-left hover:bg-slate-800/50 transition-colors">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1.5">
              <span className={clsx('text-[10px] font-semibold', meta.color)}>{meta.label}</span>
              <span className={clsx('text-[10px] px-1.5 py-0.5 rounded-full border font-medium shrink-0',
                SOURCE_COLORS[ev.source] ?? SOURCE_COLORS.unknown)}>{ev.source}</span>
              {ev.is_open_access && <span className="text-[9px] text-teal-400 border border-teal-500/30 bg-teal-500/8 px-1.5 py-0.5 rounded">OA</span>}
              {ev.supports_mechanism && <span className="text-[9px] text-purple-400 border border-purple-500/30 bg-purple-500/8 px-1.5 py-0.5 rounded">Mechanism</span>}
            </div>
            <p className="text-xs font-medium text-slate-200 leading-snug">{ev.title}</p>
            <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1.5 text-[11px] text-slate-500">
              {ev.publication_date && <span className="flex items-center gap-1"><Clock size={9} />{ev.publication_date}</span>}
              {ev.journal && <span className="italic">{ev.journal}</span>}
              {ev.authors?.[0] && <span>{ev.authors.slice(0, 2).join(', ')}{(ev.authors?.length ?? 0) > 2 ? ' et al.' : ''}</span>}
            </div>
            {ev.relevance_explanation && (
              <p className="text-[11px] text-slate-500 mt-1.5 leading-relaxed">
                <span className="text-slate-400 font-medium">Contribution: </span>{ev.relevance_explanation}
              </p>
            )}
          </div>
          <div className="shrink-0 flex items-center gap-2">
            <div className="text-center">
              <span className="text-xs font-bold text-slate-300 tabular-nums">{Math.round((ev.relevance_score ?? 0) * 100)}</span>
              <p className="text-[9px] text-slate-600">rel.</p>
            </div>
            {open ? <ChevronUp size={13} className="text-slate-500" /> : <ChevronDown size={13} className="text-slate-500" />}
          </div>
        </button>
        {open && (
          <div className="border-t border-slate-700/50 px-4 pb-4 pt-3 space-y-3">
            {ev.journal && <p className="text-[11px] text-slate-500 italic">{ev.journal}</p>}
            {ev.abstract && (
              <div className="text-xs text-slate-500 leading-relaxed border-l-2 border-slate-700 pl-3 max-h-40 overflow-y-auto">{ev.abstract}</div>
            )}
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 pt-1">
              {ev.pmid   && <span className="text-[10px] font-mono text-slate-500">PMID: {ev.pmid}</span>}
              {ev.pmcid  && <span className="text-[10px] font-mono text-slate-500">PMCID: {ev.pmcid}</span>}
              {ev.doi    && <span className="text-[10px] font-mono text-slate-500">DOI: {ev.doi}</span>}
              {ev.nct_id && <span className="text-[10px] font-mono text-slate-500">NCT: {ev.nct_id}</span>}
              {ev.source_url && (
                <a href={ev.source_url} target="_blank" rel="noopener noreferrer"
                  className="flex items-center gap-1 text-[11px] text-brand-400 hover:text-brand-300 transition-colors ml-auto">
                  <ExternalLink size={10} />View Source
                </a>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function EvidenceTimelineSection({ liveEv, signal }: { liveEv: LiveEvidenceResponse | null; signal: Signal }) {
  // Use live evidence from the dedicated endpoint; fall back to signal.evidence_items filtered to live
  const rawItems: LiveEvidenceRecord[] = liveEv?.evidence ?? []
  const fallback = (signal.evidence_items ?? [])
    .filter(e => !e.is_demo_data)
    .map(e => ({
      id: e.id, source: e.data_source || e.source_name || 'unknown',
      source_url: e.source_url, title: e.title, authors: e.authors ?? [],
      publication_date: e.publication_date, journal: e.journal, abstract: e.abstract,
      doi: e.doi, pmid: e.pmid, pmcid: (e as any).pmcid ?? null, nct_id: e.nct_id,
      evidence_type: e.evidence_type, is_open_access: false,
      relevance_score: e.relevance_score, relevance_explanation: e.relevance_explanation,
      supports_mechanism: e.supports_mechanism, is_demo_data: false as const,
    }))
  const items = (rawItems.length > 0 ? rawItems : fallback)
    .slice().sort((a, b) => (b.publication_date ?? '').localeCompare(a.publication_date ?? ''))

  return (
    <Section id="timeline">
      <SectionHead
        icon={<Clock size={15} className="text-blue-400" />}
        title="Evidence Timeline"
        subtitle="Live research records — sorted newest first. Demo records excluded."
        badge={<span className="text-[10px] text-slate-500">{items.length} live record{items.length !== 1 ? 's' : ''}</span>}
      />
      {items.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-800/20 p-6 text-center">
          <Clock size={22} className="text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-400 mb-1">No live evidence records yet</p>
          <p className="text-xs text-slate-500">Run live ingestion to populate this timeline with real research dates.</p>
        </div>
      ) : (
        items.map((ev, i) => <EvidenceTimelineItem key={ev.id} ev={ev} isLast={i === items.length - 1} />)
      )}
    </Section>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 7 — EVIDENCE GRAPH
// Nodes built exclusively from live ingested evidence. No hardcoded relationships.
// ─────────────────────────────────────────────────────────────────────────────

function GNode({ icon, label, sub, colorClass }: { icon: React.ReactNode; label: string; sub?: string; colorClass: string }) {
  return (
    <div className={clsx('flex items-center gap-2.5 px-3 py-2 rounded-xl border text-xs font-medium', colorClass)}>
      {icon}
      <div><p className="font-semibold">{label}</p>{sub && <p className="text-[10px] opacity-60 font-normal">{sub}</p>}</div>
    </div>
  )
}

function GConnector({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center py-0.5 my-0.5">
      <div className="w-px h-4 bg-slate-700" />
      <span className="text-[10px] text-slate-600 italic px-2">{label}</span>
      <div className="w-px h-4 bg-slate-700" />
    </div>
  )
}

function EvidenceGraphSection({ signal, liveEv }: { signal: Signal; liveEv: LiveEvidenceResponse | null }) {
  const drugName    = signal.drug?.name    ?? signal.drug_name    ?? '—'
  const diseaseName = signal.disease?.name ?? signal.disease_name ?? '—'

  // Build graph from live evidence + drug/disease profiles
  const targets  = (signal.drug?.molecular_targets  ?? []).slice(0, 4)
  const pathways = (signal.disease?.affected_pathways ?? []).slice(0, 4)
  const liveRecs = liveEv?.evidence ?? (signal.evidence_items ?? []).filter(e => !e.is_demo_data).map(e => ({
    id: e.id, title: e.title, evidence_type: e.evidence_type, source_url: e.source_url,
    source: (e as any).data_source || e.source_name || 'unknown', is_demo_data: false as const,
  } as any))

  // Group live evidence by type for graph nodes
  const paperNodes = liveRecs.filter(e => ['research_paper','preprint','review_article'].includes(e.evidence_type)).slice(0, 3)
  const trialNodes = liveRecs.filter(e => e.evidence_type === 'clinical_trial').slice(0, 2)
  const proteinNodes = liveRecs.filter(e => e.evidence_type === 'protein_annotation').slice(0, 2)

  const hasLiveNodes = liveRecs.length > 0

  return (
    <Section id="graph">
      <SectionHead
        icon={<Network size={15} className="text-purple-400" />}
        title="Evidence Graph"
        subtitle="Biological pathway — evidence nodes built from live ingested records only"
      />

      {!hasLiveNodes && (
        <div className="rounded-xl border border-slate-800 bg-slate-800/20 p-5 text-center mb-4">
          <Network size={22} className="text-slate-600 mx-auto mb-2" />
          <p className="text-xs text-slate-500">No live evidence nodes yet — run ingestion to populate this graph.</p>
        </div>
      )}

      <div className="flex flex-col items-start max-w-lg gap-0">
        <GNode icon={<Pill size={13} className="text-brand-400" />}
          label={drugName} sub={signal.drug?.drug_class ?? 'Drug'}
          colorClass="bg-brand-500/10 border-brand-500/30 text-brand-300" />

        {targets.length > 0 && <><GConnector label="acts on molecular targets" />
          <div className="flex flex-wrap gap-2 pl-4">
            {targets.map((t, i) => (
              <div key={i} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-rose-500/25 bg-rose-500/8 text-[11px] text-rose-300">
                <Target size={10} className="text-rose-400" /><span className="font-medium">{t}</span>
              </div>
            ))}
          </div>
        </>}

        {pathways.length > 0 && <><GConnector label="modulates pathways" />
          <div className="flex flex-wrap gap-2 pl-4">
            {pathways.map((p, i) => (
              <div key={i} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-amber-500/25 bg-amber-500/8 text-[11px] text-amber-300">
                <Waypoints size={10} className="text-amber-400" /><span className="font-medium">{p}</span>
              </div>
            ))}
          </div>
        </>}

        <GConnector label="pathway dysregulated in" />
        <GNode icon={<Microscope size={13} className="text-purple-400" />}
          label={diseaseName} sub={signal.disease?.category ?? 'Disease'}
          colorClass="bg-purple-500/10 border-purple-500/30 text-purple-300" />

        {paperNodes.length > 0 && <><GConnector label="supported by live research evidence" />
          <div className="space-y-1.5 pl-4 w-full">
            {paperNodes.map((e, i) => (
              <div key={i} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-blue-500/25 bg-blue-500/8 text-[11px] text-blue-300">
                <BookOpen size={10} className="text-blue-400 shrink-0" />
                <span className="truncate flex-1">{e.title?.slice(0, 55)}{(e.title?.length ?? 0) > 55 ? '…' : ''}</span>
                {e.source_url && (
                  <a href={e.source_url} target="_blank" rel="noopener noreferrer" className="shrink-0 text-brand-400 hover:text-brand-300">
                    <ExternalLink size={9} />
                  </a>
                )}
              </div>
            ))}
          </div>
        </>}

        {trialNodes.length > 0 && <><GConnector label="tested in clinical trials" />
          <div className="space-y-1.5 pl-4 w-full">
            {trialNodes.map((e, i) => (
              <div key={i} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-emerald-500/25 bg-emerald-500/8 text-[11px] text-emerald-300">
                <Activity size={10} className="text-emerald-400 shrink-0" />
                <span className="truncate flex-1">{e.title?.slice(0, 55)}{(e.title?.length ?? 0) > 55 ? '…' : ''}</span>
                {e.source_url && (
                  <a href={e.source_url} target="_blank" rel="noopener noreferrer" className="shrink-0 text-brand-400 hover:text-brand-300">
                    <ExternalLink size={9} />
                  </a>
                )}
              </div>
            ))}
          </div>
        </>}

        {proteinNodes.length > 0 && <><GConnector label="protein / target evidence" />
          <div className="space-y-1.5 pl-4 w-full">
            {proteinNodes.map((e, i) => (
              <div key={i} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-violet-500/25 bg-violet-500/8 text-[11px] text-violet-300">
                <Cpu size={10} className="text-violet-400 shrink-0" />
                <span className="truncate flex-1">{e.title?.slice(0, 55)}{(e.title?.length ?? 0) > 55 ? '…' : ''}</span>
              </div>
            ))}
          </div>
        </>}

        <GConnector label="generates" />
        <GNode icon={<Zap size={13} className="text-brand-400" />}
          label="Potential Repurposing Signal"
          sub={`${signal.evidence_score.toFixed(0)}/100 · ${signal.confidence_level} · requires expert validation`}
          colorClass="bg-brand-600/15 border-brand-500/40 text-brand-200" />
      </div>
      <p className="text-[10px] text-slate-600 mt-4">
        Evidence nodes represent live ingested records. Clicking ExternalLink icons opens the original source.
        {!hasLiveNodes && ' Run ingestion to populate with real evidence.'}
      </p>
    </Section>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 8 — CROSS-SOURCE MATCHING
// ─────────────────────────────────────────────────────────────────────────────

function CrossSourceSection({ signal, liveEv, breakdown }: {
  signal: Signal; liveEv: LiveEvidenceResponse | null; breakdown: SignalSourceBreakdown | null
}) {
  const liveRecs = liveEv?.evidence ?? []
  const drugName  = signal.drug?.name ?? signal.drug_name ?? '—'
  const disName   = signal.disease?.name ?? signal.disease_name ?? '—'

  const byType: Record<string, LiveEvidenceRecord[]> = {}
  liveRecs.forEach(e => { if (!byType[e.evidence_type]) byType[e.evidence_type] = []; byType[e.evidence_type].push(e) })

  const sourceCount = Object.keys(liveEv?.per_source_counts ?? {}).length
  const strength = sourceCount >= 4 ? 'strong' : sourceCount >= 2 ? 'moderate' : 'weak'
  const strengthStyle = { strong: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/25', moderate: 'text-amber-400 bg-amber-500/10 border-amber-500/25', weak: 'text-rose-400 bg-rose-500/10 border-rose-500/25' }[strength]
  const crossDupes = breakdown?.cross_source_duplicates ?? []

  return (
    <Section id="matching">
      <SectionHead icon={<Layers size={15} className="text-emerald-400" />}
        title="Cross-Source Matching"
        subtitle="How BioArbitrage corroborated evidence across independent live sources" />

      {liveRecs.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-800/20 p-5 text-center">
          <p className="text-xs text-slate-500">No live evidence available for cross-source analysis.</p>
        </div>
      ) : (
        <>
          <div className="space-y-3 mb-5">
            {Object.entries(byType).map(([evType, items], idx) => {
              const meta = EV_TYPE_META[evType] ?? { label: evType.replace(/_/g, ' '), color: 'text-slate-400' }
              return (
                <div key={evType} className="flex items-start gap-3 rounded-lg border border-slate-800 bg-slate-800/30 px-4 py-3">
                  <div className="flex items-center justify-center w-6 h-6 rounded-full bg-slate-700/60 text-[10px] font-bold text-slate-300 shrink-0">{idx + 1}</div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={clsx('text-xs font-semibold', meta.color)}>{meta.label}</span>
                      <span className="text-[10px] text-slate-600">({items.length} record{items.length !== 1 ? 's' : ''})</span>
                    </div>
                    {items.slice(0, 3).map((ev, i) => (
                      <p key={i} className="text-[11px] text-slate-400 leading-snug">
                        · {ev.title.slice(0, 85)}{ev.title.length > 85 ? '…' : ''}
                        {ev.source_url && (
                          <a href={ev.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-0.5 text-brand-400 hover:text-brand-300 ml-1">
                            <ExternalLink size={8} />
                          </a>
                        )}
                      </p>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>

          <div className={clsx('flex items-start gap-3 rounded-xl border px-4 py-3 mb-4', strengthStyle)}>
            <CheckCircle2 size={16} className="shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-semibold mb-1">Cross-source support — <span className="capitalize">{strength}</span></p>
              <p className="text-xs leading-relaxed opacity-90">
                {sourceCount} independent source{sourceCount !== 1 ? 's' : ''} corroborate a {drugName}–{disName} research association.
              </p>
            </div>
          </div>

          {crossDupes.length > 0 && (
            <div className="rounded-lg border border-brand-500/20 bg-brand-500/5 px-4 py-3">
              <p className="text-[11px] font-semibold text-brand-300 mb-2">Cross-Source Duplicates Removed ({crossDupes.length})</p>
              {crossDupes.slice(0, 5).map((d, i) => (
                <p key={i} className="text-[11px] text-slate-500">
                  {d.type.toUpperCase()}: {d.identifier.slice(0, 40)} — found in {d.sources.join(', ')} → counted once
                </p>
              ))}
            </div>
          )}
        </>
      )}
    </Section>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 9 — ON-DEMAND SEARCH
// Lets researcher trigger live ingestion for this exact drug+disease.
// ─────────────────────────────────────────────────────────────────────────────

function OnDemandSearchSection({ signal, onIngestionComplete }: {
  signal: Signal; onIngestionComplete: () => void
}) {
  const drugName    = signal.drug?.name    ?? signal.drug_name    ?? ''
  const diseaseName = signal.disease?.name ?? signal.disease_name ?? ''
  const [running, setRunning] = useState(false)
  const [result, setResult]   = useState<string | null>(null)
  const [error, setError]     = useState<string | null>(null)

  const run = useCallback(async () => {
    if (!drugName || !diseaseName || running) return
    setRunning(true)
    setResult(null)
    setError(null)
    try {
      const run = await ingestionApi.search(drugName, diseaseName)
      setResult(
        `Ingestion complete: ${run.total_new} new records fetched, ` +
        `${run.signals_updated} signal(s) updated, ${run.signals_created} new signal(s) created.`
      )
      onIngestionComplete()
    } catch (e: any) {
      const msg = e?.response?.data?.detail ?? e?.message ?? 'Ingestion failed'
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
    } finally {
      setRunning(false)
    }
  }, [drugName, diseaseName, running, onIngestionComplete])

  return (
    <Section id="search">
      <SectionHead
        icon={<Search size={15} className="text-brand-400" />}
        title="Run Live Research"
        subtitle={`Fetch the latest evidence for ${drugName} + ${diseaseName} from all 7 connected sources`}
      />
      <div className="rounded-xl border border-brand-500/20 bg-brand-500/5 p-4">
        <div className="flex flex-wrap items-center gap-3 mb-3">
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-brand-600/10 border border-brand-500/25">
            <Pill size={13} className="text-brand-400" /><span className="text-sm font-semibold text-brand-300">{drugName || '—'}</span>
          </div>
          <span className="text-slate-600">+</span>
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-purple-600/10 border border-purple-500/25">
            <Microscope size={13} className="text-purple-400" /><span className="text-sm font-semibold text-purple-300">{diseaseName || '—'}</span>
          </div>
        </div>
        <p className="text-xs text-slate-500 mb-3 leading-relaxed">
          Queries PubMed, Europe PMC, ClinicalTrials.gov, Elsevier, UniProt, bioRxiv, and medRxiv dynamically.
          Results are deduplicated, entity-matched, and the Evidence Score is recomputed from live evidence.
        </p>
        <div className="flex items-center gap-3">
          <button onClick={run} disabled={running || !drugName || !diseaseName}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              running || !drugName || !diseaseName
                ? 'bg-slate-700/50 text-slate-500 cursor-not-allowed'
                : 'bg-brand-600 hover:bg-brand-500 text-white'
            )}>
            <RefreshCw size={14} className={running ? 'animate-spin' : ''} />
            {running ? 'Fetching live research…' : 'Run Live Research Now'}
          </button>
          {running && <p className="text-xs text-slate-500 animate-pulse">Querying all sources — this may take 10–30 s</p>}
        </div>
        {result && (
          <div className="mt-3 flex items-start gap-2 px-3 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/25">
            <CheckCircle2 size={13} className="text-emerald-400 shrink-0 mt-0.5" />
            <p className="text-xs text-emerald-300">{result}</p>
          </div>
        )}
        {error && (
          <div className="mt-3 flex items-start gap-2 px-3 py-2 rounded-lg bg-rose-500/10 border border-rose-500/25">
            <XCircle size={13} className="text-rose-400 shrink-0 mt-0.5" />
            <p className="text-xs text-rose-300">{error}</p>
          </div>
        )}
      </div>
    </Section>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 10 — SOURCE TRACEABILITY TABLE
// Full provenance — every live record. No demo records shown.
// ─────────────────────────────────────────────────────────────────────────────

function SourceTraceabilitySection({ liveEv, signal }: { liveEv: LiveEvidenceResponse | null; signal: Signal }) {
  const items: LiveEvidenceRecord[] = liveEv?.evidence ?? []

  return (
    <Section id="traceability">
      <SectionHead
        icon={<BookOpen size={15} className="text-slate-400" />}
        title="Source Traceability"
        subtitle="Complete provenance — every live evidence record. Demo records excluded."
        badge={<span className="text-[10px] text-slate-500">{items.length} live records</span>}
      />
      {items.length === 0 ? (
        <p className="text-xs text-slate-500 text-center py-6">
          No live evidence records. Run ingestion to populate.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr>
                {['#', 'Source', 'Type', 'Title', 'Date', 'Identifier', 'View'].map(h => (
                  <th key={h} className="text-left text-[10px] text-slate-500 font-medium pb-2 pr-3 whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((ev, i) => {
                const meta = EV_TYPE_META[ev.evidence_type]
                const ref  = ev.doi ?? ev.pmid ?? ev.pmcid ?? ev.nct_id ?? '—'
                return (
                  <tr key={ev.id} className="border-b border-slate-800/60 hover:bg-slate-800/20 transition-colors">
                    <td className="py-2.5 pr-3 text-slate-600">{i + 1}</td>
                    <td className="py-2.5 pr-3">
                      <span className={clsx('text-[10px] px-1.5 py-0.5 rounded border font-semibold',
                        SOURCE_COLORS[ev.source] ?? SOURCE_COLORS.unknown)}>{ev.source}</span>
                    </td>
                    <td className="py-2.5 pr-3">
                      <span className={clsx('font-medium', meta?.color ?? 'text-slate-400')}>
                        {(meta?.label ?? ev.evidence_type).replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="py-2.5 pr-3 text-slate-300 max-w-[200px]">
                      <span className="line-clamp-2">{ev.title}</span>
                    </td>
                    <td className="py-2.5 pr-3 text-slate-500 whitespace-nowrap">{ev.publication_date ?? '—'}</td>
                    <td className="py-2.5 pr-3 font-mono text-[10px] text-slate-500">
                      {ref !== '—' && ev.source_url ? (
                        <a href={ev.source_url} target="_blank" rel="noopener noreferrer"
                          className="text-brand-400 hover:text-brand-300 flex items-center gap-1">
                          {ref.length > 30 ? ref.slice(0, 30) + '…' : ref}
                          <ExternalLink size={9} />
                        </a>
                      ) : ref}
                    </td>
                    <td className="py-2.5">
                      {ev.source_url ? (
                        <a href={ev.source_url} target="_blank" rel="noopener noreferrer"
                          className="flex items-center gap-0.5 text-[10px] text-brand-400 hover:text-brand-300 whitespace-nowrap">
                          <ExternalLink size={9} />Source
                        </a>
                      ) : <span className="text-slate-700">—</span>}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
      <p className="text-[10px] text-slate-600 mt-3">
        All identifiers (DOI, PMID, PMCID, NCT) link to the original source record.
        No fabricated citations. Demo records completely excluded from this table.
      </p>
    </Section>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 11 — DRUG & DISEASE PROFILES
// ─────────────────────────────────────────────────────────────────────────────

function ProfilesSection({ signal }: { signal: Signal }) {
  return (
    <Section id="profiles">
      <SectionHead icon={<Layers size={15} className="text-slate-400" />}
        title="Drug & Disease Profiles"
        subtitle="Molecular profile of each entity involved in this signal" />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {signal.drug && (
          <div className="rounded-xl border border-brand-500/20 bg-brand-500/5 p-4 space-y-3">
            <div className="flex items-center gap-2 mb-1">
              <Pill size={14} className="text-brand-400" />
              <p className="text-sm font-semibold text-brand-300">{signal.drug.name}</p>
            </div>
            <div className="space-y-2 text-xs">
              <KV label="Generic Name" value={signal.drug.generic_name} />
              <KV label="Drug Class"   value={signal.drug.drug_class} />
              <KV label="FDA Status"   value={signal.drug.fda_status} />
              {signal.drug.atc_code && <KV label="ATC Code" value={signal.drug.atc_code} />}
            </div>
            {signal.drug.mechanism_of_action && (
              <div>
                <p className="text-[10px] text-slate-500 font-medium mb-1 uppercase tracking-wide">Mechanism of Action</p>
                <p className="text-xs text-slate-400 leading-relaxed">{signal.drug.mechanism_of_action}</p>
              </div>
            )}
            {(signal.drug.molecular_targets?.length ?? 0) > 0 && (
              <div>
                <p className="text-[10px] text-slate-500 font-medium mb-1.5 uppercase tracking-wide">Molecular Targets</p>
                <div className="flex flex-wrap gap-1">{signal.drug.molecular_targets.map(t => <Tag key={t} label={t} color="brand" />)}</div>
              </div>
            )}
          </div>
        )}
        {signal.disease && (
          <div className="rounded-xl border border-purple-500/20 bg-purple-500/5 p-4 space-y-3">
            <div className="flex items-center gap-2 mb-1">
              <Microscope size={14} className="text-purple-400" />
              <p className="text-sm font-semibold text-purple-300">{signal.disease.name}</p>
            </div>
            <div className="space-y-2 text-xs">
              <KV label="Category"   value={signal.disease.category} />
              <KV label="ICD-10"     value={signal.disease.icd10_code} />
              <KV label="Prevalence" value={signal.disease.prevalence} />
            </div>
            {signal.disease.description && (
              <p className="text-xs text-slate-400 leading-relaxed">{signal.disease.description}</p>
            )}
            {(signal.disease.affected_pathways?.length ?? 0) > 0 && (
              <div>
                <p className="text-[10px] text-slate-500 font-medium mb-1.5 uppercase tracking-wide">Affected Pathways</p>
                <div className="flex flex-wrap gap-1">{signal.disease.affected_pathways.map(p => <Tag key={p} label={p} color="purple" />)}</div>
              </div>
            )}
            {signal.disease.unmet_needs && (
              <div className="rounded-lg border border-amber-500/20 bg-amber-500/8 px-3 py-2">
                <p className="text-[10px] text-amber-400 font-medium mb-0.5">Unmet Need</p>
                <p className="text-xs text-slate-400 leading-relaxed">{signal.disease.unmet_needs}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </Section>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// STICKY NAVIGATION
// ─────────────────────────────────────────────────────────────────────────────

const NAV_ITEMS = [
  { id: 'overview',          label: 'Overview',           icon: Zap        },
  { id: 'live-evidence',     label: 'Live Evidence',      icon: Wifi       },
  { id: 'why',               label: 'Why This Signal?',   icon: Brain      },
  { id: 'sources-breakdown', label: 'Source Contribution',icon: Layers     },
  { id: 'score',             label: 'Score Breakdown',    icon: BarChart2  },
  { id: 'timeline',          label: 'Evidence Timeline',  icon: Clock      },
  { id: 'graph',             label: 'Evidence Graph',     icon: Network    },
  { id: 'matching',          label: 'Cross-Source',       icon: Layers     },
  { id: 'search',            label: 'Run Live Research',  icon: Search     },
  { id: 'traceability',      label: 'Traceability',       icon: BookOpen   },
  { id: 'profiles',          label: 'Drug & Disease',     icon: Microscope },
]

function SectionNav({ activeId }: { activeId: string }) {
  const scrollTo = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  return (
    <nav className="hidden xl:flex flex-col gap-0.5 w-44 shrink-0 sticky top-20 self-start">
      <p className="text-[9px] text-slate-600 uppercase tracking-widest mb-2 px-2">Sections</p>
      {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
        <button key={id} onClick={() => scrollTo(id)}
          className={clsx('flex items-center gap-2 px-3 py-2 rounded-lg text-[11px] text-left transition-colors',
            activeId === id ? 'bg-brand-600/20 text-brand-300 font-medium' : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/50')}>
          <Icon size={11} />{label}
        </button>
      ))}
    </nav>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN PAGE
// ─────────────────────────────────────────────────────────────────────────────

export function SignalDetailPage() {
  const { id }    = useParams<{ id: string }>()
  const navigate  = useNavigate()

  const [signal,          setSignal]          = useState<Signal | null>(null)
  const [pipelineData,    setPipelineData]     = useState<SignalPipelineData | null>(null)
  const [sourceBreakdown, setSourceBreakdown]  = useState<SignalSourceBreakdown | null>(null)
  const [liveEv,          setLiveEv]           = useState<LiveEvidenceResponse | null>(null)
  const [loading,         setLoading]          = useState(true)
  const [activeNav,       setActiveNav]        = useState('overview')

  const drugName    = signal?.drug?.name    ?? signal?.drug_name    ?? '—'
  const diseaseName = signal?.disease?.name ?? signal?.disease_name ?? '—'

  const loadData = useCallback((n: number) => {
    return Promise.all([
      signalsApi.get(n),
      pipelineApi.get(n).catch(() => null),
      sourceBreakdownApi.get(n).catch(() => null),
      liveEvidenceApi.get(n).catch(() => null),
    ]).then(([sig, pipe, breakdown, live]) => {
      setSignal(sig)
      setPipelineData(pipe)
      setSourceBreakdown(breakdown)
      setLiveEv(live)
    })
  }, [])

  useEffect(() => {
    if (!id) return
    const n = Number(id)
    setLoading(true)
    loadData(n).finally(() => setLoading(false))
  }, [id, loadData])

  // Refresh after on-demand ingestion
  const handleIngestionComplete = useCallback(() => {
    if (!id) return
    loadData(Number(id))
  }, [id, loadData])

  // Track which section is in view for nav highlight
  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => entries.forEach(e => { if (e.isIntersecting) setActiveNav(e.target.id) }),
      { rootMargin: '-20% 0px -70% 0px', threshold: 0 },
    )
    NAV_ITEMS.forEach(({ id: navId }) => { const el = document.getElementById(navId); if (el) observer.observe(el) })
    return () => observer.disconnect()
  }, [loading])

  if (loading) return <div><Header title="Signal Investigation" /><PageLoader /></div>
  if (!signal) return (
    <div><Header title="Signal Investigation" />
      <div className="p-6"><p className="text-rose-400 text-sm">Signal not found.</p></div>
    </div>
  )

  return (
    <div>
      <Header
        title="Signal Investigation"
        subtitle={`${drugName} \u2192 ${diseaseName} \u00b7 Potential Research Signal \u00b7 Requires Expert Validation`}
      />
      <div className="flex gap-6 p-6 max-w-6xl">
        <SectionNav activeId={activeNav} />
        <div className="flex-1 min-w-0 space-y-5">
          <button onClick={() => navigate(-1)}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors">
            <ArrowLeft size={13} />Back to Signals
          </button>

          {/* 1. Overview */}
          <SignalOverview signal={signal} liveEv={liveEv} />

          {/* 2. Live Evidence Summary */}
          <LiveEvidenceSummarySection liveEv={liveEv} signal={signal} />

          {/* 3. Why This Signal */}
          <WhyThisSignalSection signal={signal} pipelineData={pipelineData} liveEv={liveEv} />

          {/* 4. Source Contribution */}
          <SourceBreakdownSection breakdown={sourceBreakdown} />

          {/* 5. Score Breakdown */}
          <ScoreBreakdownSection signal={signal} pipelineData={pipelineData} breakdown={sourceBreakdown} />

          {/* 6. Evidence Timeline */}
          <EvidenceTimelineSection liveEv={liveEv} signal={signal} />

          {/* 7. Evidence Graph */}
          <EvidenceGraphSection signal={signal} liveEv={liveEv} />

          {/* 8. Cross-Source Matching */}
          <CrossSourceSection signal={signal} liveEv={liveEv} breakdown={sourceBreakdown} />

          {/* 9. On-Demand Search */}
          <OnDemandSearchSection signal={signal} onIngestionComplete={handleIngestionComplete} />

          {/* 10. Source Traceability */}
          <SourceTraceabilitySection liveEv={liveEv} signal={signal} />

          {/* 11. Drug & Disease Profiles */}
          <ProfilesSection signal={signal} />

          {/* Footer */}
          <div className="flex items-start gap-2 px-4 py-3 rounded-xl border border-amber-500/20 bg-amber-500/5">
            <AlertTriangle size={14} className="text-amber-400 shrink-0 mt-0.5" />
            <p className="text-[11px] text-amber-400/80 leading-relaxed">
              <strong>BioArbitrage is a research decision-support tool only.</strong>{' '}
              All signals are <em>potential research associations</em> requiring expert validation.
              This platform does not diagnose patients, prescribe medicines, or provide treatment recommendations.
              All evidence records are real metadata fetched from connected research sources.
              No fabricated citations, authors, DOIs, or PMIDs.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
