/**
 * RegisterPage
 * POST /api/auth/register → creates account → redirect to /login
 * Auth-redirect (already-logged-in) handled at route level in App.tsx.
 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FlaskConical, Eye, EyeOff, ArrowLeft, CheckCircle2, UserPlus } from 'lucide-react'
import { authApi } from '../api'
import { Spinner } from '../components/ui/Spinner'

const PERKS = [
  'Access 7 connected biomedical evidence sources',
  'Explore drug–disease repurposing signals',
  'Full source traceability — DOI, PMID, NCT ID',
  'Research-only platform — not clinical guidance',
]

export function RegisterPage() {
  const navigate = useNavigate()

  const [fullName,     setFullName]    = useState('')
  const [email,        setEmail]       = useState('')
  const [username,     setUsername]    = useState('')
  const [institution,  setInstitution] = useState('')
  const [password,     setPassword]    = useState('')
  const [confirm,      setConfirm]     = useState('')
  const [showPw,       setShowPw]      = useState(false)
  const [isLoading,    setIsLoading]   = useState(false)
  const [error,        setError]       = useState<string | null>(null)
  const [success,      setSuccess]     = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (password !== confirm) {
      setError('Passwords do not match')
      return
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }

    setIsLoading(true)
    try {
      await authApi.register({ full_name: fullName, email, username, password, institution: institution || undefined })
      setSuccess(true)
      setTimeout(() => navigate('/login'), 2000)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Registration failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex bg-white">

      {/* Left panel — navy brand */}
      <div className="hidden lg:flex flex-col justify-between w-5/12 p-10 text-white"
        style={{ background: '#0B1F3A' }}>
        <div>
          <div className="flex items-center gap-3 mb-10">
            <div className="w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center">
              <FlaskConical size={18} className="text-white" />
            </div>
            <div>
              <p className="text-[13px] font-bold leading-tight">BioArbitrage</p>
              <p className="text-[10px] text-white/50 leading-none">Drug Repurposing Intelligence</p>
            </div>
          </div>

          <div className="mb-8">
            <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center mb-4">
              <UserPlus size={24} className="text-white" />
            </div>
            <h1 className="text-2xl font-bold leading-snug mb-3">
              Join the Research Intelligence Platform
            </h1>
            <p className="text-white/60 text-sm leading-relaxed">
              Create your researcher account to access biomedical evidence intelligence,
              drug repurposing signals, and source traceability tools.
            </p>
          </div>

          <div className="space-y-3">
            {PERKS.map(p => (
              <div key={p} className="flex items-start gap-2.5">
                <CheckCircle2 size={14} className="text-green-400 shrink-0 mt-0.5" />
                <p className="text-[13px] text-white/70">{p}</p>
              </div>
            ))}
          </div>
        </div>

        <p className="text-[11px] text-white/25 leading-relaxed border-t border-white/10 pt-5">
          Research decision-support only. Not for clinical use, diagnosis, or treatment recommendations.
        </p>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-10 bg-slate-50">
        <div className="w-full max-w-sm">

          <Link to="/login"
            className="inline-flex items-center gap-1.5 text-[13px] text-slate-500 hover:text-slate-700 mb-6 transition-colors">
            <ArrowLeft size={14} /> Back to Sign In
          </Link>

          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-5">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: '#0B1F3A' }}>
              <FlaskConical size={15} className="text-white" />
            </div>
            <div>
              <p className="text-[13px] font-bold text-slate-900">BioArbitrage</p>
              <p className="text-[10px] text-slate-500">Drug Repurposing Intelligence</p>
            </div>
          </div>

          {/* Card */}
          {success ? (
            <div className="bg-white rounded-xl border border-slate-200 p-8 text-center"
              style={{ boxShadow: '0 1px 3px 0 rgba(0,0,0,.06), 0 4px 16px 0 rgba(0,0,0,.04)' }}>
              <CheckCircle2 size={40} className="text-green-500 mx-auto mb-3" />
              <h2 className="text-lg font-bold text-slate-900 mb-1">Account Created!</h2>
              <p className="text-[13px] text-slate-500">Redirecting you to sign in…</p>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-slate-200 p-7"
              style={{ boxShadow: '0 1px 3px 0 rgba(0,0,0,.06), 0 4px 16px 0 rgba(0,0,0,.04)' }}>
              <h2 className="text-lg font-bold text-slate-900 mb-0.5">Create Your Research Account</h2>
              <p className="text-[13px] text-slate-500 mb-5">Access the BioArbitrage research intelligence platform</p>

              <form onSubmit={handleSubmit} className="space-y-3.5" noValidate>

                <div>
                  <label className="block text-[12px] font-semibold text-slate-600 mb-1" htmlFor="fullName">
                    Full Name <span className="text-red-400">*</span>
                  </label>
                  <input id="fullName" type="text" required value={fullName} onChange={e => setFullName(e.target.value)}
                    placeholder="Dr. Jane Smith"
                    className="w-full px-3 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900
                               focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 transition-colors" />
                </div>

                <div>
                  <label className="block text-[12px] font-semibold text-slate-600 mb-1" htmlFor="regEmail">
                    Email <span className="text-red-400">*</span>
                  </label>
                  <input id="regEmail" type="email" required value={email} onChange={e => setEmail(e.target.value)}
                    placeholder="jane@university.edu"
                    className="w-full px-3 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900
                               focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 transition-colors" />
                </div>

                <div>
                  <label className="block text-[12px] font-semibold text-slate-600 mb-1" htmlFor="regUsername">
                    Username <span className="text-red-400">*</span>
                  </label>
                  <input id="regUsername" type="text" required value={username} onChange={e => setUsername(e.target.value)}
                    placeholder="jane_researcher"
                    className="w-full px-3 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900
                               focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 transition-colors" />
                </div>

                <div>
                  <label className="block text-[12px] font-semibold text-slate-600 mb-1" htmlFor="institution">
                    Institution <span className="text-slate-400 font-normal">(optional)</span>
                  </label>
                  <input id="institution" type="text" value={institution} onChange={e => setInstitution(e.target.value)}
                    placeholder="University / Organization"
                    className="w-full px-3 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900
                               focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 transition-colors" />
                </div>

                <div>
                  <label className="block text-[12px] font-semibold text-slate-600 mb-1" htmlFor="regPw">
                    Password <span className="text-red-400">*</span>
                  </label>
                  <div className="relative">
                    <input id="regPw" type={showPw ? 'text' : 'password'} required value={password}
                      onChange={e => setPassword(e.target.value)} placeholder="Min 6 characters"
                      className="w-full pl-3 pr-10 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900
                                 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 transition-colors" />
                    <button type="button" onClick={() => setShowPw(v => !v)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                      aria-label={showPw ? 'Hide password' : 'Show password'}>
                      {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-[12px] font-semibold text-slate-600 mb-1" htmlFor="confirmPw">
                    Confirm Password <span className="text-red-400">*</span>
                  </label>
                  <input id="confirmPw" type="password" required value={confirm} onChange={e => setConfirm(e.target.value)}
                    placeholder="Re-enter password"
                    className="w-full px-3 py-2.5 text-sm bg-white border border-slate-300 rounded-lg text-slate-900
                               focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 transition-colors" />
                </div>

                {error && (
                  <div role="alert" className="text-[13px] text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2.5">
                    {error}
                  </div>
                )}

                <button type="submit" disabled={isLoading}
                  className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-[13px] font-semibold
                             text-white transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                  style={{ background: '#0B1F3A', boxShadow: '0 1px 3px 0 rgba(0,0,0,.15)' }}>
                  {isLoading ? <Spinner className="w-4 h-4 border-white/40 border-t-white" /> : (
                    <><UserPlus size={15} />Create Research Account</>
                  )}
                </button>
              </form>
            </div>
          )}

          <p className="mt-4 text-center text-[12px] text-slate-500">
            Already have an account?{' '}
            <Link to="/login" className="font-semibold hover:underline" style={{ color: '#0B1F3A' }}>
              Sign In
            </Link>
          </p>

          <p className="mt-4 text-center text-[11px] text-slate-400 leading-relaxed">
            For qualified biomedical researchers only.
            Not for clinical use or treatment decisions.
          </p>
        </div>
      </div>
    </div>
  )
}
