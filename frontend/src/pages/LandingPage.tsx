/**
 * LandingPage
 *
 * Public — no auth logic here. Auth-redirect is handled at the route level
 * in App.tsx (PublicHome wrapper), which prevents any flash or re-mount.
 *
 * Stats are fetched on mount with silent error handling; placeholders show
 * immediately so there is no loading flicker.
 */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  FlaskConical, ArrowRight, Shield, Database,
  BarChart2, CheckCircle2, ExternalLink,
  Layers, Zap, BookOpen, Activity, Lock,
  Award, ChevronRight, Menu, X, ChevronDown,
  Search, FileText,
} from 'lucide-react'
import { dashboardApi, signalsApi } from '../api'
import type { SignalListItem } from '../types'

// ─── static data ──────────────────────────────────────────────────────────────

const SOURCES = [
  { name: 'PubMed / NCBI',       type: 'Biomedical Literature',   desc: 'Peer-reviewed life-sciences research indexed by the US National Library of Medicine.',              accent: 'border-blue-200   bg-blue-50   text-blue-900',   dot: 'bg-blue-500'    },
  { name: 'ClinicalTrials.gov',  type: 'Clinical Evidence',       desc: 'Registered clinical studies providing structured human trial data across therapeutic areas.',       accent: 'border-green-200  bg-green-50  text-green-900',  dot: 'bg-green-600'   },
  { name: 'Elsevier / Scopus',   type: 'Scientific Literature',   desc: 'Global multidisciplinary publication database covering biomedical and pharmaceutical research.',    accent: 'border-orange-200 bg-orange-50 text-orange-900', dot: 'bg-orange-500'  },
  { name: 'Europe PMC',          type: 'Open-Access Literature',  desc: 'EBI open-access biomedical literature repository with full-text content and author manuscripts.',   accent: 'border-teal-200   bg-teal-50   text-teal-900',   dot: 'bg-teal-500'    },
  { name: 'UniProt',             type: 'Protein / Target Data',   desc: 'Curated protein sequence and functional annotation database including drug-target associations.',   accent: 'border-violet-200 bg-violet-50 text-violet-900', dot: 'bg-violet-500'  },
  { name: 'bioRxiv',             type: 'Preprint Server',         desc: 'Life-sciences preprint server providing early access to biological and biomedical manuscripts.',    accent: 'border-amber-200  bg-amber-50  text-amber-900',  dot: 'bg-amber-500'   },
  { name: 'medRxiv',             type: 'Medical Preprints',       desc: 'Health-sciences preprint server covering clinical medicine and epidemiological research.',           accent: 'border-rose-200   bg-rose-50   text-rose-900',   dot: 'bg-rose-500'    },
]

const PIPELINE_STEPS = [
  { n: '01', label: 'Ingest',      icon: Database,  desc: 'Research records fetched from all connected biomedical sources via official APIs with pagination.' },
  { n: '02', label: 'Normalize',   icon: FileText,  desc: 'Records standardised into a common schema. DOI, PMID, NCT ID and source URLs are preserved.' },
  { n: '03', label: 'Match',       icon: Search,    desc: 'Drug and disease entities are matched against the knowledge base using structured identifier lookup.' },
  { n: '04', label: 'Deduplicate', icon: Layers,    desc: 'Cross-source duplicates identified via DOI → PMID → title priority and counted only once.' },
  { n: '05', label: 'Prioritize',  icon: BarChart2, desc: 'Evidence scored across five factors: volume, clinical data, mechanism fit, source diversity, and recency.' },
]

