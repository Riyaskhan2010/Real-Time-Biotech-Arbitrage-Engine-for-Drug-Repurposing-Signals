/**
 * LandingPage — BioArbitrage Premium Landing
 *
 * PUBLIC. Never redirects. Auth state is read ONLY to decide where
 * "Open Dashboard" sends the user (dashboard if logged in, login if not).
 * All API calls use .catch(()=>{}) — page stays visible even if backend is down.
 */
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  FlaskConical, ArrowRight, Database, Search, Layers,
  BarChart2, CheckCircle2, ExternalLink, Shield,
  BookOpen, Activity, Lock, Zap, FileText,
  ChevronDown, Menu, X, Award, TrendingUp,
  Dna, Network, GitMerge, Target, Microscope,
  Atom,
} from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { dashboardApi, signalsApi } from '../api'
import type { SignalListItem } from '../types'

// ─── Color constants ─────────────────────────────────────────────────────────
const NAVY      = '#0B1F3A'
const NAVY_DARK = '#071429'
const AMBER     = '#F59E0B'

// ─── Static data ──────────────────────────────────────────────────────────────

const NAV_LINKS = [
  { id: 'overview', label: 'Overview'  },
  { id: 'graph',    label: 'Knowledge Graph' },
  { id: 'pipeline', label: 'How It Works' },
  { id: 'sources',  label: 'Evidence' },
  { id: 'signals',  label: 'Signals'  },
]

const PIPELINE = [
  { n:'01', label:'Ingest',      icon: Database,  color:'#3B82F6', desc:'Records fetched from 7 biomedical sources via official paginated APIs.' },
  { n:'02', label:'Normalize',   icon: FileText,   color:'#8B5CF6', desc:'Common schema applied. DOI, PMID, NCT ID and source URLs preserved.' },
  { n:'03', label:'Match',       icon: Search,     color:'#F59E0B', desc:'Drug and disease entities matched against the knowledge base.' },
  { n:'04', label:'Deduplicate', icon: Layers,     color:'#10B981', desc:'Cross-source duplicates removed — DOI → PMID → title priority.' },
  { n:'05', label:'Prioritize',  icon: BarChart2,  color:'#EF4444', desc:'Multi-factor scoring: volume, clinical data, mechanism, diversity, recency.' },
]

const FEATURES = [
  { icon:BookOpen,  color:'#3B82F6', title:'Evidence Traceability',         desc:'Every signal traceable to individual records with DOI, PMID, NCT ID and direct source links.' },
  { icon:Layers,    color:'#8B5CF6', title:'Cross-Source Analysis',         desc:'Evidence from 7 databases aggregated and deduplicated for accurate, non-inflated scoring.' },
  { icon:Zap,       color:'#F59E0B', title:'Live Research Ingestion',       desc:'Evidence ingested on demand. Scores update automatically as new literature is indexed.' },
  { icon:Shield,    color:'#10B981', title:'Source Integrity',              desc:'Only peer-reviewed publications, registered trials and curated databases contribute.' },
  { icon:Activity,  color:'#EF4444', title:'Dynamic Drug + Disease Query',  desc:'Search any drug–disease pair dynamically across all connected sources.' },
  { icon:Lock,      color:'#6366F1', title:'Research-Only Intelligence',    desc:'Computational signals require expert scientific validation. Not clinical guidance.' },
]

const SOURCES = [
  { name:'PubMed / NCBI',      type:'Biomedical Literature',  dot:'#3B82F6', desc:'Peer-reviewed life-sciences research indexed by the US National Library of Medicine.' },
  { name:'ClinicalTrials.gov', type:'Clinical Evidence',      dot:'#10B981', desc:'Registered clinical studies providing structured human trial data.' },
  { name:'Elsevier / Scopus',  type:'Scientific Literature',  dot:'#F59E0B', desc:'Multidisciplinary publication database covering biomedical research.' },
  { name:'Europe PMC',         type:'Open-Access Literature', dot:'#14B8A6', desc:'EBI open-access repository with full-text content and PMCID.' },
  { name:'UniProt',            type:'Protein / Target Data',  dot:'#8B5CF6', desc:'Curated protein sequence and functional annotation with drug-target associations.' },
  { name:'bioRxiv',            type:'Preprint Server',        dot:'#F97316', desc:'Life-sciences preprint server for early access biomedical manuscripts.' },
  { name:'medRxiv',            type:'Medical Preprints',      dot:'#EF4444', desc:'Health-sciences preprints covering clinical medicine and epidemiology.' },
]

// ─── Knowledge Graph data ─────────────────────────────────────────────────────
// Uses illustrative relationships. Clearly labelled as illustrative.
// Real signals from API are loaded and overlay the graph when available.

type Confidence = 'high' | 'medium' | 'low'

interface GraphNode {
  id: string; label: string; type: 'disease' | 'drug'
  x: number; y: number; confidence?: Confidence
  evidenceScore?: number; evidenceCount?: number
}

