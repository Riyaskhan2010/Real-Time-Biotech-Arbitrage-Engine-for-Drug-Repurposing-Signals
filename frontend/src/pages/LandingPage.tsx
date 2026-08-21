/**
 * LandingPage — BioArbitrage
 *
 * PUBLIC route. No auth redirect here. Auth-redirect removed from PublicHome
 * in App.tsx and from the axios interceptor in client.ts (401 without a token
 * no longer triggers window.location.href = '/login').
 *
 * API calls use .catch(() => {}) so backend unavailability never crashes the page.
 */
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  FlaskConical, ArrowRight, Database, Search, Layers,
  BarChart2, CheckCircle2, ExternalLink, Shield,
  BookOpen, Activity, Lock, Zap, FileText,
  ChevronDown, Menu, X, Award, TrendingUp,
  Dna, Network, GitMerge, Target, Microscope,
} from 'lucide-react'
import { dashboardApi, signalsApi } from '../api'
import type { SignalListItem } from '../types'

// ─── Design tokens ────────────────────────────────────────────────────────────
// Dark navy hero, white content sections — consistent with app shell
const NAVY  = '#0B1F3A'
const NAVY2 = '#071429'
const ACCENT= '#F59E0B'   // amber/saffron accent

// ─── Static content ───────────────────────────────────────────────────────────

const NAV_LINKS = [
  { id: 'overview', label: 'Overview' },
  { id: 'pipeline', label: 'How It Works' },
  { id: 'features', label: 'Features' },
  { id: 'sources',  label: 'Evidence' },
  { id: 'signals',  label: 'Signals' },
]

const PIPELINE_STEPS = [
  {
    n: '01', label: 'Ingest', icon: Database, color: '#3B82F6',
    desc: 'Research records fetched from 7 connected biomedical sources via official APIs with full pagination.',
  },
  {
    n: '02', label: 'Normalize', icon: FileText, color: '#8B5CF6',
    desc: 'Records standardized into a common schema. DOI, PMID, NCT ID and source URLs are preserved.',
  },
  {
    n: '03', label: 'Match', icon: Search, color: '#F59E0B',
    desc: 'Drug and disease entities matched against the knowledge base using structured identifier lookup.',
  },
  {
    n: '04', label: 'Deduplicate', icon: Layers, color: '#10B981',
    desc: 'Cross-source duplicates identified via DOI → PMID → title priority and counted only once.',
  },
  {
    n: '05', label: 'Prioritize', icon: BarChart2, color: '#EF4444',
    desc: 'Evidence scored across five factors: volume, clinical data, mechanism fit, source diversity, recency.',
  },
]

const FEATURES = [
  {
    icon: BookOpen, color: '#3B82F6', title: 'Evidence Traceability',
    desc: 'Every signal is traceable to individual evidence records with DOI, PMID, NCT ID and direct source links.',
  },
  {
    icon: Layers, color: '#8B5CF6', title: 'Cross-Source Analysis',
    desc: 'Evidence from 7 biomedical databases aggregated and deduplicated for accurate, non-inflated scoring.',
  },
  {
    icon: Zap, color: '#F59E0B', title: 'Live Research Ingestion',
    desc: 'Evidence ingested on demand. Scores update automatically as new literature and trials are indexed.',
  },
  {
    icon: Shield, color: '#10B981', title: 'Source Integrity',
    desc: 'Only peer-reviewed publications, registered trials and curated databases contribute to signals.',
  },
  {
    icon: Activity, color: '#EF4444', title: 'Dynamic Drug + Disease Query',
    desc: 'Search any drug–disease combination. Queries sent to all sources dynamically — no hard-coded results.',
  },
  {
    icon: Lock, color: '#6366F1', title: 'Research-Only Intelligence',
    desc: 'Computational signals require expert scientific validation. Explicitly not clinical guidance.',
  },
]