const CAPABILITIES = [
  { icon: BookOpen, title: 'Evidence Traceability',        desc: 'Every score is traceable to individual records with DOI, PMID, NCT ID and direct source links.' },
  { icon: Layers,   title: 'Cross-Source Analysis',        desc: 'Evidence from 7 databases aggregated and deduplicated for accurate, non-inflated scoring.' },
  { icon: Zap,      title: 'Live Research Ingestion',      desc: 'Real evidence ingested on demand. Scores update automatically as new literature is indexed.' },
  { icon: Shield,   title: 'Source Integrity',             desc: 'Only peer-reviewed publications, registered trials, and curated databases contribute.' },
  { icon: Activity, title: 'Dynamic Drug + Disease Query', desc: 'Search any drug–disease pair. Queries sent to all sources dynamically — no hard-coded results.' },
  { icon: Lock,     title: 'Research-Only Platform',       desc: 'Computational intelligence exclusively. All signals require expert validation. Not clinical guidance.' },
]

const CHAIN_NODES = [
  { label: 'Drug',             sub: 'Matched entity',             bg: 'bg-blue-600'    },
  { label: 'Disease',          sub: 'Matched entity',             bg: 'bg-violet-600'  },
  { label: 'Evidence Record',  sub: 'From live source API',       bg: 'bg-sky-500'     },
  { label: 'Source Database',  sub: 'PubMed · EuropePMC · etc.',  bg: 'bg-teal-500'    },
  { label: 'Identifier',       sub: 'DOI · PMID · NCT',           bg: 'bg-emerald-500' },
  { label: 'Evidence Score',   sub: 'Computed from live records',  bg: 'bg-amber-500'   },
  { label: 'Research Signal',  sub: 'Prioritization candidate',   bg: 'bg-slate-500'   },
]

// ─── helpers ──────────────────────────────────────────────────────────────────

function ConfidenceDot({ level }: { level: string }) {
  const cls = level === 'high' ? 'bg-emerald-500' : level === 'medium' ? 'bg-amber-400' : 'bg-slate-400'
  return <span className={`w-2 h-2 rounded-full ${cls} shrink-0`} aria-hidden="true" />
}

function ScoreBar({ score }: { score: number }) {
  const fill = score >= 75 ? 'bg-emerald-500' : score >= 50 ? 'bg-amber-500' : 'bg-slate-400'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-slate-200 overflow-hidden">
        <div className={`h-full rounded-full ${fill} transition-all`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-xs font-semibold text-slate-700 w-7 text-right tabular-nums">{Math.round(score)}</span>
    </div>
  )
}

// ─── component ────────────────────────────────────────────────────────────────

