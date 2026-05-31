import { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import { createApiKey, listApiKeys, revokeApiKey, getHealth } from '@/lib/api'

interface KeyEntry {
  prefix: string
  name: string
  role: string
  is_active: boolean
}

export default function SettingsPage() {
  const { key } = useAuth()
  const navigate = useNavigate()
  const [keys, setKeys] = useState<KeyEntry[]>([])
  const [newKeyName, setNewKeyName] = useState('')
  const [newKeyRole, setNewKeyRole] = useState('user')
  const [createdKey, setCreatedKey] = useState<string | null>(null)
  const [health, setHealth] = useState<Record<string, string> | null>(null)
  const [error, setError] = useState('')

  const fetchData = async () => {
    try {
      const [keyData, healthData] = await Promise.all([
        listApiKeys(),
        getHealth(),
      ])
      setKeys(keyData.keys)
      setHealth(healthData.components)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load settings')
    }
  }

  useEffect(() => { fetchData() }, [key])

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newKeyName.trim()) return
    try {
      const result = await createApiKey(newKeyName, newKeyRole)
      setCreatedKey(result.key)
      setNewKeyName('')
      fetchData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create key')
    }
  }

  const handleRevoke = async (prefix: string) => {
    if (!confirm(`Revoke key ${prefix}?`)) return
    try {
      await revokeApiKey(prefix)
      fetchData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke key')
    }
  }

  const clearCreatedKey = () => setCreatedKey(null)
  const activeKeys = keys.filter((k) => k.is_active)
  const inactiveKeys = keys.filter((k) => !k.is_active)

  return (
    <div className="max-w-3xl mx-auto p-4">
      <header className="flex items-center justify-between mb-8 py-3 border-b border-border">
        <div className="flex items-center gap-3">
          <span className="text-lg">🔐</span>
          <h1 className="font-semibold text-text-primary">Settings</h1>
        </div>
        <nav className="flex items-center gap-4 text-sm">
          <button onClick={() => navigate('/')} className="text-text-secondary hover:text-text-primary">Query</button>
          <button onClick={() => navigate('/documents')} className="text-text-secondary hover:text-text-primary">Documents</button>
          <button onClick={() => navigate('/ingest')} className="text-text-secondary hover:text-text-primary">Ingest</button>
          <button onClick={() => navigate('/settings')} className="text-accent hover:underline">Settings</button>
        </nav>
      </header>

      {error && (
        <div className="card mb-4 border-error/30 bg-error/5">
          <p className="text-sm text-error">{error}</p>
          <button onClick={() => setError('')} className="text-xs text-text-secondary mt-1">Dismiss</button>
        </div>
      )}

      {/* Created Key Banner */}
      {createdKey && (
        <div className="card mb-4 border-success/30 bg-success/5">
          <p className="text-sm text-success font-medium mb-2">API Key Created</p>
          <div className="bg-elevated rounded p-3 mb-2">
            <code className="text-accent text-sm break-all">{createdKey}</code>
          </div>
          <p className="text-xs text-text-secondary">⚠ Copy this key now. It won't be shown again.</p>
          <button onClick={clearCreatedKey} className="text-xs text-text-secondary mt-2 hover:underline">Dismiss</button>
        </div>
      )}

      {/* System Health */}
      <div className="card mb-6">
        <h2 className="text-sm font-medium text-text-primary mb-3">System Health</h2>
        <div className="grid grid-cols-3 gap-3">
          {health && Object.entries(health).map(([component, status]) => (
            <div key={component} className="bg-elevated rounded-lg p-3 text-center">
              <p className="text-xs text-text-secondary capitalize">{component}</p>
              <p className={`text-sm font-medium mt-1 ${
                status === 'connected' ? 'text-success' :
                status === 'configured' ? 'text-warning' : 'text-error'
              }`}>
                {status}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* API Keys */}
      <div className="card mb-6">
        <h2 className="text-sm font-medium text-text-primary mb-4">API Keys</h2>

        <form onSubmit={handleCreateKey} className="flex gap-2 mb-4">
          <input
            className="input flex-1"
            placeholder="Key name (e.g., web-ui)"
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
          />
          <select className="input w-32" value={newKeyRole} onChange={(e) => setNewKeyRole(e.target.value)}>
            <option value="user">user</option>
            <option value="admin">admin</option>
          </select>
          <button type="submit" className="btn-primary" disabled={!newKeyName.trim()}>
            Create
          </button>
        </form>

        {activeKeys.length > 0 && (
          <div className="space-y-2">
            {activeKeys.map((k) => (
              <div key={k.prefix} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                <div>
                  <p className="text-sm text-text-primary">{k.name}</p>
                  <p className="text-xs text-text-secondary">{k.prefix} &middot; {k.role}</p>
                </div>
                <button onClick={() => handleRevoke(k.prefix)} className="text-error text-xs hover:underline">Revoke</button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
