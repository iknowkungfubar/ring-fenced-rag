# ring-fenced-rag — Agent Context

## Overview

Self-hosted, zero-trust RAG with role-based access control enforced at the database level using PostgreSQL pgvector JSONB @> operator.

## Tech Stack

- **Language:** Python 3.13+
- **Build System:** hatchling
- **Framework:** FastAPI (REST API), Textual (TUI), Click (CLI), Flask/React (Web UI)
- **Vector DB:** PostgreSQL + pgvector (HNSW index)
- **Embedding:** sentence-transformers
- **LLM:** Ollama, vLLM, LM Studio, or any OpenAI-compatible provider
- **Database Migrations:** Alembic
- **Task Queue:** Celery + Redis
- **Testing:** pytest, pytest-asyncio, hypothesis, syrupy, respx

## Architecture

```
User (CLI/Web/TUI) -> FastAPI API -> LCEL Pipeline
                                        |
                              PostgreSQL (pgvector)
                              JSONB @> role filter
                              HNSW vector index
                                        |
                              LLM (Ollama/vLLM)
```

## Key Differentiator

- **RBAC at database level**: Document chunks tagged with role metadata at ingestion. The PostgreSQL `@>` operator on JSONB columns enforces access at query time. Unauthorized queries return zero results.
- **Idempotent ingestion**: LangChain SQLRecordManager tracks content hashes.
- **100% local**: Zero data egress by default.

## Repository Structure

```
src/rfr/
├── api/           # FastAPI web API (routes, auth, providers, pipeline)
├── cli/           # Click CLI + Textual TUI
├── ingestion/     # Chunking, embedding, parsing, ingestion pipeline
├── models/        # SQLAlchemy ORM, Alembic migrations
├── config.py      # Configuration
└── __about__.py   # Version info
```

## Conventions

- Type hints required
- Tests use pytest with asyncio_mode=auto
- Docker Compose for production (PostgreSQL + pgvector)
- Standalone mode uses SQLite (no Docker needed)
