1|const API_BASE = '/api/v1'
2|
3|function getHeaders(): HeadersInit {
4|  const key = sessionStorage.getItem('rfr_api_key')
5|  return {
6|    'Content-Type': 'application/json',
7|    ...(key ? { Authorization: `Bearer ${key}` } : {}),
8|  }
9|}
10|
11|async function handleResponse<T>(res: Response): Promise<T> {
12|  if (!res.ok) {
13|    const body = await res.json().catch(() => ({}))
14|    const msg = body?.error?.message ?? body?.detail ?? `HTTP ${res.status}`
15|    throw new Error(msg)
16|  }
17|  return res.json()
18|}
19|
20|export interface HealthResponse {
21|  status: string
22|  version: string
23|  components: Record<string, string>
24|  uptime_seconds: number
25|}
26|
27|export interface QueryResponse {
28|  answer: string
29|  sources: Array<{
30|    content: string
31|    metadata: Record<string, unknown>
32|    relevance_score: number
33|  }>
34|  token_usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number }
35|  latency_ms: number
36|}
37|
38|export interface DocumentInfo {
39|  doc_id: string
40|  source: string
41|  title: string
42|  chunk_count: number
43|  allowed_roles: string[]
44|  ingested_at: string | null
45|}
46|
47|export interface IngestJob {
48|  task_id: string
49|  status: string
50|  source: string
51|  started_at: string | null
52|  completed_at: string | null
53|  result: Record<string, number> | null
54|  error_message: string | null
55|}
56|
57|// ── API Functions ──
58|
59|export async function getHealth(): Promise<HealthResponse> {
60|  const res = await fetch(`${API_BASE}/health`, { headers: getHeaders() })
61|  return handleResponse<HealthResponse>(res)
62|}
63|
64|export async function postQuery(query: string, topK = 3): Promise<QueryResponse> {
65|  const res = await fetch(`${API_BASE}/query`, {
66|    method: 'POST',
67|    headers: getHeaders(),
68|    body: JSON.stringify({ query, top_k: topK }),
69|  })
70|  return handleResponse<QueryResponse>(res)
71|}
72|
73|export async function getDocuments(): Promise<{ items: DocumentInfo[]; total: number }> {
74|  const res = await fetch(`${API_BASE}/documents`, { headers: getHeaders() })
75|  return handleResponse<{ items: DocumentInfo[]; total: number }>(res)
76|}
77|
78|export async function deleteDocument(docId: string): Promise<void> {
79|  const res = await fetch(`${API_BASE}/documents/${docId}`, {
80|    method: 'DELETE',
81|    headers: getHeaders(),
82|  })
83|  await handleResponse(res)
84|}
85|
86|export async function postIngest(path: string, defaultRole = 'user'): Promise<{ task_id: string }> {
87|  const res = await fetch(`${API_BASE}/ingest`, {
88|    method: 'POST',
89|    headers: getHeaders(),
90|    body: JSON.stringify({ type: 'directory', path, default_role: defaultRole }),
91|  })
92|  return handleResponse<{ task_id: string }>(res)
93|}
94|
95|export async function getIngestStatus(taskId: string): Promise<IngestJob> {
96|  const res = await fetch(`${API_BASE}/ingest/${taskId}`, { headers: getHeaders() })
97|  return handleResponse<IngestJob>(res)
98|}
99|
100|export async function createApiKey(name: string, role = 'user'): Promise<{ key: string; key_prefix: string }> {
101|  const res = await fetch(`${API_BASE}/auth/keys`, {
102|    method: 'POST',
103|    headers: getHeaders(),
104|    body: JSON.stringify({ name, role }),
105|  })
106|  return handleResponse<{ key: string; key_prefix: string }>(res)
107|}
108|
109|export async function listApiKeys(): Promise<{ keys: Array<{ prefix: string; name: string; role: string; is_active: boolean }> }> {
110|  const res = await fetch(`${API_BASE}/auth/keys`, { headers: getHeaders() })
111|  return handleResponse<{ keys: Array<{ prefix: string; name: string; role: string; is_active: boolean }> }>(res)
112|}
113|
114|export async function revokeApiKey(prefix: string): Promise<void> {
115|  const res = await fetch(`${API_BASE}/auth/keys/${prefix}`, {
116|    method: 'DELETE',
117|    headers: getHeaders(),
118|  })
119|  await handleResponse(res)
120|}
121|