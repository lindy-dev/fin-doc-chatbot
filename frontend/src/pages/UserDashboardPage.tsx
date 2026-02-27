import { Link } from 'react-router-dom'
import PageShell from '../components/PageShell'
import { useAuth } from '../services/auth'

const UserDashboardPage = () => {
  const { user, logout } = useAuth()

  return (
    <PageShell
      title="User dashboard"
      subtitle="Review your account and start chatting"
      action={
        <button
          className="rounded-full border border-white/20 px-4 py-2 text-sm"
          onClick={logout}
        >
          Log out
        </button>
      }
    >
      <div className="space-y-6">
        <div className="rounded-2xl border border-white/10 bg-slate-950 px-4 py-4 text-sm text-slate-200">
          Signed in as <span className="font-semibold">{user?.name}</span> ({user?.email})
        </div>
        <div className="flex flex-col gap-3">
          <Link
            to="/chat"
            className="inline-flex items-center justify-center rounded-full bg-emerald-400 px-4 py-3 text-sm font-semibold text-slate-950"
          >
            Go to chat
          </Link>
          <p className="text-xs text-slate-400">
            You can start asking questions about your financial documents and receive
            AI-powered insights.
          </p>
        </div>
      </div>
    </PageShell>
  )
}

export default UserDashboardPage
