# Quickstart

Get up and running in under 5 minutes.

## Prerequisites

- Python 3.11+
- Docker & Docker Compose (for production mode)

## Install

```bash
pip install ring-fenced-rag
```

## Initialize

```bash
cd my-project
rfr init
```

This creates `~/.rfr/config.toml` and `docker-compose.yml`.

## Start the Stack

```bash
# Production mode (Docker — recommended)
rfr up

# Standalone mode (no Docker, mock LLM)
rfr standalone
```

## Ingest Documents

```bash
# Directory with a default role
rfr ingest ./manuals/ --role senior_engineer

# Single file
rfr ingest ./onboarding.md --role junior_engineer
```

## Ask Questions

```bash
rfr query "How do I restart the Nginx server?"
```

## Create an API Key for the Web UI

```bash
rfr keys create web-access --role admin
# Copy the displayed key, then open http://localhost:8000/docs
```

## Configuration

Edit `~/.rfr/config.toml` or use environment variables:

```bash
# Use LM Studio (default on port 1234)
export RFR_LLM__PROVIDER=lm-studio
export RFR_LLM__BASE_URL=http://localhost:1234/v1

# Use vLLM
export RFR_LLM__PROVIDER=vllm
export RFR_LLM__BASE_URL=http://localhost:8000/v1
export RFR_LLM__MODEL=meta-llama/Meta-Llama-3-8B-Instruct

# Use Ollama
export RFR_LLM__PROVIDER=ollama
export RFR_LLM__MODEL=llama3.2:3b

# Or OpenAI (data leaves your network — explicit opt-in)
export RFR_LLM__PROVIDER=openai
export RFR_LLM__API_KEY=sk-...
```
