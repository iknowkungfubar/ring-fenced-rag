# Ring-Fenced RAG

> Self-hosted, zero-trust RAG with role-based access control enforced at the database level.

Ring-Fenced RAG (RFR) is a documentation Q&A system where **access control is enforced at the database level** — not the application layer. Every document chunk is tagged with role metadata at ingestion time. When a user queries the system, PostgreSQL's JSONB `@>` containment operator **refuses** to return chunks the user isn't authorized to see.

## Key Features

- **🔒 Ring-Fenced Retrieval** — RBAC enforced via SQL-level JSONB containment
- **🏠 100% Local** — Embedding, storage, and generation all run on your hardware
- **♻️ Idempotent Ingestion** — SQLRecordManager tracks content hashes, no duplicates
- **🔌 Pluggable LLMs** — vLLM, Ollama, LM Studio, or any OpenAI-compatible API
- **🎛️ Four Interfaces** — CLI, Web UI, TUI, REST API
- **🐧 AMD ROCm Support** — Works on AMD GPUs via ROCm vLLM or Ollama

## Quick Install

```bash
pip install ring-fenced-rag
rfr init
rfr up
rfr ingest ./docs/
rfr query "How do I deploy this?"
```

## Architecture

```
User (CLI/Web/TUI) → FastAPI API → LCEL Pipeline → pgvector (JSONB @> filter) → LLM
                    └─ Celery Worker ─▶ Embedding → pgvector ─┘
```
