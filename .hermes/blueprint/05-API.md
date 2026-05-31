# API Contracts

## Base URL

Production: `http://localhost:8080/api/v1` (behind Caddy reverse proxy)
Standalone dev: `http://localhost:8000/api/v1`

## Authentication

All endpoints except `/health` require an API key in the `Authorization` header:

```
Authorization: Bearer rfr_abc123def456...
```

API keys are generated via CLI or admin API and map to a role (e.g., `"admin"`, `"senior_engineer"`, `"junior_engineer"`). The role controls which documents the caller can retrieve.

### Error Response Format

All errors follow a standard structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": {}
  }
}
```

## Endpoints

---

### GET /health
**Description:** Health check. Returns service status and component connectivity.
**Auth:** None

**Success (200):**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "components": {
    "database": "connected",
    "redis": "connected",
    "llm": "connected"
  },
  "uptime_seconds": 3600
}
```

**Degraded (200 - partial):**
```json
{
  "status": "degraded",
  "version": "1.0.0",
  "components": {
    "database": "connected",
    "redis": "disconnected",
    "llm": "unconfigured"
  },
  "uptime_seconds": 3600
}
```

---

### POST /api/v1/query
**Description:** Execute a RAG query. Returns generated answer with source citations.
**Auth:** Bearer token (derives user_role from the key)

**Request:**
```json
{
  "query": "How do I restart the Nginx server?",
  "top_k": 3,
  "stream": false
}
```

**Success (200):**
```json
{
  "answer": "To restart the Nginx server, execute `systemctl restart nginx` on the management node. Ensure you are connected to the management VPN first.\n\n**Source:** [Nginx Restart Procedure](confluence/nginx_guide_v2)",
  "sources": [
    {
      "content": "To restart the primary Nginx reverse proxy, execute: systemctl restart nginx. Ensure you are on the management VPN.",
      "metadata": {
        "source": "confluence/nginx_guide_v2",
        "title": "Nginx Restart Procedure",
        "allowed_roles": ["senior_engineer"]
      },
      "relevance_score": 0.92
    }
  ],
  "token_usage": {
    "prompt_tokens": 412,
    "completion_tokens": 87,
    "total_tokens": 499
  },
  "latency_ms": 1245
}
```

**Empty (200 - no matching docs):**
```json
{
  "answer": "I could not find any relevant documentation for your query. Your role may not have access to the requested information, or the documentation may not exist.",
  "sources": [],
  "token_usage": {"prompt_tokens": 89, "completion_tokens": 28, "total_tokens": 117},
  "latency_ms": 340
}
```

**Errors:**
| Code | Status | Condition |
|------|--------|-----------|
| INVALID_API_KEY | 401 | Missing or malformed Authorization header |
| FORBIDDEN_ROLE | 403 | API key is expired or deactivated |
| QUERY_TOO_LONG | 422 | Query exceeds 10,000 characters |
| LLM_UNAVAILABLE | 503 | LLM provider is not running or unreachable |
| DB_UNAVAILABLE | 503 | Vector database is not responding |
| RATE_LIMITED | 429 | Too many requests per minute |

---

### POST /api/v1/ingest
**Description:** Trigger async document ingestion from a source. Returns a task ID for status polling.
**Auth:** Bearer token (requires `admin` role)

**Request (directory):**
```json
{
  "source": {
    "type": "directory",
    "path": "/data/docs",
    "glob_pattern": "**/*.{md,txt,pdf}",
    "default_role": "senior_engineer"
  }
}
```

**Request (single file):**
```json
{
  "source": {
    "type": "file",
    "path": "/data/manuals/server-config.pdf",
    "allowed_roles": ["admin", "senior_engineer"]
  }
}
```

**Request (raw text):**
```json
{
  "source": {
    "type": "raw",
    "content": "To restart the primary Nginx reverse proxy...",
    "metadata": {
      "source": "manual/nginx",
      "doc_id": "NG-001",
      "title": "Nginx Restart",
      "allowed_roles": ["senior_engineer"]
    }
  }
}
```

