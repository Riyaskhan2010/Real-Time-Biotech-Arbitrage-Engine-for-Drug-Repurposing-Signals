/**
 * App.tsx — Root router
 *
 * /           → always LandingPage (public, never redirects)
 * /login      → LoginPage (redirects authenticated users to /dashboard)
 * /register   → RegisterPage (redirects authenticated users to /dashboard)
 * /dashboard+ → protected, redirects unauthenticated to /login
 *
 * On mount, App calls initAuth() to validate any stored token against
 * /api/auth/me BEFORE rendering protected routes. This prevents the
 * "Failed to load dashboard data" error caused by stale/expired tokens
 * reaching the dashboard before being cleared.
 */
import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout }          from './components/Layout'
import { LandingPage }     from './pages/LandingPage'
import { LoginPage }       from './pages/LoginPage'
import { RegisterPage }    from './pages/RegisterPage'
import { DashboardPage }   from './pages/DashboardPage'
import { SignalsPage }     from './pages/SignalsPage'
import { SignalDetailPage }from './pages/SignalDetailPage'
import { DrugsPage }       from './pages/DrugsPage'
import { DiseasesPage }    from './pages/DiseasesPage'
import { EvidencePage }    from './pages/EvidencePage'
import { AlertsPage }      from './pages/AlertsPage'
import { SettingsPage }    from './pages/SettingsPage'
import { useAuthStore }    from './store/authStore'

/** / — always public, never redirects. */
function PublicHome() {
  return <LandingPage />
}

/** /login — redirects authenticated users to dashboard. */
function PublicLogin() {
  const { isAuthenticated, isInitializing } = useAuthStore()
  if (isInitializing) return null   // wait for token validation
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return <LoginPage />
}

/** /register — redirects authenticated users to dashboard. */
function PublicRegister() {
  const { isAuthenticated, isInitializing } = useAuthStore()
  if (isInitializing) return null   // wait for token validation
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return <RegisterPage />
}

export default function App() {
  const { initAuth, isInitializing } = useAuthStore()

  // Validate any stored token before rendering protected routes.
  // This runs once on mount and clears expired tokens before the
  // dashboard page attempts its own API calls.
  useEffect(() => {
    initAuth()
  }, [])   // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"         element={<PublicHome />} />
        <Route path="/login"    element={<PublicLogin />} />
        <Route path="/register" element={<PublicRegister />} />

        {/* Protected routes — Layout redirects to /login if not authenticated.
            While initAuth is still running (isInitializing=true), Layout shows
            a blank screen rather than loading protected data with a stale token. */}
        <Route element={<Layout />}>
          <Route path="/dashboard"   element={<DashboardPage />} />
          <Route path="/signals"     element={<SignalsPage />} />
          <Route path="/signals/:id" element={<SignalDetailPage />} />
          <Route path="/drugs"       element={<DrugsPage />} />
          <Route path="/diseases"    element={<DiseasesPage />} />
          <Route path="/evidence"    element={<EvidencePage />} />
          <Route path="/alerts"      element={<AlertsPage />} />
          <Route path="/settings"    element={<SettingsPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
