# Architecture

## System Overview

```
rfr CLI/TUI    ─────┐
Web UI (React) ─────┤
                     ▼
              ┌──────────────┐     ┌──────────────────┐
              │  FastAPI API  │────▶│  Ingestion Worker│
              │  (LCEL RAG)   │     │  (Celery)        │
              └──────┬───────┘     └────────┬─────────┘
                     │                       │
              ┌──────▼──────┐        ┌───────▼──────────┐
              │  pgvector   │        │  Embedding Engine│
              │  Postgres   │        │  (sentence-trf.) │
              │  JSONB @>   │        └──────────────────┘
              │  HNSW idx   │
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │  vLLM/Ollama│
              │  (zero egr.)│
              └─────────────┘
```

## Core Security Principle

The ring-fence is **not** enforced at the application level. It is enforced by PostgreSQL's JSONB containment operator (`@>`) in the SQL query itself:

```sql
SELECT content FROM document_chunks
WHERE metadata->'allowed_roles' @> '["senior_engineer"]'::jsonb
ORDER BY embedding <=> <query_vector>
LIMIT 3;
```

The database literally has no path to return unauthorized results — the WHERE clause rejects them before the distance calculation runs.

## Components

### API Server (FastAPI)
- Handles all query, ingestion, and management operations
- Extracts user role from API key → applies as metadata filter
- LCEL pipeline ensures explicit, observable data flow

### Vector Database (pgvector)
- Single PostgreSQL instance with pgvector extension
- HNSW index for fast approximate nearest neighbor search
- GIN index on `metadata` JSONB for fast role containment checks

### Ingestion Worker (Celery)
- Async batch processing — embedding is compute-bound
- LangChain SQLRecordManager tracks content hashes
- Incremental cleanup mode: update changed docs, preserve unchanged

### LLM Provider
- Pluggable: vLLM, Ollama, LM Studio, OpenAI-compatible
- Zero outbound internet access by default
- Low temperature (0.1) for deterministic factual responses
