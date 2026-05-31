# Build Plan

## Overview

**Product:** Ring-Fenced RAG (RFR) v1.0.0
**Timeline:** 8 weeks target (aggressive solo dev — adjust based on capacity)
**Strategy:** Parallel backend/frontend/infra build with integration pass

## Dependency Graph

```
                    ┌─────────────────────────────┐
                    │  Phase 1: Foundation (wk 1)  │
                    │  Scaffold, configs, CI, repo │
                    └────────────┬────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                   ▼
  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
  │ Phase 2: Data    │ │ Phase 3: API     │ │ Phase 4: CLI     │
  │ Layer (wk 2)     │ │ Layer (wk 3-4)   │ │ Shell (wk 2)     │
  │ Models, DB,      │ │ Endpoints, auth, │ │ Commands,        │
  │ Ingestion engine │ │ LCEL pipeline    │ │ init, up/down    │
  └──────────────────┘ └──────────────────┘ └──────────────────┘
         │                      │                    │
         └──────────────────────┼────────────────────┘
                                ▼
              ┌─────────────────────────────────────┐
              │  Phase 5: Frontend (wk 3-5)          │
              │  Web UI, TUI, query interface        │
              │  (parallel with Phase 2-3)           │
              └──────────────────┬──────────────────┘
                                 │
                                ▼
              ┌─────────────────────────────────────┐
              │  Phase 6: Integration (wk 6-7)       │
              │  Integration tests, Docker compose,  │
              │  contract tests, docs                │
              └──────────────────┬──────────────────┘
                                 │
                                ▼
              ┌─────────────────────────────────────┐
              │  Phase 7: Release (wk 8)             │
              │  PyPI publish, GitHub release,       │
              │  README, demo video                  │
              └─────────────────────────────────────┘
```

## Phase Breakdown

### Phase 1: Foundation (Week 1)

**Goal:** Scaffolded repo with CI, linting, type checking, and base config.

| ID | Task | Est. | Depends | Description |
|----|------|------|---------|-------------|
| 1.1 | Initialize project structure | 2h | — | Create Python package `ring_fenced_rag/`, `pyproject.toml`, `src/rfr/` layout, `uv init` |
| 1.2 | Configure tooling | 1h | 1.1 | ruff config, pyright, pytest setup, pre-commit hooks |
| 1.3 | Set up CI (GitHub Actions) | 2h | 1.2 | Test on 3.12-3.13, lint check, type check, coverage gate |
| 1.4 | Create Docker Compose skeleton | 2h | 1.1 | Base compose with pgvector, Redis, and Caddy (no app images yet) |
| 1.5 | Create AGENTS.md | 30m | — | Project conventions for agent-assisted development |
| 1.6 | Create config module | 2h | 1.1 | `pydantic-settings`-based config with env/file/CLI overrides |
| 1.7 | Set up mkdocs docs skeleton | 1h | 1.1 | Basic docs structure, auto-publish via CI |

**Acceptance:** `ci passes ✓`, `make lint ✓`, `make typecheck ✓`, `docker compose up pgvector redis ✓`

---

### Phase 2: Data Layer (Week 2)

**Goal:** Production data models, Alembic migrations, embedding engine, ingestion pipeline.

| ID | Task | Est. | Depends | Description |
|----|------|------|---------|-------------|
| 2.1 | Data models (SQLAlchemy) | 3h | 1.1 | `document_chunks`, `api_keys`, `ingestion_jobs` models with types |
| 2.2 | Alembic migrations | 2h | 2.1 | V001-V004 migrations with pgvector extension |
| 2.3 | Embedding engine module | 3h | 1.6 | `LocalEmbeddings` wrapper, model cache, dimension-aware |
| 2.4 | Document parsing module | 4h | 1.6 | Parse markdown, PDF, txt, JSON; extract metadata; validate `allowed_roles` |
| 2.5 | Chunking module | 2h | 1.6 | Configurable chunk size/overlap, token-count-aware truncation |
| 2.6 | Ingestion pipeline | 6h | 2.3, 2.4, 2.5 | `SQLRecordManager` + `PGVector` + `index()` with incremental cleanup |
| 2.7 | Ingestion test suite | 3h | 2.6 | Unit tests: idempotency, metadata validation, chunk integrity |
| 2.8 | Database indexing tests | 2h | 2.1 | Verify HNSW index, verify metadata GIN index query performance |

