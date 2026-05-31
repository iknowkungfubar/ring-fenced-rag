# Data Model

## Entity Relationship Diagram

```
┌──────────────┐     ┌───────────────────┐     ┌─────────────────┐
│   api_keys   │     │  document_chunks  │     │  ingestion_jobs │
│──────────────│     │───────────────────│     │─────────────────│
│ id (PK)      │     │ id (PK, UUID)     │     │ id (PK, UUID)   │
│ key_hash     │     │ content (TEXT)    │     │ source          │
│ prefix       │     │ embedding (vec)   │     │ status          │
│ name         │     │ metadata (JSONB)  │     │ error_message   │
│ role         │     │ source            │     │ started_at      │
│ created_at   │     │ doc_id            │     │ completed_at    │
│ last_used_at │     │ chunk_index       │     │ result (JSONB)  │
│ is_active    │     │ created_at        │     │ created_at      │
└──────────────┘     └───────────────────┘     └─────────────────┘
                           │
                           │ hashed by
                           ▼
                    ┌───────────────┐
                    │upsertion_record│  (LangChain SQLRecordManager)
                    │───────────────│
                    │ uuid (PK)     │
                    │ key           │
                    │ namespace     │
                    │ group_id      │
                    │ updated_at    │
                    └───────────────┘
```

## Entities

### document_chunks
The core entity. Each row is one chunk of a source document, with its embedding vector and RBAC metadata.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | |
| `content` | TEXT | NOT NULL | The chunk text |
| `embedding` | vector(n) | NOT NULL | Dimension matches embedding model (384 for all-MiniLM, 1024 for bge-large) |
| `metadata` | JSONB | NOT NULL, DEFAULT '{}' | Contains `allowed_roles`, `source`, `doc_id`, title, etc. |
| `source` | VARCHAR(500) | NOT NULL | Original document path/URL (used by SQLRecordManager) |
| `doc_id` | VARCHAR(255) | NOT NULL | Document identifier within the source system |
| `chunk_index` | INTEGER | NOT NULL | Position of this chunk in the source document |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes:**
- `idx_doc_chunks_embedding` — HNSW index on `embedding` vector (cosine distance)
- `idx_doc_chunks_source` — BTREE on `source`
- `idx_doc_chunks_metadata_roles` — GIN on `metadata jsonb_path_ops` (enables fast `@>` containment queries)
- `idx_doc_chunks_doc_id` — BTREE on `doc_id`

### api_keys
Authentication entities. Each key maps to one or more roles.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | |
| `key_hash` | VARCHAR(64) | NOT NULL, UNIQUE | SHA-256 hash of the raw key |
| `key_prefix` | VARCHAR(10) | NOT NULL | First 8 chars of raw key for identification |
| `name` | VARCHAR(255) | NOT NULL | Human-readable name (e.g., "dev-cli-key") |
| `role` | VARCHAR(100) | NOT NULL | The role this key grants (e.g., "admin", "senior_engineer") |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true | Soft-delete / disable |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `last_used_at` | TIMESTAMPTZ | NULL | Updated on each query |

**Indexes:**
- `idx_api_keys_key_hash` — UNIQUE BTREE on `key_hash`

### ingestion_jobs
Tracks async ingestion tasks.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | |
| `source` | VARCHAR(500) | NOT NULL | Path, URL, or description of what was ingested |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | `pending`, `running`, `completed`, `failed` |
| `error_message` | TEXT | NULL | Only set if status = 'failed' |
| `started_at` | TIMESTAMPTZ | NULL | |
| `completed_at` | TIMESTAMPTZ | NULL | |
| `result` | JSONB | NULL | `{num_added, num_updated, num_skipped, num_deleted}` |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes:**
- `idx_ingestion_jobs_status` — BTREE on `status`

## Embedding Vector Dimension

The `embedding` column uses `vector(n)` where `n` is configurable per deployment:

| Embedding Model | Dimensions | Notes |
|----------------|-----------|-------|
| `all-MiniLM-L6-v2` | 384 | Default for CPU, fast, ~80MB |
| `BAAI/bge-small-en-v1.5` | 384 | Better retrieval than MiniLM, small |
| `BAAI/bge-base-en-v1.5` | 768 | Good quality, ~1GB |
| `BAAI/bge-large-en-v1.5` | 1024 | Best quality, ~2GB, needs GPU for bulk |
| `intfloat/multilingual-e5-small` | 384 | Multi-language support |
| `Alibaba-NLP/gte-Qwen2-1.5B-instruct` | 1536 | High quality, instruct-tuned |

The schema is created dynamically based on the configured model dimension. A migration step updates the vector type when changing models (requires re-indexing all documents).

## Document Metadata Schema (JSONB)

Every `metadata` field in `document_chunks` must conform to this schema:

```json
{
  "allowed_roles": ["senior_engineer"],
  "source": "confluence/nginx_guide_v2",
  "doc_id": "NG-001",
  "title": "Nginx Restart Procedure",
  "author": "jane.doe",
  "created_at": "2025-01-15T10:00:00Z",
  "tags": ["infrastructure", "nginx", "production"]
}
```

**Required fields** (enforced at ingestion time):
- `allowed_roles` (list[str]) — The RBAC containment boundary. Ingestion raises an error if missing.
- `source` (str) — Must match the `source_id_key` used by SQLRecordManager.

**Optional but recommended:**
- `doc_id` (str) — Unique within source. Used for idempotent dedup.
- `title` (str) — Displayed in source citations.
- `tags` (list[str]) — Additional filtering dimension.

## DB Migrations (Alembic)

```
migrations/
├── env.py
├── alembic.ini
└── versions/
    ├── V001_create_api_keys.py
    ├── V002_create_document_chunks.py
    ├── V003_create_hnsw_index.py
    └── V004_create_ingestion_jobs.py
```

### V001: Create api_keys table
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash VARCHAR(64) UNIQUE NOT NULL,
    key_prefix VARCHAR(10) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_used_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
```

### V002: Create document_chunks table
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    source VARCHAR(500) NOT NULL,
    doc_id VARCHAR(255) NOT NULL,
    chunk_index INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_doc_chunks_source ON document_chunks(source);
CREATE INDEX idx_doc_chunks_doc_id ON document_chunks(doc_id);
CREATE INDEX idx_doc_chunks_metadata_roles ON document_chunks USING GIN (metadata jsonb_path_ops);
```

### V003: Create HNSW vector index (run after data loaded for speed)
```sql
CREATE INDEX idx_doc_chunks_embedding_hnsw 
ON document_chunks 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 200);
```

### V004: Create ingestion_jobs table
```sql
CREATE TABLE ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(500) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX idx_ingestion_jobs_status ON ingestion_jobs(status);
```

## SQLRecordManager Tables

LangChain's `SQLRecordManager` automatically creates:

- `upsertion_record` — Tracks document hashes for idempotent indexing. Schema managed by LangChain internals.
- `langchain_pg_collection` — Maps collection names to UUIDs (used by PGVector).
- `langchain_pg_embedding` — Alternative storage mode if PGVector's collection API is used (our schema uses direct table access with metadata filter, so this may or may not be used depending on configuration).

These tables are created automatically at runtime and are not managed by Alembic.