const SOURCES = [
  { name: 'PubMed / NCBI',      type: 'Biomedical Literature',  desc: 'Peer-reviewed life-sciences research indexed by the US National Library of Medicine.',        dot: '#3B82F6' },
  { name: 'ClinicalTrials.gov', type: 'Clinical Evidence',      desc: 'Registered clinical studies providing structured human trial data across therapeutic areas.',    dot: '#10B981' },
  { name: 'Elsevier / Scopus',  type: 'Scientific Literature',  desc: 'Multidisciplinary publication database covering biomedical and pharmaceutical research.',        dot: '#F59E0B' },
  { name: 'Europe PMC',         type: 'Open-Access Literature', desc: 'EBI open-access repository with full-text content, PMCID, and author manuscripts.',            dot: '#14B8A6' },
  { name: 'UniProt',            type: 'Protein / Target Data',  desc: 'Curated protein sequence and functional annotation database with drug-target associations.',    dot: '#8B5CF6' },
  { name: 'bioRxiv',            type: 'Preprint Server',        desc: 'Life-sciences preprint server providing early access to biological and biomedical manuscripts.', dot: '#F97316' },
  { name: 'medRxiv',            type: 'Medical Preprints',      desc: 'Health-sciences preprint server covering clinical medicine and epidemiological research.',       dot: '#EF4444' },
]

const PROVENANCE_ITEMS = [
  { id: 'DOI',        desc: 'Digital Object Identifier' },
  { id: 'PMID',       desc: 'PubMed unique record ID' },
  { id: 'PMCID',      desc: 'PubMed Central full-text ID' },
  { id: 'NCT ID',     desc: 'ClinicalTrials registration' },
  { id: 'UniProt ID', desc: 'Protein accession' },
  { id: 'Source URL', desc: 'Direct original source link' },
]

// ─── Tiny helpers ─────────────────────────────────────────────────────────────

function ScorePill({ score }: { score: number }) {
  const pct  = Math.min(score, 100)
  const fill = pct >= 75 ? '#10B981' : pct >= 50 ? '#F59E0B' : '#94A3B8'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-slate-200 overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: fill }} />
      </div>
      <span className="text-xs font-bold tabular-nums" style={{ color: fill }}>{Math.round(pct)}</span>
    </div>
  )
}

function ConfDot({ level }: { level: string }) {
  const c = level === 'high' ? '#10B981' : level === 'medium' ? '#F59E0B' : '#94A3B8'
  return <span className="w-2 h-2 rounded-full inline-block" style={{ background: c }} />
}

// ─── Sections ────────────────────────────────────────────────────────────────

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-widest px-3 py-1 rounded-full border mb-4"
      style={{ background: '#EFF6FF', border: '1px solid #BFDBFE', color: '#1D4ED8' }}>
      {children}
    </span>
  )
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mb-3" style={{ color: NAVY }}>{children}</h2>
}

function SectionSub({ children }: { children: React.ReactNode }) {
  return <p className="text-slate-500 text-sm sm:text-base leading-relaxed max-w-xl">{children}</p>
}

// ─── Main component ───────────────────────────────────────────────────────────

