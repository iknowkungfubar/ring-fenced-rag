# Configuration

Ring-Fenced RAG uses [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) for configuration, with three override layers:

1. **Environment variables** (highest priority) — prefix `RFR_*`
2. **Config file** — `~/.rfr/config.toml`
3. **Defaults** (lowest priority)

## Config File Example

```toml
[llm]
provider = "ollama"
base_url = "http://localhost:11434/v1"
model = "llama3.2:3b"
temperature = 0.1

[embedding]
model = "all-MiniLM-L6-v2"
dimension = 384

[ingestion]
chunk_size = 512
default_role = "user"

[database]
url = "postgresql+psycopg://admin:password@localhost:5432/rag_internal"

[server]
host = "0.0.0.0"
port = 8000
log_level = "INFO"

[auth]
enabled = true
admin_roles = ["admin"]
allowed_roles = ["admin", "senior_engineer", "junior_engineer", "user"]
```

## Environment Variables

Nested config keys use `__` as delimiter:

| Variable | Maps To | Default |
|----------|---------|---------|
| `RFR_LLM__PROVIDER` | `llm.provider` | `ollama` |
| `RFR_LLM__BASE_URL` | `llm.base_url` | `http://localhost:11434/v1` |
| `RFR_LLM__MODEL` | `llm.model` | `llama3.2:3b` |
| `RFR_LLM__TEMPERATURE` | `llm.temperature` | `0.1` |
| `RFR_EMBEDDING__MODEL` | `embedding.model` | `all-MiniLM-L6-v2` |
| `RFR_INGESTION__CHUNK_SIZE` | `ingestion.chunk_size` | `512` |
| `RFR_DB__URL` | `database.url` | PostgreSQL connection string |
| `RFR_SERVER__PORT` | `server.port` | `8000` |
| `RFR_AUTH__ENABLED` | `auth.enabled` | `true` |
| `RFR_API_KEY` | `api_key` | (auto-generated) |

## CLI Commands

```bash
# View current config
rfr config show

# Set a value
rfr config set llm.model llama3.2:3b
```
