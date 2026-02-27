import { useState } from 'react'
import { Link } from 'react-router-dom'
import PageShell from '../components/PageShell'
import { registerUser } from '../services/api'

type FormState = {
  name: string
  email: string
  password: string
}

const RegisterPage = () => {
  const [form, setForm] = useState<FormState>({
    name: '',
    email: '',
    password: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleChange = (field: keyof FormState) =>
    (event: React.ChangeEvent<HTMLInputElement>) => {
      setForm((prev) => ({ ...prev, [field]: event.target.value }))
    }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setSuccess(null)
    setLoading(true)
    try {
      await registerUser(form)
      setSuccess(
        'Registration submitted. Your account is pending approval by an administrator.'
      )
      setForm({ name: '', email: '', password: '' })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <PageShell
      title="Create your account"
      subtitle="Request access to Financial Document Chat"
      action={
        <Link
          to="/login"
          className="rounded-full border border-white/20 px-4 py-2 text-sm"
        >
          Sign in
        </Link>
      }
    >
      <form className="space-y-5" onSubmit={handleSubmit}>
        <div className="grid gap-3">
          <label className="text-sm text-slate-200">Name</label>
          <input
            className="rounded-xl border border-white/15 bg-slate-950 px-3 py-2 text-sm text-white"
            value={form.name}
            onChange={handleChange('name')}
            required
            placeholder="Jane Doe"
          />
        </div>
        <div className="grid gap-3">
          <label className="text-sm text-slate-200">Email</label>
          <input
            className="rounded-xl border border-white/15 bg-slate-950 px-3 py-2 text-sm text-white"
            type="email"
            value={form.email}
            onChange={handleChange('email')}
            required
            placeholder="jane@company.com"
          />
        </div>
        <div className="grid gap-3">
          <label className="text-sm text-slate-200">Password</label>
          <input
            className="rounded-xl border border-white/15 bg-slate-950 px-3 py-2 text-sm text-white"
            type="password"
            value={form.password}
            onChange={handleChange('password')}
            required
            minLength={8}
            placeholder="Minimum 8 characters"
          />
        </div>
        {error && (
          <div className="rounded-xl border border-red-400/40 bg-red-400/10 px-4 py-3 text-sm text-red-200">
            {error}
          </div>
        )}
        {success && (
          <div className="rounded-xl border border-emerald-400/40 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-200">
            {success}
          </div>
        )}
        <button
          className="w-full rounded-full bg-emerald-400 px-4 py-2 text-sm font-semibold text-slate-950 disabled:opacity-60"
          type="submit"
          disabled={loading}
        >
          {loading ? 'Submitting...' : 'Request access'}
        </button>
      </form>
    </PageShell>
  )
}

export default RegisterPage
