# Technology Stack

## Languages & Runtimes

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| Backend core | Python | 3.13 | Team/user expertise, LangChain/Sentence-Transformer ecosystem, installable via pip |
| API server | Python (FastAPI) | 0.115+ | Async-native, auto OpenAPI docs, Pydantic v2 integration |
| Web frontend | TypeScript | 5.x | React ecosystem, type safety |
| Database | PostgreSQL + pgvector | 17 + 0.8+ | ACID compliance, native vector support, JSONB for metadata filtering |
| Ingestion worker | Python (Celery) | 5.x | Async batch processing, Redis broker |

## Frameworks & Libraries

### Core (Python)
| Purpose | Choice | Alternative Considered | Why This Won |
|---------|--------|----------------------|--------------|
| RAG orchestration | LangChain (LCEL only) | LlamaIndex, Haystack | LCEL forces explicit pipeline declaration; legacy wrappers (RetrievalQA) are explicitly **banned** in this project |
| Embedding | sentence-transformers | OpenAI Embeddings, TEI | Runs 100% offline, huge model zoo, simple API |
| Vector store driver | pgvector + psycopg | Qdrant, Chroma | Same DB as metadata = simpler ops; JSONB containment operators are the ring-fence |
| Document parsing | unstructured, markdown-it | langchain-community parsers | Handles PDF, HTML, Markdown, Confluence export, Office docs |
| LLM client | langchain-openai | Direct httpx | OpenAI-compatible API works for vLLM, Ollama, LM Studio, and cloud |
| Config | pydantic-settings | Dynaconf, python-dotenv | Type-safe config with env override, built on Pydantic v2 |
| Task queue | Celery + Redis | Arq, Huey | Mature, reliable, dead-letter queues; Redis is well-known |
| CLI framework | click + rich | typer, argparse | click is the standard; rich for beautiful terminal output |
| Async | httpx, anyio | aiohttp, asyncio | httpx has cleaner API, anyio for structured concurrency |

### Frontend (TypeScript)
| Purpose | Choice | Alternative Considered | Why This Won |
|---------|--------|----------------------|--------------|
| Framework | React 19 + Vite | Next.js, Svelte | SPA fits single-page query interface; Vite for fast dev |
| UI components | shadcn/ui + Tailwind | MUI, Ant Design | Lightweight, accessible, tree-shakeable, dark mode native |
| State management | React Query (TanStack Query) | Redux, Zustand | Server state caching, loading/error states built-in |
| API client | fetch + React Query | Axios, tRPC | Minimal deps; React Query handles caching/retry |

## Infrastructure

| Component | Choice | Purpose |
|-----------|--------|---------|
| Container runtime | Docker Compose | Primary deployment — orchestrates pgvector, Redis, vLLM, API server |
| Vector DB | PostgreSQL 17 + pgvector | Single deployment for vectors + metadata + tracking |
| Task broker | Redis 7 | Celery broker + result backend |
| LLM inference | vLLM (ROCm) or Ollama | Local GPU inference; Ollama as lighter alternative |
| Reverse proxy | Caddy (embedded in compose) | Auto HTTPS, path routing, basic auth gate |
| Monitoring | Self-hosted Langfuse or Arize Phoenix | Open-source LLM observability, no data egress |
| File storage | Local filesystem or S3-compatible | Document originals, config |

## Development Environment

| Category | Tool | Notes |
|----------|------|-------|
| Package manager | uv | 10-100x faster than pip, lockfile support |
| Virtual env | `uv venv` | Project-local |
| Linting | ruff (rules: ALL, select subset) | 1000x faster than flake8 |
| Formatting | ruff format | Zero-config |
| Type checking | pyright (strict) | For Python; tsc --strict for TS |
| Testing | pytest + pytest-asyncio + pytest-cov | Async test support; coverage ≥85% |
| Pre-commit | pre-commit with ruff | CI-local lint gates |
| CI | GitHub Actions | Test on ubuntu-latest, matrix Python 3.12-3.13 |
| Build | hatchling | PEP 517 build backend, pyproject.toml |
| Docs | mkdocs-material | Documentation site from markdown |

## Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Vector DB metadata filter | PostgreSQL JSONB `@>` operator | Database-level enforcement — not application-level. An attacker who bypasses the API still can't retrieve unauthorized data from the DB directly. |
| LLM protocol | OpenAI-compatible API | Single protocol works for vLLM, Ollama, LM Studio, OpenAI, Anthropic, etc. User chooses at config time. |
| Ingestion trigger | CLI + API trigger (not file watcher) | Simpler to implement, no filesystem event complexity. Scheduled cron job can trigger periodic re-ingestion. |
| Auth model | API key → Role mapping | Simple, auditable, no SSO dependency. Role derived from API key at request time. |
| Chunking | RecursiveCharacterTextSplitter (default) + semantic chunker (optional) | Start simple, offer upgrade path for better chunk quality. |
