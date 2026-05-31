# Quickstart

Get up and running in under 5 minutes.

## Prerequisites

- Python 3.13+
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
export RFR_LLM__PROVIDER=vllm
export RFR_LLM__BASE_URL=http://localhost:8000/v1
export RFR_LLM__MODEL=meta-llama/Meta-Llama-3-8B-Instruct
```
