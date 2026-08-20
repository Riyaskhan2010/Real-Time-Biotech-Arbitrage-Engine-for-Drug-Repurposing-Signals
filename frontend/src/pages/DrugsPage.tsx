import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Pill, ChevronDown, ChevronUp, Zap } from 'lucide-react'
import { Header } from '../components/Header'
import { SearchInput } from '../components/ui/SearchInput'
import { PageLoader } from '../components/ui/Spinner'
import { EmptyState } from '../components/ui/EmptyState'
import { SignalCard } from '../components/SignalCard'
import { drugsApi } from '../api'
import type { Drug, SignalListItem } from '../types'
import { useDebounce } from '../hooks/useDebounce'

function DrugRow({ drug }: { drug: Drug }) {
  const navigate  = useNavigate()
  const [expanded, setExpanded] = useState(false)
  const [signals,  setSignals]  = useState<SignalListItem[]>([])
  const [sigLoading, setSigLoading] = useState(false)

  const toggle = () => {
    if (!expanded && signals.length === 0) {
      setSigLoading(true)
      drugsApi.signals(drug.id).then(setSignals).finally(() => setSigLoading(false))
    }
    setExpanded(e => !e)
  }

  const hasSignals = drug.signal_count > 0

  return (
    <div className="ui-card overflow-hidden">
      <div
        className="flex items-center gap-4 p-4 cursor-pointer hover:bg-slate-50 transition-colors"
        onClick={toggle}
      >
        {/* Icon */}
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-navy-50 border border-navy-200 shrink-0">
          <Pill size={16} className="text-navy-700" aria-hidden="true" />
        </div>

        {/* Name + meta */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-[14px] font-semibold text-slate-900">{drug.name}</p>
            {drug.generic_name && drug.generic_name !== drug.name && (
              <span className="text-[12px] text-slate-400">({drug.generic_name})</span>
            )}
          </div>
          <div className="flex items-center gap-2 mt-0.5 flex-wrap">
            {drug.drug_class && (
              <span className="text-[12px] text-slate-500">{drug.drug_class}</span>
            )}
            {drug.fda_status && (
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-green-50 text-green-700 border border-green-200 font-medium">
                {drug.fda_status}
              </span>
            )}
          </div>
        </div>

        {/* Signal count */}
        <div className="flex items-center gap-4 shrink-0">
          <div className="text-right">
            <div className="flex items-center gap-1 justify-end">
              <Zap size={13} className={hasSignals ? 'text-amber-500' : 'text-slate-300'} aria-hidden="true" />
              <p className={`text-[14px] font-bold tabular-nums ${hasSignals ? 'text-amber-600' : 'text-slate-400'}`}>
                {drug.signal_count}
              </p>
            </div>
            <p className="text-[10px] text-slate-400">signal{drug.signal_count !== 1 ? 's' : ''}</p>
          </div>
          {expanded
            ? <ChevronUp size={14} className="text-slate-400" />
            : <ChevronDown size={14} className="text-slate-400" />
          }
        </div>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-slate-100 px-4 pb-4 pt-3 bg-slate-50/50">
          {drug.description && (
            <p className="text-[13px] text-slate-600 leading-relaxed mb-4">{drug.description}</p>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {(drug.approved_indications?.length ?? 0) > 0 && (
              <div>
                <p className="text-[11px] text-slate-500 mb-1.5 font-semibold uppercase tracking-wide">Approved Indications</p>
                <div className="flex flex-wrap gap-1">
                  {drug.approved_indications.map(ind => (
                    <span key={ind} className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                      {ind}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {(drug.molecular_targets?.length ?? 0) > 0 && (
              <div>
                <p className="text-[11px] text-slate-500 mb-1.5 font-semibold uppercase tracking-wide">Molecular Targets</p>
                <div className="flex flex-wrap gap-1">
                  {drug.molecular_targets.map(t => (
                    <span key={t} className="text-[11px] px-2 py-0.5 rounded-full bg-navy-50 text-navy-700 border border-navy-200">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {sigLoading ? (
            <p className="text-[13px] text-slate-500">Loading signals…</p>
          ) : signals.length > 0 ? (
            <div>
              <p className="text-[11px] text-slate-500 mb-2 font-semibold uppercase tracking-wide">
                Repurposing Signals ({signals.length})
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {signals.map(s => <SignalCard key={s.id} signal={s} compact />)}
              </div>
            </div>
          ) : (
            <div className="py-4 text-center rounded-lg border border-dashed border-slate-200">
              <p className="text-[13px] text-slate-400">No active research signals for this drug.</p>
              <p className="text-[12px] text-slate-400 mt-0.5">
                Run ingestion to search for new research associations.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function DrugsPage() {
  const [drugs,   setDrugs]   = useState<Drug[]>([])
  const [loading, setLoading] = useState(true)
  const [search,  setSearch]  = useState('')
  const debouncedSearch = useDebounce(search, 350)

  useEffect(() => {
    setLoading(true)
    drugsApi.list({ search: debouncedSearch || undefined })
      .then(setDrugs)
      .finally(() => setLoading(false))
  }, [debouncedSearch])

  return (
    <div className="bg-app-bg min-h-screen">
      <Header title="Drug Intelligence" subtitle="Browse monitored drugs and their repurposing signals" />

      <div className="p-6 space-y-5">

        <div className="flex items-center gap-3 flex-wrap">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search drugs by name or class…"
            className="w-80"
          />
          <span className="text-[12px] text-slate-500 ml-auto">
            {drugs.length} drug{drugs.length !== 1 ? 's' : ''}
          </span>
        </div>

        {loading ? (
          <PageLoader />
        ) : drugs.length === 0 ? (
          <EmptyState icon={<Pill size={32} />} title="No drugs found" description="Try a different search." />
        ) : (
          <div className="space-y-3">
            {drugs.map(d => <DrugRow key={d.id} drug={d} />)}
          </div>
        )}
      </div>
    </div>
  )
}
