# Architecture

## System Diagram

```
                           ┌─────────────────────────────────┐
                           │         USER INTERFACES         │
                           │  ┌──────┐  ┌────┐  ┌─────────┐ │
                           │  │ CLI  │  │TUI │  │ Web UI  │ │
                           │  └──┬───┘  └──┬─┘  └────┬────┘ │
                           └─────┼─────────┼──────────┼───────┘
                                 │         │          │
                           ┌─────▼─────────▼──────────▼───────┐
                           │       REVERSE PROXY (Caddy)      │
                           │  /api/* → FastAPI                │
                           │  /ui/*  → Vite static files      │
                           └─────────────────┬────────────────┘
                                              │
                           ┌──────────────────▼────────────────┐
                           │        FASTAPI API SERVER          │
                           │                                   │
                           │  POST /api/v1/query               │
                           │  POST /api/v1/ingest              │
                           │  GET  /api/v1/documents           │
                           │  POST /api/v1/documents           │
                           │  POST /api/v1/auth/keys           │
                           │  GET  /api/v1/health              │
                           │                                   │
                           │  ┌─────────────────────────┐      │
                           │  │   LCEL RAG Pipeline     │      │
                           │  │  secure_retriever       │      │
                           │  │  → filter per role      │      │
                           │  │  → format_docs          │      │
                           │  │  → prompt + llm         │      │
                           │  │  → str_output           │      │
                           │  └─────────────────────────┘      │
                           └──────┬──────────────┬─────────────┘
                                  │              │
                    ┌─────────────▼──┐    ┌──────▼──────────────┐
                    │  PGVECTOR DB  │    │  INGESTION WORKER   │
                    │  (PostgreSQL) │    │  (Celery)           │
                    │               │    │                     │
                    │  ┌─────────┐  │    │  Parse → Chunk →    │
                    │  │ vectors │  │    │  Embed → Index()   │
                    │  │ metadata│  │    │                     │
                    │  │ hashes  │  │    │  ┌──────────────┐   │
                    │  └─────────┘  │    │  │ Embed Engine │   │
                    └───────────────┘    │  │(sentence-tr.)│   │
                                         │  └──────────────┘   │
                                         └─────────────────────┘
                                                    │
                                          ┌─────────▼───────────┐
                                          │   DOCUMENT SOURCES  │
                                          │                     │
                                          │  Local dirs/files   │
                                          │  Git repos          │
                                          │  Confluence export  │
                                          │  Raw text API       │
                                          └─────────────────────┘

                    ┌──────────────────────────────────────────┐
                    │          LLM PROVIDER (pluggable)        │
                    │                                          │
                    │  vLLM (ROCm/CUDA) — recommended           │
                    │  Ollama — lighter alternative             │
                    │  LM Studio — desktop-friendly             │
                    │  OpenAI/Anthropic — explicit opt-in       │
                    └──────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                     OBSERVABILITY                             │
│                                                              │
│  Langfuse/Phoenix traces → Postgres (7-day retention)        │
│  → agg stats → Prometheus metrics                            │
└──────────────────────────────────────────────────────────────┘
```

## Component Overview

### rfr-api (FastAPI Server)
**Responsibility:** HTTP API gateway for all query, ingestion, and management operations. Enforces auth, routes requests to LCEL pipeline, manages API keys.
**Dependencies:** pgvector DB (for retrieval), LLM provider (for generation), Redis (Celery broker for async ingestion)
**Owns:** API keys table, role mappings, request/response contracts
**Exposes:** REST API at `:8080/api/v1/*`
**Failure mode:** Down = no queries, no ingestion. Health endpoint returns 503. Docker Compose auto-restarts.

### rfr-ingestion (Celery Worker)
**Responsibility:** Async document ingestion pipeline. Parses raw documents, chunks them, generates embeddings, executes idempotent indexing via LangChain's `SQLRecordManager`.
**Dependencies:** pgvector DB, embedding model (sentence-transformers), Redis broker
**Owns:** Document chunk creation, hash tracking, deduplication
**Exposes:** Celery task queue (tasks triggered by API or CLI)
**Failure mode:** Queue backs up. Documents remain unindexed. API query returns stale results. Dead-letter queue captures failed tasks.

