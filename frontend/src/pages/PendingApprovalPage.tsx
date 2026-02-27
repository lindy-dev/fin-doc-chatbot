import { Link } from 'react-router-dom'
import PageShell from '../components/PageShell'

const PendingApprovalPage = () => {
  return (
    <PageShell
      title="Approval pending"
      subtitle="Your request is still under review"
      action={
        <Link
          to="/login"
          className="rounded-full border border-white/20 px-4 py-2 text-sm"
        >
          Back to login
        </Link>
      }
    >
      <div className="space-y-4 text-sm text-slate-200">
        <p>
          Your account has been created, but an administrator still needs to approve
          access before you can use the chat app.
        </p>
        <p>Please check back later or contact support if this takes too long.</p>
      </div>
    </PageShell>
  )
}

export default PendingApprovalPage
