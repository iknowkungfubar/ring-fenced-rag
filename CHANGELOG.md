# Changelog

All notable changes to Ring-Fenced RAG will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0a1] — 2025-05-31

### Added

- **LM Studio support**: New `LMStudioProvider` with default endpoint `localhost:1234/v1` and `local-model` preset. Supports all LM Studio inference backends (CUDA, ROCm, Metal, CPU). Configurable via `RFR_LLM__PROVIDER=lm-studio`.
- **Dynamic versioning**: Version is now derived from `git describe` tags at runtime, with static fallback. `rfr version` subcommand shows detailed version, git commit, Python version, and platform info.
- **Provider factory**: `get_provider()` factory function dispatches by name to the correct provider class.
- **32 provider tests**: Full coverage for vLLM, Ollama, LM Studio, OpenAI defaults and factory dispatch.

### Added

- **CLI interface** (`rfr`): 18 commands including `init`, `up`, `down`, `status`, `config show/set`, `ingest`, `query`, `keys create/list/revoke`, `docs list/delete`, `standalone`, `logs`, `tui`
- **REST API**: 12 endpoints at `/api/v1/*` — health, query, ingest, documents CRUD, auth keys CRUD, admin reindex
- **Ring-fenced RAG pipeline**: LCEL-based retrieval with PostgreSQL JSONB `@>` role filtering, mock LLM fallback for testing
- **Auth system**: SHA-256 hashed API keys with Bearer token auth, role extraction, admin role enforcement
- **Data layer**: SQLAlchemy ORM models (DocumentChunk, ApiKey, IngestionJob), Alembic migrations, pgvector support
- **Ingestion pipeline**: document parsing (md/txt/pdf), chunking, sentence-transformers embedding, SQLRecordManager idempotent indexing
- **Web UI**: React 19 SPA with Vite, Tailwind dark theme — Login, Dashboard/Query, Documents, Ingest, Settings pages
- **Configuration**: pydantic-settings with env var override (`RFR_*`), TOML config file, CLI `config set`
- **Docker support**: Production Docker Compose (6 services), Dockerfiles for API and web, health checks
- **Documentation**: mkdocs site with 6 pages (quickstart, architecture, config, API, CLI, development)
- **CI**: GitHub Actions — lint (ruff), type check (pyright), test (pytest + coverage), build

### Architecture

- Zero-trust retrieval: RBAC enforced via PostgreSQL JSONB `@>` containment operator at query time
- LCEL-only policy: no legacy `RetrievalQA` chains, all pipelines use explicit `RunnableLambda`
- 100% local by default: embedding (sentence-transformers), storage (pgvector), inference (Ollama/vLLM)
- Idempotent ingestion: LangChain SQLRecordManager prevents duplicate vectors
- Redacted telemetry: PII regex scrubbing, 7-day trace retention

[1.0.0a1]: https://github.com/iknowkungfubar/ring-fenced-rag/releases/tag/v1.0.0a1
