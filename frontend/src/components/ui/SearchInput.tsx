import { Search, X } from 'lucide-react'
import { clsx } from 'clsx'

interface SearchInputProps {
  value: string
  onChange: (v: string) => void
  placeholder?: string
  className?: string
}

export function SearchInput({ value, onChange, placeholder = 'Search…', className }: SearchInputProps) {
  return (
    <div className={clsx('relative', className)}>
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" aria-hidden="true" />
      <input
        type="search"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-9 pr-8 py-2 text-[13px] bg-white border border-slate-300 rounded-lg
                   text-slate-900 placeholder:text-slate-400
                   focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/15
                   transition-colors"
        style={{ boxShadow: '0 1px 2px 0 rgba(0,0,0,.04)' }}
      />
      {value && (
        <button
          type="button"
          onClick={() => onChange('')}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus-ring rounded"
          aria-label="Clear search"
        >
          <X className="w-3.5 h-3.5" aria-hidden="true" />
        </button>
      )}
    </div>
  )
}
