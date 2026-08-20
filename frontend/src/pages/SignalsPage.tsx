import { useEffect, useState } from 'react'
import { Header } from '../components/Header'
import { SignalCard } from '../components/SignalCard'
import { SearchInput } from '../components/ui/SearchInput'
import { PageLoader } from '../components/ui/Spinner'
import { EmptyState } from '../components/ui/EmptyState'
import { Card, CardHeader, CardTitle } from '../components/ui/Card'
import { ConfidenceDistributionChart } from '../components/ConfidenceDistributionChart'
import { signalsApi } from '../api'
import type { SignalListItem } from '../types'
import { useDebounce } from '../hooks/useDebounce'
import { Zap } from 'lucide-react'
import { clsx } from 'clsx'

const CONFIDENCE_OPTIONS = [
  { label: 'All', value: '' },
  { label: 'High', value: 'high' },
  { label: 'Medium', value: 'medium' },
  { label: 'Low', value: 'low' },
]

const SORT_OPTIONS = [
  { label: 'Evidence Score', value: 'evidence_score' },
  { label: 'Most Recent', value: 'detected_at' },
]

export function SignalsPage() {
  const [signals, setSignals] = useState<SignalListItem[]>([])
  const [allSignals, setAllSignals] = useState<SignalListItem[]>([]) // unfiltered, for chart
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [page, setPage] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [search, setSearch] = useState('')
  const [confidence, setConfidence] = useState('')
  const [sortBy, setSortBy] = useState('evidence_score')
  const PAGE_SIZE = 12

  const debouncedSearch = useDebounce(search, 350)

  // fetch unfiltered list once for distribution chart
  useEffect(() => {
    signalsApi.list({ limit: 200 }).then(setAllSignals).catch(() => {})
  }, [])

  // Reset page when filters change
  useEffect(() => { setPage(0) }, [debouncedSearch, confidence, sortBy])

  useEffect(() => {
    if (page === 0) setLoading(true)
    else setLoadingMore(true)

    signalsApi.list({
      search: debouncedSearch || undefined,
      confidence: confidence || undefined,
      sort_by: sortBy,
      limit: PAGE_SIZE + 1,   // fetch one extra to check if more exist
      offset: page * PAGE_SIZE,
    })
      .then((res) => {
        const hasNext = res.length > PAGE_SIZE
        const items = hasNext ? res.slice(0, PAGE_SIZE) : res
        setSignals((prev) => page === 0 ? items : [...prev, ...items])
        setHasMore(hasNext)
      })
      .finally(() => { setLoading(false); setLoadingMore(false) })
  }, [debouncedSearch, confidence, sortBy, page])

  const distHigh   = allSignals.filter((s) => s.confidence_level === 'high').length
  const distMedium = allSignals.filter((s) => s.confidence_level === 'medium').length
  const distLow    = allSignals.filter((s) => s.confidence_level === 'low').length

  return (
    <div>
      <Header
        title="Research Signals"
        subtitle="Drug repurposing candidates ranked by evidence score — live evidence only"
      />

      <div className="p-6 space-y-5">

        {/* Disclaimer */}
        <div className="text-[12px] text-slate-500 bg-slate-50 rounded-lg px-4 py-2 border border-slate-200">
          Evidence scores are experimental research-prioritization scores — not clinical probabilities or treatment recommendations.
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search signals, drugs, diseases…"
            className="w-72"
          />

          <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-lg p-1"
            style={{ boxShadow: '0 1px 2px 0 rgba(0,0,0,.04)' }}>
            {CONFIDENCE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setConfidence(opt.value)}
                className={clsx(
                  'px-3 py-1.5 text-[12px] rounded-md transition-colors font-medium',
                  confidence === opt.value
                    ? 'bg-navy-900 text-white'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-2 text-[12px] bg-white border border-slate-300 rounded-lg
                       text-slate-700 focus:outline-none focus:border-navy-500 focus:ring-2 focus:ring-navy-500/15"
            style={{ boxShadow: '0 1px 2px 0 rgba(0,0,0,.04)' }}
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>

          <span className="text-[12px] text-slate-500 ml-auto">{signals.length} signal{signals.length !== 1 ? 's' : ''}</span>
        </div>

        {/* Distribution chart + signal grid */}
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          {/* Sidebar: distribution */}
          <Card className="xl:col-span-1 h-fit">
            <CardHeader>
              <CardTitle>Confidence Distribution</CardTitle>
            </CardHeader>
            <ConfidenceDistributionChart
              high={distHigh}
              medium={distMedium}
              low={distLow}
            />
            <div className="mt-3 space-y-1.5 text-xs">
              {[
                ['high','emerald',distHigh],
                ['medium','amber',distMedium],
                ['low','slate',distLow],
              ].map(([level, color, count]) => (
                <div key={level as string} className="flex items-center justify-between">
                  <span className="text-slate-500 capitalize">{level as string}</span>
                  <span className={`font-semibold text-${color as string}-600`}>{count as number}</span>
                </div>
              ))}
            </div>
          </Card>

          {/* Main grid */}
          <div className="xl:col-span-3 space-y-4">
            {loading ? (
              <PageLoader />
            ) : signals.length === 0 ? (
              <EmptyState
                icon={<Zap size={32} />}
                title="No signals found"
                description="Try adjusting your search or filter criteria."
              />
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {signals.map((s) => (
                    <SignalCard key={s.id} signal={s} />
                  ))}
                </div>
                {hasMore && (
                  <div className="flex justify-center pt-2">
                    <button
                      onClick={() => setPage((p) => p + 1)}
                      disabled={loadingMore}
                      className="px-5 py-2 rounded-lg border border-slate-300 text-[12px] text-slate-600
                                 hover:border-navy-400 hover:text-navy-700 transition-colors disabled:opacity-50 bg-white"
                    >
                      {loadingMore ? 'Loading…' : 'Load more signals'}
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