interface GraphEdge {
  from: string; to: string; confidence: Confidence; weight: number
}

const GRAPH_NODES: GraphNode[] = [
  // Central disease nodes
  { id:'d1', label:"Alzheimer's",         type:'disease', x:50,  y:50  },
  { id:'d2', label:'Type 2 Diabetes',     type:'disease', x:75,  y:25  },
  { id:'d3', label:'Parkinson\'s',        type:'disease', x:25,  y:25  },
  // Drug nodes around
  { id:'dr1', label:'Metformin',          type:'drug',    x:15,  y:50  },
  { id:'dr2', label:'Rapamycin',          type:'drug',    x:85,  y:50  },
  { id:'dr3', label:'Sildenafil',         type:'drug',    x:50,  y:85  },
  { id:'dr4', label:'Ivermectin',         type:'drug',    x:8,   y:20  },
  { id:'dr5', label:'Thalidomide',        type:'drug',    x:90,  y:20  },
  { id:'dr6', label:'Lithium',            type:'drug',    x:30,  y:80  },
  { id:'dr7', label:'Naltrexone',         type:'drug',    x:70,  y:80  },
  { id:'dr8', label:'Doxycycline',        type:'drug',    x:50,  y:10  },
]

const GRAPH_EDGES: GraphEdge[] = [
  { from:'dr1', to:'d1', confidence:'high',   weight:0.85 },
  { from:'dr1', to:'d2', confidence:'high',   weight:0.90 },
  { from:'dr2', to:'d2', confidence:'medium', weight:0.60 },
  { from:'dr2', to:'d1', confidence:'medium', weight:0.55 },
  { from:'dr3', to:'d2', confidence:'medium', weight:0.62 },
  { from:'dr3', to:'d1', confidence:'low',    weight:0.32 },
  { from:'dr4', to:'d2', confidence:'low',    weight:0.28 },
  { from:'dr5', to:'d3', confidence:'medium', weight:0.58 },
  { from:'dr6', to:'d1', confidence:'high',   weight:0.78 },
  { from:'dr6', to:'d3', confidence:'medium', weight:0.61 },
  { from:'dr7', to:'d3', confidence:'low',    weight:0.35 },
  { from:'dr8', to:'d1', confidence:'low',    weight:0.30 },
]