**Acceptance:** `ingest same doc 2x → skipped on 2nd run ✓`, `doc missing allowed_roles → error ✓`, `all tests pass ✓`, `coverage ≥ 85% ✓`

---

### Phase 3: API Layer (Week 3-4)

**Goal:** FastAPI server with auth, LCEL pipeline, query and management endpoints.

| ID | Task | Est. | Depends | Description |
|----|------|------|---------|-------------|
| 3.1 | FastAPI app scaffold | 2h | 1.1 | App factory, middleware (CORS, logging, error), lifespan |
| 3.2 | Auth module | 4h | 2.1 | API key hashing (SHA-256), key→role resolution, bearer middleware |
| 3.3 | API key management endpoints | 2h | 3.2 | CRUD endpoints from API contracts (05-API.md) |
| 3.4 | LCEL RAG pipeline | 6h | 2.6, 3.2 | `SecureQueryRequest`, `secure_retriever` with role filter, prompt template, LLM client |
| 3.5 | Query endpoint (POST /query) | 2h | 3.4 | Request validation, LCEL invocation, response formatting |
| 3.6 | Ingestion endpoints | 3h | 2.6, 3.2 | POST/GET ingestion, Celery task creation, polling |
| 3.7 | Document management endpoints | 2h | 2.6, 3.2 | List/delete documents, list sources |
| 3.8 | Health endpoint | 1h | 3.1 | Component health checks (DB, Redis, LLM) |
| 3.9 | Admin endpoints | 1h | 3.2 | Re-index, system info |
| 3.10 | Rate limiting | 2h | 3.1 | Token bucket rate limiter per API key |
| 3.11 | Telemetry/observability integration | 3h | 3.4 | Langfuse/Phoenix integration, redaction callback |
| 3.12 | API integration tests | 4h | 3.1-3.9 | httpx-based async tests for all endpoints |
| 3.13 | Standalone server mode | 2h | 3.1 | `rfr standalone` — runs FastAPI directly without Docker |

**Acceptance:** `POST /query returns answer with sources ✓`, `unauthorized query returns empty ✓`, `POST /ingest returns task_id ✓`, `all integration tests pass ✓`, `standalone mode works ✓`

---

### Phase 4: CLI Shell (Week 2-3, parallel with Phase 3)

**Goal:** Complete CLI with all commands, Docker orchestration, and standalone mode.

| ID | Task | Est. | Depends | Description |
|----|------|------|---------|-------------|
| 4.1 | CLI scaffold + click app | 2h | 1.1 | Main CLI group, help text, version, rich console |
| 4.2 | `rfr init` command | 2h | 4.1 | Generate config file + docker-compose.yml in current dir |
| 4.3 | `rfr up/down/status` commands | 3h | 4.2 | Docker Compose lifecycle management via Python subprocess |
| 4.4 | `rfr config` commands | 1h | 4.1 | Config show/set with pydantic-settings integration |
| 4.5 | API client module | 3h | 3.1 | httpx-based client wrapping all endpoints, auth header injection |
| 4.6 | `rfr query` command | 2h | 4.5, 3.4 | Query with rich output, optional no-llm mode |
| 4.7 | `rfr ingest` command | 1h | 4.5 | Trigger + poll ingestion |
| 4.8 | `rfr keys` commands | 1h | 4.5 | Create, list, revoke API keys |
| 4.9 | `rfr docs` commands | 1h | 4.5 | List, delete documents |
| 4.10 | `rfr standalone` command | 2h | 3.13 | Launch API server in standalone mode |
| 4.11 | `rfr logs` command | 1h | 4.2 | Tail Docker Compose logs |
| 4.12 | CLI test suite | 2h | 4.1-4.11 | Click testing, mock API responses |

