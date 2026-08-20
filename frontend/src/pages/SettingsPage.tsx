import { useEffect, useState } from 'react'
import { clsx } from 'clsx'
import { Header } from '../components/Header'
import { useAuthStore } from '../store/authStore'
import {
  User, Shield, Database, Cpu,
  CheckCircle2, XCircle, Clock, MinusCircle,
  RefreshCw, Wifi,
} from 'lucide-react'
import { ingestionApi } from '../api'
import type { SourceStatusItem } from '../types'

// ── Researcher profile override ────────────────────────────────────────────
// Displayed instead of demo credentials from auth store
const RESEARCHER_PROFILE = {
  full_name:   'MOHAMED RIYASKHAN S',
  username:    'RIYASKHAN_researcher',
  email:       'mohamedriyaskhans.bit25@rathinam.in',
  role:        'Researcher',
  institution: 'BioArbitrage Research Platform',
}

// ── Source status config ───────────────────────────────────────────────────

const STATUS_META: Record<string, { label: string; icon: typeof CheckCircle2; iconCls: string; textCls: string }> = {
  connected:      { label: 'Connected',       icon: CheckCircle2, iconCls: 'text-emerald-600', textCls: 'text-emerald-700' },
  error:          { label: 'Error',           icon: XCircle,      iconCls: 'text-red-500',     textCls: 'text-red-700'     },
  timeout:        { label: 'Timeout',         icon: Clock,        iconCls: 'text-amber-600',   textCls: 'text-amber-700'   },
  disabled:       { label: 'Disabled',        icon: MinusCircle,  iconCls: 'text-slate-400',   textCls: 'text-slate-500'   },
  not_configured: { label: 'Not Configured',  icon: MinusCircle,  iconCls: 'text-slate-400',   textCls: 'text-slate-600'   },
  invalid_key:    { label: 'Invalid API Key', icon: XCircle,      iconCls: 'text-red-500',     textCls: 'text-red-700'     },
  rate_limited:   { label: 'Rate Limited',    icon: Clock,        iconCls: 'text-amber-600',   textCls: 'text-amber-700'   },
  loading:        { label: 'Checking…',       icon: RefreshCw,    iconCls: 'text-slate-500',   textCls: 'text-slate-600'   },
}

// ── Source row ─────────────────────────────────────────────────────────────

function SourceRow({ name, status, error }: {
  name: string; status: string; error?: string | null
}) {
  const meta = STATUS_META[status] ?? STATUS_META.error
  const Icon = meta.icon

  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-slate-100 last:border-0">
      <Icon
        size={14}
        className={clsx(meta.iconCls, status === 'loading' ? 'animate-spin' : '')}
        aria-hidden="true"
      />
      <span className="flex-1 text-[13px] font-medium text-slate-800">{name}</span>
      <span className={clsx('text-[12px] font-semibold', meta.textCls)}>
        {meta.label}
      </span>
      {error && (
        <span className="text-[11px] text-slate-500 max-w-[200px] truncate" title={error}>
          {error}
        </span>
      )}
    </div>
  )
}

// ── Settings card wrapper ──────────────────────────────────────────────────

function SettingsCard({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={clsx(
        'bg-white rounded-xl border border-slate-200 p-5',
        className,
      )}
      style={{ boxShadow: '0 1px 3px 0 rgba(0,0,0,.06), 0 1px 2px -1px rgba(0,0,0,.04)' }}
    >
      {children}
    </div>
  )
}

// ── Profile row ────────────────────────────────────────────────────────────

function ProfileRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start gap-3 py-2.5 border-b border-slate-100 last:border-0">
      <span className="text-[12px] font-semibold text-slate-500 uppercase tracking-wide w-28 shrink-0 pt-0.5">
        {label}
      </span>
      <span className="text-[14px] font-medium text-slate-900 break-all">{value}</span>
    </div>
  )
}

// ── Card section header ────────────────────────────────────────────────────

function CardHeading({ icon: Icon, iconCls, title }: {
  icon: React.ElementType; iconCls: string; title: string
}) {
  return (
    <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-100">
      <Icon size={16} className={iconCls} aria-hidden="true" />
      <h2 className="text-[15px] font-semibold text-slate-900">{title}</h2>
    </div>
  )
}

// ── Security bullet ────────────────────────────────────────────────────────