export function LandingPage() {
  const [signalCount,    setSignalCount]    = useState<number | null>(null)
  const [evidenceCount,  setEvidenceCount]  = useState<number | null>(null)
  const [highConfCount,  setHighConfCount]  = useState<number | null>(null)
  const [signals,        setSignals]        = useState<SignalListItem[]>([])
  const [mobileOpen,     setMobileOpen]     = useState(false)

  useEffect(() => {
    // Silent — never blocks or flickers render
    dashboardApi.get().then(d => {
      setSignalCount(d.stats.total_signals)
      // total_research_sources = ResearchSource table count (raw fetched records)
      // We show this as "Research Sources Indexed" not "Evidence Records"
      setEvidenceCount(d.stats.total_research_sources)
      setHighConfCount(d.stats.high_confidence_signals)
    }).catch(() => {})

    signalsApi.list({ limit: 6, include_demo: false, sort_by: 'evidence_score' })
      .then(setSignals).catch(() => {})
  }, [])

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    setMobileOpen(false)
  }

  const NAV = [
    { id: 'overview',  label: 'Overview'         },
    { id: 'pipeline',  label: 'How It Works'     },
    { id: 'sources',   label: 'Evidence Sources' },
    { id: 'signals',   label: 'Signals'          },
    { id: 'about',     label: 'About'            },
  ]

  return (
    <div className="bg-white text-slate-900 antialiased">

      {/* ── INSTITUTIONAL TOP BAR ───────────────────────────────────────── */}
      <div className="hidden sm:block bg-[#0f2347] text-white/60 text-[11px] py-1.5">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <span>Government Research Intelligence Platform — Biotechnology · Drug Repurposing · Evidence Intelligence</span>
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" aria-hidden="true" />
            Research Platform Operational
          </span>
        </div>
      </div>

      {/* ── NAVIGATION ──────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 bg-white border-b border-slate-200" style={{ boxShadow: '0 1px 3px rgba(0,0,0,.06)' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-14">

            {/* Logo */}
            <Link to="/" className="flex items-center gap-2.5 shrink-0">
              <div className="w-8 h-8 rounded-lg bg-[#0f2347] flex items-center justify-center">
                <FlaskConical size={16} className="text-white" aria-hidden="true" />
              </div>
              <div className="leading-none">
                <p className="text-[13px] font-bold text-slate-900">BioArbitrage</p>
                <p className="text-[10px] text-slate-500">Drug Repurposing Intelligence</p>
              </div>
            </Link>

            {/* Desktop nav */}
            <nav className="hidden md:flex items-center gap-0.5" aria-label="Primary">
              {NAV.map(({ id, label }) => (
                <button key={id} onClick={() => scrollTo(id)}
                  className="px-3 py-1.5 text-[13px] text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-md transition-colors">
                  {label}
                </button>
              ))}
            </nav>

            {/* Actions */}
            <div className="hidden md:flex items-center gap-2">
              <Link to="/login"
                className="px-3 py-1.5 text-[13px] font-medium text-slate-700 hover:bg-slate-50 rounded-md transition-colors">
                Sign In
              </Link>
              <Link to="/login"
                className="px-4 py-1.5 text-[13px] font-semibold text-white bg-[#0f2347] hover:bg-[#183d73] rounded-md transition-colors"
                style={{ boxShadow: '0 1px 3px rgba(0,0,0,.18)' }}>
                Open Dashboard
              </Link>
            </div>

            {/* Mobile toggle */}
            <button className="md:hidden p-2 rounded-md text-slate-500 hover:bg-slate-100"
              onClick={() => setMobileOpen(v => !v)}
              aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={mobileOpen}>
              {mobileOpen ? <X size={18} /> : <Menu size={18} />}
            </button>
          </div>
        </div>

        {/* Mobile nav panel */}
        {mobileOpen && (
          <div className="md:hidden border-t border-slate-100 bg-white px-4 py-3 space-y-0.5">
            {NAV.map(({ id, label }) => (
              <button key={id} onClick={() => scrollTo(id)}
                className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md">
                {label}
              </button>
            ))}
            <div className="pt-3 border-t border-slate-100">
              <Link to="/login" onClick={() => setMobileOpen(false)}
                className="flex items-center justify-center gap-2 py-2 px-4 rounded-md bg-[#0f2347] text-white text-sm font-semibold">
                Open Research Dashboard <ArrowRight size={14} />
              </Link>
            </div>
          </div>
        )}
      </header>

      {/* ── HERO ────────────────────────────────────────────────────────── */}
      <section id="overview" className="bg-[#0f2347] text-white" aria-labelledby="hero-h1">

        {/* Top saffron rule */}
        <div className="h-1 bg-gradient-to-r from-amber-400 via-amber-500 to-amber-400" aria-hidden="true" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-16 lg:py-24">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">

            {/* Left — copy */}
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/20 bg-white/8 text-[11px] text-white/70 mb-6">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400" aria-hidden="true" />
                Live Research Platform · 7 Connected Sources
              </div>
              <h1 id="hero-h1" className="text-3xl sm:text-4xl font-bold leading-tight mb-4">
                Real-Time Intelligence for<br />
                <span className="text-amber-400">Drug Repurposing Research</span>
              </h1>
              <p className="text-white/70 text-base leading-relaxed mb-4 max-w-lg">
                A research intelligence platform that continuously aggregates biomedical literature,
                clinical trial data, and molecular annotations to identify and prioritize
                potential drug repurposing opportunities.
              </p>
              <p className="text-white/45 text-sm leading-relaxed mb-8 max-w-lg border-l-2 border-white/15 pl-4">
                All signals are computational research candidates requiring expert scientific and
                clinical validation. Not clinical guidance or treatment recommendations.
              </p>

              <div className="flex flex-wrap gap-3">
                <Link to="/login"
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-amber-500 hover:bg-amber-400 text-white font-semibold rounded-md transition-colors text-sm"
                  style={{ boxShadow: '0 2px 8px rgba(0,0,0,.25)' }}>
                  Explore Research Dashboard
                  <ArrowRight size={15} />
                </Link>
                <button onClick={() => scrollTo('sources')}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-white/10 hover:bg-white/18 text-white font-medium rounded-md border border-white/25 transition-colors text-sm">
                  View Evidence Sources
                  <ChevronDown size={15} />
                </button>
              </div>

              {/* Trust row */}
              <div className="flex flex-wrap gap-6 mt-10 pt-8 border-t border-white/10 text-[12px] text-white/55">
                {[
                  { v: signalCount,   label: 'Research Signals'       },
                  { v: evidenceCount, label: 'Research Sources Indexed'},
                  { v: 7,             label: 'Biomedical Databases'    },
                  { v: highConfCount, label: 'High-Confidence Signals' },
                ].map(({ v, label }) => (
                  <div key={label}>
                    <p className="text-xl font-bold text-white tabular-nums">{v != null ? v.toLocaleString() : '—'}</p>
                    <p>{label}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Right — evidence flow diagram */}
            <div className="hidden lg:flex flex-col items-start gap-0 bg-white/6 rounded-2xl border border-white/10 p-7">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-white/40 mb-5">Evidence → Signal Flow</p>
              {[
                { label: 'Research Source',  sub: 'PubMed · EuropePMC · Elsevier · UniProt', color: 'bg-blue-500'   },
                { label: 'Evidence Record',  sub: 'Normalized · Deduplicated · Identified',   color: 'bg-teal-500'  },
                { label: 'Drug Entity',      sub: 'Matched against knowledge base',           color: 'bg-amber-500' },
                { label: 'Disease Entity',   sub: 'Matched against knowledge base',           color: 'bg-violet-500'},
                { label: 'Evidence Score',   sub: 'Multi-factor · Live evidence only',        color: 'bg-emerald-500'},
                { label: 'Research Signal',  sub: 'Traceable · Expert validation required',   color: 'bg-slate-400' },
              ].map(({ label, sub, color }, i, arr) => (
                <div key={label} className="w-full">
                  <div className="flex items-center gap-3 py-2.5">
                    <div className={`w-2.5 h-2.5 rounded-full ${color} shrink-0`} aria-hidden="true" />
                    <div>
                      <span className="text-sm font-semibold text-white">{label}</span>
                      <span className="text-[11px] text-white/40 ml-2">{sub}</span>
                    </div>
                  </div>
                  {i < arr.length - 1 && (
                    <div className="ml-[5px] h-4 w-px bg-white/10" aria-hidden="true" />
                  )}
                </div>
              ))}
            </div>

          </div>
        </div>
      </section>

      {/* ── CAPABILITIES ────────────────────────────────────────────────── */}
      <section className="py-14 lg:py-20 bg-slate-50 border-y border-slate-200" aria-labelledby="cap-h2">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-10">
            <h2 id="cap-h2" className="text-2xl font-bold text-slate-900 mb-2">From Biomedical Evidence to Research Signals</h2>
            <p className="text-slate-500 max-w-xl mx-auto text-sm">
              Designed for biomedical researchers, pharmaceutical scientists, and research institutions.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {CAPABILITIES.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="bg-white rounded-xl border border-slate-200 p-5 hover:border-slate-300 transition-colors"
                style={{ boxShadow: '0 1px 3px rgba(0,0,0,.05)' }}>
                <div className="w-9 h-9 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-center mb-3">
                  <Icon size={16} className="text-[#0f2347]" aria-hidden="true" />
                </div>
                <h3 className="text-sm font-semibold text-slate-900 mb-1.5">{title}</h3>
                <p className="text-[13px] text-slate-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ────────────────────────────────────────────────── */}
      <section id="pipeline" className="py-14 lg:py-20 bg-white" aria-labelledby="pipe-h2">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-10">
            <h2 id="pipe-h2" className="text-2xl font-bold text-slate-900 mb-2">Scientific Methodology</h2>
            <p className="text-slate-500 max-w-xl mx-auto text-sm">A transparent, reproducible pipeline from evidence retrieval to signal prioritization.</p>
          </div>

          {/* Horizontal steps — desktop */}
          <div className="hidden md:flex items-start gap-0 max-w-5xl mx-auto">
            {PIPELINE_STEPS.map(({ n, label, icon: Icon, desc }, i) => (
              <div key={n} className="flex-1 flex items-start gap-0">
                <div className="flex flex-col items-center flex-1">
                  {/* Connector line */}
                  <div className="flex items-center w-full">
                    <div className={`flex-none w-10 h-10 rounded-full bg-[#0f2347] flex items-center justify-center text-white ${i === 0 ? 'ml-auto mr-0' : 'mx-auto'}`}>
                      <Icon size={16} aria-hidden="true" />
                    </div>
                    {i < PIPELINE_STEPS.length - 1 && (
                      <div className="flex-1 h-px bg-slate-200" aria-hidden="true" />
                    )}
                  </div>
                  <div className="mt-3 px-2 text-center">
                    <p className="text-[10px] font-bold text-slate-400 font-mono">{n}</p>
                    <p className="text-sm font-semibold text-slate-900 mt-0.5">{label}</p>
                    <p className="text-[12px] text-slate-500 mt-1 leading-relaxed">{desc}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Vertical — mobile */}
          <div className="md:hidden max-w-lg mx-auto space-y-0">
            {PIPELINE_STEPS.map(({ n, label, icon: Icon, desc }, i) => (
              <div key={n} className="flex gap-4">
                <div className="flex flex-col items-center shrink-0">
                  <div className="w-9 h-9 rounded-full bg-[#0f2347] flex items-center justify-center text-white shrink-0">
                    <Icon size={15} aria-hidden="true" />
                  </div>
                  {i < PIPELINE_STEPS.length - 1 && <div className="w-px flex-1 bg-slate-200 my-1" aria-hidden="true" />}
                </div>
                <div className="pb-6">
                  <span className="text-[10px] font-bold font-mono text-slate-400">{n}</span>
                  <p className="text-sm font-semibold text-slate-900 mt-0.5">{label}</p>
                  <p className="text-[13px] text-slate-500 mt-1 leading-relaxed">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── EVIDENCE SOURCES ────────────────────────────────────────────── */}
      <section id="sources" className="py-14 lg:py-20 bg-slate-50 border-y border-slate-200" aria-labelledby="src-h2">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-green-50 border border-green-200 text-[11px] text-green-700 font-medium mb-4">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500" aria-hidden="true" />
              Integrated Evidence Sources
            </div>
            <h2 id="src-h2" className="text-2xl font-bold text-slate-900 mb-2">Trusted Biomedical Databases</h2>
            <p className="text-slate-500 max-w-xl mx-auto text-sm">
              Evidence retrieved via official APIs with full source attribution and identifier preservation.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {SOURCES.map(({ name, type, desc, accent, dot }) => (
              <div key={name} className={`rounded-xl border p-4 ${accent}`}>
                <div className="flex items-center gap-2 mb-2">
                  <span className={`w-2 h-2 rounded-full ${dot} shrink-0`} aria-hidden="true" />
                  <span className="text-[10px] font-semibold uppercase tracking-wide opacity-60">{type}</span>
                </div>
                <p className="text-sm font-bold mb-1">{name}</p>
                <p className="text-[12px] leading-relaxed opacity-75">{desc}</p>
              </div>
            ))}
          </div>
          <p className="text-center text-[11px] text-slate-400 mt-6">
            Connectivity verified at runtime. Source availability subject to API key configuration and provider uptime.
          </p>
        </div>
      </section>

      {/* ── TRACEABILITY ────────────────────────────────────────────────── */}
      <section className="py-14 lg:py-20 bg-[#0f2347] text-white" aria-labelledby="trace-h2">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 id="trace-h2" className="text-2xl font-bold mb-4 leading-tight">Every Signal Is Traceable to Its Evidence</h2>
              <p className="text-white/65 text-sm leading-relaxed mb-6">
                The platform maintains an unbroken provenance chain from evidence score back to the source record.
                Every contributing evidence item can be inspected with its original identifier and direct link.
              </p>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { id: 'DOI',        desc: 'Digital Object Identifier for publications'    },
                  { id: 'PMID',       desc: 'PubMed unique record identifier'               },
                  { id: 'PMCID',      desc: 'PubMed Central full-text identifier'           },
                  { id: 'NCT ID',     desc: 'ClinicalTrials.gov trial registration number'  },
                  { id: 'UniProt ID', desc: 'Protein accession identifier'                  },
                  { id: 'Source URL', desc: 'Direct link to the original source record'     },
                ].map(({ id, desc }) => (
                  <div key={id} className="flex items-start gap-2">
                    <CheckCircle2 size={13} className="text-green-400 shrink-0 mt-0.5" aria-hidden="true" />
                    <div>
                      <p className="text-xs font-semibold text-white">{id}</p>
                      <p className="text-[11px] text-white/45 leading-snug">{desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-[#081225] rounded-2xl border border-white/10 p-6">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-white/35 mb-4">Evidence → Signal Provenance Chain</p>
              {CHAIN_NODES.map(({ label, sub, bg }, i, arr) => (
                <div key={label}>
                  <div className="flex items-center gap-3 py-2">
                    <div className={`w-2.5 h-2.5 rounded-full ${bg} shrink-0`} aria-hidden="true" />
                    <div>
                      <span className="text-sm font-semibold text-white">{label}</span>
                      <span className="text-[11px] text-white/40 ml-2">{sub}</span>
                    </div>
                  </div>
                  {i < arr.length - 1 && <div className="ml-[5px] h-4 w-px bg-white/10" aria-hidden="true" />}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── SIGNAL PREVIEW ──────────────────────────────────────────────── */}
      <section id="signals" className="py-14 lg:py-20 bg-white" aria-labelledby="sig-h2">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
            <div>
              <h2 id="sig-h2" className="text-2xl font-bold text-slate-900 mb-1">Latest Research Signals</h2>
              <p className="text-slate-500 text-sm">Live data — ranked by evidence score. Sign in to explore all signals.</p>
            </div>
            <Link to="/login"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-[#0f2347] border border-slate-300 hover:border-slate-400 hover:bg-slate-50 px-4 py-2 rounded-md transition-colors shrink-0">
              View All <ChevronRight size={14} />
            </Link>
          </div>

          {signals.length === 0 ? (
            <div className="text-center py-12 border border-dashed border-slate-200 rounded-xl text-slate-400">
              <BookOpen size={28} className="mx-auto mb-2 opacity-40" aria-hidden="true" />
              <p className="text-sm">Sign in to view live research signals</p>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50">
                    {['Drug', 'Disease', 'Evidence Score', 'Records', 'Sources', 'Confidence', ''].map(h => (
                      <th key={h} className="text-left text-[11px] font-semibold text-slate-500 px-4 py-3 whitespace-nowrap">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {signals.map(sig => (
                    <tr key={sig.id} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3">
                        <span className="text-[13px] font-semibold text-slate-900">{sig.drug_name}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-[13px] text-slate-700">{sig.disease_name}</span>
                      </td>
                      <td className="px-4 py-3 w-36">
                        <ScoreBar score={sig.evidence_score} />
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-[13px] text-slate-600 tabular-nums">{sig.unique_evidence_count ?? sig.source_count}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-[13px] text-slate-600">{(sig.source_names ?? []).filter(s => s !== 'demo').length || sig.source_count}</span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5">
                          <ConfidenceDot level={sig.confidence_level} />
                          <span className="text-[12px] text-slate-600 capitalize">{sig.confidence_level}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Link to="/login"
                          className="inline-flex items-center gap-1 text-[12px] text-[#0f2347] hover:underline font-medium"
                          aria-label={`View signal for ${sig.drug_name}`}>
                          View <ExternalLink size={10} />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────────────────────── */}
      <section className="py-12 bg-slate-50 border-t border-slate-200">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 text-center">
          <h2 className="text-xl font-bold text-slate-900 mb-2">Explore the Research Intelligence Dashboard</h2>
          <p className="text-slate-500 text-sm mb-6">
            Access live signals, source breakdowns, evidence traceability, and ingestion controls.
          </p>
          <Link to="/login"
            className="inline-flex items-center gap-2 px-6 py-2.5 bg-[#0f2347] hover:bg-[#183d73] text-white font-semibold rounded-md transition-colors text-sm"
            style={{ boxShadow: '0 2px 8px rgba(0,0,0,.18)' }}>
            Open Dashboard <ArrowRight size={15} />
          </Link>
        </div>
      </section>

      {/* ── DISCLAIMER ──────────────────────────────────────────────────── */}
      <section id="about" className="py-10 bg-white border-t border-slate-200">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 text-center">
          <div className="w-9 h-9 rounded-full bg-amber-50 border border-amber-200 flex items-center justify-center mx-auto mb-3">
            <Award size={16} className="text-amber-600" aria-hidden="true" />
          </div>
          <h2 className="text-base font-bold text-slate-800 mb-2">Research Intelligence Platform — Not Clinical Guidance</h2>
          <p className="text-[13px] text-slate-500 leading-relaxed">
            This platform provides computational research intelligence and evidence aggregation for research prioritization only.
            Drug repurposing signals are candidates generated through automated analysis of published literature,
            clinical trial registries, and biological databases. They do not establish clinical efficacy,
            safety, or fitness for medical use. Rigorous scientific investigation and regulatory review
            are required before any finding can be applied in clinical practice.
            Platform intended for use by qualified biomedical researchers and research institutions.
          </p>
        </div>
      </section>

      {/* ── FOOTER ──────────────────────────────────────────────────────── */}
      <footer className="bg-[#0a1a38] text-white py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-6">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-md bg-white/10 flex items-center justify-center">
                <FlaskConical size={14} className="text-white" aria-hidden="true" />
              </div>
              <div>
                <p className="text-[13px] font-bold">Real-Time Biotech Arbitrage Engine</p>
                <p className="text-[11px] text-white/40">AI-Assisted Drug Repurposing Intelligence Platform</p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-5 text-[12px] text-white/40">
              {['overview','pipeline','sources','signals','about'].map(id => (
                <button key={id} onClick={() => scrollTo(id)} className="hover:text-white/70 capitalize transition-colors">
                  {id === 'pipeline' ? 'How It Works' : id.charAt(0).toUpperCase() + id.slice(1)}
                </button>
              ))}
            </div>
            <Link to="/login"
              className="inline-flex items-center gap-2 px-4 py-1.5 bg-white/10 hover:bg-white/18 text-sm font-medium text-white rounded-md border border-white/15 transition-colors">
              Open Dashboard <ArrowRight size={13} />
            </Link>
          </div>
          <div className="pt-5 border-t border-white/8 flex flex-col md:flex-row items-center justify-between gap-2 text-[11px] text-white/25">
            <p>Research decision-support tool only. Not for clinical use, diagnosis, or treatment recommendations.</p>
            <p>Evidence sourced from publicly accessible biomedical databases via official APIs.</p>
          </div>
        </div>
      </footer>

    </div>
  )
}
