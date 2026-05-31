import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { postIngest, getIngestStatus } from '@/lib/api'

export default function IngestPage() {
  const navigate = useNavigate()
  const [path, setPath] = useState('')
  const [role, setRole] = useState('user')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{ task_id: string } | null>(null)
  const [error, setError] = useState('')

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!path.trim()) return
    setLoading(true)
    setError('')
    try {
      const task = await postIngest(path, role)
      setResult(task)
      // Poll for completion
      const poll = async () => {
        const status = await getIngestStatus(task.task_id)
        if (status.status === 'completed' || status.status === 'failed') {
          setLoading(false)
          if (status.status === 'failed') {
            setError(status.error_message || 'Ingestion failed')
          }
          return
        }
        setTimeout(poll, 2000)
      }
      poll()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ingestion failed')
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-4">
      <header className="flex items-center justify-between mb-8 py-3 border-b border-border">
        <div className="flex items-center gap-3">
          <span className="text-lg">🔐</span>
          <h1 className="font-semibold text-text-primary">Ingest Documents</h1>
        </div>
        <nav className="flex items-center gap-4 text-sm">
          <button onClick={() => navigate('/')} className="text-text-secondary hover:text-text-primary">Query</button>
          <button onClick={() => navigate('/documents')} className="text-text-secondary hover:text-text-primary">Documents</button>
          <button onClick={() => navigate('/ingest')} className="text-accent hover:underline">Ingest</button>
          <button onClick={() => navigate('/settings')} className="text-text-secondary hover:text-text-primary">Settings</button>
        </nav>
      </header>

      <form onSubmit={handleIngest} className="card space-y-4">
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1.5">Source Type</label>
          <select className="input" value="directory" disabled>
            <option value="directory">Directory</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1.5">Path</label>
          <input
            className="input"
            placeholder="/path/to/docs"
            value={path}
            onChange={(e) => setPath(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1.5">Default Role</label>
          <select className="input" value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="user">user</option>
            <option value="junior_engineer">junior_engineer</option>
            <option value="senior_engineer">senior_engineer</option>
            <option value="admin">admin</option>
          </select>
        </div>
        <button type="submit" className="btn-primary w-full" disabled={loading || !path.trim()}>
          {loading ? 'Ingesting...' : 'Start Ingestion'}
        </button>
      </form>

      {error && (
        <div className="card mt-4 border-error/30 bg-error/5">
          <p className="text-sm text-error">{error}</p>
        </div>
      )}

      {result && !loading && (
        <div className="card mt-4 border-success/30 bg-success/5">
          <p className="text-sm text-success">Ingestion completed successfully</p>
        </div>
      )}
    </div>
  )
}