**Success (202):**
```json
{
  "task_id": "uuid-here",
  "status": "pending",
  "source": "manual/nginx"
}
```

**Errors:**
| Code | Status | Condition |
|------|--------|-----------|
| INVALID_API_KEY | 401 | Missing or invalid auth |
| FORBIDDEN_ROLE | 403 | Key does not have admin role |
| INVALID_SOURCE | 422 | Source path doesn't exist or type is unknown |
| INGESTION_QUEUE_FULL | 503 | Too many pending ingestion tasks |

---

### GET /api/v1/ingest/{task_id}
**Description:** Poll the status of an async ingestion task.
**Auth:** Bearer token (any role)

**Success (200):**
```json
{
  "task_id": "uuid-here",
  "status": "running",
  "source": "manual/nginx",
  "started_at": "2025-06-01T10:00:00Z",
  "completed_at": null,
  "result": null,
  "error_message": null
}
```

**Completed (200):**
```json
{
  "task_id": "uuid-here",
  "status": "completed",
  "source": "manual/nginx",
  "started_at": "2025-06-01T10:00:00Z",
  "completed_at": "2025-06-01T10:00:03Z",
  "result": {
    "num_added": 3,
    "num_updated": 0,
    "num_skipped": 0,
    "num_deleted": 0
  }
}
```

**Failed (200):**
```json
{
  "task_id": "uuid-here",
  "status": "failed",
  "error_message": "Document missing required 'allowed_roles' metadata: confluence/old_doc.md",
  ...
}
```

**Errors:**
| Code | Status | Condition |
|------|--------|-----------|
| NOT_FOUND | 404 | No ingestion task with this ID |

---

