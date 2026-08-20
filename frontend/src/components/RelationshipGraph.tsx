/**
 * RelationshipGraph
 * =================
 * Drug → Target → Pathway → Disease → Evidence
 * Visual flow diagram using CSS flex — no extra charting lib required.
 * Reuses existing Tailwind colour tokens.
 */
import { Pill, Target, Waypoints, Microscope, BookOpen, ArrowDown } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { clsx } from 'clsx'
import type { RelationshipGraph as RelationshipGraphType, GraphNode } from '../types'

interface Props {
  graph: RelationshipGraphType
}

interface NodeProps {
  node: GraphNode
  compact?: boolean
}

const NODE_STYLES: Record<string, string> = {
  drug:     'bg-brand-500/10  border-brand-500/30  text-brand-300',
  target:   'bg-rose-500/10   border-rose-500/30   text-rose-300',
  pathway:  'bg-amber-500/10  border-amber-500/30  text-amber-300',
  disease:  'bg-purple-500/10 border-purple-500/30 text-purple-300',
  evidence: 'bg-blue-500/10   border-blue-500/30   text-blue-300',
}

const NODE_ICONS: Record<string, LucideIcon> = {
  drug:     Pill,
  target:   Target,
  pathway:  Waypoints,
  disease:  Microscope,
  evidence: BookOpen,
}

function NodeBadge({ node, compact = false }: NodeProps) {
  const style = NODE_STYLES[node.type] ?? NODE_STYLES.evidence
  const Icon  = NODE_ICONS[node.type]  ?? BookOpen

  return (
    <div className={clsx(
      'flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium',
      style,
      compact ? 'text-[11px] px-2 py-1' : ''
    )}>
      <Icon size={compact ? 10 : 12} />
      <span className="truncate max-w-[180px]">{node.label}</span>
      {node.action && (
        <span className="ml-1 opacity-60 font-normal text-[10px] hidden sm:inline">
          ({node.action})
        </span>
      )}
    </div>
  )
}

/* ── Layer section ────────────────────────────────────────────────────────── */

interface LayerProps {
  title: string
  subtitle?: string
  nodes: GraphNode[]
  accent: string
}

function Layer({ title, subtitle, nodes, accent }: LayerProps) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <div className={clsx('w-2 h-2 rounded-full', accent)} />
        <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">{title}</p>
        {subtitle && <p className="text-[10px] text-slate-600">{subtitle}</p>}
      </div>
      <div className="flex flex-wrap gap-2">
        {nodes.map((n, i) => <NodeBadge key={i} node={n} />)}
      </div>
    </div>
  )
}

/* ── Connector ────────────────────────────────────────────────────────────── */

function Connector({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center py-1">
      <div className="w-px h-3 bg-slate-700" />
      <div className="flex items-center gap-1.5">
        <ArrowDown size={12} className="text-slate-600" />
        <span className="text-[10px] text-slate-600 italic">{label}</span>
      </div>
      <div className="w-px h-3 bg-slate-700" />
    </div>
  )
}

/* ── Main component ───────────────────────────────────────────────────────── */

export function RelationshipGraph({ graph }: Props) {
  return (
    <div className="space-y-0">
      {/* Drug */}
      <div className="p-4 rounded-xl border border-brand-500/20 bg-brand-500/5">
        <Layer
          title="Drug"
          subtitle={graph.drug_node.approved_for ? `Approved for: ${graph.drug_node.approved_for}` : undefined}
          nodes={[graph.drug_node]}
          accent="bg-brand-500"
        />
      </div>

      <Connector label="modulates targets" />

      {/* Targets */}
      {graph.target_nodes?.length > 0 && (
        <>
          <div className="p-4 rounded-xl border border-rose-500/20 bg-rose-500/5">
            <Layer
              title="Molecular Targets"
              subtitle="drug acts on these proteins/enzymes"
              nodes={graph.target_nodes}
              accent="bg-rose-500"
            />
          </div>
          <Connector label="activates / inhibits pathways" />
        </>
      )}

      {/* Pathways */}
      {graph.pathway_nodes?.length > 0 && (
        <>
          <div className="p-4 rounded-xl border border-amber-500/20 bg-amber-500/5">
            <Layer
              title="Biological Pathways"
              subtitle="shared with disease biology"
              nodes={graph.pathway_nodes}
              accent="bg-amber-500"
            />
          </div>
          <Connector label="pathway dysregulated in" />
        </>
      )}

      {/* Disease */}
      <div className="p-4 rounded-xl border border-purple-500/20 bg-purple-500/5">
        <Layer
          title="Disease"
          subtitle={graph.disease_node.affected_by ? `Affected by: ${graph.disease_node.affected_by}` : undefined}
          nodes={[graph.disease_node]}
          accent="bg-purple-500"
        />
      </div>

      {/* Evidence */}
      {graph.evidence_nodes?.length > 0 && (
        <>
          <Connector label="supported by" />
          <div className="p-4 rounded-xl border border-blue-500/20 bg-blue-500/5">
            <Layer
              title="Supporting Evidence"
              subtitle="indexed research records"
              nodes={graph.evidence_nodes}
              accent="bg-blue-500"
            />
            {/* Strength legend */}
            <div className="flex gap-3 mt-3 flex-wrap">
              {[
                { label: 'Strong',    color: 'text-emerald-400' },
                { label: 'Moderate', color: 'text-amber-400'  },
                { label: 'Weak',     color: 'text-rose-400'   },
              ].map(({ label, color }) => (
                <div key={label} className="flex items-center gap-1">
                  <div className={clsx('w-1.5 h-1.5 rounded-full', color.replace('text-', 'bg-'))} />
                  <span className={clsx('text-[10px]', color)}>{label}</span>
                </div>
              ))}
              <span className="text-[10px] text-slate-600 ml-auto">DEMO DATA</span>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
