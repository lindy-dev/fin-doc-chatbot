import { useEffect, useState } from 'react'
import PageShell from '../components/PageShell'
import { approveUser, getPendingUsers, type PendingUser } from '../services/api'
import { useAuth } from '../services/auth'

const AdminDashboardPage = () => {
  const { logout } = useAuth()
  const [users, setUsers] = useState<PendingUser[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionId, setActionId] = useState<string | null>(null)

  const loadUsers = async () => {
    setLoading(true)
    setError(null)
    try {
      const pending = await getPendingUsers()
      setUsers(pending)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadUsers()
  }, [])

  const handleAction = async (userId: string, approve: boolean) => {
    setActionId(userId)
    setError(null)
    try {
      await approveUser(userId, { is_approved: approve })
      setUsers((prev) => prev.filter((user) => user.id !== userId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed')
    } finally {
      setActionId(null)
    }
  }

  return (
    <PageShell
      title="Admin approvals"
      subtitle="Manage pending access requests"
      action={
        <button
          className="rounded-full border border-white/20 px-4 py-2 text-sm"
          onClick={logout}
        >
          Log out
        </button>
      }
    >
      <div className="space-y-4">
        {error && (
          <div className="rounded-xl border border-red-400/40 bg-red-400/10 px-4 py-3 text-sm text-red-200">
            {error}
          </div>
        )}
        {loading ? (
          <div className="text-sm text-slate-300">Loading pending users...</div>
        ) : users.length === 0 ? (
          <div className="rounded-xl border border-white/10 bg-slate-950 px-4 py-6 text-sm text-slate-300">
            No pending approvals right now.
          </div>
        ) : (
          <div className="space-y-3">
            {users.map((user) => (
              <div
                key={user.id}
                className="flex flex-col gap-4 rounded-2xl border border-white/10 bg-slate-950 px-4 py-4 md:flex-row md:items-center md:justify-between"
              >
                <div>
                  <div className="text-sm font-semibold text-white">
                    {user.name}
                  </div>
                  <div className="text-xs text-slate-400">{user.email}</div>
                  <div className="text-xs text-slate-500">
                    Requested {new Date(user.created_at).toLocaleString()}
                  </div>
                </div>
                <div className="flex gap-3">
                  <button
                    className="rounded-full bg-emerald-400 px-4 py-2 text-xs font-semibold text-slate-950 disabled:opacity-60"
                    onClick={() => handleAction(user.id, true)}
                    disabled={actionId === user.id}
                  >
                    Approve
                  </button>
                  <button
                    className="rounded-full border border-white/20 px-4 py-2 text-xs text-slate-200 disabled:opacity-60"
                    onClick={() => handleAction(user.id, false)}
                    disabled={actionId === user.id}
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </PageShell>
  )
}

export default AdminDashboardPage
