# Development

## Setup

```bash
# Clone
git clone https://github.com/iknowkungfubar/ring-fenced-rag.git
cd ring-fenced-rag

# Install with dev dependencies
uv sync --group dev

# Run tests
uv run pytest tests/ -q --tb=short --cov=src/rfr

# Lint
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Type check
uv run pyright src/rfr/
```

## Project Structure

```
ring-fenced-rag/
├── src/rfr/              # Python package
│   ├── api/              # FastAPI server, routes, auth, LCEL pipeline
│   ├── cli/              # CLI commands + HTTP API client
│   ├── ingestion/        # Document parsing, chunking, embedding
│   ├── models/           # SQLAlchemy ORM + Alembic migrations
│   └── config.py         # pydantic-settings configuration
├── src/rfr/web/          # React frontend (Vite + TypeScript)
│   └── src/
│       ├── pages/        # Login, Dashboard, Documents, Ingest, Settings
│       ├── hooks/        # Auth context
│       └── lib/          # API client, utilities
├── tests/                # Python test suite (pytest)
├── docs/                 # mkdocs documentation
├── .hermes/blueprint/    # Product blueprint (8 documents)
├── docker-compose.yml    # Dev Docker Compose
├── docker-compose.prod.yml  # Production Docker Compose
├── Dockerfile            # API server container
└── Dockerfile.web        # Web UI container
```

## Architecture Rules

1. **LCEL-only** — Never use `RetrievalQA` / `ConversationalRetrievalChain`
2. **DB-level ring-fence** — Metadata filtering via PostgreSQL JSONB `@>`, never app-level
3. **Idempotent ingestion** — Every ingestion uses `SQLRecordManager` with incremental cleanup
4. **Zero egress by default** — Default LLM is Ollama (local). OpenAI requires explicit opt-in
5. **Redacted telemetry** — Trace redaction enabled by default, 7-day retention

## Running Locally

```bash
# Start PostgreSQL + Redis
docker compose up -d vector-db redis

# Run the API server
uv run uvicorn rfr.api.app:create_app --reload --port 8000

# In another terminal, run the CLI
uv run rfr status
uv run rfr query "test"

# Or run the frontend
cd src/rfr/web && pnpm dev
```