### rfr-vector-db (PostgreSQL + pgvector)
**Responsibility:** Primary data store. Holds document chunks + embeddings + RBAC metadata + indexing hashes + API keys.
**Dependencies:** None (stateful)
**Owns:** All persistent data
**Exposes:** PostgreSQL wire protocol (port 5432, internal network only)
**Failure mode:** Everything breaks. Read replica warm standby recommended for production.

### rfr-redis (Redis)
**Responsibility:** Celery message broker + result backend. Optional session store for web UI.
**Dependencies:** None (stateful)
**Owns:** Task queue state, ephemeral results
**Failure mode:** New ingestion tasks can't be queued. Already-running tasks continue. Queries continue working (no Redis dependency for reads).

### rfr-llm (vLLM / Ollama / etc.)
**Responsibility:** Text generation. Receives prompts from the LCEL pipeline, returns completions. Must have zero outbound internet access.
**Dependencies:** GPU (ROCm or CUDA), model weights cache
**Owns:** Model inference state (KV cache)
**Exposes:** OpenAI-compatible API at `:8000/v1` (internal network only)
**Failure mode:** Queries fail with "LLM unavailable" error. Queries go to degraded mode (return retrieved context without generation) if configured.

### rfr-web (React SPA)
**Responsibility:** Browser-based query interface, document management UI, settings panel.
**Dependencies:** `rfr-api` for all data
**Owns:** UI state, local preferences
**Failure mode:** API still usable via CLI. Web UI shows error state.

### rfr-cli (Python CLI — installed via pip)
**Responsibility:** Local CLI for setup, management, and query. Ships with the Python package. Connects to `rfr-api` when available, supports standalone mode for dev/light use.
**Dependencies:** Python 3.13, Docker (for `rfr up` command), `rfr-api` for remote queries
**Owns:** Local configuration, environment management
**Failure mode:** Self-contained — CLI commands that don't require the backend work offline (config, status).

## Data Flow

### Query Flow (critical path)
1. User sends query via CLI/Web UI/TUI → HTTP POST to `/api/v1/query`
2. FastAPI validates auth token → extracts `user_role` from API key
3. API constructs `SecureQueryRequest(query, user_role)`
4. LCEL pipeline executes:
   a. `secure_retriever` → pgvector search with `{"allowed_roles": {"$in": [user_role]}}` filter
   b. `format_docs` → concatenates results with source citations
   c. Prompt assembly → system prompt + context + user question
   d. LLM call → local vLLM/Ollama generates answer
   e. `StrOutputParser` → extracts text from response
5. Response returned to user + trace logged to observability (redacted)

### Ingestion Flow (async via Celery)
1. User triggers ingestion via CLI/API (`POST /api/v1/ingest`)
2. API validates source path/config, enqueues Celery task
3. Celery worker picks up task:
   a. Parse documents from source (unstructured, markdown parser, etc.)
   b. Validate required metadata exists (`allowed_roles`, `source`)
   c. Chunk documents (RecursiveCharacterTextSplitter, 512 tokens)
   d. Embed chunks (sentence-transformers bilingual/bge)
   e. Execute `index()` with `SQLRecordManager` (incremental mode)
   f. Log result (`num_added`, `num_updated`, `num_skipped`, `num_deleted`)
4. API returns task ID; user can poll task status

## Architecture Decision Records

### ADR-001: Metadata Filtering at Database Level, Not Application Level
**Context:** The core security requirement is that a user must never retrieve documents they're not authorized to see. If filtering happens in application code (after retrieval), a bug or bypass could leak data.
**Decision:** The `allowed_roles` metadata filter is embedded in the SQL query executed against pgvector. PostgreSQL's JSONB `@>` containment operator ensures that the mathematical vector comparison **only** considers rows where the user's role is in the `allowed_roles` array. The database literally has no path to return unauthorized results — the WHERE clause rejects them before the distance calculation runs.
**Consequences:** + Zero-trust retrieval — no app-layer filter can be bypassed. + No additional infrastructure for auth enforcement. - Must ensure embedding dimension matches schema. - Role schema changes require data migration.
**Alternatives considered:**
- Application-level filter (after retrieval) — rejected because a bug in the LCEL pipeline would leak data silently
- Per-user collection in vector DB — rejected as operationally complex, doesn't scale to dynamic role assignments

