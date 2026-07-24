# Changelog

All notable changes to Ring-Fenced RAG will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-07-24

### Changed
- Promoted from alpha (v1.0.0a1) to stable (v1.0.0)
- Dropped Python requirement to >=3.11 (was >=3.13) — unlocks pip install on all modern runtimes
- Updated Python classifiers for 3.11, 3.12, 3.13
- Updated ruff target-version to py311

## [1.0.0a1] — 2025-05-31

### Added

- **CLI interface** (`rfr`): 13 commands — `init`, `up`, `down`, `status`, `version`, `config`, `ingest`, `query`, `keys`, `docs`, `standalone`, `logs`, `tui`
- **REST API**: 12 endpoints at `/api/v1/*` — health, query, ingest, documents CRUD, auth CRUD, admin reindex
- **Ring-fenced RAG pipeline**: LCEL-based retrieval with PostgreSQL JSONB `@>` role filtering, mock LLM fallback for testing
- **Auth system**: SHA-256 hashed API keys with Bearer token auth, role extraction, admin role enforcement
- **Data layer**: SQLAlchemy ORM models (DocumentChunk, ApiKey, IngestionJob), Alembic migrations, pgvector support
- **Ingestion pipeline**: document parsing (md/txt/pdf), chunking, sentence-transformers embedding, SQLRecordManager idempotent indexing
- **Web UI**: React 19 SPA with Vite, Tailwind dark theme — Login, Dashboard/Query, Documents, Ingest, Settings pages
- **Terminal UI**: Textual-based TUI with query screen and system status screen. Launch with `rfr tui`
- **Configuration**: pydantic-settings with env var override (`RFR_*`), TOML config file, CLI `config set`
- **LM Studio support**: `LMStudioProvider` with default endpoint `localhost:1234/v1`. Configurable via `RFR_LLM__PROVIDER=lm-studio`.
- **Dynamic versioning**: Version derived from `git describe` tags at runtime with static fallback. `rfr version` command shows version, git commit, Python, platform.
- **Provider factory**: `get_provider()` factory function dispatches by name to the correct provider class.
- **Docker support**: Production Docker Compose (6 services), Dockerfiles for API and web, health checks
- **Documentation**: mkdocs site with 8 pages (quickstart, architecture, config, API, CLI, development, optimization)
- **CI**: GitHub Actions — format check, lint, tests (126), build

### Architecture

- Zero-trust retrieval: RBAC enforced via PostgreSQL JSONB `@>` containment operator at query time
- LCEL-only policy: no legacy `RetrievalQA` chains, all pipelines use explicit `RunnableLambda`
- 100% local by default: embedding (sentence-transformers), storage (pgvector), inference (Ollama/vLLM/LM Studio)
- Idempotent ingestion: LangChain SQLRecordManager prevents duplicate vectors
- Redacted telemetry: PII regex scrubbing, 7-day trace retention

### Fixed

- CLI entry point in pyproject.toml (`rfr.cli.main` → `rfr.cli`)
- Duplicate `http_status` import in auth module
- `site/` (mkdocs build output) tracked in git — removed, added to .gitignore
- Coverage drop from TUI stub replacement — tui_app.py excluded (UI code, can't unit-test)

[1.0.0a1]: https://github.com/iknowkungfubar/ring-fenced-rag/releases/tag/v1.0.0a1
