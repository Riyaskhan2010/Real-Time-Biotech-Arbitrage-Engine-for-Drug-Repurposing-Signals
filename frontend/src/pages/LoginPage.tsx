/**
 * LoginPage — Institutional split-panel style.
 * Auth-redirect is handled by PublicLogin wrapper in App.tsx — not here.
 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FlaskConical, Eye, EyeOff, ArrowLeft, CheckCircle2 } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { Spinner } from '../components/ui/Spinner'

const TRUST_POINTS = [
  'Evidence aggregated from 7 biomedical sources',
  'Full source traceability — DOI, PMID, NCT ID',
  'Cross-source deduplication for accurate scoring',
  'Research-only platform — not clinical guidance',
]

export function LoginPage() {
  const [username, setUsername] = useState('demo_researcher')
  const [password, setPassword] = useState('demo1234')
  const [showPw, setShowPw] = useState(false)
  const { login, isLoading, error, clearError } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    try {
      await login(username, password)
      navigate('/dashboard', { replace: true })
    } catch {
      /* error stored in authStore */
    }
  }

  return (
    <div className="min-h-screen flex bg-white">

      {/* Left — brand panel */}
      <div className="hidden lg:flex flex-col justify-between w-5/12 bg-navy-900 text-white p-10">
        <div>
          {/* Logo */}
          <div className="flex items-center gap-3 mb-10">
            <div className="w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center">
              <FlaskConical size={18} className="text-white" aria-hidden="true" />
            </div>
            <div>
              <p className="text-[13px] font-bold leading-tight">BioArbitrage Engine</p>
              <p className="text-[10px] text-white/50 leading-none">Drug Repurposing Intelligence</p>
            </div>
          </div>

          <h1 className="text-2xl font-bold leading-snug mb-3">
            Real-Time Biotech Arbitrage Engine for Drug Repurposing Signals
          </h1>
          <p className="text-white/60 text-sm leading-relaxed mb-8">
            AI-assisted evidence discovery and research prioritization. Evidence from 7 connected
            biomedical databases, deduplicated and scored for research relevance.
          </p>

          <div className="space-y-3">
            {TRUST_POINTS.map(point => (
              <div key={point} className="flex items-start gap-2.5">
                <CheckCircle2 size={14} className="text-green-400 shrink-0 mt-0.5" aria-hidden="true" />
                <p className="text-[13px] text-white/70">{point}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="border-t border-white/10 pt-5">
          <p className="text-[11px] text-white/35 leading-relaxed">
            Research decision-support tool only. Not for clinical use, diagnosis,
            or treatment recommendations. All signals require expert validation.
          </p>
        </div>
      </div>

      {/* Right — form */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12 bg-slate-50">
        <div className="w-full max-w-sm">

          {/* Back */}
          <Link to="/"
            className="inline-flex items-center gap-1.5 text-[13px] text-slate-500 hover:text-slate-700 mb-8 transition-colors focus-ring rounded"
            aria-label="Back to portal home">
            <ArrowLeft size={14} aria-hidden="true" />
            Back to Portal
          </Link>

          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-6">
            <div className="w-8 h-8 rounded-lg bg-navy-900 flex items-center justify-center">
              <FlaskConical size={15} className="text-white" aria-hidden="true" />
            </div>
            <div>
              <p className="text-[13px] font-bold text-slate-900">BioArbitrage Engine</p>
              <p className="text-[10px] text-slate-500">Drug Repurposing Intelligence</p>
            </div>
          </div>

          {/* Card */}
          <div className="bg-white rounded-xl border border-slate-200 p-7"
            style={{ boxShadow: '0 1px 3px 0 rgba(0,0,0,.06), 0 4px 16px 0 rgba(0,0,0,.04)' }}>
            <h2 className="text-lg font-bold text-slate-900 mb-0.5">Researcher Sign In</h2>
            <p className="text-[13px] text-slate-500 mb-6">Access the research intelligence platform</p>

            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
              <div>
                <label className="block text-[13px] font-medium text-slate-700 mb-1.5" htmlFor="username">
                  Username
                </label>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  required
                  autoComplete="username"
                  className="w-full px-3 py-2.5 text-sm bg-white border border-slate-300 rounded-lg
                             text-slate-900 placeholder:text-slate-400
                             focus:outline-none focus:border-navy-500 focus:ring-2 focus:ring-navy-500/15
                             transition-colors"
                />
              </div>

              <div>
                <label className="block text-[13px] font-medium text-slate-700 mb-1.5" htmlFor="password">
                  Password
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPw ? 'text' : 'password'}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                    className="w-full pl-3 pr-10 py-2.5 text-sm bg-white border border-slate-300 rounded-lg
                               text-slate-900 placeholder:text-slate-400
                               focus:outline-none focus:border-navy-500 focus:ring-2 focus:ring-navy-500/15
                               transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw(v => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus-ring rounded"
                    aria-label={showPw ? 'Hide password' : 'Show password'}
                  >
                    {showPw ? <EyeOff size={15} aria-hidden="true" /> : <Eye size={15} aria-hidden="true" />}
                  </button>
                </div>
              </div>

              {error && (
                <div role="alert" className="text-[13px] text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2.5">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg
                           bg-navy-900 hover:bg-navy-800 text-white text-[13px] font-semibold
                           transition-colors disabled:opacity-60 disabled:cursor-not-allowed focus-ring"
                style={{ boxShadow: '0 1px 3px 0 rgba(0,0,0,.15)' }}
              >
                {isLoading
                  ? <Spinner className="w-4 h-4 border-white/40 border-t-white" />
                  : 'Sign In to Platform'
                }
              </button>
            </form>
          </div>

          {/* Demo credentials */}
          <div className="mt-4 bg-white rounded-lg border border-slate-200 px-4 py-3">
            <p className="text-[11px] font-semibold text-slate-500 mb-1.5">Demo Credentials</p>
            <div className="space-y-0.5 text-[11px] text-slate-600 font-mono">
              <p>demo_researcher / demo1234</p>
              <p>demo_admin / admin1234</p>
            </div>
          </div>

          <p className="mt-4 text-center text-[12px] text-slate-500">
            Don&apos;t have an account?{' '}
            <Link to="/register" className="font-semibold text-navy-700 hover:underline">
              Create Account
            </Link>
          </p>

          <p className="mt-3 text-center text-[11px] text-slate-400 leading-relaxed">
            For qualified biomedical researchers only.
            Not for clinical use or treatment decisions.
          </p>
        </div>
      </div>
    </div>
  )
}
