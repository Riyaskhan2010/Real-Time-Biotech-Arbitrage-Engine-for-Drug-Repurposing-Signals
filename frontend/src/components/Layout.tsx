import { Outlet, Navigate } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { useAuthStore } from '../store/authStore'

export function Layout() {
  const { isAuthenticated } = useAuthStore()

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
