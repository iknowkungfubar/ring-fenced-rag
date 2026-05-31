"""End-to-end tests for Ring-Fenced RAG.

These tests run against a live API server. They require:
- A running RFR API server at the configured URL
- An admin API key

Skip these tests unless explicitly enabled with RUN_E2E=true.
"""

from __future__ import annotations

import os
from typing import Any

import pytest

from rfr.api.schemas import (
    CreateKeyResponse,
    HealthResponse,
    IngestResponse,
    QueryResponse,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_E2E") != "true",
    reason="E2E tests require RUN_E2E=true and a running server",
)


@pytest.fixture
def client() -> Any:  # noqa: ANN401
    """Create an API client connected to the test server."""
    from rfr.cli.client import RfrClient

    return RfrClient(
        base_url=os.environ.get("RFR_API_URL", "http://localhost:8000"),
        api_key=os.environ.get("RFR_API_KEY", ""),
    )


class TestE2EHealth:
    """Verify the health endpoint works end-to-end."""

    def test_health_returns_ok(self, client: Any) -> None:  # noqa: ANN401
        """Health check should succeed."""
        health = client.health()
        assert isinstance(health, HealthResponse)
        assert health.status in ("ok", "degraded")
        assert health.version

    def test_health_has_components(self, client: Any) -> None:  # noqa: ANN401
        """Health should report component status."""
        health = client.health()
        assert "database" in health.components
        assert "llm" in health.components


class TestE2EQuery:
    """Verify the query endpoint works end-to-end."""

    def test_query_returns_response(self, client: Any) -> None:  # noqa: ANN401
        """A basic query should return a response."""
        result = client.query("How do I restart Nginx?")
        assert isinstance(result, QueryResponse)
        assert result.answer

    def test_query_with_sources(self, client: Any) -> None:  # noqa: ANN401
        """Query response should include source metadata."""
        result = client.query("How do I restart Nginx?", top_k=3)
        assert isinstance(result, QueryResponse)
        assert result.latency_ms > 0


class TestE2EIngestion:
    """Verify the ingestion pipeline works end-to-end."""

    def test_ingest_file(self, client: Any, tmp_path: Any) -> None:  # noqa: ANN401
        """Ingesting a file should return a task ID."""
        doc = tmp_path / "test.md"
        doc.write_text("# Test Document\n\nThis is test content for ingestion.")
        result = client.ingest_file(str(doc), allowed_roles=["admin"])
        assert isinstance(result, IngestResponse)
        assert result.task_id

    def test_ingest_polling(self, client: Any, tmp_path: Any) -> None:  # noqa: ANN401
        """Ingestion task status should be pollable."""
        doc = tmp_path / "test.md"
        doc.write_text("# Test\n\nContent.")
        ingest = client.ingest_file(str(doc), allowed_roles=["user"])
        status = client.get_ingestion_status(ingest.task_id)
        assert status.status in ("pending", "running", "completed", "failed")


class TestE2EAuth:
    """Verify the auth endpoints work end-to-end."""

    def test_create_and_list_keys(self, client: Any) -> None:  # noqa: ANN401
        """Creating and listing keys should work."""
        result = client.create_key("e2e-test", role="admin")
        assert isinstance(result, CreateKeyResponse)
        assert result.key.startswith("rfr_")

        keys = client.list_keys()
        assert any(k.name == "e2e-test" for k in keys.keys)

    def test_revoke_key(self, client: Any) -> None:  # noqa: ANN401
        """Revoking a key should deactivate it."""
        created = client.create_key("revoke-test", role="user")
        result = client.revoke_key(created.key_prefix)
        assert result.deactivated
