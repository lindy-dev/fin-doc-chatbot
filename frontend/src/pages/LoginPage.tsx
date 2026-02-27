import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import PageShell from '../components/PageShell'
import { useAuth } from '../services/auth'

const LoginPage = () => {
  const navigate = useNavigate()
  const { login, user } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!user) return
    navigate(user.role === 'admin' ? '/admin' : '/dashboard', { replace: true })
  }, [navigate, user])

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const profile = await login(email, password)
      navigate(profile.role === 'admin' ? '/admin' : '/dashboard', {
        replace: true,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed'
      if (message.includes('not approved')) {
        setError('Your account is pending approval. Please try again later.')
      } else {
        setError(message)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <PageShell
      title="Welcome back"
      subtitle="Sign in to continue"
      action={
        <Link
          to="/register"
          className="rounded-full border border-white/20 px-4 py-2 text-sm"
        >
          Request access
        </Link>
      }
    >
      <form className="space-y-5" onSubmit={handleSubmit}>
        <div className="grid gap-3">
          <label className="text-sm text-slate-200">Email</label>
          <input
            className="rounded-xl border border-white/15 bg-slate-950 px-3 py-2 text-sm text-white"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
            placeholder="you@company.com"
          />
        </div>
        <div className="grid gap-3">
          <label className="text-sm text-slate-200">Password</label>
          <input
            className="rounded-xl border border-white/15 bg-slate-950 px-3 py-2 text-sm text-white"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            placeholder="Enter your password"
          />
        </div>
        {error && (
          <div className="rounded-xl border border-red-400/40 bg-red-400/10 px-4 py-3 text-sm text-red-200">
            {error}
          </div>
        )}
        <button
          className="w-full rounded-full bg-sky-400 px-4 py-2 text-sm font-semibold text-slate-950 disabled:opacity-60"
          type="submit"
          disabled={loading}
        >
          {loading ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
    </PageShell>
  )
}

export default LoginPage
