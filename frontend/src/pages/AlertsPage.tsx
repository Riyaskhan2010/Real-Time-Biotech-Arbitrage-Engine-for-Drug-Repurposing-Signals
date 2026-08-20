import { useEffect, useState } from 'react'
import { Bell, BellOff, CheckCheck, Zap, BookOpen, TrendingUp } from 'lucide-react'
import { Header } from '../components/Header'
import { PageLoader } from '../components/ui/Spinner'
import { EmptyState } from '../components/ui/EmptyState'
import { Badge } from '../components/ui/Badge'
import { alertsApi } from '../api'
import { useAlertStore } from '../store/alertStore'
import type { Alert } from '../types'
import { clsx } from 'clsx'
import { formatDistanceToNow, parseISO } from 'date-fns'

function alertIcon(type: string) {
  if (type === 'new_signal') return <Zap size={14} className="text-amber-400" />
  if (type === 'new_evidence') return <BookOpen size={14} className="text-blue-400" />
  if (type === 'score_change') return <TrendingUp size={14} className="text-emerald-400" />
  return <Bell size={14} className="text-slate-400" />
}

function AlertRow({ alert, onRead, onDismiss }: {
  alert: Alert
  onRead: (id: number) => void
  onDismiss: (id: number) => void
}) {
  const timeAgo = alert.created_at
    ? formatDistanceToNow(parseISO(alert.created_at), { addSuffix: true })
    : null

  return (
    <div className={clsx(
      'rounded-xl border bg-surface-800 p-4 transition-opacity',
      alert.is_read ? 'border-slate-800 opacity-70' : 'border-slate-700'
    )}>
      <div className="flex items-start gap-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-slate-700/50 shrink-0">
          {alertIcon(alert.alert_type)}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <Badge variant={
              alert.alert_type === 'new_signal' ? 'medium' :
              alert.alert_type === 'new_evidence' ? 'info' : 'high'
            }>
              {alert.alert_type.replace(/_/g, ' ')}
            </Badge>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-700/50 text-slate-400">
              {alert.entity_name}
            </span>
            {!alert.is_read && (
              <span className="w-1.5 h-1.5 rounded-full bg-brand-500" title="Unread" />
            )}
          </div>

          <p className="text-sm font-medium text-slate-200">{alert.title}</p>
          {alert.message && (
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">{alert.message}</p>
          )}

          <div className="flex items-center gap-3 mt-2.5">
            {timeAgo && <span className="text-[11px] text-slate-600">{timeAgo}</span>}
            {!alert.is_read && (
              <button
                onClick={() => onRead(alert.id)}
                className="text-[11px] text-brand-400 hover:text-brand-300 transition-colors"
              >
                Mark read
              </button>
            )}
            <button
              onClick={() => onDismiss(alert.id)}
              className="text-[11px] text-slate-600 hover:text-slate-400 transition-colors"
            >
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const { decrement, reset, fetchUnreadCount } = useAlertStore()

  const load = () => {
    alertsApi.list().then(setAlerts).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleRead = async (id: number) => {
    await alertsApi.markRead(id)
    setAlerts((prev) => prev.map((a) => a.id === id ? { ...a, is_read: true } : a))
    decrement()
  }

  const handleDismiss = async (id: number) => {
    const alert = alerts.find((a) => a.id === id)
    await alertsApi.dismiss(id)
    setAlerts((prev) => prev.filter((a) => a.id !== id))
    if (alert && !alert.is_read) decrement()
  }

  const handleMarkAllRead = async () => {
    await alertsApi.markAllRead()
    setAlerts((prev) => prev.map((a) => ({ ...a, is_read: true })))
    reset()
    // Force a fresh count from the server
    fetchUnreadCount()
  }

  const unreadCount = alerts.filter((a) => !a.is_read).length

  return (
    <div>
      <Header title="Research Alerts" subtitle="New signals and evidence updates for monitored entities" />

      <div className="p-6 space-y-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bell size={14} className="text-slate-400" />
            <span className="text-sm text-slate-300">
              {alerts.length} alert{alerts.length !== 1 ? 's' : ''}
            </span>
            {unreadCount > 0 && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-brand-600 text-white font-medium">
                {unreadCount} unread
              </span>
            )}
          </div>

          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              className="flex items-center gap-1.5 text-xs text-brand-400 hover:text-brand-300 transition-colors"
            >
              <CheckCheck size={13} />
              Mark all read
            </button>
          )}
        </div>

        {loading ? (
          <PageLoader />
        ) : alerts.length === 0 ? (
          <EmptyState
            icon={<BellOff size={32} />}
            title="No alerts"
            description="Alerts appear here when new evidence or signals are detected for monitored drugs and diseases."
          />
        ) : (
          <div className="space-y-3">
            {alerts.map((a) => (
              <AlertRow key={a.id} alert={a} onRead={handleRead} onDismiss={handleDismiss} />
            ))}
          </div>
        )}

        {/* Info about alerts */}
        <div className="rounded-lg border border-slate-800 bg-surface-900/50 p-4 text-xs text-slate-500">
          <p className="font-medium text-slate-400 mb-1">About Research Alerts</p>
          <p>
            Alerts notify you when new evidence is indexed or signal scores change for drugs and diseases
            you're tracking. In the MVP, these are pre-seeded demo alerts. Future versions will support
            real-time notifications when new bioRxiv/PubMed papers are ingested.
          </p>
        </div>
      </div>
    </div>
  )
}