### ADR-002: LCEL Over Legacy LangChain Chains
**Context:** LangChain's legacy `RetrievalQA` chain obscures the data pipeline, making it impossible to verify that metadata filtering is actually happening at query time.
**Decision:** This project uses ONLY LangChain Expression Language (LCEL) with explicit `RunnableLambda`, `RunnablePassthrough`, and `RunnableConfig`. The legacy `RetrievalQA`, `ConversationalRetrievalChain`, and similar wrappers are prohibited by convention and enforced in linting.
**Consequences:** + Every pipeline step is explicit and observable. + Stack traces point to user code, not LangChain internals. - More verbose than wrapper chains. - Requires understanding of LCEL dictionary routing.
**Alternatives considered:**
- Direct SQL queries without LangChain — rejected because LangChain's `SQLRecordManager` and `PGVector` provide hash tracking and collection management that would require significant custom code
- LlamaIndex — rejected because it's heavier and less well-documented for the LCEL pattern we need

### ADR-003: Standalone Mode (No Docker Required for Dev/Testing)
**Context:** Not all users can or want to run Docker. Initial setup and testing should work with just `pip install` and a local PostgreSQL instance (or SQLite for basic testing).
**Decision:** The Python package ships a `rfr standalone` mode that uses SQLite + sentence-transformers + direct httpx to a configured LLM. Docker Compose is the recommended production deployment, but standalone mode is always available for testing, development, and light use. The LCEL pipeline and ring-fence logic are identical in both modes — only the DB backend differs.
**Consequences:** + Lower barrier to entry + Easier CI testing - SQLite doesn't support pgvector — vector search falls back to brute-force cosine similarity on numpy arrays. The RBAC metadata filter still works via Python dict filtering.
**Alternatives considered:** Docker-only — rejected because it increases setup friction for evaluation

### ADR-004: API Key Over JWT for Auth (v1)
**Context:** Need authentication for the API that's simple to implement and audit, without SSO dependencies.
**Decision:** v1 uses API key → role mapping. API keys are stored hashed in the database. The key prefix (`rfr_`) identifies the type. Role is derived from the key, not the user. A single key can map to `["admin", "senior_engineer"]` if desired. Admin keys can create/revoke other keys.
**Consequences:** + Dead simple to implement + Audit log shows which key (and thus which role) made each query - No per-user granularity (key is shared within a role) - Key rotation requires admin action
**Alternatives considered:** JWT with OIDC — pushed to v2. Basic auth — rejected because it would require shared passwords.

### ADR-005: Async Ingestion via Celery
**Context:** Document ingestion (parsing + chunking + embedding + indexing) can take minutes for large doc sets. Blocking the API request during ingestion would cause timeouts and poor UX.
**Decision:** Ingestion runs via Celery workers with Redis as the broker. The API immediately returns a task ID; clients poll for status. The ingestion queue is separate from the query path, so a busy ingestion doesn't impact query latency.
**Consequences:** + Query path is always fast + Ingestion can be retried without affecting queries - Operational complexity of Redis - Need to monitor Celery worker health
**Alternatives considered:** FastAPI background tasks — rejected because they block the event loop for CPU-bound embedding work. asyncio subprocess — rejected because error handling and retries are harder than Celery's built-in mechanisms.

### ADR-006: Docker Compose as Primary Deployment
**Context:** Need a deployment method that works on any Linux host with Docker, doesn't require K8s expertise, and can be set up in minutes.
**Decision:** Docker Compose is the primary deployment method. A single `rfr up` command generates a `docker-compose.yml` and starts all services. The compose file pins specific versions for reproducibility. Helm chart for Kubernetes is explicitly v2.
**Consequences:** + One-command deploy + Easy to customize (volumes, ports, GPU flags) - Requires Docker - No scaling beyond single host
**Alternatives considered:** Helm chart — pushed to v2. Ansible playbook — overkill for the target audience.

### ADR-007: Redacted Telemetry by Default
**Context:** LLM traces contain the full prompt (doc content + user query) and response. Storing this raw creates a secondary, unsecured database of sensitive IP.
**Decision:** The `SensitiveDataRedactionCallback` (from the original design) is mandatory and enabled by default. It redacts IP addresses, credentials, and any content matching configurable regex patterns before traces are written. Full trace retention is 7 days max; after 7 days, only aggregated metrics (latency, token count, error rate) are kept.
**Consequences:** + Sensitive data doesn't leak into observability storage + Compliant with data retention policies - Harder to debug retrieval quality issues from historical traces (no raw queries after 7 days)
