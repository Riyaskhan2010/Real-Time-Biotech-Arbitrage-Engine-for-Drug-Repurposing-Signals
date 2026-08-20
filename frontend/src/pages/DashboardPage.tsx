import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Zap, Pill, Microscope, BookOpen, TrendingUp, Search, Database,
} from 'lucide-react'
import { Header } from '../components/Header'
import { Card, CardHeader, CardTitle } from '../components/ui/Card'
import { SignalCard } from '../components/SignalCard'
import { SignalTrendChart } from '../components/SignalTrendChart'
import { PageLoader } from '../components/ui/Spinner'
import { ResearchMonitor } from '../components/ResearchMonitor'
import { dashboardApi, signalsApi } from '../api'
import { useAlertStore } from '../store/alertStore'
import type { DashboardData, SignalListItem } from '../types'
import { useDebounce } from '../hooks/useDebounce'

// ─── stat card ─────────────────────────────────────────────────────────────

interface KpiProps {
  label: string
  value: number | string
  sub?: string
  icon: React.ReactNode
  iconBg: string
}

function KpiCard({ label, value, sub, icon, iconBg }: KpiProps) {
  return (
    <Card className="flex items-start gap-3 p-4">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${iconBg}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-2xl font-bold text-slate-900 tabular-nums leading-tight">{value}</p>
        <p className="text-[12px] text-slate-500 mt-0.5 leading-tight">{label}</p>
        {sub && <p className="text-[11px] text-slate-400 mt-0.5">{sub}</p>}
      </div>
    </Card>
  )
}

// ─── page ──────────────────────────────────────────────────────────────────

