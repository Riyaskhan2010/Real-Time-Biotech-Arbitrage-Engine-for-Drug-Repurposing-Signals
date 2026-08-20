/**
 * SignalPipeline
 * ==============
 * Visual 6-step pipeline showing exactly HOW BioArbitrage detected a signal.
 * This is the primary "How did we find this?" component for hackathon judges.
 *
 * Steps: Ingestion → Entity Extraction → Mechanism ID → Cross-Source Matching
 *        → Evidence Scoring → Signal Generated
 */
import { useState } from 'react'
import {
  Database, Cpu, GitMerge, Layers, BarChart2, Zap,
  ChevronDown, ChevronUp, CheckCircle2, FlaskConical,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { clsx } from 'clsx'
import type { PipelineStep } from '../types'

interface Props {
  steps: PipelineStep[]
  drugName: string
  diseaseName: string
}

const ICON_MAP: Record<string, LucideIcon> = {
  database:      Database,
  cpu:           Cpu,
  'git-merge':   GitMerge,
  layers:        Layers,
  'bar-chart-2': BarChart2,
  zap:           Zap,
}

const STEP_COLORS = [
  'border-blue-500/40   bg-blue-500/8   text-blue-400',
  'border-violet-500/40 bg-violet-500/8 text-violet-400',
  'border-purple-500/40 bg-purple-500/8 text-purple-400',
  'border-amber-500/40  bg-amber-500/8  text-amber-400',
  'border-orange-500/40 bg-orange-500/8 text-orange-400',
  'border-emerald-500/40 bg-emerald-500/8 text-emerald-400',
]

const CONNECTOR_COLORS = [
  'from-blue-500/30',
  'from-violet-500/30',
  'from-purple-500/30',
  'from-amber-500/30',
  'from-orange-500/30',
]

export function SignalPipeline({ steps, drugName, diseaseName }: Props) {
  const [expandedStep, setExpandedStep] = useState<number | null>(null)

  const toggle = (step: number) =>
    setExpandedStep((prev) => (prev === step ? null : step))

  return (
    <div className="space-y-2">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <div className="flex items-center justify-center w-6 h-6 rounded-full bg-brand-600/20 border border-brand-500/30">
          <Zap size={12} className="text-brand-400" />
        </div>
        <div>
          <p className="text-xs font-semibold text-slate-200">
            Detection Pipeline: <span className="text-brand-300">{drugName}</span>
            <span className="text-slate-500 mx-1.5">→</span>
            <span className="text-purple-300">{diseaseName}</span>
          </p>
          <p className="text-[10px] text-slate-500 mt-0.5">
            Click any step to see exactly what the system did at that stage
          </p>
        </div>
      </div>

      {/* Steps */}
      <div className="relative">
        {steps.map((step, idx) => {
          const IconComp = ICON_MAP[step.icon] ?? Zap
          const colorClass = STEP_COLORS[idx % STEP_COLORS.length]
          const isExpanded = expandedStep === step.step
          const isLast = idx === steps.length - 1

          return (
            <div key={step.step} className="relative">
              {/* Connector line */}
              {!isLast && (
                <div className="absolute left-[19px] top-[52px] w-px h-4 bg-gradient-to-b from-slate-600 to-slate-700 z-0" />
              )}

              <div className={clsx('relative z-10 rounded-xl border transition-all duration-200 mb-2', colorClass,
                isExpanded ? 'shadow-lg' : 'hover:brightness-110 cursor-pointer'
              )}>
                {/* Step row */}
                <button
                  onClick={() => toggle(step.step)}
                  className="w-full flex items-center gap-3 px-4 py-3 text-left"
                  aria-expanded={isExpanded}
                >
                  {/* Step number + icon */}
                  <div className="flex items-center gap-2 shrink-0">
                    <div className={clsx(
                      'flex items-center justify-center w-7 h-7 rounded-full border-2 text-xs font-bold',
                      colorClass
                    )}>
                      {step.step}
                    </div>
                    <IconComp size={14} />
                  </div>

                  {/* Stage name + description */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-xs font-semibold">{step.stage}</p>
                      <CheckCircle2 size={11} className="text-emerald-500 shrink-0" />
                      {step.is_demo && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-slate-700/60 text-slate-500 border border-slate-600/40">
                          DEMO
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] opacity-70 mt-0.5">{step.description}</p>
                  </div>

                  {/* Output badge */}
                  <div className="hidden sm:flex items-center gap-2 shrink-0">
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-black/20 border border-current/20 opacity-80 max-w-[160px] truncate">
                      {step.output}
                    </span>
                    {isExpanded
                      ? <ChevronUp size={12} className="opacity-60" />
                      : <ChevronDown size={12} className="opacity-60" />
                    }
                  </div>
                </button>

                {/* Expanded detail */}
                {isExpanded && (
                  <div className="px-4 pb-4 pt-1 border-t border-current/10">
                    <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
                      {step.detail}
                    </p>
                    <div className="mt-2.5 flex items-center gap-2">
                      <span className="text-[10px] text-slate-500">Output:</span>
                      <span className="text-[10px] font-mono text-slate-300 bg-black/20 px-2 py-0.5 rounded">
                        {step.output}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Footer disclaimer */}
      <div className="flex items-start gap-2 mt-3 px-3 py-2 rounded-lg bg-slate-800/40 border border-slate-700/40">
        <FlaskConical size={11} className="text-slate-500 shrink-0 mt-0.5" />
        <p className="text-[10px] text-slate-500 leading-relaxed">
          <strong className="text-slate-400">DEMO DATA</strong> — This pipeline trace uses
          simulated research records to illustrate the BioArbitrage detection process.
          All signals require expert validation. This is NOT clinical guidance.
        </p>
      </div>
    </div>
  )
}
