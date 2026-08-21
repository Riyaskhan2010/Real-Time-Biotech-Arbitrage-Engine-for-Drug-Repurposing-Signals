/**
 * App.tsx — Root router
 *
 * Landing page (/) is always public — never redirects regardless of auth state.
 * A stored token in localStorage would previously cause isAuthenticated=true
 * on first render, making PublicHome immediately navigate away before the
 * landing page could display. Removing that redirect fixes the disappearing page.
 *
 * Login page (/login) still redirects authenticated users to /dashboard.
 * Protected routes (/dashboard etc.) redirect unauthenticated users to /login.
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { LandingPage } from './pages/LandingPage'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { SignalsPage } from './pages/SignalsPage'
import { SignalDetailPage } from './pages/SignalDetailPage'
import { DrugsPage } from './pages/DrugsPage'
import { DiseasesPage } from './pages/DiseasesPage'
import { EvidencePage } from './pages/EvidencePage'
import { AlertsPage } from './pages/AlertsPage'
import { SettingsPage } from './pages/SettingsPage'
import { useAuthStore } from './store/authStore'

/** Always renders the landing page — no auth redirect.
 *  Authenticated users can navigate to the dashboard via the UI buttons.
 *  The landing page must always be accessible regardless of login state. */
function PublicHome() {
  return <LandingPage />
}

/** Redirects authenticated users away from login. */
function PublicLogin() {
  const { isAuthenticated } = useAuthStore()
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return <LoginPage />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes — guard at route level, not inside components */}
        <Route path="/"      element={<PublicHome />} />
        <Route path="/login" element={<PublicLogin />} />

        {/* Authenticated app routes */}
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

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