**Acceptance:** `rfr init → creates config + compose ✓`, `rfr up → docker compose up -d ✓`, `rfr query "test" → answer ✓`, `rfr status → component health ✓`

---

### Phase 5: Frontend (Week 3-5, parallel with Phase 3)

**Goal:** React web interface and Textual TUI.

| ID | Task | Est. | Depends | Description |
|----|------|------|---------|-------------|
| 5.1 | Frontend scaffold | 2h | — | Vite + React + TypeScript + Tailwind + shadcn/ui |
| 5.2 | Design system | 2h | 5.1 | Theme tokens, global CSS, typography, component primitives |
| 5.3 | Login screen | 2h | 5.1 | API key entry, validation, localStorage persistence |
| 5.4 | Query interface | 6h | 5.1 | Query bar, result panel, markdown rendering, source citations |
| 5.5 | Document browser | 3h | 5.1 | Document list with source filter, delete action |
| 5.6 | Ingestion UI | 3h | 5.1 | Ingest form, job history, progress polling |
| 5.7 | Settings pages | 4h | 5.1 | API key management, LLM config, roles, system tab |
| 5.8 | API client (React Query) | 3h | 5.1 | Typed API hooks, error handling, loading states |
| 5.9 | Error boundaries + empty states | 2h | 5.1 | Loading skeletons, error banners, empty state illustrations |
| 5.10 | Frontend tests | 3h | 5.1-5.8 | vitest + testing-library for key components |
| 5.11 | TUI scaffold | 3h | 4.1 | Textual app shell, screens, keybindings |
| 5.12 | TUI query screen | 3h | 5.11 | Query input, answer display, source panel |
| 5.13 | TUI status + management | 2h | 5.11 | Component health, ingestion queue, key management |

**Acceptance:** `Login → query → answer flow works ✓`, `empty states render correctly ✓`, `role badge shows current role ✓`, `TUI launches and accepts queries ✓`

---

### Phase 6: Integration (Week 6-7)

**Goal:** Everything works together. Docker Compose deployment, end-to-end tests, docs.

| ID | Task | Est. | Depends | Description |
|----|------|------|---------|-------------|
| 6.1 | Docker Compose production config | 4h | 4.2 | All services with health checks, volumes, networks, GPU |
| 6.2 | Dockerfiles for API + web | 3h | 3.1, 5.1 | Multi-stage builds, slim images |
| 6.3 | Celery worker Dockerfile | 1h | 2.6 | Ingestion worker as separate service |
| 6.4 | End-to-end tests | 6h | 3.1, 5.1 | Full flow: ingest → query → verify answer contains expected content |
| 6.5 | Contract tests | 3h | 3.1 | Verify every endpoint matches API spec (05-API.md) |
| 6.6 | Performance tests | 3h | 6.4 | Latency targets, throughput, memory under load |
| 6.7 | Security audit | 4h | 3.2, 6.1 | Auth bypass attempts, injection tests, network isolation verify |
| 6.8 | Documentation | 6h | 4.1, 5.1 | README, quickstart, user guide, API reference, architecture docs |
| 6.9 | Blueprint sync | 2h | 6.4-6.8 | Update any blueprint sections that diverged during implementation |

**Acceptance:** `docker compose up --build → all services healthy ✓`, `e2e: ingest file → query → answer ✓`, `contract tests all pass ✓`, `coverage ≥ 85% ✓`

---

### Phase 7: Release (Week 8)

**Goal:** Published package, GitHub release, changelog, demo.

