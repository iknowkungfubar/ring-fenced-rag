# syntax=docker/dockerfile:1
FROM python:3.13-slim AS builder

WORKDIR /build

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /bin/uv

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-group dev --no-install-project

# Install the package
COPY src/ src/
RUN uv sync --frozen --no-group dev

# ── Runtime image ──
FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

RUN addgroup --system rfr && adduser --system --ingroup rfr rfr
USER rfr

WORKDIR /app

COPY --from=builder /build/.venv /app/.venv
COPY --from=builder /build/src /app/src
COPY pyproject.toml /app/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# To enable HTTPS, set RFR_SERVER__SSL_CERTFILE and RFR_SERVER__SSL_KEYFILE
# environment variables pointing to PEM-encoded certificate and key files.
# Example:
#   docker run -e RFR_SERVER__SSL_CERTFILE=/certs/cert.pem \
#              -e RFR_SERVER__SSL_KEYFILE=/certs/key.pem \
#              -v /host/certs:/certs:ro ...

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "rfr.api.app:create_app", "--host", "0.0.0.0", "--port", "8000"]
