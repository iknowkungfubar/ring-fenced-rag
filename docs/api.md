# API Reference

Interactive API docs are available at `/docs` when the server is running.

Base URL: `http://localhost:8000/api/v1`

## Authentication

All endpoints except `/health` require a Bearer token:

```
Authorization: Bearer rfr_abc123def456...
```

Create a key: `rfr keys create <name> --role <role>`

## Endpoints

### Health

```
GET /health
```

Returns service status and component connectivity.

### Query

```
POST /query
```

Execute a RAG query. Returns generated answer with sources.

**Request:**
```json
{"query": "How do I restart Nginx?", "top_k": 3}
```

**Response:**
```json
{
  "answer": "To restart Nginx, run: systemctl restart nginx",
  "sources": [{"content": "...", "metadata": {...}, "relevance_score": 0.92}],
  "token_usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
  "latency_ms": 450.0
}
```

### Ingest

```
POST /ingest       → Trigger ingestion (202)
GET /ingest/{id}   → Poll status
```

### Documents

```
GET  /documents          → List documents
DELETE /documents/{id}   → Delete document
GET  /documents/sources  → List sources
```

### Auth / API Keys

```
POST /auth/keys       → Create key (201, key shown once)
GET  /auth/keys       → List keys
DELETE /auth/keys/{p} → Revoke key
```

### Admin

```
POST /admin/reindex   → Full re-index (202)
```