| ID | Task | Est. | Depends | Description |
|----|------|------|---------|-------------|
| 7.1 | PyPI publishing | 2h | 6.1 | `hatch build && hatch publish`, PyPI API token config |
| 7.2 | CHANGELOG + release notes | 2h | 6.8 | Conventional commits → changelog, GitHub release |
| 7.3 | Demo video / GIF | 2h | 6.4 | Terminal recording of install → init → ingest → query |
| 7.4 | GitHub repo polish | 2h | 6.8 | README badges, tags, GitHub topics, CI badges |
| 7.5 | Post-release validation | 2h | 7.1 | `pip install ring-fenced-rag` from clean env → works |
| 7.6 | v1.1 issue triage | 1h | — | Collect known gaps, plan v1.1 improvements |

**Acceptance:** `pip install ring-fenced-rag && rfr init && rfr up && rfr query "test" → works ✓`, GitHub release published ✓, docs live ✓

---

## Task Details

### Task 2.6 — Ingestion Pipeline

**Files:**
- Create: `src/rfr/ingestion/pipeline.py`
- Create: `src/rfr/ingestion/embedding.py`
- Create: `src/rfr/ingestion/parsing.py`
- Create: `src/rfr/ingestion/chunking.py`
- Create: `tests/test_ingestion.py`

**Acceptance Criteria:**
- [ ] `ingest_documents()` accepts list of Document objects with metadata
- [ ] Validates `allowed_roles` is present in every chunk's metadata
- [ ] Uses `SQLRecordManager` with incremental cleanup
- [ ] Uses `source` as `source_id_key`
- [ ] Running same batch twice → `num_added: 0, num_skipped: N`
- [ ] Updating document content → `num_updated: 1` on re-ingest
- [ ] Missing `allowed_roles` → raises `IngestionError`
- [ ] All unit tests pass

**Depends on:** 2.3 (embedding), 2.4 (parsing), 2.5 (chunking)

### Task 3.4 — LCEL RAG Pipeline

**Files:**
- Create: `src/rfr/api/pipeline.py`
- Create: `src/rfr/api/models.py` (Pydantic request/response models)
- Create: `tests/test_pipeline.py`

**Acceptance Criteria:**
- [ ] `SecureQueryRequest` accepts `query` and `user_role`
- [ ] `secure_retriever` applies `{"allowed_roles": {"$in": [user_role]}}` filter
- [ ] `format_docs` produces string with source citations
- [ ] Prompt template enforces "ONLY the provided context" instruction
- [ ] `RunnableConfig` sets timeout on LLM call
- [ ] Pipeline raises `RAGExecutionError` on LLM failure (sanitized message)
- [ ] Pipeline raises `RAGExecutionError` on DB failure
- [ ] Token-count-aware context truncation (safe threshold)
- [ ] All unit tests pass

**Depends on:** 2.6 (ingestion), 3.2 (auth for role extraction)

---

## Parallelization Strategy

```
Week 1:  [Phase 1: Foundation]
Week 2:  [Phase 2: Data Layer]───────[Phase 4: CLI Shell]
Week 3:  [Phase 3: API Layer (pt 1)]─[Phase 4: CLI]───[Phase 5: Frontend (pt 1)]
Week 4:  [Phase 3: API Layer (pt 2)]─[Phase 5: Frontend (pt 2)]
Week 5:  [Phase 3: API tests]─────────[Phase 5: Frontend (pt 3)]
Week 6:  [Phase 6: Integration pt 1]
Week 7:  [Phase 6: Integration pt 2]
Week 8:  [Phase 7: Release]
```

Maximum parallelism: **3 sub-agents** (data, CLI, frontend) during weeks 3-4.

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| pgvector dimension mismatch after model change | Medium | High | Schema migration documented in data model; re-index endpoint exists |
| AMD ROCm vLLM unavailable/stale image | Medium | High | Support Ollama as drop-in replacement; document both paths |
| LangChain API breaking changes | Low | Medium | Pin LangChain versions in pyproject.toml; use LCEL only (no legacy chains) |
| Large doc ingestion blocks API server | Low | High | Celery async ingestion; queue isolation from query path |
| User has no GPU | High | High | CPU inference via llama.cpp + Ollama; sentence-transformers runs on CPU |
| Textual TUI complexity | Medium | Low | TUI is Phase 5, not blocking web UI; defer if time is tight |