### GET /api/v1/documents
**Description:** List indexed documents (metadata only, no vectors or full content).
**Auth:** Bearer token (any role — only returns documents the key's role can see)

**Query params:** `?source=confluence&limit=20&offset=0`

**Success (200):**
```json
{
  "items": [
    {
      "doc_id": "NG-001",
      "source": "confluence/nginx_guide_v2",
      "title": "Nginx Restart Procedure",
      "chunk_count": 3,
      "allowed_roles": ["senior_engineer"],
      "ingested_at": "2025-06-01T10:00:03Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

---

### DELETE /api/v1/documents/{doc_id}
**Description:** Delete all chunks for a specific document by its `doc_id`. Triggers deletion in both the vector store and the SQLRecordManager hash table.
**Auth:** Bearer token (requires `admin` role)

**Success (200):**
```json
{
  "deleted": true,
  "doc_id": "NG-001",
  "chunks_removed": 3
}
```

**Errors:**
| Code | Status | Condition |
|------|--------|-----------|
| NOT_FOUND | 404 | No document with this doc_id |
| FORBIDDEN_ROLE | 403 | Key does not have admin role |

---

### GET /api/v1/documents/sources
**Description:** List distinct document sources (for the UI source selector).
**Auth:** Bearer token (any role)

**Success (200):**
```json
{
  "sources": [
    "confluence/nginx_guide_v2",
    "confluence/office_wifi",
    "/data/manuals/server-config.pdf"
  ]
}
```

---

### POST /api/v1/auth/keys
**Description:** Create a new API key. Returns the raw key once (it will not be shown again).
**Auth:** Bearer token (requires `admin` role)

**Request:**
```json
{
  "name": "dev-cli-key",
  "role": "senior_engineer"
}
```

**Success (201):**
```json
{
  "key": "rfr_a1b2c3d4e5f6...",
  "key_prefix": "rfr_a1b2",
  "name": "dev-cli-key",
  "role": "senior_engineer",
  "created_at": "2025-06-01T10:00:00Z"
}
```

**Errors:**
| Code | Status | Condition |
|------|--------|-----------|
| INVALID_ROLE | 422 | Role not in configured role list |
| FORBIDDEN_ROLE | 403 | Key does not have admin role |

---

### GET /api/v1/auth/keys
**Description:** List all API keys (key hashes only, no raw keys).
**Auth:** Bearer token (requires `admin` role)

**Success (200):**
```json
{
  "keys": [
    {
      "prefix": "rfr_a1b2",
      "name": "dev-cli-key",
      "role": "senior_engineer",
      "is_active": true,
      "created_at": "2025-06-01T10:00:00Z",
      "last_used_at": "2025-06-01T12:00:00Z"
    }
  ]
}
```

---

### DELETE /api/v1/auth/keys/{prefix}
**Description:** Deactivate an API key by its prefix.
**Auth:** Bearer token (requires `admin` role)

**Success (200):**
```json
{
  "deactivated": true,
  "prefix": "rfr_a1b2"
}
```

---

### POST /api/v1/admin/reindex
**Description:** Re-index all documents. Useful after changing embedding model or chunk strategy. Clears existing vectors and re-runs ingestion on all known sources.
**Auth:** Bearer token (requires `admin` role)

**Success (202):**
```json
{
  "task_id": "uuid-here",
  "status": "pending",
  "message": "Full re-index started. Track progress via GET /api/v1/ingest/{task_id}"
}
```

---

## Event Contracts

### ingestion.completed
Emitted when an ingestion task finishes.

**Channel:** Redis pub/sub (internal, for real-time UI updates)

**Payload:**
```json
{
  "task_id": "uuid",
  "source": "confluence/nginx_guide_v2",
  "status": "completed",
  "result": {"num_added": 3, "num_updated": 0, "num_skipped": 0, "num_deleted": 0},
  "timestamp": "2025-06-01T10:00:03Z"
}
```

### ingestion.failed
Emitted when an ingestion task fails.

**Payload:**
```json
{
  "task_id": "uuid",
  "source": "confluence/nginx_guide_v2",
  "status": "failed",
  "error": "Document missing required 'allowed_roles' metadata",
  "timestamp": "2025-06-01T10:00:03Z"
}
```

## CLI Command API

The CLI is the primary interaction surface for operators. It maps CLI commands to API calls (when the server is running) or calls the LCEL pipeline directly (in standalone mode).

```
rfr init                   → Generate default config + docker-compose.yml
rfr up                     → docker compose up -d
rfr down                   → docker compose down
rfr status                 → GET /health
rfr config show            → Print current config
rfr config set <key> <val> → Update config value
rfr ingest <path>          → POST /api/v1/ingest
rfr query "question"       → POST /api/v1/query
rfr query --role "role"    → Query with explicit role override
rfr keys create <name>     → POST /api/v1/auth/keys
rfr keys list              → GET /api/v1/auth/keys
rfr keys revoke <prefix>   → DELETE /api/v1/auth/keys/{prefix}
rfr docs list              → GET /api/v1/documents
rfr docs delete <doc_id>   → DELETE /api/v1/documents/{doc_id}
rfr standalone             → Run API server without Docker
rfr tui                    → Launch terminal UI
```

## Error Codes Reference

| Code | HTTP Status | Meaning |
|------|-------------|---------|
| INVALID_API_KEY | 401 | Missing, malformed, or expired API key |
| FORBIDDEN_ROLE | 403 | API key's role is not authorized for this operation |
| NOT_FOUND | 404 | Requested resource doesn't exist |
| QUERY_TOO_LONG | 422 | Query exceeds maximum length |
| INVALID_SOURCE | 422 | Source path or type is invalid/missing |
| INVALID_ROLE | 422 | Role name not in configured role list |
| VALIDATION_ERROR | 422 | Request body failed Pydantic validation |
| RATE_LIMITED | 429 | Rate limit exceeded |
| LLM_UNAVAILABLE | 503 | LLM provider is down or unreachable |
| DB_UNAVAILABLE | 503 | Database connection failed |
| INGESTION_QUEUE_FULL | 503 | Too many pending ingestion tasks |
| INTERNAL_ERROR | 500 | Unexpected server error |
