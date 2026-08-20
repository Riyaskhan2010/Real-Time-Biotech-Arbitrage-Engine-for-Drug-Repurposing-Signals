import { NavLink, Link } from 'react-router-dom'
import { clsx } from 'clsx'
import {
  LayoutDashboard, Zap, Pill, Microscope, FileText,
  Bell, Settings, FlaskConical, LogOut, Home,
} from 'lucide-react'
import { useAuthStore } from '../store/authStore'

const NAV_SECTIONS = [
  {
    label: 'Research',
    items: [
      { to: '/dashboard', label: 'Dashboard',       icon: LayoutDashboard },
      { to: '/signals',   label: 'Research Signals', icon: Zap             },
      { to: '/drugs',     label: 'Drugs',            icon: Pill            },
      { to: '/diseases',  label: 'Diseases',         icon: Microscope      },
      { to: '/evidence',  label: 'Evidence',         icon: FileText        },
    ],
  },
  {
    label: 'System',
    items: [
      { to: '/alerts',   label: 'Research Alerts', icon: Bell     },
      { to: '/settings', label: 'Settings',         icon: Settings },
    ],
  },
]

export function Sidebar() {
  const { user, logout } = useAuthStore()

  return (
    <aside
      className="fixed inset-y-0 left-0 z-30 flex flex-col w-60"
      style={{ background: '#0B1F3A', boxShadow: '2px 0 8px 0 rgba(0,0,0,.18)' }}
      role="navigation"
      aria-label="Application navigation"
    >
      {/* Brand */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-white/8">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-primary-600 shrink-0">
          <FlaskConical className="text-white" size={18} aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <p className="text-[13px] font-bold text-white leading-tight tracking-tight truncate">BioArbitrage</p>
          <p className="text-[10px] text-white/40 leading-none truncate">Drug Repurposing Intelligence</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 overflow-y-auto space-y-0.5">
        {NAV_SECTIONS.map(({ label, items }) => (
          <div key={label} className="mb-4">
            <p className="px-3 mb-2 text-[9px] font-semibold uppercase tracking-widest text-white/30">
              {label}
            </p>
            {items.map(({ to, label: itemLabel, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-medium transition-colors mb-0.5',
                    isActive
                      ? 'bg-primary-600 text-white'
                      : 'text-white/60 hover:text-white hover:bg-white/8'
                  )
                }
              >
                <Icon size={15} aria-hidden="true" />
                {itemLabel}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* Portal home */}
      <div className="px-3 pb-2">
        <Link
          to="/"
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-[12px] text-white/35 hover:text-white/60 hover:bg-white/5 transition-colors"
          aria-label="Back to landing page"
        >
          <Home size={13} aria-hidden="true" />
          Portal Home
        </Link>
      </div>

      {/* User */}
      <div className="border-t border-white/8 px-3 py-3">
        <div className="flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-white/5 transition-colors">
          <div
            className="flex items-center justify-center w-7 h-7 rounded-full bg-primary-700 text-white text-xs font-bold shrink-0"
            aria-hidden="true"
          >
            {user?.full_name?.[0] ?? user?.username?.[0]?.toUpperCase() ?? 'R'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[13px] font-medium text-white/80 truncate">{user?.full_name ?? user?.username}</p>
            <p className="text-[10px] text-white/35 capitalize truncate">{user?.role}</p>
          </div>
          <button
            onClick={logout}
            className="text-white/30 hover:text-white/60 transition-colors p-1 rounded"
            title="Sign out"
            aria-label="Sign out"
          >
            <LogOut size={14} aria-hidden="true" />
          </button>
        </div>
        <p className="mt-1.5 px-2 text-[9px] leading-relaxed text-white/20">
          Research decision-support only. Not for clinical use.
        </p>
      </div>
    </aside>
  )
}
