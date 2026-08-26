import { Outlet, Navigate } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { useAuthStore } from '../store/authStore'
import { PageLoader } from './ui/Spinner'

export function Layout() {
  const { isAuthenticated, isInitializing } = useAuthStore()

  // While the token validation request is in flight, show a loader.
  // This prevents DashboardPage from firing its own API calls with a
  // stale/expired token before initAuth() has finished clearing it.
  if (isInitializing) {
    return <PageLoader />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Dark navy sidebar */}
      <Sidebar />
      {/* Light content area */}
      <main className="flex-1 ml-60 overflow-y-auto bg-app-bg min-h-screen">
        <Outlet />
      </main>
    </div>
  )
}
