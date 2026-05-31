# Ring-Fenced RAG — AGENTS.md

## Project Conventions

### Package Structure
- Python package: `rfr` (import as `from rfr import ...`)
- Source: `src/rfr/`
- Tests: `tests/` (mirrors `src/rfr/` structure with `test_` prefix)
- Blueprint: `.hermes/blueprint/`

### Key Architecture Rules
1. **LCEL-only** — Never use `RetrievalQA`, `ConversationalRetrievalChain`, or other legacy LangChain wrappers. All RAG pipelines use LangChain Expression Language with explicit `RunnableLambda` and `RunnablePassthrough`.
2. **DB-level ring-fence** — Metadata filtering (`allowed_roles`) must happen in the SQL query via PostgreSQL JSONB `@>` operator, never in application code.
3. **Idempotent ingestion** — Every ingestion must use `SQLRecordManager` with incremental cleanup. Running the same ingestion twice must produce zero duplicate vectors.
4. **Zero egress by default** — Default LLM provider is Ollama (local). OpenAI requires explicit opt-in in config.
5. **Redacted telemetry** — Traces must redact PII (IPs, credentials, internal paths) before storage. Full traces expire after 7 days.

### Code Quality
- Lint: `ruff check src/ tests/` — must pass before merge
- Format: `ruff format src/ tests/` — must be clean
- Type check: `pyright src/rfr/` — strict mode
- Tests: `pytest tests/ -q --cov=src/rfr --cov-fail-under=85`
- Pre-commit: Run `pre-commit install` after cloning

### Testing
- Unit tests go in `tests/test_<module>.py`
- Use `pytest-asyncio` for async tests
- Use `syrupy` for snapshot testing
- Use `respx` for mocking HTTP calls
- Integration tests requiring Docker use `docker compose` in CI

### Commit Convention
- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation
- `refactor:` — code restructuring
- `test:` — test changes
- `chore:` — maintenance, deps, CI

### Running Locally
```bash
# Install
uv sync --group dev

# Lint & test
uv run ruff check src/ tests/
uv run pytest tests/ -q --tb=short

# Development server
uv run uvicorn rfr.api.app:create_app --reload

# CLI
uv run rfr --help
```
