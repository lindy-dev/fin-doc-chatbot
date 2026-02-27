import { Navigate, Route, Routes } from 'react-router-dom'
import RegisterPage from './pages/RegisterPage'
import LoginPage from './pages/LoginPage'
import AdminDashboardPage from './pages/AdminDashboardPage'
import UserDashboardPage from './pages/UserDashboardPage'
import ChatPage from './pages/ChatPage'
import PendingApprovalPage from './pages/PendingApprovalPage'
import { useAuth } from './services/auth'

const LoadingScreen = () => (
  <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-200">
    Loading...
  </div>
)

type GuardProps = {
  children: React.ReactNode
  role?: 'admin' | 'user'
}

const Guard = ({ children, role }: GuardProps) => {
  const { user, loading } = useAuth()

  if (loading) {
    return <LoadingScreen />
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (role && user.role !== role) {
    return <Navigate to="/" replace />
  }

  if (user.role === 'user' && !user.is_approved) {
    return <Navigate to="/pending" replace />
  }

  return <>{children}</>
}

const LandingRedirect = () => {
  const { user, loading } = useAuth()

  if (loading) {
    return <LoadingScreen />
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return (
    <Navigate
      to={user.role === 'admin' ? '/admin' : '/dashboard'}
      replace
    />
  )
}

const AppRouter = () => {
  return (
    <Routes>
      <Route path="/" element={<LandingRedirect />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/pending" element={<PendingApprovalPage />} />
      <Route
        path="/admin"
        element={
          <Guard role="admin">
            <AdminDashboardPage />
          </Guard>
        }
      />
      <Route
        path="/dashboard"
        element={
          <Guard role="user">
            <UserDashboardPage />
          </Guard>
        }
      />
      <Route
        path="/chat"
        element={
          <Guard role="user">
            <ChatPage />
          </Guard>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default AppRouter
