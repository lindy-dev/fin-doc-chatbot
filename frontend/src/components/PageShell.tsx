import { Link } from 'react-router-dom'

type PageShellProps = {
  title: string
  subtitle?: string
  action?: React.ReactNode
  children: React.ReactNode
}

const PageShell = ({ title, subtitle, action, children }: PageShellProps) => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-white/10">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
          <div>
            <Link to="/" className="text-lg font-semibold text-white">
              FinDoc Chat
            </Link>
            <p className="text-xs text-slate-400">{subtitle}</p>
          </div>
          {action}
        </div>
      </header>
      <main className="mx-auto w-full max-w-5xl px-6 py-10">
        <h1 className="text-2xl font-semibold text-white">{title}</h1>
        <div className="mt-6 rounded-3xl border border-white/10 bg-slate-900/60 p-6">
          {children}
        </div>
      </main>
    </div>
  )
}

export default PageShell
