# Ring-Fenced RAG

> Self-hosted, zero-trust RAG with role-based access control enforced at the database level.

[![CI](https://github.com/iknowkungfubar/ring-fenced-rag/actions/workflows/ci.yml/badge.svg)](https://github.com/iknowkungfubar/ring-fenced-rag/actions/workflows/ci.yml)
[![CodeQL](https://github.com/iknowkungfubar/ring-fenced-rag/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/iknowkungfubar/ring-fenced-rag/security/code-scanning)
[![Dependabot](https://img.shields.io/badge/dependabot-active-brightgreen.svg)](https://github.com/iknowkungfubar/ring-fenced-rag/security/dependabot)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/ring-fenced-rag)](https://pypi.org/project/ring-fenced-rag/)


## What is Ring-Fenced RAG?

Ring-Fenced RAG (RFR) is a self-hosted document Q&A system where **access control is enforced at the database level** — not the application layer. Every document chunk is tagged with role metadata at ingestion time. When a user queries the system, the vector database **mathematically refuses** to return chunks the user isn't authorized to see.

No cloud APIs. No data egress. No "we promise to filter after retrieval."

```bash
pip install ring-fenced-rag
rfr init
rfr up
rfr ingest ./docs/ --role senior_engineer
rfr query "How do I restart Nginx?"
```

## Key Features

- **🔒 Ring-Fenced Retrieval** — PostgreSQL JSONB `@>` operator enforces role-based access at query time. Unauthorized queries return zero results.
- **🏠 100% Local** — Embedding (sentence-transformers), storage (pgvector), and generation (Ollama/vLLM/LM Studio) all run on your hardware. Zero data egress by default.
- **♻️ Idempotent Ingestion** — LangChain `SQLRecordManager` tracks content hashes. Ingest the same doc 10 times, get exactly 1 copy.
- **🔌 Pluggable LLMs** — Supports vLLM, Ollama, LM Studio, and any OpenAI-compatible API. Configure in `~/.rfr/config.toml`.
- **🎛️ Four Interfaces** — CLI, Web UI, TUI, REST API.
- **🐧 AMD ROCm Support** — Works on AMD GPUs via ROCm vLLM or Ollama.

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (for production mode)
- Or: just Python (for standalone mode with SQLite)

### Installation

```bash
pip install ring-fenced-rag
```

### Initialize

```bash
cd my-project
rfr init
```

This creates:
- `~/.rfr/config.toml` — your configuration
- `docker-compose.yml` — ready to run

### Start the Stack

```bash
# Production mode (Docker — recommended)
rfr up

# Standalone mode (no Docker)
rfr standalone
```

### Access the Web UI

Once the stack is running, open **[http://localhost:8080](http://localhost:8080)** in your browser.

The Web UI provides:
- **Dashboard** — Ask questions against your documents
- **Documents** — Browse and manage indexed documents
- **Ingest** — Upload documents with role metadata
- **Settings** — Manage API keys and view system health

> The Web UI is a React + TypeScript SPA served by the FastAPI backend. To develop it locally: `cd src/rfr/web && npm install && npm run dev` (runs on port 5173 with API proxy).

### Ingest Documents

```bash
rfr ingest ./manuals/ --role senior_engineer
rfr ingest ./onboarding/ --role junior_engineer
```

### Ask Questions

```bash
rfr query "How do I restart the Nginx server?"
```

## CLI Reference

All CLI commands at a glance:

| Command | Description |
|---------|-------------|
| `rfr init` | Generate config + docker-compose.yml |
| `rfr up [-d]` | Start Docker services |
| `rfr down` | Stop Docker services |
| `rfr status` | Show component health |
| `rfr version` | Show version, git commit, platform |
| `rfr --version` | Show version (short) |
| `rfr standalone` | Run in standalone mode (SQLite, no Docker) |
| `rfr config show` | Print current config |
| `rfr config set <k> <v>` | Update config value |
| `rfr ingest <path>` | Ingest documents from file/directory |
| `rfr query <question>` | Ask a question against your docs |
| `rfr keys create/list/revoke` | Manage API keys |
| `rfr docs list/delete` | Browse and delete indexed documents |
| `rfr logs [service]` | Tail Docker service logs |
| `rfr tui` | Launch terminal UI (Textual) |

## Configuration

Edit `~/.rfr/config.toml` or use `RFR_*` environment variables:

```toml
[llm]
provider = "ollama"        # vllm, ollama, lm-studio, openai
base_url = "http://localhost:11434/v1"
model = "llama3.2:3b"

[embedding]
model = "all-MiniLM-L6-v2"  # 384-dim, CPU-friendly

[ingestion]
chunk_size = 512
default_role = "user"
```

## Architecture

```
User (CLI/Web/TUI) → FastAPI API → LCEL Pipeline
                                        │
                              ┌─────────▼──────────┐
                              │  pgvector (PostgreSQL)
                              │  JSONB @> role filter
                              │  HNSW vector index
                              └─────────┬──────────┘
                                        │
                              ┌─────────▼──────────┐
                              │  LLM (Ollama/vLLM)  │
                              │  Zero egress        │
                              └────────────────────┘
```

## Development

```bash
# Clone
git clone https://github.com/iknowkungfubar/ring-fenced-rag.git
cd ring-fenced-rag

# Install with dev dependencies
uv sync --group dev

# Run tests
uv run pytest tests/ -q --tb=short --cov=src/rfr

# Format and lint
uv run ruff format src/ tests/
uv run ruff check src/ tests/

# Install TUI dependencies (optional)
uv pip install textual
```

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on our development process, coding standards, PR workflow, and code of conduct.

## License

MIT
