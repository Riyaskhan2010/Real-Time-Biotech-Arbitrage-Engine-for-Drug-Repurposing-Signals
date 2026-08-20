import { useEffect, useState } from 'react'
import { FileText, ExternalLink, BookOpen, FlaskConical, ChevronDown, ChevronUp, Database } from 'lucide-react'
import { Header } from '../components/Header'
import { SearchInput } from '../components/ui/SearchInput'
import { PageLoader } from '../components/ui/Spinner'
import { EmptyState } from '../components/ui/EmptyState'
import { evidenceApi } from '../api'
import type { Evidence } from '../types'
import { useDebounce } from '../hooks/useDebounce'
import { clsx } from 'clsx'

const TYPE_OPTIONS = [
  { label: 'All Types',           value: '' },
  { label: 'Research Papers',     value: 'research_paper' },
  { label: 'Clinical Trials',     value: 'clinical_trial' },
  { label: 'Preprints',           value: 'preprint' },
  { label: 'Reviews',             value: 'review_article' },
  { label: 'Protein Annotations', value: 'protein_annotation' },
]

const PROVENANCE_OPTIONS = [
  { label: 'All Records', value: '' },
  { label: 'Live Only',   value: 'live' },
  { label: 'Demo Only',   value: 'demo' },
]

const SOURCE_PILL: Record<string, string> = {
  pubmed:         'bg-blue-50   text-blue-800   border-blue-200',
  europepmc:      'bg-teal-50   text-teal-800   border-teal-200',
  uniprot:        'bg-violet-50 text-violet-800 border-violet-200',
  elsevier:       'bg-orange-50 text-orange-800 border-orange-200',
  biorxiv:        'bg-amber-50  text-amber-800  border-amber-200',
  medrxiv:        'bg-rose-50   text-rose-800   border-rose-200',
  clinicaltrials: 'bg-green-50  text-green-800  border-green-200',
}

function SourcePill({ source }: { source: string }) {
  const key   = (source || 'unknown').toLowerCase()
  const style = SOURCE_PILL[key] ?? 'bg-slate-50 text-slate-700 border-slate-200'
  return (
    <span className={clsx('text-[10px] px-2 py-0.5 rounded-full border font-medium', style)}>
      {source}
    </span>
  )
}

function LiveBadge({ isDemo }: { isDemo: boolean }) {
  if (!isDemo) {
    return (
      <span className="flex items-center gap-0.5 text-[9px] px-1.5 py-0.5 rounded-full border border-green-200 bg-green-50 text-green-700 font-semibold uppercase tracking-wide">
        <span className="w-1.5 h-1.5 rounded-full bg-green-500 shrink-0" aria-hidden="true" />
        LIVE
      </span>
    )
  }
  return (
    <span className="text-[9px] px-1.5 py-0.5 rounded-full border border-amber-200 bg-amber-50 text-amber-700 font-semibold uppercase tracking-wide">
      DEMO
    </span>
  )
}

function EvidenceRow({ ev }: { ev: Evidence }) {
  const [expanded, setExpanded] = useState(false)

  const typeIcon = ev.evidence_type === 'clinical_trial'
    ? <FlaskConical size={14} className="text-green-600 shrink-0 mt-0.5" />
    : ev.evidence_type === 'protein_annotation'
    ? <Database size={14} className="text-violet-600 shrink-0 mt-0.5" />
    : <BookOpen size={14} className="text-blue-600 shrink-0 mt-0.5" />

  return (
    <div className={clsx(
      'ui-card overflow-hidden',
      ev.is_demo_data && 'opacity-75',
    )}>
      <div className="p-4">
        <div className="flex items-start gap-3">
          {typeIcon}
          <div className="flex-1 min-w-0">
            {/* Badge row */}
            <div className="flex items-center gap-2 flex-wrap mb-1.5">
              <LiveBadge isDemo={ev.is_demo_data} />
              <span className="text-[10px] px-2 py-0.5 rounded-full border border-slate-200 bg-slate-50 text-slate-600 font-medium">
                {ev.evidence_type.replace(/_/g, ' ')}
              </span>
              {ev.data_source && <SourcePill source={ev.data_source} />}
              {ev.drug_name && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-navy-50 text-navy-800 border border-navy-200 font-medium">
                  {ev.drug_name}
                </span>
              )}
              {ev.disease_name && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-50 text-violet-800 border border-violet-200 font-medium">
                  {ev.disease_name}
                </span>
              )}
            </div>

            {/* Title */}
            <p className="text-[14px] font-semibold text-slate-900 leading-snug">{ev.title}</p>

            {/* Authors / journal / date */}
            <div className="flex items-center gap-3 mt-1 flex-wrap text-[11px] text-slate-500">
              {(ev.authors?.length ?? 0) > 0 && (
                <span>{ev.authors.slice(0, 2).join(', ')}{(ev.authors?.length ?? 0) > 2 ? ' et al.' : ''}</span>
              )}
              {ev.journal && <span className="italic">{ev.journal}</span>}
              {ev.publication_date && <span>{ev.publication_date}</span>}
            </div>

            {ev.summary && (
              <p className="text-[12px] text-slate-500 mt-1.5 leading-relaxed">{ev.summary}</p>
            )}

            {/* Identifiers / source links */}
            <div className="flex items-center gap-3 mt-2 flex-wrap">
              {ev.is_demo_data ? (
                <span className="text-[11px] text-slate-400 italic">Demonstration record — no external source link</span>
              ) : ev.source_url ? (
                <a href={ev.source_url} target="_blank" rel="noopener noreferrer"
                  className="flex items-center gap-1 text-[11px] text-navy-600 hover:text-navy-800 font-medium transition-colors">
                  <ExternalLink size={10} /> View Source
                </a>
              ) : null}
              {!ev.is_demo_data && ev.doi    && <span className="text-[10px] text-slate-400 font-mono">DOI: {ev.doi}</span>}
              {!ev.is_demo_data && ev.pmid   && <span className="text-[10px] text-slate-400 font-mono">PMID: {ev.pmid}</span>}
              {!ev.is_demo_data && (ev as any).pmcid && <span className="text-[10px] text-slate-400 font-mono">PMCID: {(ev as any).pmcid}</span>}
              {!ev.is_demo_data && ev.nct_id && <span className="text-[10px] text-slate-400 font-mono">NCT: {ev.nct_id}</span>}
            </div>
          </div>

          {/* Expand toggle for abstract */}
          <button
            onClick={() => setExpanded(e => !e)}
            className="text-slate-400 hover:text-slate-600 transition-colors shrink-0 p-1 rounded hover:bg-slate-100"
            aria-label={expanded ? 'Collapse abstract' : 'Expand abstract'}
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>

        {/* Abstract */}
        {expanded && ev.abstract && (
          <div className="mt-3 ml-5 text-[12px] text-slate-500 leading-relaxed border-l-2 border-slate-200 pl-3 max-h-48 overflow-y-auto">
            {ev.abstract}
          </div>
        )}
      </div>
    </div>
  )
}

