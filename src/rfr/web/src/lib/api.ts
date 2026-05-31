const API_BASE = '/api/v1'

function getHeaders(): HeadersInit {
  const key = localStorage.getItem('rfr_api_key')
  return {
    'Content-Type': 'application/json',
    ...(key ? { Authorization: `Bearer ${key}` } : {}),
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const msg = body?.error?.message ?? body?.detail ?? `HTTP ${res.status}`
    throw new Error(msg)
  }
  return res.json()
}

export interface HealthResponse {
  status: string
  version: string
  components: Record<string, string>
  uptime_seconds: number
}

export interface QueryResponse {
  answer: string
  sources: Array<{
    content: string
    metadata: Record<string, unknown>
    relevance_score: number
  }>
  token_usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number }
  latency_ms: number
}

export interface DocumentInfo {
  doc_id: string
  source: string
  title: string
  chunk_count: number
  allowed_roles: string[]
  ingested_at: string | null
}

export interface IngestJob {
  task_id: string
  status: string
  source: string
  started_at: string | null
  completed_at: string | null
  result: Record<string, number> | null
  error_message: string | null
}

// ── API Functions ──

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`, { headers: getHeaders() })
  return handleResponse<HealthResponse>(res)
}

export async function postQuery(query: string, topK = 3): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ query, top_k: topK }),
  })
  return handleResponse<QueryResponse>(res)
}

export async function getDocuments(): Promise<{ items: DocumentInfo[]; total: number }> {
  const res = await fetch(`${API_BASE}/documents`, { headers: getHeaders() })
  return handleResponse<{ items: DocumentInfo[]; total: number }>(res)
}

export async function deleteDocument(docId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/documents/${docId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  })
  await handleResponse(res)
}

export async function postIngest(path: string, defaultRole = 'user'): Promise<{ task_id: string }> {
  const res = await fetch(`${API_BASE}/ingest`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ type: 'directory', path, default_role: defaultRole }),
  })
  return handleResponse<{ task_id: string }>(res)
}

export async function getIngestStatus(taskId: string): Promise<IngestJob> {
  const res = await fetch(`${API_BASE}/ingest/${taskId}`, { headers: getHeaders() })
  return handleResponse<IngestJob>(res)
}

export async function createApiKey(name: string, role = 'user'): Promise<{ key: string; key_prefix: string }> {
  const res = await fetch(`${API_BASE}/auth/keys`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ name, role }),
  })
  return handleResponse<{ key: string; key_prefix: string }>(res)
}

export async function listApiKeys(): Promise<{ keys: Array<{ prefix: string; name: string; role: string; is_active: boolean }> }> {
  const res = await fetch(`${API_BASE}/auth/keys`, { headers: getHeaders() })
  return handleResponse<{ keys: Array<{ prefix: string; name: string; role: string; is_active: boolean }> }>(res)
}

export async function revokeApiKey(prefix: string): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/keys/${prefix}`, {
    method: 'DELETE',
    headers: getHeaders(),
  })
  await handleResponse(res)
}
