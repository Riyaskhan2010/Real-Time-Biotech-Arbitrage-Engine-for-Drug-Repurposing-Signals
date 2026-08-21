/**
 * App.tsx — Root router
 *
 * /           → always LandingPage (public, never redirects)
 * /login      → LoginPage (redirects authenticated users to /dashboard)
 * /register   → RegisterPage (redirects authenticated users to /dashboard)
 * /dashboard+ → protected, redirects unauthenticated to /login
 *
 * The 401 redirect-to-login logic lives in client.ts interceptor, NOT here.
 */
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
  const { isAuthenticated } = useAuthStore()
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return <LoginPage />
}

/** /register — redirects authenticated users to dashboard. */
function PublicRegister() {
  const { isAuthenticated } = useAuthStore()
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return <RegisterPage />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"         element={<PublicHome />} />
        <Route path="/login"    element={<PublicLogin />} />
        <Route path="/register" element={<PublicRegister />} />

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
