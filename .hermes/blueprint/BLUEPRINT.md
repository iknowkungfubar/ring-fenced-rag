# SWE Blueprint: Ring-Fenced RAG

## Master Index

This blueprint defines the complete product architecture and build plan for Ring-Fenced RAG (RFR) — a self-hosted, secure document Q&A system with role-based access control enforced at the retrieval layer.

### Blueprint Documents

| File | Contents |
|------|----------|
| `01-VISION.md` | Product vision, target users, goals, success metrics |
| `02-TECH-STACK.md` | Technology choices with justifications |
| `03-ARCHITECTURE.md` | Component architecture, data flow, ADRs |
| `04-DATA-MODEL.md` | Entities, relationships, schema, migrations |
| `05-API.md` | REST/gRPC endpoints, events, auth, error codes |
| `06-UI.md` | Web UI screens, user flows, component tree, CLI/TUI spec |
| `07-BUILD-PLAN.md` | Phases, tasks, dependencies, estimates |
| `08-GLOSSARY.md` | Domain terms, conventions, acronyms |

### Conventions

- **Language:** Python 3.13+, TypeScript (frontend)
- **Package manager:** uv (Python), pnpm (JS)
- **Linting:** ruff (Python), eslint + prettier (TS)
- **Testing:** pytest with pytest-asyncio (Python), vitest + testing-library (TS)
- **Formatting:** ruff format, prettier
- **Commit style:** Conventional Commits
- **Documentation:** Docstrings (Google style) for all public APIs
- **Target install:** `pip install ring-fenced-rag` + `docker compose up`

### Related Documents

- Source design: `/home/turin/projects/ring-fenced-rag/rag-design.md`
- This blueprint lives in: `.hermes/blueprint/`

---

## Quick Reference

```
┌──────────────┐     ┌───────────────┐     ┌──────────────────┐
│  CLI / TUI   │────▶│  FastAPI API  │────▶│  Ingestion Worker│
│  Web UI      │     │  Server       │     │  (Celery)        │
└──────────────┘     └───────┬───────┘     └────────┬─────────┘
                            │                       │
                     ┌──────▼──────┐        ┌───────▼──────────┐
                     │  LCEL RAG   │        │  Embedding Engine│
                     │  Pipeline   │        │  (bge/all-MiniLM)│
                     └──────┬──────┘        └───────┬──────────┘
                            │                       │
                     ┌──────▼───────────────────────▼──────────┐
                     │              pgvector (PostgreSQL)       │
                     │  ┌─ internal_docs (vectors+metadata) ─┐ │
                     │  └─ upsertion_record (hash tracking)  ─┘ │
                     └──────────────────────────────────────────┘
                            │
                     ┌──────▼──────┐
                     │  vLLM /     │
                     │  Ollama LLM │
                     └─────────────┘
```
