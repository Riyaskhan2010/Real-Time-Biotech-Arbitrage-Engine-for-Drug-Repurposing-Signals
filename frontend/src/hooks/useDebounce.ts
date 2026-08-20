import { useState, useEffect } from 'react'

/**
 * Returns a debounced copy of `value` that only updates after
 * `delay` ms of silence. Apply to search inputs so API calls
 * only fire when the user pauses typing.
 */
export function useDebounce<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState<T>(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])

  return debounced
}