export function EvidencePage() {
  const [evidence,     setEvidence]     = useState<Evidence[]>([])
  const [loading,      setLoading]      = useState(true)
  const [loadingMore,  setLoadingMore]  = useState(false)
  const [page,         setPage]         = useState(0)
  const [hasMore,      setHasMore]      = useState(false)
  const [search,       setSearch]       = useState('')
  const [evidenceType, setEvidenceType] = useState('')
  const [provenance,   setProvenance]   = useState('')
  const PAGE_SIZE = 20
  const debouncedSearch = useDebounce(search, 350)

  useEffect(() => { setPage(0) }, [debouncedSearch, evidenceType, provenance])

  useEffect(() => {
    if (page === 0) setLoading(true)
    else setLoadingMore(true)

    const isDemo = provenance === 'demo' ? true : provenance === 'live' ? false : undefined
    evidenceApi.list({
      search: debouncedSearch || undefined,
      evidence_type: evidenceType || undefined,
      is_demo: isDemo,
      limit: PAGE_SIZE + 1,
      offset: page * PAGE_SIZE,
    })
      .then(res => {
        const hasNext = res.length > PAGE_SIZE
        const items = hasNext ? res.slice(0, PAGE_SIZE) : res
        setEvidence(prev => page === 0 ? items : [...prev, ...items])
        setHasMore(hasNext)
      })
      .finally(() => { setLoading(false); setLoadingMore(false) })
  }, [debouncedSearch, evidenceType, provenance, page])

  return (
    <div className="bg-app-bg min-h-screen">
      <Header title="Evidence Explorer" subtitle="Browse all indexed research evidence — fully source-traceable" />

      <div className="p-6 space-y-5">

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search evidence titles…"
            className="w-72"
          />

          {/* Type filter */}
          <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-lg p-1"
            style={{ boxShadow: '0 1px 2px 0 rgba(0,0,0,.04)' }}>
            {TYPE_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => setEvidenceType(opt.value)}
                className={clsx(
                  'px-2.5 py-1.5 text-[11px] rounded-md transition-colors font-medium whitespace-nowrap',
                  evidenceType === opt.value
                    ? 'bg-navy-900 text-white'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>

          {/* Live/demo filter */}
          <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-lg p-1"
            style={{ boxShadow: '0 1px 2px 0 rgba(0,0,0,.04)' }}>
            {PROVENANCE_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => setProvenance(opt.value)}
                className={clsx(
                  'px-2.5 py-1.5 text-[11px] rounded-md transition-colors font-medium',
                  provenance === opt.value
                    ? opt.value === 'live'
                      ? 'bg-green-600 text-white'
                      : opt.value === 'demo'
                      ? 'bg-amber-500 text-white'
                      : 'bg-navy-900 text-white'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>

          <span className="text-[12px] text-slate-500 ml-auto">
            {evidence.length} item{evidence.length !== 1 ? 's' : ''}
          </span>
        </div>

        {loading ? (
          <PageLoader />
        ) : evidence.length === 0 ? (
          <EmptyState icon={<FileText size={32} />} title="No evidence found" description="Adjust your search or filters." />
        ) : (
          <>
            <div className="space-y-3">
              {evidence.map(ev => <EvidenceRow key={ev.id} ev={ev} />)}
            </div>
            {hasMore && (
              <div className="flex justify-center pt-2">
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={loadingMore}
                  className="px-5 py-2 rounded-lg border border-slate-300 text-[12px] text-slate-600
                             hover:border-navy-400 hover:text-navy-700 transition-colors disabled:opacity-50 bg-white"
                >
                  {loadingMore ? 'Loading…' : 'Load more evidence'}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