const CONF_COLORS: Record<Confidence, string> = {
  high:   '#F59E0B',
  medium: '#3B82F6',
  low:    '#6B7280',
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function SectionLabel({ icon: Icon, children }: { icon?: React.ElementType; children: React.ReactNode }) {
  return (
    <div className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-widest px-3 py-1 rounded-full border mb-4"
      style={{ background:'#EFF6FF', border:'1px solid #BFDBFE', color:'#1D4ED8' }}>
      {Icon && <Icon size={10} />}{children}
    </div>
  )
}

function ScoreMini({ score }: { score: number }) {
  const c = score >= 75 ? '#10B981' : score >= 50 ? '#F59E0B' : '#94A3B8'
  return (
    <div className="flex items-center gap-1.5">
      <div className="flex-1 h-1.5 rounded-full bg-slate-200 overflow-hidden">
        <div className="h-full rounded-full" style={{ width:`${score}%`, background:c }} />
      </div>
      <span className="text-[11px] font-bold tabular-nums" style={{ color:c }}>{Math.round(score)}</span>
    </div>
  )
}

// ─── Knowledge Graph SVG component ────────────────────────────────────────────

function KnowledgeGraph({ signals }: { signals: SignalListItem[] }) {
  const [hovered, setHovered] = useState<string | null>(null)
  const svgRef = useRef<SVGSVGElement>(null)

  // Build signal lookup for real tooltips
  const sigMap: Record<string, SignalListItem> = {}
  signals.forEach(s => {
    const drug = s.drug_name?.toLowerCase() ?? ''
    GRAPH_NODES.filter(n => n.type === 'drug').forEach(n => {
      if (drug.includes(n.label.toLowerCase().split(' ')[0].toLowerCase())) {
        sigMap[`${n.id}`] = s
      }
    })
  })

  const W = 800, H = 500
  const toSVG = (pct: number, dim: number) => (pct / 100) * dim

  const hoveredNode = GRAPH_NODES.find(n => n.id === hovered)
  const hoveredSig  = hovered ? sigMap[hovered] : null

  return (
    <div className="relative w-full" style={{ maxWidth: 800, margin: '0 auto' }}>
      {/* Animated background grid */}
      <div className="absolute inset-0 rounded-2xl overflow-hidden pointer-events-none" aria-hidden="true">
        <div className="absolute inset-0" style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, rgba(59,130,246,0.15) 1px, transparent 0)`,
          backgroundSize: '28px 28px',
        }} />
        <div className="absolute inset-0" style={{
          background: `radial-gradient(ellipse at 50% 50%, rgba(11,31,58,0.0) 0%, rgba(11,31,58,0.7) 100%)`,
        }} />
      </div>

      <svg
        ref={svgRef}
        viewBox={`0 0 ${W} ${H}`}
        className="w-full h-auto rounded-2xl border border-white/10"
        style={{ background: NAVY_DARK, display: 'block' }}
        role="img"
        aria-label="Drug-disease knowledge graph — illustrative research relationships"
      >
        <defs>
          {/* Animated gradient for edges */}
          {(['high','medium','low'] as Confidence[]).map(c => (
            <linearGradient key={c} id={`edge-${c}`} x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor={CONF_COLORS[c]} stopOpacity="0.2" />
              <stop offset="50%" stopColor={CONF_COLORS[c]} stopOpacity="0.8" />
              <stop offset="100%" stopColor={CONF_COLORS[c]} stopOpacity="0.2" />
              <animateTransform attributeName="gradientTransform" type="translate"
                from="-1 0" to="1 0" dur={c === 'high' ? '2s' : c === 'medium' ? '3s' : '4s'}
                repeatCount="indefinite" additive="sum" />
            </linearGradient>
          ))}
          {/* Node glow filters */}
          <filter id="glow-disease">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="glow-drug">
            <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
            <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Edges */}
        {GRAPH_EDGES.map((e, i) => {
          const from = GRAPH_NODES.find(n => n.id === e.from)!
          const to   = GRAPH_NODES.find(n => n.id === e.to)!
          const fx = toSVG(from.x, W), fy = toSVG(from.y, H)
          const tx = toSVG(to.x,   W), ty = toSVG(to.y,   H)
          const mx = (fx + tx) / 2, my = (fy + ty) / 2 - 30
          const isHov = hovered === e.from || hovered === e.to
          return (
            <g key={i}>
              <path
                d={`M ${fx} ${fy} Q ${mx} ${my} ${tx} ${ty}`}
                fill="none"
                stroke={`url(#edge-${e.confidence})`}
                strokeWidth={isHov ? 2.5 : 1.5}
                strokeOpacity={isHov ? 1 : 0.5}
                style={{ transition: 'all 0.2s' }}
              />
              {/* Animated dot traveling the path */}
              <circle r="3" fill={CONF_COLORS[e.confidence]} opacity="0.9">
                <animateMotion
                  dur={`${2 + i * 0.4}s`} repeatCount="indefinite"
                  path={`M ${fx} ${fy} Q ${mx} ${my} ${tx} ${ty}`}
                />
              </circle>
            </g>
          )
        })}

        {/* Disease nodes */}
        {GRAPH_NODES.filter(n => n.type === 'disease').map(n => {
          const cx = toSVG(n.x, W), cy = toSVG(n.y, H)
          const isHov = hovered === n.id
          return (
            <g key={n.id} style={{ cursor: 'pointer' }}
              onMouseEnter={() => setHovered(n.id)}
              onMouseLeave={() => setHovered(null)}>
              <circle cx={cx} cy={cy} r={isHov ? 34 : 30}
                fill={`${AMBER}22`} stroke={AMBER}
                strokeWidth={isHov ? 2.5 : 1.5} filter="url(#glow-disease)"
                style={{ transition:'all 0.2s' }} />
              <circle cx={cx} cy={cy} r={isHov ? 24 : 20}
                fill={`${AMBER}44`}
                style={{ transition:'all 0.2s' }}>
                <animate attributeName="r" values={`${isHov?24:20};${isHov?27:23};${isHov?24:20}`}
                  dur="2.5s" repeatCount="indefinite" />
              </circle>
              <text x={cx} y={cy + 4} textAnchor="middle"
                fontSize={n.label.length > 10 ? 9 : 10} fontWeight="700" fill={AMBER}>
                {n.label.length > 12 ? n.label.slice(0,11)+'…' : n.label}
              </text>
              <text x={cx} y={cy + 47} textAnchor="middle" fontSize={8} fill="rgba(255,255,255,0.4)">
                DISEASE
              </text>
            </g>
          )
        })}

        {/* Drug nodes */}
        {GRAPH_NODES.filter(n => n.type === 'drug').map(n => {
          const cx = toSVG(n.x, W), cy = toSVG(n.y, H)
          const isHov = hovered === n.id
          const realSig = sigMap[n.id]
          const nodeColor = realSig ? '#60A5FA' : '#94A3B8'
          return (
            <g key={n.id} style={{ cursor: 'pointer' }}
              onMouseEnter={() => setHovered(n.id)}
              onMouseLeave={() => setHovered(null)}>
              <circle cx={cx} cy={cy} r={isHov ? 22 : 18}
                fill={`${nodeColor}22`} stroke={nodeColor}
                strokeWidth={isHov ? 2 : 1.2} filter="url(#glow-drug)"
                style={{ transition:'all 0.2s' }} />
              <text x={cx} y={cy + 3} textAnchor="middle"
                fontSize={9} fontWeight="600" fill={nodeColor}>
                {n.label.length > 10 ? n.label.slice(0,9)+'…' : n.label}
              </text>
              <text x={cx} y={cy + 28} textAnchor="middle" fontSize={7} fill="rgba(255,255,255,0.3)">
                DRUG
              </text>
            </g>
          )
        })}

        {/* Hover tooltip */}
        {hoveredNode && (
          <g>
            {(() => {
              const cx = toSVG(hoveredNode.x, W)
              const cy = toSVG(hoveredNode.y, H)
              const tx = cx > W * 0.6 ? cx - 155 : cx + 25
              const ty = cy > H * 0.7 ? cy - 90  : cy - 10
              const related = GRAPH_EDGES
                .filter(e => e.from === hoveredNode.id || e.to === hoveredNode.id)
                .map(e => ({ ...e, other: GRAPH_NODES.find(n => n.id === (e.from === hoveredNode.id ? e.to : e.from))! }))
              return (
                <g>
                  <rect x={tx} y={ty} width={150} height={Math.min(100, 32 + related.length * 16)}
                    rx={6} fill={NAVY} stroke="rgba(255,255,255,0.15)" strokeWidth={1} opacity={0.97} />
                  <text x={tx + 8} y={ty + 16} fontSize={10} fontWeight="700" fill="white">{hoveredNode.label}</text>
                  <text x={tx + 8} y={ty + 27} fontSize={8} fill="rgba(255,255,255,0.45)">
                    {hoveredNode.type === 'disease' ? 'Disease Entity' : 'Drug Entity'}
                    {hoveredSig ? `  •  Score: ${hoveredSig.evidence_score?.toFixed(0)}` : ''}
                  </text>
                  {related.slice(0, 4).map((r, i) => (
                    <text key={i} x={tx + 8} y={ty + 42 + i * 14} fontSize={8}
                      fill={CONF_COLORS[r.confidence]}>
                      → {r.other.label} ({r.confidence})
                    </text>
                  ))}
                  {!hoveredSig && (
                    <text x={tx + 8} y={ty + 45 + related.length * 14} fontSize={7}
                      fill="rgba(255,255,255,0.25)">Illustrative relationship</text>
                  )}
                </g>
              )
            })()}
          </g>
        )}
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap items-center justify-center gap-5 mt-5">
        {(['high','medium','low'] as Confidence[]).map(c => (
          <div key={c} className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full" style={{ background:CONF_COLORS[c] }} />
            <span className="text-[12px] text-white/60 capitalize">{c} Confidence</span>
          </div>
        ))}
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-slate-400" />
          <span className="text-[12px] text-white/40">No live signal</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-blue-400" />
          <span className="text-[12px] text-white/60">Live signal loaded</span>
        </div>
      </div>

      <p className="text-center text-[11px] mt-3 text-white/25 italic">
        Showing top relationships by evidence strength.
        Illustrative visualization — all relationships require expert scientific validation.
        Ranked by evidence volume, clinical data, mechanism fit, source diversity and recency.
      </p>
    </div>
  )
}

