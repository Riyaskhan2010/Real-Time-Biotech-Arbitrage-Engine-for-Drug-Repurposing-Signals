import { clsx } from 'clsx'

export function Spinner({ className }: { className?: string }) {
  return (
    <div
      className={clsx(
        'inline-block animate-spin rounded-full border-2 border-slate-200 border-t-primary-600',
        'w-5 h-5',
        className
      )}
      role="status"
      aria-label="Loading"
    />
  )
}

export function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64" role="status" aria-label="Loading">
      <Spinner className="w-8 h-8" />
    </div>
  )
}
