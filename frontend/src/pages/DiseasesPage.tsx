import { useEffect, useState } from 'react'
import { Microscope, ChevronDown, ChevronUp, Zap } from 'lucide-react'
import { Header } from '../components/Header'
import { SearchInput } from '../components/ui/SearchInput'
import { PageLoader } from '../components/ui/Spinner'
import { EmptyState } from '../components/ui/EmptyState'
import { SignalCard } from '../components/SignalCard'
import { diseasesApi } from '../api'
import type { Disease, SignalListItem } from '../types'
import { useDebounce } from '../hooks/useDebounce'

function DiseaseRow({ disease }: { disease: Disease }) {
  const [expanded,   setExpanded]   = useState(false)
  const [signals,    setSignals]    = useState<SignalListItem[]>([])
  const [sigLoading, setSigLoading] = useState(false)

  const toggle = () => {
    if (!expanded && signals.length === 0) {
      setSigLoading(true)
      diseasesApi.signals(disease.id).then(setSignals).finally(() => setSigLoading(false))
    }
    setExpanded(e => !e)
  }

  const hasSignals = disease.signal_count > 0

  return (
    <div className="ui-card overflow-hidden">
      <div
        className="flex items-center gap-4 p-4 cursor-pointer hover:bg-slate-50 transition-colors"
        onClick={toggle}
      >
        {/* Icon */}
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-violet-50 border border-violet-200 shrink-0">
          <Microscope size={16} className="text-violet-700" aria-hidden="true" />
        </div>

        {/* Name + meta */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-[14px] font-semibold text-slate-900">{disease.name}</p>
            {disease.icd10_code && (
              <span className="text-[11px] text-slate-400 font-mono">{disease.icd10_code}</span>
            )}
          </div>
          <div className="flex items-center gap-2 mt-0.5 flex-wrap">
            {disease.category && <span className="text-[12px] text-slate-500">{disease.category}</span>}
            {disease.prevalence && (
              <span className="text-[11px] text-slate-400">{disease.prevalence}</span>
            )}
          </div>
        </div>

        {/* Signal count */}
        <div className="flex items-center gap-4 shrink-0">
          <div className="text-right">
            <div className="flex items-center gap-1 justify-end">
              <Zap size={13} className={hasSignals ? 'text-amber-500' : 'text-slate-300'} aria-hidden="true" />
              <p className={`text-[14px] font-bold tabular-nums ${hasSignals ? 'text-amber-600' : 'text-slate-400'}`}>
                {disease.signal_count}
              </p>
            </div>
            <p className="text-[10px] text-slate-400">signal{disease.signal_count !== 1 ? 's' : ''}</p>
          </div>
          {expanded
            ? <ChevronUp size={14} className="text-slate-400" />
            : <ChevronDown size={14} className="text-slate-400" />
          }
        </div>
      </div>

      {/* Expanded */}
      {expanded && (
        <div className="border-t border-slate-100 px-4 pb-4 pt-3 bg-slate-50/50">
          {disease.description && (
            <p className="text-[13px] text-slate-600 leading-relaxed mb-4">{disease.description}</p>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {(disease.current_treatments?.length ?? 0) > 0 && (
              <div>
                <p className="text-[11px] text-slate-500 mb-1.5 font-semibold uppercase tracking-wide">Current Treatments</p>
                <div className="flex flex-wrap gap-1">
                  {disease.current_treatments.map(t => (
                    <span key={t} className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {(disease.affected_pathways?.length ?? 0) > 0 && (
              <div>
                <p className="text-[11px] text-slate-500 mb-1.5 font-semibold uppercase tracking-wide">Affected Pathways</p>
                <div className="flex flex-wrap gap-1">
                  {disease.affected_pathways.map(p => (
                    <span key={p} className="text-[11px] px-2 py-0.5 rounded-full bg-violet-50 text-violet-700 border border-violet-200">
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {disease.unmet_needs && (
            <div className="mb-4 px-3 py-2 rounded-lg bg-amber-50 border border-amber-200 text-[12px] text-amber-800">
              <span className="font-semibold">Unmet Need: </span>{disease.unmet_needs}
            </div>
          )}

          {sigLoading ? (
            <p className="text-[13px] text-slate-500">Loading signals…</p>
          ) : signals.length > 0 ? (
            <div>
              <p className="text-[11px] text-slate-500 mb-2 font-semibold uppercase tracking-wide">
                Potential Repurposed Drugs ({signals.length})
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {signals.map(s => <SignalCard key={s.id} signal={s} compact />)}
              </div>
            </div>
          ) : (
            <div className="py-4 text-center rounded-lg border border-dashed border-slate-200">
              <p className="text-[13px] text-slate-400">No active repurposing candidates for this disease.</p>
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

export function DiseasesPage() {
  const [diseases, setDiseases] = useState<Disease[]>([])
  const [loading,  setLoading]  = useState(true)
  const [search,   setSearch]   = useState('')
  const debouncedSearch = useDebounce(search, 350)

  useEffect(() => {
    setLoading(true)
    diseasesApi.list({ search: debouncedSearch || undefined })
      .then(setDiseases)
      .finally(() => setLoading(false))
  }, [debouncedSearch])

  return (
    <div className="bg-app-bg min-h-screen">
      <Header title="Disease Intelligence" subtitle="Browse tracked diseases and potential repurposing candidates" />

      <div className="p-6 space-y-5">

        <div className="flex items-center gap-3 flex-wrap">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search diseases…"
            className="w-80"
          />
          <span className="text-[12px] text-slate-500 ml-auto">
            {diseases.length} disease{diseases.length !== 1 ? 's' : ''}
          </span>
        </div>

        {loading ? (
          <PageLoader />
        ) : diseases.length === 0 ? (
          <EmptyState icon={<Microscope size={32} />} title="No diseases found" description="Try a different search." />
        ) : (
          <div className="space-y-3">
            {diseases.map(d => <DiseaseRow key={d.id} disease={d} />)}
          </div>
        )}
      </div>
    </div>
  )
}
