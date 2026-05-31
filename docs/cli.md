# CLI Reference

The `rfr` CLI is the primary user interface.

## Commands

| Command | Description |
|---------|-------------|
| `rfr init` | Generate config + docker-compose.yml |
| `rfr up [-d] [--gpu rocm\|cuda\|none]` | Start all Docker services |
| `rfr down` | Stop all Docker services |
| `rfr status [--watch]` | Show component health |
| `rfr config show` | Print current config |
| `rfr config set <k> <v>` | Update config value |
| `rfr ingest <path> [--role R] [--pattern P]` | Ingest documents |
| `rfr query <question> [--role R] [--top-k N] [--no-llm]` | Ask a question |
| `rfr keys create <name> [--role R]` | Create API key |
| `rfr keys list` | List API keys |
| `rfr keys revoke <prefix>` | Revoke an API key |
| `rfr docs list` | List indexed documents |
| `rfr docs delete <id>` | Delete a document |
| `rfr standalone [--port N]` | Run API server without Docker |
| `rfr logs [service] [-f]` | Tail Docker logs |
| `rfr tui` | Launch terminal UI |

## Example Session

```bash
# Install
pip install ring-fenced-rag

# Initialize
cd my-docs
rfr init

# Start the stack
rfr up

# Ingest some docs
rfr ingest ./manuals/ --role senior_engineer

# Ask a question
rfr query "How do I restart Nginx?"

# Create an API key for the web UI
rfr keys create web-access --role admin
> Created key: rfr_a1b2c3d4e5f6... (shown once)
```
