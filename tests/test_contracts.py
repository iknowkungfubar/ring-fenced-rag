"""Contract tests — verify API responses match the blueprint contracts from 05-API.md.

These tests verify the shape and content of API responses without requiring a running server.
They use the Pydantic models directly to validate serialization/deserialization.
"""

from __future__ import annotations

from datetime import UTC, datetime

from rfr.api.schemas import (
    CreateKeyRequest,
    CreateKeyResponse,
    DeactivateKeyResponse,
    DeleteDocumentResponse,
    DocumentInfo,
    DocumentListResponse,
    HealthResponse,
    IngestResponse,
    IngestStatusResponse,
    KeyInfo,
    KeyListResponse,
    QueryRequest,
    QueryResponse,
    SourceInfo,
    SourceListResponse,
    TokenUsage,
)


class TestContractHealthResponse:
    """Validate HealthResponse shape per blueprint."""

    def test_health_shape(self) -> None:
        """Health response should have status, version, components, uptime."""
        resp = HealthResponse()
        assert resp.status == "ok"
        assert resp.version
        assert isinstance(resp.components, dict)
        assert resp.uptime_seconds >= 0

    def test_health_serialization(self) -> None:
        """Health response should serialize to JSON correctly."""
        data = HealthResponse().model_dump()
        assert "status" in data
        assert "version" in data
        assert "components" in data
        assert "uptime_seconds" in data


class TestContractQueryResponse:
    """Validate QueryResponse shape per blueprint."""

    def test_query_full_response(self) -> None:
        """Full query response should match the API contract."""
        resp = QueryResponse(
            answer="To restart Nginx, run: systemctl restart nginx.",
            sources=[
                SourceInfo(
                    content="Restart Nginx with systemctl restart nginx",
                    metadata={"source": "nginx.md", "title": "Nginx Guide"},
                    relevance_score=0.92,
                ),
            ],
            token_usage=TokenUsage(prompt_tokens=100, completion_tokens=20, total_tokens=120),
            latency_ms=450.0,
        )
        data = resp.model_dump()
        assert "answer" in data
        assert "sources" in data
        assert len(data["sources"]) == 1
        assert data["sources"][0]["relevance_score"] == 0.92
        assert data["token_usage"]["total_tokens"] == 120
        assert data["latency_ms"] == 450.0

    def test_query_empty_sources(self) -> None:
        """Query response with empty sources should still be valid."""
        resp = QueryResponse(answer="No results found.")
        data = resp.model_dump()
        assert data["sources"] == []
        assert data["token_usage"]["total_tokens"] == 0

    def test_query_request_validation(self) -> None:
        """QueryRequest should validate query length."""
        QueryRequest(query="valid query")
        import pytest

        with pytest.raises(Exception):
            QueryRequest(query="", top_k=3)


class TestContractIngestResponse:
    """Validate ingestion response shapes per blueprint."""

    def test_ingest_trigger_response(self) -> None:
        """POST /ingest should return 202 with task_id."""
        resp = IngestResponse(task_id="uuid-here", status="pending", source="test/docs")
        data = resp.model_dump()
        assert data["task_id"] == "uuid-here"
        assert data["status"] == "pending"

    def test_ingest_status_response(self) -> None:
        """GET /ingest/{id} should return status with optional result."""
        now = datetime.now(UTC)
        resp = IngestStatusResponse(
            task_id="uuid-here",
            status="completed",
            source="test/docs",
            started_at=now,
            completed_at=now,
            result={"num_added": 3, "num_updated": 0, "num_skipped": 0, "num_deleted": 0},
        )
        data = resp.model_dump()
        assert data["status"] == "completed"
        assert data["result"]["num_added"] == 3


class TestContractDocumentResponse:
    """Validate document response shapes per blueprint."""

    def test_document_list_response(self) -> None:
        """GET /documents should return paginated list."""
        resp = DocumentListResponse(
            items=[
                DocumentInfo(
                    doc_id="NG-001",
                    source="confluence/nginx_guide",
                    title="Nginx Guide",
                    chunk_count=3,
                    allowed_roles=["senior_engineer"],
                ),
            ],
            total=1,
            limit=20,
            offset=0,
        )
        data = resp.model_dump()
        assert data["total"] == 1
        assert data["items"][0]["doc_id"] == "NG-001"
        assert data["items"][0]["chunk_count"] == 3

    def test_delete_document_response(self) -> None:
        """DELETE /documents/{id} should return deletion confirmation."""
        resp = DeleteDocumentResponse(deleted=True, doc_id="NG-001", chunks_removed=3)
        data = resp.model_dump()
        assert data["deleted"] is True
        assert data["chunks_removed"] == 3

    def test_source_list_response(self) -> None:
        """GET /documents/sources should return source list."""
        resp = SourceListResponse(sources=["confluence/nginx_guide", "confluence/office_wifi"])
        data = resp.model_dump()
        assert len(data["sources"]) == 2


class TestContractAuthResponse:
    """Validate auth response shapes per blueprint."""

    def test_create_key_response(self) -> None:
        """POST /auth/keys should return raw key (shown once)."""
        resp = CreateKeyResponse(
            key="rfr_a1b2c3d4e5f6...",
            key_prefix="rfr_a1b2",
            name="dev-cli-key",
            role="senior_engineer",
            created_at=datetime.now(UTC),
        )
        data = resp.model_dump()
        assert data["key"].startswith("rfr_")
        assert data["key_prefix"] == "rfr_a1b2"

    def test_create_key_request_validation(self) -> None:
        """CreateKeyRequest should validate name and role."""
        CreateKeyRequest(name="test", role="admin")
        import pytest

        with pytest.raises(Exception):
            CreateKeyRequest(name="", role="admin")

    def test_key_list_response(self) -> None:
        """GET /auth/keys should return key list (no raw keys)."""
        resp = KeyListResponse(
            keys=[
                KeyInfo(
                    prefix="rfr_a1b2",
                    name="dev-cli-key",
                    role="admin",
                    is_active=True,
                    created_at=datetime.now(UTC),
                ),
            ],
        )
        data = resp.model_dump()
        assert len(data["keys"]) == 1
        assert "key_hash" not in data["keys"][0]  # Hashes never exposed

    def test_deactivate_key_response(self) -> None:
        """DELETE /auth/keys/{prefix} should confirm deactivation."""
        resp = DeactivateKeyResponse(deactivated=True, prefix="rfr_a1b2")
        data = resp.model_dump()
        assert data["deactivated"] is True