export function DashboardPage() {
  const navigate = useNavigate()
  const { reset: resetAlertStore } = useAlertStore()
  const [data,    setData]    = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState<string | null>(null)

  const [quickSearch,    setQuickSearch]    = useState('')
  const [searchResults,  setSearchResults]  = useState<SignalListItem[]>([])
  const [searchLoading,  setSearchLoading]  = useState(false)
  const [showDropdown,   setShowDropdown]   = useState(false)
  const debouncedQ = useDebounce(quickSearch, 300)

  const load = useCallback(() => {
    dashboardApi.get()
      .then(setData)
      .catch(() => setError('Failed to load dashboard data'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    if (!debouncedQ.trim()) { setSearchResults([]); setShowDropdown(false); return }
    setSearchLoading(true)
    signalsApi.list({ search: debouncedQ, limit: 6 })
      .then(r => { setSearchResults(r); setShowDropdown(true) })
      .finally(() => setSearchLoading(false))
  }, [debouncedQ])

  const onIngestionComplete = useCallback(() => {
    load(); resetAlertStore()
  }, [load, resetAlertStore])

  if (loading) return (
    <div className="bg-app-bg min-h-screen">
      <Header title="Research Intelligence Dashboard" />
      <PageLoader />
    </div>
  )

  if (error || !data) return (
    <div className="bg-app-bg min-h-screen">
      <Header title="Research Intelligence Dashboard" />
      <div className="p-6"><p className="text-red-600 text-sm">{error ?? 'Unknown error'}</p></div>
    </div>
  )

  const { stats, signal_trend, recent_signals, high_confidence_signals } = data

  return (
    <div className="bg-app-bg min-h-screen">
      <Header
        title="Research Intelligence Dashboard"
        subtitle="Real-time overview of drug repurposing evidence and emerging signals"
      />

      <div className="p-6 space-y-6 max-w-screen-2xl">

        {/* Quick search */}
        <div className="relative max-w-md">
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-300 bg-white
                          focus-within:border-navy-500 focus-within:ring-2 focus-within:ring-navy-500/15 transition-colors"
            style={{ boxShadow: '0 1px 2px 0 rgba(0,0,0,.04)' }}>
            <Search size={15} className="text-slate-400 shrink-0" aria-hidden="true" />
            <input
              type="text"
              value={quickSearch}
              onChange={e => setQuickSearch(e.target.value)}
              onFocus={() => searchResults.length > 0 && setShowDropdown(true)}
              onBlur={() => setTimeout(() => setShowDropdown(false), 150)}
              placeholder="Quick search signals, drugs, diseases…"
              className="flex-1 bg-transparent text-[13px] text-slate-800 placeholder:text-slate-400 focus:outline-none"
            />
            {searchLoading && (
              <div className="w-4 h-4 rounded-full border-2 border-slate-200 border-t-navy-600 animate-spin shrink-0" />
            )}
            {quickSearch && !searchLoading && (
              <button onClick={() => { setQuickSearch(''); setShowDropdown(false) }}
                className="text-slate-400 hover:text-slate-600 text-xs shrink-0">✕</button>
            )}
          </div>

          {showDropdown && searchResults.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 z-50 bg-white rounded-xl border border-slate-200 overflow-hidden"
              style={{ boxShadow: '0 8px 24px 0 rgba(0,0,0,.10)' }}>
              <p className="px-4 py-2 text-[11px] text-slate-400 border-b border-slate-100">
                {searchResults.length} signal{searchResults.length !== 1 ? 's' : ''} matching "{quickSearch}"
              </p>
              {searchResults.map(s => (
                <button key={s.id} onMouseDown={() => navigate(`/signals/${s.id}`)}
                  className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-50 transition-colors text-left">
                  <Zap size={12} className={
                    s.confidence_level === 'high' ? 'text-emerald-500' :
                    s.confidence_level === 'medium' ? 'text-amber-500' : 'text-slate-400'
                  } aria-hidden="true" />
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-medium text-slate-800 truncate">{s.drug_name} → {s.disease_name}</p>
                    <p className="text-[11px] text-slate-400 truncate">{s.title}</p>
                  </div>
                  <span className={`text-[13px] font-bold tabular-nums ${
                    s.evidence_score >= 75 ? 'text-emerald-600' :
                    s.evidence_score >= 55 ? 'text-amber-600' : 'text-slate-500'
                  }`}>{s.evidence_score.toFixed(0)}</span>
                </button>
              ))}
              <div className="border-t border-slate-100 px-4 py-2">
                <button onMouseDown={() => navigate(`/signals?search=${encodeURIComponent(quickSearch)}`)}
                  className="text-[12px] text-navy-600 hover:text-navy-800 transition-colors">
                  View all results on Signals page →
                </button>
              </div>
            </div>
          )}
        </div>

        {/* KPI cards */}
        <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {/* total_research_sources = rows in ResearchSource table (raw fetched records from all sources) */}
          <KpiCard label="Sources Indexed"    value={stats.total_research_sources} iconBg="bg-blue-50"    icon={<BookOpen  size={17} className="text-blue-600"    />} />
          <KpiCard label="Drugs Monitored"    value={stats.drugs_monitored}         iconBg="bg-navy-50"   icon={<Pill      size={17} className="text-navy-700"   />} />
          <KpiCard label="Diseases Tracked"   value={stats.diseases_tracked}        iconBg="bg-violet-50" icon={<Microscope size={17} className="text-violet-600" />} />
          <KpiCard label="Research Signals"   value={stats.total_signals}           iconBg="bg-amber-50"  icon={<Zap       size={17} className="text-amber-600"   />} />
          <KpiCard label="High Confidence"    value={stats.high_confidence_signals} iconBg="bg-green-50"  icon={<TrendingUp size={17} className="text-green-600"  />} />
          <KpiCard label="Recent Updates"     value={stats.recent_updates}          iconBg="bg-rose-50"   icon={<Database  size={17} className="text-rose-500"    />} />
        </div>

        {/* Trend + High-confidence */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
          <Card className="xl:col-span-2 p-5">
            <CardHeader>
              <CardTitle>Signal Detection Trend</CardTitle>
              <span className="text-[11px] text-slate-400">Cumulative signals over time</span>
            </CardHeader>
            <SignalTrendChart data={signal_trend} />
          </Card>

          <Card className="p-5">
            <CardHeader>
              <CardTitle>High-Confidence Signals</CardTitle>
              <span className="text-[11px] text-green-600 font-medium">{stats.high_confidence_signals} active</span>
            </CardHeader>
            <div className="space-y-3">
              {high_confidence_signals.length === 0 ? (
                <p className="text-[13px] text-slate-400 text-center py-6">No high-confidence signals yet</p>
              ) : (
                high_confidence_signals.map(s => <SignalCard key={s.id} signal={s} compact />)
              )}
            </div>
          </Card>
        </div>

        {/* Recent signals */}
        <Card className="p-5">
          <CardHeader>
            <CardTitle>Recent Signals</CardTitle>
            <Link to="/signals" className="text-[12px] text-navy-600 hover:text-navy-800 font-medium transition-colors">
              View all signals →
            </Link>
          </CardHeader>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recent_signals.map(s => <SignalCard key={s.id} signal={s} />)}
          </div>
        </Card>

        {/* Research Monitor */}
        <Card className="p-5">
          <CardHeader>
            <CardTitle>Research Monitor</CardTitle>
            <span className="text-[11px] text-slate-400">Live Ingestion Pipeline</span>
          </CardHeader>
          <p className="text-[13px] text-slate-500 mb-4">
            Fetch real research records from all connected biomedical sources.
            Dashboard stats, signals, and alerts refresh automatically after each run.
          </p>
          <ResearchMonitor compact showRunButton onIngestionComplete={onIngestionComplete} />
        </Card>
      </div>
    </div>
  )
}
