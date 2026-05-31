import { useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'

export default function LoginPage() {
  const [inputKey, setInputKey] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputKey.trim()) return
    setLoading(true)
    setError('')
    try {
      // Store key and validate by checking health
      login(inputKey.trim())
      const { getHealth } = await import('@/lib/api')
      await getHealth()
      navigate('/')
    } catch {
      setError('Invalid API key or server not reachable')
      login('') // clear invalid key
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="card w-full max-w-md">
        <div className="text-center mb-8">
          <div className="text-3xl mb-2">🔒</div>
          <h1 className="text-xl font-bold text-text-primary">Ring-Fenced RAG</h1>
          <p className="text-sm text-text-secondary mt-1">Secure Document Q&A</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="api-key" className="block text-sm font-medium text-text-secondary mb-1.5">
              API Key
            </label>
            <input
              id="api-key"
              type="password"
              className="input"
              placeholder="rfr_..."
              value={inputKey}
              onChange={(e) => setInputKey(e.target.value)}
            />
          </div>
          {error && <p className="text-sm text-error">{error}</p>}
          <button type="submit" className="btn-primary w-full" disabled={loading || !inputKey.trim()}>
            {loading ? 'Connecting...' : 'Connect'}
          </button>
        </form>
        <p className="text-xs text-text-secondary text-center mt-6">
          Don't have a key? Run{' '}
          <code className="text-accent bg-elevated px-1 rounded">rfr keys create web</code>
        </p>
      </div>
    </div>
  )
}
