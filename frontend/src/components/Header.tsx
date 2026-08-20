import { Bell } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useEffect } from 'react'
import { useAlertStore } from '../store/alertStore'
import { useAuthStore } from '../store/authStore'

interface HeaderProps {
  title: string
  subtitle?: string
}

export function Header({ title, subtitle }: HeaderProps) {
  const { unreadCount, fetchUnreadCount } = useAlertStore()
  const { isAuthenticated } = useAuthStore()

  useEffect(() => {
    if (isAuthenticated) fetchUnreadCount()
  }, [isAuthenticated, fetchUnreadCount])

  return (
    <header
      className="flex items-center justify-between px-6 py-3.5 bg-white border-b border-app-border sticky top-0 z-10"
      style={{ boxShadow: '0 1px 3px 0 rgba(0,0,0,.06)' }}
    >
      <div>
        <h1 className="text-[15px] font-semibold text-slate-900 leading-tight">{title}</h1>
        {subtitle && (
          <p className="text-[11px] text-slate-500 mt-0.5 leading-tight">{subtitle}</p>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* Pipeline status */}
        <div className="hidden sm:flex items-center gap-1.5 text-[11px] text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-3 py-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 pulse-green shrink-0" aria-hidden="true" />
          Pipeline Operational
        </div>

        {/* Alerts */}
        <Link
          to="/alerts"
          className="relative p-2 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors focus-ring"
          aria-label={`Alerts${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
        >
          <Bell size={16} aria-hidden="true" />
          {unreadCount > 0 && (
            <span
              className="absolute top-1 right-1 flex items-center justify-center w-4 h-4 rounded-full bg-primary-600 text-[9px] font-bold text-white"
              aria-hidden="true"
            >
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Link>
      </div>
    </header>
  )
}
