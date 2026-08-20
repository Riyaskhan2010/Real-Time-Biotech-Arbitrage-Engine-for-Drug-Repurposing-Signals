/**
 * WhyThisSignal
 * =============
 * The primary "How did BioArbitrage discover this signal?" section.
 * Shows: mechanism summary, how_detected narrative, pathway overlap,
 * evidence type breakdown, research gaps, and clinical readiness.
 *
 * All content is evidence-based. Demo data clearly labelled.
 * Never makes clinical recommendations.
 */
import {
  HelpCircle, GitMerge, FileSearch, AlertTriangle,
  CheckCircle2, XCircle, FlaskConical, Target, Waypoints,
} from 'lucide-react'
import { clsx } from 'clsx'
import type { DetectionRationale, EvidenceMatching } from '../types'

interface Props {
  drugName: string
  diseaseName: string
  rationale: DetectionRationale
  matching: EvidenceMatching
  biologicalMechanism?: string | null
}

const STRENGTH_STYLE: Record<string, string> = {
  strong:   'text-emerald-400 bg-emerald-500/10 border-emerald-500/25',
  moderate: 'text-amber-400   bg-amber-500/10   border-amber-500/25',
  weak:     'text-rose-400    bg-rose-500/10    border-rose-500/25',
}

export function WhyThisSignal({ drugName, diseaseName, rationale, matching, biologicalMechanism }: Props) {
  const strengthStyle = STRENGTH_STYLE[matching.support_strength] ?? STRENGTH_STYLE.weak

  return (
    <div className="space-y-5">
      {/* Title banner */}
      <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-brand-600/10 border border-brand-500/25">
        <HelpCircle size={16} className="text-brand-400 shrink-0" />
        <div>
          <p className="text-sm font-semibold text-brand-300">
            How did BioArbitrage detect this signal?
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5">
            <strong className="text-brand-400">{drugName}</strong>
            <span className="mx-1.5 text-slate-600">→</span>
            <strong className="text-purple-400">{diseaseName}</strong>
            <span className="mx-1.5 text-slate-600">·</span>
            Candidate research association · Requires expert validation
          </p>
        </div>
      </div>

      {/* How it was detected */}
      <section>
        <div className="flex items-center gap-2 mb-2">
          <FileSearch size={13} className="text-brand-400" />
          <h4 className="text-xs font-semibold text-slate-200">Detection Narrative</h4>
        </div>
        <p className="text-sm text-slate-300 leading-relaxed bg-slate-800/40 rounded-lg px-4 py-3 border border-slate-700/50">
          {rationale.how_detected}
        </p>
      </section>

      {/* Mechanism summary */}
      {(rationale.mechanism_summary || biologicalMechanism) && (
        <section>
          <div className="flex items-center gap-2 mb-2">
            <GitMerge size={13} className="text-purple-400" />
            <h4 className="text-xs font-semibold text-slate-200">Biological Mechanism Chain</h4>
          </div>
          <div className="px-4 py-3 rounded-lg bg-purple-500/8 border border-purple-500/20">
            <p className="text-sm font-mono text-purple-300 leading-relaxed tracking-wide">
              {rationale.mechanism_summary || biologicalMechanism}
            </p>
          </div>
          {biologicalMechanism && rationale.mechanism_summary !== biologicalMechanism && (
            <p className="text-xs text-slate-400 leading-relaxed mt-2 pl-1">
              {biologicalMechanism}
            </p>
          )}
        </section>
      )}

      {/* Two-column: pathway overlap + shared targets */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {rationale.pathway_overlap?.length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-2">
              <Waypoints size={12} className="text-amber-400" />
              <h4 className="text-xs font-semibold text-slate-200">Shared Pathways</h4>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {rationale.pathway_overlap.map((p) => (
                <span key={p} className="text-[11px] px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/25 text-amber-300">
                  {p}
                </span>
              ))}
            </div>
          </section>
        )}

        {rationale.shared_targets?.length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-2">
              <Target size={12} className="text-rose-400" />
              <h4 className="text-xs font-semibold text-slate-200">Shared Molecular Targets</h4>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {rationale.shared_targets.map((t) => (
                <span key={t} className="text-[11px] px-2.5 py-1 rounded-full bg-rose-500/10 border border-rose-500/25 text-rose-300 font-mono">
                  {t}
                </span>
              ))}
            </div>
          </section>
        )}
      </div>

      {/* Cross-source matching result */}
      <section>
        <div className="flex items-center gap-2 mb-2">
          <CheckCircle2 size={13} className="text-emerald-400" />
          <h4 className="text-xs font-semibold text-slate-200">Cross-Source Evidence Matching</h4>
        </div>
        <div className={clsx('px-4 py-3 rounded-lg border', strengthStyle)}>
          <div className="flex items-center justify-between mb-1.5">
            <p className="text-xs font-semibold capitalize">
              {matching.support_strength} support across independent sources
            </p>
          </div>
          <p className="text-xs leading-relaxed opacity-90">{matching.consensus}</p>
          {matching.key_finding && (
            <p className="text-xs mt-2 opacity-75 italic">{matching.key_finding}</p>
          )}
        </div>
      </section>

      {/* Evidence types found */}
      {rationale.evidence_types_found?.length > 0 && (
        <section>
          <div className="flex items-center gap-2 mb-2">
            <FlaskConical size={12} className="text-blue-400" />
            <h4 className="text-xs font-semibold text-slate-200">Evidence Types Identified</h4>
          </div>
          <div className="flex flex-wrap gap-2">
            {rationale.evidence_types_found.map((t) => (
              <span key={t} className="text-[11px] px-2.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/25 text-blue-300">
                {t.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Research gaps */}
      {matching.gaps?.length > 0 || rationale.research_gaps?.length > 0 ? (
        <section>
          <div className="flex items-center gap-2 mb-2">
            <XCircle size={13} className="text-rose-400" />
            <h4 className="text-xs font-semibold text-slate-200">Research Gaps & Limitations</h4>
          </div>
          <ul className="space-y-1.5">
            {[...(rationale.research_gaps ?? []), ...(matching.gaps ?? [])].map((gap, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
                <span className="text-rose-500 mt-0.5 shrink-0">·</span>
                {gap}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {/* Clinical readiness */}
      {rationale.clinical_readiness && (
        <section>
          <div className="flex items-center gap-2 mb-2">
            <FlaskConical size={12} className="text-emerald-400" />
            <h4 className="text-xs font-semibold text-slate-200">Current Research Stage</h4>
          </div>
          <p className="text-xs text-slate-300 px-3 py-2 rounded-lg bg-slate-800/50 border border-slate-700/50">
            {rationale.clinical_readiness}
          </p>
        </section>
      )}

      {/* Safety disclaimer */}
      <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg bg-amber-500/8 border border-amber-500/20">
        <AlertTriangle size={12} className="text-amber-400 shrink-0 mt-0.5" />
        <p className="text-[10px] text-amber-400/80 leading-relaxed">
          This explanation is a <strong>research-prioritization signal</strong> generated by an
          experimental system. It describes a <em>candidate research association</em> that requires
          expert validation. It is NOT a clinical recommendation, medical advice, or evidence of
          drug efficacy. Do not use for patient care or treatment decisions.
        </p>
      </div>
    </div>
  )
}