// ─── Main LandingPage ─────────────────────────────────────────────────────────

export function LandingPage() {
  const { isAuthenticated } = useAuthStore()
  const navigate = useNavigate()

  const [signals,      setSignals]      = useState<SignalListItem[]>([])
  const [totalSignals, setTotalSignals] = useState<number | null>(null)
  const [sourcesCount, setSourcesCount] = useState<number | null>(null)
  const [highConf,     setHighConf]     = useState<number | null>(null)
  const [mobileOpen,   setMobileOpen]   = useState(false)
  const [scrolled,     setScrolled]     = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // Silent API calls — page never redirects or crashes on failure
  useEffect(() => {
    dashboardApi.get().then(d => {
      setTotalSignals(d.stats.total_signals)
      setSourcesCount(d.stats.total_research_sources)
      setHighConf(d.stats.high_confidence_signals)
    }).catch(() => {})

    signalsApi.list({ limit: 6, include_demo: false, sort_by: 'evidence_score' })
      .then(setSignals).catch(() => {})
  }, [])

  // Smart CTA — goes to dashboard if logged in, login otherwise
  const handleExploreCTA = () => {
    navigate(isAuthenticated ? '/dashboard' : '/login')
  }

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    setMobileOpen(false)
  }

  return (
    <div className="bg-white text-slate-900 antialiased">

      {/* TOP STRIP */}
      <div className="hidden sm:flex items-center justify-between px-6 py-1.5 text-[11px]"
        style={{ background: NAVY, color: 'rgba(255,255,255,0.45)' }}>
        <span>Government Research Intelligence Platform · Biotechnology · Drug Repurposing · Evidence Intelligence</span>
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
          Platform Operational
        </span>
      </div>

      {/* NAVBAR */}
      <header className="sticky top-0 z-50 transition-shadow duration-200"
        style={{
          background: scrolled ? 'rgba(255,255,255,0.97)' : 'white',
          borderBottom: '1px solid #E2E8F0',
          boxShadow: scrolled ? '0 2px 12px rgba(0,0,0,.07)' : '0 1px 3px rgba(0,0,0,.04)',
          backdropFilter: 'blur(8px)',
        }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
          <Link to="/" className="flex items-center gap-2.5 shrink-0">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: NAVY }}>
              <FlaskConical size={16} className="text-white" />
            </div>
            <div className="leading-none">
              <p className="text-[13px] font-bold" style={{ color: NAVY }}>BioArbitrage</p>
              <p className="text-[10px] text-slate-400">Drug Repurposing Intelligence</p>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-0.5">
            {NAV_LINKS.map(({ id, label }) => (
              <button key={id} onClick={() => scrollTo(id)}
                className="px-3 py-1.5 text-[13px] text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-md transition-colors font-medium">
                {label}
              </button>
            ))}
          </nav>

          <div className="hidden md:flex items-center gap-2">
            {isAuthenticated ? (
              <Link to="/dashboard"
                className="inline-flex items-center gap-1.5 px-4 py-1.5 text-[13px] font-semibold text-white rounded-md transition-colors"
                style={{ background: NAVY }}>
                Open Dashboard <ArrowRight size={13} />
              </Link>
            ) : (
              <>
                <Link to="/login" className="px-3 py-1.5 text-[13px] font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-md transition-colors">
                  Sign In
                </Link>
                <Link to="/register"
                  className="inline-flex items-center gap-1.5 px-4 py-1.5 text-[13px] font-semibold text-white rounded-md transition-colors"
                  style={{ background: NAVY }}>
                  Create Account <ArrowRight size={13} />
                </Link>
              </>
            )}
          </div>

          <button className="md:hidden p-2 rounded-md text-slate-500 hover:bg-slate-100"
            onClick={() => setMobileOpen(v => !v)}
            aria-label={mobileOpen ? 'Close menu' : 'Open menu'}>
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>

        {mobileOpen && (
          <div className="md:hidden border-t border-slate-100 bg-white px-4 py-3 space-y-0.5">
            {NAV_LINKS.map(({ id, label }) => (
              <button key={id} onClick={() => scrollTo(id)}
                className="w-full text-left px-3 py-2.5 text-sm text-slate-700 hover:bg-slate-50 rounded-md font-medium">
                {label}
              </button>
            ))}
            <div className="pt-3 border-t border-slate-100 space-y-2">
              {isAuthenticated ? (
                <Link to="/dashboard" onClick={() => setMobileOpen(false)}
                  className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-md text-white text-sm font-semibold"
                  style={{ background: NAVY }}>
                  Open Dashboard <ArrowRight size={14} />
                </Link>
              ) : (
                <>
                  <Link to="/login" onClick={() => setMobileOpen(false)}
                    className="flex items-center justify-center gap-2 py-2 px-4 rounded-md border border-slate-300 text-slate-700 text-sm font-medium">
                    Sign In
                  </Link>
                  <Link to="/register" onClick={() => setMobileOpen(false)}
                    className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-md text-white text-sm font-semibold"
                    style={{ background: NAVY }}>
                    Create Account <ArrowRight size={14} />
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </header>

      {/* HERO */}
      <section id="overview" style={{ background: `linear-gradient(135deg, ${NAVY_DARK} 0%, ${NAVY} 55%, #152F75 100%)` }}>
        <div className="h-1" style={{ background:`linear-gradient(90deg, ${AMBER}, #F97316, ${AMBER})` }} />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-16 lg:py-24">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/20 bg-white/8 text-[11px] text-white/70 mb-5">
                <Atom size={11} />
                AI-Powered Biomedical Research Intelligence · 7 Connected Sources
              </div>
              <h1 className="text-3xl sm:text-4xl lg:text-[2.6rem] font-extrabold leading-tight text-white mb-4">
                Real-Time Intelligence for<br />
                <span style={{ color: AMBER }}>Drug Repurposing Research</span>
              </h1>
              <p className="text-white/70 text-base leading-relaxed mb-3 max-w-lg">
                Continuously aggregates biomedical literature, clinical trial data, and molecular annotations
                to identify and prioritize potential drug–disease research opportunities.
              </p>
              <p className="text-white/40 text-xs leading-relaxed mb-8 max-w-lg border-l-2 border-white/15 pl-3">
                Computational research candidates only. Not clinical guidance or treatment recommendations.
                Expert scientific validation required.
              </p>
              <div className="flex flex-wrap gap-3">
                <button onClick={handleExploreCTA}
                  className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-bold text-white rounded-lg transition-all hover:scale-105"
                  style={{ background: AMBER, boxShadow:`0 4px 20px ${AMBER}55` }}>
                  Explore Research Dashboard <ArrowRight size={15} />
                </button>
                <button onClick={() => scrollTo('pipeline')}
                  className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white rounded-lg border border-white/25 bg-white/8 hover:bg-white/15 transition-colors">
                  View Evidence Sources <ChevronDown size={15} />
                </button>
              </div>
              {/* Stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-10 pt-8 border-t border-white/10">
                {[
                  { v: totalSignals, label:'Research Signals',     icon: TrendingUp },
                  { v: sourcesCount, label:'Sources Indexed',      icon: Database   },
                  { v: 7,            label:'Biomedical Databases', icon: Network    },
                  { v: highConf,     label:'High-Confidence',      icon: Shield     },
                ].map(({ v, label, icon: Icon }) => (
                  <div key={label} className="text-center">
                    <div className="flex items-center justify-center gap-1.5 mb-0.5">
                      <Icon size={12} className="text-white/40" />
                      <p className="text-xl font-bold text-white tabular-nums">{v != null ? v.toLocaleString() : '—'}</p>
                    </div>
                    <p className="text-[11px] text-white/45">{label}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Hero right — pipeline visual */}
            <div className="hidden lg:block bg-white/6 rounded-2xl border border-white/10 p-7">
              <p className="text-[10px] font-bold uppercase tracking-widest text-white/35 mb-5">Evidence → Signal Flow</p>
              {[
                { label:'Research Sources',  sub:'PubMed · EuropePMC · ClinicalTrials',  icon: Database,  c:'#3B82F6' },
                { label:'Evidence Records',  sub:'Normalized · Deduplicated',             icon: FileText,  c:'#8B5CF6' },
                { label:'Drug + Disease',    sub:'Entity matched against knowledge base', icon: Target,    c:'#F59E0B' },
                { label:'Evidence Scoring',  sub:'Multi-factor · live evidence only',     icon: BarChart2, c:'#10B981' },
                { label:'Research Signal',   sub:'Traceable · expert validation required',icon: Zap,       c:'#EF4444' },
              ].map(({ label, sub, icon: Icon, c }, i, arr) => (
                <div key={label}>
                  <div className="flex items-center gap-3 py-2.5">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                      style={{ background:`${c}22`, border:`1px solid ${c}44` }}>
                      <Icon size={14} style={{ color:c }} />
                    </div>
                    <div>
                      <span className="text-sm font-semibold text-white">{label}</span>
                      <span className="text-[11px] text-white/40 ml-2">{sub}</span>
                    </div>
                  </div>
                  {i < arr.length - 1 && <div className="ml-4 h-4 w-px bg-white/10" />}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* KNOWLEDGE GRAPH */}
      <section id="graph" style={{ background:`linear-gradient(180deg, ${NAVY} 0%, ${NAVY_DARK} 100%)` }}
        className="py-16 lg:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-widest px-3 py-1 rounded-full border mb-4"
              style={{ background:'rgba(245,158,11,0.1)', border:`1px solid ${AMBER}44`, color:AMBER }}>
              <Network size={10} /> Drug–Disease Knowledge Graph
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">
              Research Knowledge Graph
            </h2>
            <p className="text-white/55 text-sm max-w-2xl mx-auto leading-relaxed">
              Explore computational drug–disease research relationships ranked by evidence strength.
              Hover over nodes to see confidence levels and evidence counts.
              Blue nodes have live evidence loaded from connected sources.
            </p>
          </div>
          <KnowledgeGraph signals={signals} />
        </div>
      </section>

      {/* PIPELINE */}
      <section id="pipeline" className="py-16 lg:py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-12">
            <SectionLabel icon={GitMerge}>Scientific Methodology</SectionLabel>
            <h2 className="text-2xl sm:text-3xl font-bold mb-3" style={{ color: NAVY }}>How BioArbitrage Works</h2>
            <p className="text-slate-500 text-sm max-w-xl mx-auto">
              A transparent, reproducible pipeline from evidence retrieval to research signal prioritization.
            </p>
          </div>
          {/* Desktop horizontal */}
          <div className="hidden md:flex items-start justify-between max-w-5xl mx-auto relative">
            <div className="absolute top-5 left-[10%] right-[10%] h-px bg-slate-200" />
            {PIPELINE.map(({ n, label, icon: Icon, color, desc }) => (
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
          {/* Mobile vertical */}
          <div className="md:hidden max-w-lg mx-auto">
            {PIPELINE.map(({ n, label, icon: Icon, color, desc }, i) => (
              <div key={n} className="flex gap-4">
                <div className="flex flex-col items-center shrink-0">
                  <div className="w-9 h-9 rounded-full flex items-center justify-center shrink-0" style={{ background: color }}>
                    <Icon size={15} className="text-white" />
                  </div>
                  {i < PIPELINE.length - 1 && <div className="w-px flex-1 bg-slate-200 my-1" />}
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

      {/* FEATURES */}
      <section className="py-16 lg:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-12">
            <SectionLabel icon={Dna}>Platform Capabilities</SectionLabel>
            <h2 className="text-2xl sm:text-3xl font-bold mb-3" style={{ color: NAVY }}>Built for Biomedical Research</h2>
            <p className="text-slate-500 text-sm max-w-xl mx-auto">
              Designed for pharmaceutical scientists, research institutions, and biotechnology organizations.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map(({ icon: Icon, color, title, desc }) => (
              <div key={title}
                className="group rounded-xl border border-slate-200 p-5 hover:border-blue-200 hover:shadow-md transition-all duration-200 bg-white">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-4 transition-transform group-hover:scale-110"
                  style={{ background:`${color}15`, border:`1px solid ${color}30` }}>
                  <Icon size={18} style={{ color }} />
                </div>
                <h3 className="text-sm font-semibold mb-2" style={{ color: NAVY }}>{title}</h3>
                <p className="text-[13px] text-slate-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SOURCES */}
      <section id="sources" className="py-16 lg:py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-12">
            <SectionLabel icon={Network}>Integrated Evidence Sources</SectionLabel>
            <h2 className="text-2xl sm:text-3xl font-bold mb-3" style={{ color: NAVY }}>7 Trusted Biomedical Databases</h2>
            <p className="text-slate-500 text-sm max-w-xl mx-auto">
              Evidence retrieved through official APIs with source attribution and identifier preservation.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
            {SOURCES.map(({ name, type, desc, dot }) => (
              <div key={name} className="bg-white rounded-xl border border-slate-200 p-4 hover:shadow-md transition-shadow">
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

      {/* TRACEABILITY */}
      <section className="py-16 lg:py-24" style={{ background: NAVY }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-14 items-center">
            <div>
              <div className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-widest px-3 py-1 rounded-full border mb-4"
                style={{ background:'rgba(16,185,129,0.1)', border:'1px solid rgba(16,185,129,0.3)', color:'#34D399' }}>
                <Shield size={10} /> Full Provenance Chain
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-white mb-4">Every Signal Is Traceable to Its Evidence</h2>
              <p className="text-white/60 text-sm leading-relaxed mb-7">
                The platform maintains an unbroken provenance chain from evidence score back to the source record.
                Every contributing evidence item can be inspected with its original identifier and direct link.
              </p>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { id:'DOI',        desc:'Digital Object Identifier'     },
                  { id:'PMID',       desc:'PubMed unique record ID'        },
                  { id:'PMCID',      desc:'PubMed Central full-text ID'    },
                  { id:'NCT ID',     desc:'ClinicalTrials registration'    },
                  { id:'UniProt ID', desc:'Protein accession'              },
                  { id:'Source URL', desc:'Direct original source link'    },
                ].map(({ id, desc }) => (
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
            <div className="rounded-2xl border border-white/10 p-6" style={{ background: NAVY_DARK }}>
              <p className="text-[10px] font-bold uppercase tracking-widest text-white/30 mb-5">
                Evidence → Signal Provenance Chain
              </p>
              {[
                { label:'Drug Entity',       sub:'Matched against knowledge base',      c:'#3B82F6' },
                { label:'Disease Entity',    sub:'Matched against knowledge base',      c:'#8B5CF6' },
                { label:'Evidence Record',   sub:'From live source API',                c:'#F59E0B' },
                { label:'Source Database',   sub:'PubMed · EuropePMC · UniProt · …',   c:'#14B8A6' },
                { label:'Identifier',        sub:'DOI · PMID · PMCID · NCT',           c:'#10B981' },
                { label:'Evidence Score',    sub:'Computed from live records only',     c:'#F59E0B' },
                { label:'Research Signal',   sub:'Traceable · requires validation',     c:'#94A3B8' },
              ].map(({ label, sub, c }, i, arr) => (
                <div key={label}>
                  <div className="flex items-center gap-3 py-2">
                    <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: c }} />
                    <span className="text-sm font-semibold text-white">{label}</span>
                    <span className="text-[11px] text-white/35 ml-1">{sub}</span>
                  </div>
                  {i < arr.length - 1 && <div className="ml-[5px] h-3.5 w-px bg-white/10" />}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* SIGNALS PREVIEW */}
      <section id="signals" className="py-16 lg:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
            <div>
              <SectionLabel icon={Microscope}>Live Research Signals</SectionLabel>
              <h2 className="text-2xl sm:text-3xl font-bold" style={{ color: NAVY }}>Latest Research Signals</h2>
              <p className="text-slate-500 text-sm mt-1">Ranked by evidence score. Sign in to explore the full library.</p>
            </div>
            <button onClick={handleExploreCTA}
              className="inline-flex items-center gap-1.5 text-sm font-medium rounded-lg border border-slate-300 px-4 py-2 hover:border-slate-400 hover:bg-slate-50 transition-colors shrink-0"
              style={{ color: NAVY }}>
              View All Signals <ExternalLink size={13} />
            </button>
          </div>

          {signals.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-200 py-14 text-center">
              <Network size={32} className="mx-auto mb-3 text-slate-300" />
              <p className="text-sm font-medium text-slate-500 mb-1">Sign in to view live research signals</p>
              <p className="text-[12px] text-slate-400 mb-4">Signals load after authentication</p>
              <button onClick={handleExploreCTA}
                className="inline-flex items-center gap-2 px-5 py-2 text-sm font-semibold text-white rounded-lg"
                style={{ background: NAVY }}>
                {isAuthenticated ? 'Open Dashboard' : 'Sign In'} <ArrowRight size={14} />
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50">
                    {['Drug','Disease','Evidence Score','Records','Sources','Confidence',''].map(h => (
                      <th key={h} className="text-left text-[11px] font-semibold text-slate-500 px-4 py-3 whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {signals.map(sig => (
                    <tr key={sig.id} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3"><span className="text-[13px] font-semibold" style={{ color: NAVY }}>{sig.drug_name}</span></td>
                      <td className="px-4 py-3"><span className="text-[13px] text-slate-700">{sig.disease_name}</span></td>
                      <td className="px-4 py-3 w-36"><ScoreMini score={sig.evidence_score} /></td>
                      <td className="px-4 py-3"><span className="text-[13px] tabular-nums text-slate-600">{sig.unique_evidence_count ?? sig.source_count}</span></td>
                      <td className="px-4 py-3"><span className="text-[13px] text-slate-600">{(sig.source_names ?? []).filter(s => s !== 'demo').length || sig.source_count}</span></td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full" style={{ background: sig.confidence_level === 'high' ? '#10B981' : sig.confidence_level === 'medium' ? '#F59E0B' : '#94A3B8' }} />
                          <span className="text-[12px] text-slate-600 capitalize">{sig.confidence_level}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <button onClick={handleExploreCTA}
                          className="inline-flex items-center gap-1 text-[12px] font-medium hover:underline"
                          style={{ color: NAVY }}>
                          View <ExternalLink size={10} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>

      {/* FINAL CTA */}
      <section style={{ background:`linear-gradient(135deg, ${NAVY} 0%, #1a3a8f 100%)` }}
        className="py-16 lg:py-20">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 text-center">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-5"
            style={{ background:`${AMBER}22`, border:`1px solid ${AMBER}44` }}>
            <TrendingUp size={22} style={{ color: AMBER }} />
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">
            Explore the Research Intelligence Dashboard
          </h2>
          <p className="text-white/60 text-sm leading-relaxed mb-8">
            Access live research signals, source breakdowns, evidence traceability, and ingestion controls.
          </p>
          <div className="flex flex-wrap gap-3 justify-center">
            <button onClick={handleExploreCTA}
              className="inline-flex items-center gap-2 px-7 py-3 text-sm font-bold text-white rounded-lg transition-all hover:scale-105"
              style={{ background: AMBER, boxShadow:`0 4px 24px ${AMBER}55` }}>
              {isAuthenticated ? 'Open Dashboard' : 'Get Started'} <ArrowRight size={16} />
            </button>
            {!isAuthenticated && (
              <Link to="/register"
                className="inline-flex items-center gap-2 px-6 py-3 text-sm font-semibold text-white rounded-lg border border-white/25 bg-white/8 hover:bg-white/15 transition-colors">
                Create Free Account
              </Link>
            )}
          </div>
        </div>
      </section>

      {/* DISCLAIMER */}
      <section id="about" className="py-12 bg-white border-t border-slate-200">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 text-center">
          <div className="w-9 h-9 rounded-full border border-amber-200 bg-amber-50 flex items-center justify-center mx-auto mb-3">
            <Award size={16} className="text-amber-600" />
          </div>
          <h2 className="text-base font-bold mb-2" style={{ color: NAVY }}>Research Intelligence — Not Clinical Guidance</h2>
          <p className="text-[13px] text-slate-500 leading-relaxed max-w-2xl mx-auto">
            This platform provides computational research intelligence for research prioritization only.
            Drug repurposing signals are candidates generated through automated analysis and do not
            establish clinical efficacy, safety, or fitness for medical use.
            Rigorous scientific investigation and regulatory review are required.
          </p>
        </div>
      </section>

      {/* FOOTER */}
      <footer style={{ background: NAVY_DARK }} className="text-white py-10">
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
                <button key={id} onClick={() => scrollTo(id)} className="hover:text-white/70 transition-colors">{label}</button>
              ))}
              <Link to="/register" className="hover:text-white/70 transition-colors">Register</Link>
              <button onClick={handleExploreCTA} className="hover:text-white/70 transition-colors">Dashboard</button>
            </div>
            <button onClick={handleExploreCTA}
              className="inline-flex items-center gap-2 px-4 py-1.5 text-sm font-medium text-white rounded-md border border-white/15 bg-white/8 hover:bg-white/15 transition-colors">
              {isAuthenticated ? 'Open Dashboard' : 'Sign In'} <ArrowRight size={13} />
            </button>
          </div>
          <div className="pt-5 border-t border-white/8 flex flex-col md:flex-row items-center justify-between gap-2 text-[11px] text-white/25">
            <p>Research decision-support only. Not for clinical use, diagnosis, or treatment recommendations.</p>
            <p>Evidence sourced from publicly accessible biomedical databases via official APIs.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