export function LandingPage() {
  const [signals,       setSignals]       = useState<SignalListItem[]>([])
  const [totalSignals,  setTotalSignals]  = useState<number | null>(null)
  const [sourcesCount,  setSourcesCount]  = useState<number | null>(null)
  const [highConf,      setHighConf]      = useState<number | null>(null)
  const [mobileOpen,    setMobileOpen]    = useState(false)
  const [scrolled,      setScrolled]      = useState(false)

  // Track scroll for navbar style
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // Fetch live data silently — never blocks render, never redirects on failure
  useEffect(() => {
    dashboardApi.get().then(d => {
      setTotalSignals(d.stats.total_signals)
      setSourcesCount(d.stats.total_research_sources)
      setHighConf(d.stats.high_confidence_signals)
    }).catch(() => {})

    signalsApi.list({ limit: 6, include_demo: false, sort_by: 'evidence_score' })
      .then(setSignals).catch(() => {})
  }, [])

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    setMobileOpen(false)
  }

  // ── Navbar ────────────────────────────────────────────────────────────────
  return (
    <div className="bg-white text-slate-900 antialiased">

      {/* TOP STRIP */}
      <div className="hidden sm:flex items-center justify-between px-6 py-1.5 text-[11px]"
        style={{ background: NAVY, color: 'rgba(255,255,255,0.5)' }}>
        <span>Government Research Intelligence Platform · Biotechnology · Drug Repurposing · Evidence Intelligence</span>
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
          Platform Operational
        </span>
      </div>

      {/* NAVBAR */}
      <header
        className="sticky top-0 z-50 transition-all duration-200"
        style={{
          background: scrolled ? 'rgba(255,255,255,0.97)' : 'white',
          borderBottom: '1px solid #E2E8F0',
          boxShadow: scrolled ? '0 2px 12px rgba(0,0,0,.06)' : '0 1px 3px rgba(0,0,0,.04)',
          backdropFilter: 'blur(8px)',
        }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
          {/* Brand */}
          <Link to="/" className="flex items-center gap-2.5 shrink-0">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: NAVY }}>
              <FlaskConical size={16} className="text-white" />
            </div>
            <div className="leading-none">
              <p className="text-[13px] font-bold" style={{ color: NAVY }}>BioArbitrage</p>
              <p className="text-[10px] text-slate-400">Drug Repurposing Intelligence</p>
            </div>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-0.5">
            {NAV_LINKS.map(({ id, label }) => (
              <button key={id} onClick={() => scrollTo(id)}
                className="px-3 py-1.5 text-[13px] text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-md transition-colors font-medium">
                {label}
              </button>
            ))}
          </nav>

          {/* Actions */}
          <div className="hidden md:flex items-center gap-2">
            <Link to="/login"
              className="px-3 py-1.5 text-[13px] font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-md transition-colors">
              Sign In
            </Link>
            <Link to="/login"
              className="inline-flex items-center gap-1.5 px-4 py-1.5 text-[13px] font-semibold text-white rounded-md transition-colors"
              style={{ background: NAVY }}>
              Open Dashboard <ArrowRight size={13} />
            </Link>
          </div>

          {/* Mobile toggle */}
          <button className="md:hidden p-2 rounded-md text-slate-500 hover:bg-slate-100"
            onClick={() => setMobileOpen(v => !v)}
            aria-label={mobileOpen ? 'Close menu' : 'Open menu'}>
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>

        {/* Mobile panel */}
        {mobileOpen && (
          <div className="md:hidden border-t border-slate-100 bg-white px-4 py-3 space-y-0.5">
            {NAV_LINKS.map(({ id, label }) => (
              <button key={id} onClick={() => scrollTo(id)}
                className="w-full text-left px-3 py-2.5 text-sm text-slate-700 hover:bg-slate-50 rounded-md font-medium">
                {label}
              </button>
            ))}
            <div className="pt-3 border-t border-slate-100">
              <Link to="/login" onClick={() => setMobileOpen(false)}
                className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-md text-white text-sm font-semibold"
                style={{ background: NAVY }}>
                Open Research Dashboard <ArrowRight size={14} />
              </Link>
            </div>
          </div>
        )}
      </header>

      {/* ── HERO ──────────────────────────────────────────────────────────── */}
      <section id="overview" style={{ background: `linear-gradient(135deg, ${NAVY2} 0%, ${NAVY} 55%, #152F75 100%)` }}>
        {/* amber rule */}
        <div className="h-1" style={{ background: `linear-gradient(90deg, ${ACCENT}, #F97316, ${ACCENT})` }} />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-16 lg:py-24">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">

            {/* Left */}
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/20 bg-white/8 text-[11px] text-white/70 mb-5">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                Live Research Platform · 7 Connected Sources
              </div>

              <h1 className="text-3xl sm:text-4xl lg:text-[2.6rem] font-extrabold leading-tight text-white mb-4">
                Real-Time Intelligence for<br />
                <span style={{ color: ACCENT }}>Drug Repurposing Research</span>
              </h1>

              <p className="text-white/70 text-base leading-relaxed mb-3 max-w-lg">
                Continuously analyze biomedical literature, clinical trial data, and molecular evidence
                to discover and prioritize potential drug–disease research opportunities.
              </p>

              <p className="text-white/40 text-xs leading-relaxed mb-8 max-w-lg border-l-2 border-white/15 pl-3">
                Computational research candidates requiring expert scientific and clinical validation.
                Not clinical guidance or treatment recommendations.
              </p>

              <div className="flex flex-wrap gap-3">
                <Link to="/login"
                  className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-bold text-white rounded-lg transition-all hover:scale-105"
                  style={{ background: ACCENT, boxShadow: `0 4px 20px ${ACCENT}55` }}>
                  Explore Research Dashboard <ArrowRight size={15} />
                </Link>
                <button onClick={() => scrollTo('pipeline')}
                  className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white rounded-lg border border-white/25 bg-white/8 hover:bg-white/15 transition-colors">
                  See How It Works <ChevronDown size={15} />
                </button>
              </div>

              {/* Stats strip */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-10 pt-8 border-t border-white/10">
                {[
                  { v: totalSignals,  label: 'Research Signals',       icon: TrendingUp },
                  { v: sourcesCount,  label: 'Sources Indexed',        icon: Database   },
                  { v: 7,             label: 'Biomedical Databases',   icon: Network    },
                  { v: highConf,      label: 'High-Confidence',        icon: Shield     },
                ].map(({ v, label, icon: Icon }) => (
                  <div key={label} className="text-center">
                    <div className="flex items-center justify-center gap-1.5 mb-0.5">
                      <Icon size={13} className="text-white/40" />
                      <p className="text-xl font-bold text-white tabular-nums">
                        {v != null ? v.toLocaleString() : '—'}
                      </p>
                    </div>
                    <p className="text-[11px] text-white/45">{label}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Right — pipeline visualization */}
            <div className="hidden lg:block bg-white/6 rounded-2xl border border-white/10 p-7">
              <p className="text-[10px] font-bold uppercase tracking-widest text-white/35 mb-5">Evidence → Signal Flow</p>
              {[
                { label: 'Research Sources',  sub: 'PubMed · EuropePMC · ClinicalTrials', icon: Database,   c: '#3B82F6' },
                { label: 'Evidence Records',  sub: 'Normalized · Deduplicated',            icon: FileText,   c: '#8B5CF6' },
                { label: 'Drug + Disease',    sub: 'Entity matched against knowledge base', icon: Target,     c: '#F59E0B' },
                { label: 'Evidence Scoring',  sub: 'Multi-factor · live evidence only',     icon: BarChart2,  c: '#10B981' },
                { label: 'Research Signal',   sub: 'Traceable · expert validation required',icon: Zap,        c: '#EF4444' },
              ].map(({ label, sub, icon: Icon, c }, i, arr) => (
                <div key={label}>
                  <div className="flex items-center gap-3 py-2.5">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                      style={{ background: `${c}22`, border: `1px solid ${c}44` }}>
                      <Icon size={14} style={{ color: c }} />
                    </div>
                    <div>
                      <span className="text-sm font-semibold text-white">{label}</span>
                      <span className="text-[11px] text-white/40 ml-2">{sub}</span>
                    </div>
                  </div>
                  {i < arr.length - 1 && (
                    <div className="ml-4 h-4 w-px bg-white/10" />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── PIPELINE ──────────────────────────────────────────────────────── */}
      <section id="pipeline" className="py-16 lg:py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-12">
            <SectionLabel><GitMerge size={11} /> Scientific Methodology</SectionLabel>
            <SectionHeading>How BioArbitrage Works</SectionHeading>
            <SectionSub>A transparent, reproducible pipeline from evidence retrieval to research signal prioritization.</SectionSub>
          </div>

          {/* Desktop: horizontal connected steps */}
          <div className="hidden md:flex items-start justify-between max-w-5xl mx-auto relative">
            <div className="absolute top-5 left-[10%] right-[10%] h-px bg-slate-200" />
            {PIPELINE_STEPS.map(({ n, label, icon: Icon, color, desc }) => (
              <div key={n} className="flex flex-col items-center text-center flex-1 px-3 relative z-10">
                <div className="w-10 h-10 rounded-full flex items-center justify-center mb-3 ring-4 ring-white"
                  style={{ background: color }}>
                  <Icon size={17} className="text-white" />
                </div>
                <span className="text-[10px] font-bold font-mono text-slate-400 mb-1">{n}</span>
                <p className="text-sm font-semibold mb-1" style={{ color: NAVY }}>{label}</p>
                <p className="text-[12px] text-slate-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>

          {/* Mobile: vertical */}
          <div className="md:hidden max-w-lg mx-auto space-y-0">
            {PIPELINE_STEPS.map(({ n, label, icon: Icon, color, desc }, i) => (
              <div key={n} className="flex gap-4">
                <div className="flex flex-col items-center shrink-0">
                  <div className="w-9 h-9 rounded-full flex items-center justify-center shrink-0"
                    style={{ background: color }}>
                    <Icon size={15} className="text-white" />
                  </div>
                  {i < PIPELINE_STEPS.length - 1 && <div className="w-px flex-1 bg-slate-200 my-1" />}
                </div>
                <div className="pb-5">
                  <span className="text-[10px] font-bold font-mono text-slate-400">{n}</span>
                  <p className="text-sm font-semibold mt-0.5 mb-1" style={{ color: NAVY }}>{label}</p>
                  <p className="text-[13px] text-slate-500 leading-relaxed">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FEATURES ──────────────────────────────────────────────────────── */}
      <section id="features" className="py-16 lg:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-12">
            <SectionLabel><Dna size={11} /> Platform Capabilities</SectionLabel>
            <SectionHeading>Built for Biomedical Research</SectionHeading>
            <SectionSub>Designed for pharmaceutical scientists, research institutions, and biotechnology organizations.</SectionSub>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map(({ icon: Icon, color, title, desc }) => (
              <div key={title}
                className="group rounded-xl border border-slate-200 p-5 hover:border-blue-200 hover:shadow-card-md transition-all duration-200 cursor-default"
                style={{ background: 'white' }}>
                <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-4 transition-all group-hover:scale-110"
                  style={{ background: `${color}15`, border: `1px solid ${color}30` }}>
                  <Icon size={18} style={{ color }} />
                </div>
                <h3 className="text-sm font-semibold mb-2" style={{ color: NAVY }}>{title}</h3>
                <p className="text-[13px] text-slate-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── SOURCES ───────────────────────────────────────────────────────── */}
      <section id="sources" className="py-16 lg:py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-12">
            <SectionLabel><Network size={11} /> Integrated Evidence Sources</SectionLabel>
            <SectionHeading>Trusted Biomedical Databases</SectionHeading>
            <SectionSub>Evidence retrieved through official APIs with source attribution and identifier preservation.</SectionSub>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {SOURCES.map(({ name, type, desc, dot }) => (
              <div key={name} className="bg-white rounded-xl border border-slate-200 p-4 hover:shadow-card transition-shadow">
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: dot }} />
                  <span className="text-[10px] font-bold uppercase tracking-wide text-slate-400">{type}</span>
                </div>
                <p className="text-sm font-semibold mb-1" style={{ color: NAVY }}>{name}</p>
                <p className="text-[12px] text-slate-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>

          <p className="text-center text-[11px] text-slate-400">
            Connectivity verified at runtime. Source availability subject to API key configuration and provider uptime.
          </p>
        </div>
      </section>

      {/* ── TRACEABILITY ──────────────────────────────────────────────────── */}
      <section className="py-16 lg:py-24" style={{ background: NAVY }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-14 items-center">
            {/* Left */}
            <div>
              <SectionLabel><Shield size={11} /> Full Provenance Chain</SectionLabel>
              <h2 className="text-2xl sm:text-3xl font-bold text-white mb-4 leading-tight">
                Every Signal Is Traceable<br />to Its Evidence
              </h2>
              <p className="text-white/60 text-sm leading-relaxed mb-7">
                The platform maintains an unbroken provenance chain from evidence score back to the
                source record. Every contributing evidence item can be inspected with its original
                identifier and direct link.
              </p>

              <div className="grid grid-cols-2 gap-3">
                {PROVENANCE_ITEMS.map(({ id, desc }) => (
                  <div key={id} className="flex items-start gap-2.5">
                    <CheckCircle2 size={14} className="text-green-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs font-bold text-white">{id}</p>
                      <p className="text-[11px] text-white/40">{desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right — provenance chain */}
            <div className="rounded-2xl border border-white/10 p-6" style={{ background: NAVY2 }}>
              <p className="text-[10px] font-bold uppercase tracking-widest text-white/30 mb-5">
                Evidence → Signal Provenance Chain
              </p>
              {[
                { label: 'Drug Entity',        sub: 'Matched against knowledge base',     c: '#3B82F6' },
                { label: 'Disease Entity',     sub: 'Matched against knowledge base',     c: '#8B5CF6' },
                { label: 'Evidence Record',    sub: 'From live source API',               c: '#F59E0B' },
                { label: 'Source Database',    sub: 'PubMed · EuropePMC · UniProt · …',  c: '#14B8A6' },
                { label: 'Identifier',         sub: 'DOI · PMID · PMCID · NCT',          c: '#10B981' },
                { label: 'Evidence Score',     sub: 'Computed from live records only',    c: '#F59E0B' },
                { label: 'Research Signal',    sub: 'Traceable · requires validation',    c: '#94A3B8' },
              ].map(({ label, sub, c }, i, arr) => (
                <div key={label}>
                  <div className="flex items-center gap-3 py-2">
                    <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: c }} />
                    <div>
                      <span className="text-sm font-semibold text-white">{label}</span>
                      <span className="text-[11px] text-white/35 ml-2">{sub}</span>
                    </div>
                  </div>
                  {i < arr.length - 1 && (
                    <div className="ml-[5px] h-3.5 w-px bg-white/10" />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── SIGNALS PREVIEW ───────────────────────────────────────────────── */}
      <section id="signals" className="py-16 lg:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
            <div>
              <SectionLabel><Microscope size={11} /> Live Research Signals</SectionLabel>
              <SectionHeading>Latest Research Signals</SectionHeading>
              <p className="text-slate-500 text-sm">Ranked by evidence score. Sign in to explore the full signal library.</p>
            </div>
            <Link to="/login"
              className="inline-flex items-center gap-1.5 text-sm font-medium rounded-lg border border-slate-300 px-4 py-2 hover:border-slate-400 hover:bg-slate-50 transition-colors shrink-0"
              style={{ color: NAVY }}>
              View All Signals <ExternalLink size={13} />
            </Link>
          </div>

          {signals.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-200 py-14 text-center">
              <Network size={32} className="mx-auto mb-3 text-slate-300" />
              <p className="text-sm font-medium text-slate-500 mb-1">Sign in to view live research signals</p>
              <p className="text-[12px] text-slate-400">Signals load after authentication</p>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50">
                    {['Drug', 'Disease', 'Evidence Score', 'Records', 'Sources', 'Confidence', ''].map(h => (
                      <th key={h} className="text-left text-[11px] font-semibold text-slate-500 px-4 py-3 whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {signals.map(sig => (
                    <tr key={sig.id} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3">
                        <span className="text-[13px] font-semibold" style={{ color: NAVY }}>{sig.drug_name}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-[13px] text-slate-700">{sig.disease_name}</span>
                      </td>
                      <td className="px-4 py-3 w-36">
                        <ScorePill score={sig.evidence_score} />
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-[13px] tabular-nums text-slate-600">
                          {sig.unique_evidence_count ?? sig.source_count}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-[13px] text-slate-600">
                          {(sig.source_names ?? []).filter(s => s !== 'demo').length || sig.source_count}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5">
                          <ConfDot level={sig.confidence_level} />
                          <span className="text-[12px] text-slate-600 capitalize">{sig.confidence_level}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Link to="/login"
                          className="inline-flex items-center gap-1 text-[12px] font-medium hover:underline"
                          style={{ color: NAVY }}>
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

      {/* ── FINAL CTA ─────────────────────────────────────────────────────── */}
      <section className="py-16 lg:py-20" style={{ background: `linear-gradient(135deg, ${NAVY} 0%, #1a3a8f 100%)` }}>
        <div className="max-w-2xl mx-auto px-4 sm:px-6 text-center">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-5"
            style={{ background: `${ACCENT}22`, border: `1px solid ${ACCENT}44` }}>
            <TrendingUp size={22} style={{ color: ACCENT }} />
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">
            Explore the Research Intelligence Dashboard
          </h2>
          <p className="text-white/60 text-sm leading-relaxed mb-8">
            Access live research signals, source breakdowns, evidence traceability, and ingestion controls.
          </p>
          <Link to="/login"
            className="inline-flex items-center gap-2 px-7 py-3 text-sm font-bold text-white rounded-lg transition-all hover:scale-105"
            style={{ background: ACCENT, boxShadow: `0 4px 24px ${ACCENT}55` }}>
            Open Research Dashboard <ArrowRight size={16} />
          </Link>
        </div>
      </section>

      {/* ── DISCLAIMER ────────────────────────────────────────────────────── */}
      <section id="about" className="py-12 bg-white border-t border-slate-200">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 text-center">
          <div className="w-9 h-9 rounded-full border border-amber-200 bg-amber-50 flex items-center justify-center mx-auto mb-3">
            <Award size={16} className="text-amber-600" />
          </div>
          <h2 className="text-base font-bold mb-2" style={{ color: NAVY }}>
            Research Intelligence — Not Clinical Guidance
          </h2>
          <p className="text-[13px] text-slate-500 leading-relaxed max-w-2xl mx-auto">
            This platform provides computational research intelligence and evidence aggregation for
            research prioritization only. Drug repurposing signals are candidates generated through
            automated analysis of published literature, clinical trial registries, and biological
            databases. They do not establish clinical efficacy, safety, or fitness for medical use.
            Rigorous scientific investigation and regulatory review are required.
          </p>
        </div>
      </section>

      {/* ── FOOTER ────────────────────────────────────────────────────────── */}
      <footer style={{ background: NAVY2 }} className="text-white py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-6">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">
                <FlaskConical size={15} className="text-white" />
              </div>
              <div>
                <p className="text-[13px] font-bold">BioArbitrage</p>
                <p className="text-[10px] text-white/35">Real-Time Drug Repurposing Intelligence</p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-5 text-[12px] text-white/40">
              {NAV_LINKS.map(({ id, label }) => (
                <button key={id} onClick={() => scrollTo(id)} className="hover:text-white/70 transition-colors">
                  {label}
                </button>
              ))}
              <Link to="/login" className="hover:text-white/70 transition-colors">Dashboard</Link>
            </div>

            <Link to="/login"
              className="inline-flex items-center gap-2 px-4 py-1.5 text-sm font-medium text-white rounded-md border border-white/15 bg-white/8 hover:bg-white/15 transition-colors">
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
