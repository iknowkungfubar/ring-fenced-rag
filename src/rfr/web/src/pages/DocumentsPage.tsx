import { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import { getDocuments, deleteDocument, type DocumentInfo } from '@/lib/api'

export default function DocumentsPage() {
  const { key } = useAuth()
  const navigate = useNavigate()
  const [docs, setDocs] = useState<DocumentInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchDocs = async () => {
    setLoading(true)
    try {
      const res = await getDocuments()
      setDocs(res.items)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchDocs() }, [key])

  const handleDelete = async (docId: string) => {
    if (!confirm(`Delete document "${docId}"?`)) return
    try {
      await deleteDocument(docId)
      setDocs((prev) => prev.filter((d) => d.doc_id !== docId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-4">
      <header className="flex items-center justify-between mb-8 py-3 border-b border-border">
        <div className="flex items-center gap-3">
          <span className="text-lg">🔐</span>
          <h1 className="font-semibold text-text-primary">Documents</h1>
        </div>
        <nav className="flex items-center gap-4 text-sm">
          <button onClick={() => navigate('/')} className="text-text-secondary hover:text-text-primary">Query</button>
          <button onClick={() => navigate('/documents')} className="text-accent hover:underline">Documents</button>
          <button onClick={() => navigate('/ingest')} className="text-text-secondary hover:text-text-primary">Ingest</button>
          <button onClick={() => navigate('/settings')} className="text-text-secondary hover:text-text-primary">Settings</button>
        </nav>
      </header>

      {error && (
        <div className="card mb-4 border-error/30 bg-error/5">
          <p className="text-sm text-error">{error}</p>
          <button onClick={() => setError('')} className="text-xs text-text-secondary mt-1">Dismiss</button>
        </div>
      )}

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-medium">
          {docs.length > 0 ? `${docs.length} document${docs.length === 1 ? '' : 's'}` : ''}
        </h2>
        <button onClick={() => navigate('/ingest')} className="btn-primary text-xs">
          + Ingest
        </button>
      </div>

      {loading && <p className="text-text-secondary text-sm">Loading...</p>}

      {!loading && docs.length === 0 && (
        <div className="text-center py-16">
          <div className="text-4xl mb-4">📄</div>
          <p className="text-text-secondary mb-4">No documents indexed yet</p>
          <button onClick={() => navigate('/ingest')} className="btn-primary">
            Ingest Your First Document
          </button>
        </div>
      )}

      <div className="space-y-2">
        {docs.map((doc) => (
          <div key={doc.doc_id} className="card flex items-center justify-between py-3">
            <div>
              <p className="text-sm font-medium text-text-primary">{doc.title || doc.doc_id}</p>
              <p className="text-xs text-text-secondary mt-0.5">
                {doc.source} &middot; {doc.chunk_count} chunks
              </p>
              {doc.allowed_roles.length > 0 && (
                <div className="flex gap-1 mt-1">
                  {doc.allowed_roles.map((r) => (
                    <span key={r} className="badge bg-accent/10 text-accent text-xs">{r}</span>
                  ))}
                </div>
              )}
            </div>
            <button
              onClick={() => handleDelete(doc.doc_id)}
              className="text-error text-xs hover:underline shrink-0"
            >
              Delete
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
