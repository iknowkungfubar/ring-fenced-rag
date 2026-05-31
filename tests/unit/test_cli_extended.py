"""Extended CLI tests — more command paths via mocked client."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

from click.testing import CliRunner

from rfr.api.schemas import (
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
    QueryResponse,
    SourceInfo,
    SourceListResponse,
    TokenUsage,
)
from rfr.cli import cli


class _RichMockClient:
    """Mock client returning rich data for testing complex CLI output."""

    def health(self) -> HealthResponse:
        return HealthResponse(
            status="ok",
            version="1.0.0a1",
            components={
                "database": "connected",
                "redis": "connected",
                "llm": "configured",
            },
            uptime_seconds=3600.0,
        )

    def query(self, question: str, top_k: int = 3) -> QueryResponse:
        return QueryResponse(
            answer="To restart the Nginx reverse proxy, execute: systemctl restart nginx.",
            sources=[
                SourceInfo(
                    content="Restart Nginx with systemctl restart nginx",
                    metadata={"source": "nginx.md", "title": "Nginx Restart"},
                    relevance_score=0.92,
                ),
                SourceInfo(
                    content="Ensure you are on the management VPN",
                    metadata={"source": "vpn.md", "title": "VPN Guide"},
                    relevance_score=0.78,
                ),
            ],
            token_usage=TokenUsage(prompt_tokens=100, completion_tokens=20, total_tokens=120),
            latency_ms=350.0,
        )

    def ingest_directory(self, path: str, default_role: str = "user", glob_pattern: str = "**/*") -> IngestResponse:
        return IngestResponse(task_id="mock-task-id", status="completed", source=path)

    def ingest_file(self, path: str, allowed_roles: list[str] | None = None) -> IngestResponse:
        return IngestResponse(task_id="mock-task-id", status="completed", source=path)

    def get_ingestion_status(self, task_id: str) -> IngestStatusResponse:
        return IngestStatusResponse(
            task_id=task_id,
            status="completed",
            source="test",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            result={"num_added": 3, "num_updated": 0, "num_skipped": 0, "num_deleted": 0},
        )

    def create_key(self, name: str, role: str = "user") -> CreateKeyResponse:
        return CreateKeyResponse(
            key="rfr_mockkey1234567890abcdef1234567890abcdef1234",
            key_prefix="rfr_mockke",
            name=name,
            role=role,
            created_at=datetime.now(timezone.utc),
        )

    def list_keys(self) -> KeyListResponse:
        return KeyListResponse(
            keys=[
                KeyInfo(
                    prefix="rfr_abc123",
                    name="test-key",
                    role="admin",
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    last_used_at=datetime.now(timezone.utc),
                ),
                KeyInfo(
                    prefix="rfr_def456",
                    name="readonly-key",
                    role="user",
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    last_used_at=None,
                ),
            ],
        )

    def revoke_key(self, prefix: str) -> DeactivateKeyResponse:
        return DeactivateKeyResponse(deactivated=True, prefix=prefix)

    def list_documents(self, source: str | None = None, limit: int = 20, offset: int = 0) -> DocumentListResponse:
        return DocumentListResponse(
            items=[
                DocumentInfo(
                    doc_id="NG-001",
                    source="confluence/nginx_guide",
                    title="Nginx Guide",
                    chunk_count=3,
                    allowed_roles=["senior_engineer"],
                    ingested_at=datetime.now(timezone.utc),
                ),
                DocumentInfo(
                    doc_id="WF-001",
                    source="confluence/wifi",
                    title="Office WiFi",
                    chunk_count=1,
                    allowed_roles=["senior_engineer", "junior_engineer"],
                    ingested_at=datetime.now(timezone.utc),
                ),
            ],
            total=2,
            limit=limit,
            offset=offset,
        )

    def delete_document(self, doc_id: str) -> DeleteDocumentResponse:
        return DeleteDocumentResponse(deleted=True, doc_id=doc_id, chunks_removed=3)

    def list_sources(self) -> SourceListResponse:
        return SourceListResponse(sources=["confluence/nginx_guide", "confluence/wifi"])

    def reindex(self) -> dict:
        return {"task_id": "reindex-123", "status": "pending", "message": "Reindex started."}

    def close(self) -> None:
        pass


class TestCliExtended:
    """Extended CLI tests with rich mock data."""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    def _invoke(self, args: list[str]) -> "Result":  # type: ignore[name-defined]
        with patch("rfr.cli.client.RfrClient", return_value=_RichMockClient()):
            return self.runner.invoke(cli, args)

    def test_docs_list(self) -> None:
        """docs list should show indexed documents."""
        result = self._invoke(["docs", "list"])
        assert result.exit_code == 0, result.output
        assert "NG-001" in result.output
        assert "WF-001" in result.output
        assert "senior_engineer" in result.output

    def test_docs_delete(self) -> None:
        """docs delete should accept a document ID."""
        result = self._invoke(["docs", "delete", "NG-001"])
        assert result.exit_code == 0, result.output
        assert "NG-001" in result.output

    def test_keys_revoke(self) -> None:
        """keys revoke should deactivate a key."""
        result = self._invoke(["keys", "revoke", "rfr_abc123"])
        assert result.exit_code == 0, result.output
        assert "deactivated" in result.output.lower()

    def test_config_set(self) -> None:
        """config set should update a config value."""
        result = self.runner.invoke(cli, ["config", "set", "llm.model", "test-model"])
        assert result.exit_code == 0
        assert "test-model" in result.output

    def test_down_command(self) -> None:
        """down command should try to stop services."""
        result = self.runner.invoke(cli, ["down"])
        # Without docker-compose.yml, shows a message but exits 0
        assert "docker-compose" in result.output or result.exit_code == 0

    def test_logs_command(self) -> None:
        """logs command should be invocable."""
        result = self.runner.invoke(cli, ["logs"])
        # Exits cleanly even without docker-compose.yml
        assert result.exit_code == 0