function SecurityPoint({ text }: { text: string }) {
  return (
    <div className="flex items-start gap-2.5">
      <CheckCircle2 size={14} className="text-emerald-600 shrink-0 mt-0.5" aria-hidden="true" />
      <p className="text-[13px] text-slate-700 leading-snug">{text}</p>
    </div>
  )
}

// ── Inline code ────────────────────────────────────────────────────────────

function Code({ children }: { children: React.ReactNode }) {
  return (
    <code className="text-[12px] font-mono text-slate-700 bg-slate-100 border border-slate-200 px-1.5 py-0.5 rounded">
      {children}
    </code>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────

export function SettingsPage() {
  const { user } = useAuthStore()

  const [sources,       setSources]       = useState<SourceStatusItem[]>([])
  const [sourceLoading, setSourceLoading] = useState(false)

  const checkSources = async () => {
    setSourceLoading(true)
    setSources([
      { source: 'PubMed',                   status: 'loading', enabled: true },
      { source: 'bioRxiv',                  status: 'loading', enabled: true },
      { source: 'medRxiv',                  status: 'loading', enabled: true },
      { source: 'ClinicalTrials.gov',       status: 'loading', enabled: true },
      { source: 'Elsevier (ScienceDirect)', status: 'loading', enabled: true },
      { source: 'Europe PMC',               status: 'loading', enabled: true },
      { source: 'UniProt',                  status: 'loading', enabled: true },
    ])
    try {
      const results = await ingestionApi.sourceStatus()
      const nameMap: Record<string, string> = {
        pubmed:         'PubMed',
        biorxiv:        'bioRxiv',
        medrxiv:        'medRxiv',
        clinicaltrials: 'ClinicalTrials.gov',
        elsevier:       'Elsevier (ScienceDirect)',
        europepmc:      'Europe PMC',
        uniprot:        'UniProt',
      }
      setSources(results.map(r => ({ ...r, source: nameMap[r.source] ?? r.source })))
    } catch {
      setSources([
        { source: 'PubMed',                   status: 'error', enabled: true, error: 'Could not reach server' },
        { source: 'bioRxiv',                  status: 'error', enabled: true, error: 'Could not reach server' },
        { source: 'medRxiv',                  status: 'error', enabled: true, error: 'Could not reach server' },
        { source: 'ClinicalTrials.gov',       status: 'error', enabled: true, error: 'Could not reach server' },
        { source: 'Elsevier (ScienceDirect)', status: 'error', enabled: true, error: 'Could not reach server' },
        { source: 'Europe PMC',               status: 'error', enabled: true, error: 'Could not reach server' },
        { source: 'UniProt',                  status: 'error', enabled: true, error: 'Could not reach server' },
      ])
    } finally {
      setSourceLoading(false)
    }
  }

  useEffect(() => { checkSources() }, [])

  const allConnected = sources.length > 0 && sources.every(s => s.status === 'connected')
  const anyError     = sources.some(s => s.status === 'error' || s.status === 'timeout' || s.status === 'invalid_key')

  // Use override profile; fall back to auth store values if present
  const profile = {
    full_name:   RESEARCHER_PROFILE.full_name,
    username:    RESEARCHER_PROFILE.username,
    email:       RESEARCHER_PROFILE.email,
    role:        RESEARCHER_PROFILE.role,
    institution: RESEARCHER_PROFILE.institution,
  }

  return (
    <div className="bg-app-bg min-h-screen">
      <Header title="Settings" subtitle="Platform configuration and account information" />

      <div className="p-6 space-y-5 max-w-2xl">

        {/* ── Researcher Profile ─────────────────────────────────────── */}
        <SettingsCard>
          <CardHeading icon={User} iconCls="text-primary-600" title="Researcher Profile" />
          <div>
            <ProfileRow label="Full Name"   value={profile.full_name}   />
            <ProfileRow label="Username"    value={profile.username}    />
            <ProfileRow label="Email"       value={profile.email}       />
            <ProfileRow label="Role"        value={profile.role}        />
            <ProfileRow label="Institution" value={profile.institution} />
          </div>
        </SettingsCard>

        {/* ── Security ───────────────────────────────────────────────── */}
        <SettingsCard>
          <CardHeading icon={Shield} iconCls="text-emerald-600" title="Security" />
          <div className="space-y-3">
            <SecurityPoint text="JWT authentication active" />
            <SecurityPoint text="API keys stored server-side only — never exposed to frontend" />
            <SecurityPoint text="All API calls require authentication" />
            <SecurityPoint text="Input validation on all endpoints" />
            <SecurityPoint text="External API credentials (NCBI_API_KEY, ELSEVIER_API_KEY) held in backend .env only" />
          </div>
        </SettingsCard>

        {/* ── Data Sources ───────────────────────────────────────────── */}
        <SettingsCard>
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Database
                size={16}
                className={allConnected ? 'text-emerald-600' : anyError ? 'text-red-500' : 'text-primary-600'}
                aria-hidden="true"
              />
              <h2 className="text-[15px] font-semibold text-slate-900">Data Sources</h2>
            </div>
            <button
              onClick={checkSources}
              disabled={sourceLoading}
              className="flex items-center gap-1.5 text-[12px] font-medium text-primary-600 hover:text-primary-700 transition-colors disabled:opacity-50"
            >
              <RefreshCw size={12} className={sourceLoading ? 'animate-spin' : ''} aria-hidden="true" />
              Re-check
            </button>
          </div>

          {/* Aggregate status banner */}
          {allConnected && (
            <div className="flex items-center gap-2 mb-4 px-3 py-2 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-[12px] font-medium">
              <Wifi size={13} aria-hidden="true" />
              All sources connected — live ingestion available
            </div>
          )}
          {anyError && !allConnected && (
            <div className="flex items-center gap-2 mb-4 px-3 py-2 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-[12px] font-medium">
              <XCircle size={13} aria-hidden="true" />
              Some sources unavailable
            </div>
          )}

          {/* Per-source rows */}
          <div>
            {sources.map(s => (
              <SourceRow
                key={s.source}
                name={s.source}
                status={s.status}
                error={s.error}
              />
            ))}
          </div>

          {/* Notes */}
          <div className="mt-4 space-y-2 pt-3 border-t border-slate-100">
            {[
              <>All sources except Elsevier use free public APIs — no API key required.</>,
              <>Set <Code>NCBI_API_KEY</Code> in <Code>backend/.env</Code> to raise PubMed rate limit from 3→10 req/s.</>,
              <>Set <Code>ELSEVIER_API_KEY</Code> in <Code>backend/.env</Code> to enable Elsevier Scopus (key never sent to frontend).</>,
              <>Europe PMC: free, no key — PMID, PMCID, DOI, abstract, keywords, open-access status.</>,
              <>UniProt: free, no key — curated protein/gene annotations, disease associations, GO terms.</>,
              <>Ingestion can be triggered from the Research Monitor panel or via <Code>POST /api/ingestion/run</Code>.</>,
            ].map((note, i) => (
              <p key={i} className="text-[12px] text-slate-600 leading-relaxed">{note}</p>
            ))}
          </div>
        </SettingsCard>

        {/* ── AI Service ─────────────────────────────────────────────── */}
        <SettingsCard>
          <CardHeading icon={Cpu} iconCls="text-violet-600" title="AI Service" />
          <div className="space-y-2.5">
            <div className="flex items-center gap-2">
              <span className="text-[13px] text-slate-600">Currently using:</span>
              <span className="text-[13px] font-semibold text-violet-700">Deterministic heuristic fallback</span>
            </div>
            <p className="text-[13px] text-slate-600 leading-relaxed">
              Entity extraction uses keyword-based matching against the known drug and disease knowledge base.
            </p>
            <p className="text-[13px] text-slate-600 leading-relaxed">
              To enable LLM-powered extraction and explanations, set{' '}
              <Code>OPENAI_API_KEY</Code> in <Code>backend/.env</Code>.
            </p>
            <p className="text-[12px] text-slate-500 leading-relaxed">
              Supported: OpenAI GPT-4o-mini. Extensible to Anthropic and local models.
            </p>
          </div>
        </SettingsCard>

        {/* Footer note */}
        <p className="text-[12px] text-slate-500 leading-relaxed px-1">
          BioArbitrage MVP v1.0 — Research decision-support tool only.
          Not for clinical use, diagnosis, or treatment recommendations.
        </p>
      </div>
    </div>
  )
}
