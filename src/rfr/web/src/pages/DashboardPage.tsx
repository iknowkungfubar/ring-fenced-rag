import { useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import { postQuery, type QueryResponse } from '@/lib/api'

export default function DashboardPage() {
  const { key, logout } = useAuth()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [result, setResult] = useState<QueryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await postQuery(query)
      setResult(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Query failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-4">
      {/* Header */}
      <header className="flex items-center justify-between mb-8 py-3 border-b border-border">
        <div className="flex items-center gap-3">
          <span className="text-lg">🔐</span>
          <h1 className="font-semibold text-text-primary">Ring-Fenced RAG</h1>
        </div>
        <nav className="flex items-center gap-4 text-sm">
          <button onClick={() => navigate('/')} className="text-accent hover:underline">Query</button>
          <button onClick={() => navigate('/documents')} className="text-text-secondary hover:text-text-primary">Documents</button>
          <button onClick={() => navigate('/ingest')} className="text-text-secondary hover:text-text-primary">Ingest</button>
          <button onClick={() => navigate('/settings')} className="text-text-secondary hover:text-text-primary">Settings</button>
          <span className="badge-success text-xs">{key?.slice(0, 10)}...</span>
          <button onClick={logout} className="text-error text-xs hover:underline">Logout</button>
        </nav>
      </header>

      {/* Query Input */}
      <form onSubmit={handleQuery} className="mb-6">
        <div className="flex gap-2">
          <input
            className="input flex-1"
            placeholder="Ask a question about your internal docs..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit" className="btn-primary" disabled={loading || !query.trim()}>
            {loading ? '...' : 'Ask'}
          </button>
        </div>
      </form>

      {/* Error */}
      {error && (
        <div className="card mb-4 border-error/30 bg-error/5">
          <p className="text-sm text-error">{error}</p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="space-y-4">
          <div className="card prose prose-invert max-w-none">
            <div className="whitespace-pre-wrap text-sm leading-relaxed">{result.answer}</div>
          </div>

          {result.sources.length > 0 && (
            <div className="card">
              <h3 className="text-sm font-medium text-text-secondary mb-3">Sources</h3>
              <div className="space-y-2">
                {result.sources.map((s, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm">
                    <span className="text-text-secondary shrink-0">📄</span>
                    <div>
                      <span className="text-text-primary">
                        {(s.metadata?.title as string) ?? (s.metadata?.source as string) ?? 'Unknown'}
                      </span>
                      <span className="text-text-secondary ml-2">
                        ({(s.relevance_score * 100).toFixed(0)}% match)
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <p className="text-xs text-text-secondary text-right">
            {result.latency_ms.toFixed(0)}ms &middot; {result.token_usage.total_tokens} tokens
          </p>
        </div>
      )}

      {/* Empty State */}
      {!result && !loading && !error && (
        <div className="text-center py-16">
          <div className="text-4xl mb-4">🔍</div>
          <p className="text-text-secondary">Ask a question to search your documentation</p>
        </div>
      )}

      {loading && (
        <div className="text-center py-8">
          <div className="animate-spin text-2xl mb-2">⏳</div>
          <p className="text-sm text-text-secondary">Searching documentation...</p>
        </div>
      )}
    </div>
  )
}
