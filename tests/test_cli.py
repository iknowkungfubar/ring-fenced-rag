from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

from click.testing import CliRunner, Result

from rfr.api.schemas import (
    CreateKeyResponse,
    DeactivateKeyResponse,
    DeleteDocumentResponse,
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


class _MockClient:
    """Mock API client that returns canned responses."""

    def health(self) -> HealthResponse:
        return HealthResponse(
            status="ok",
            version="1.0.0a1",
            components={"database": "connected", "redis": "connected", "llm": "configured"},
            uptime_seconds=3600.0,
        )

    def query(self, question: str, top_k: int = 3) -> QueryResponse:
        return QueryResponse(
            answer="To restart Nginx, run: systemctl restart nginx",
            sources=[
                SourceInfo(
                    content="Restart Nginx with systemctl",
                    metadata={"source": "nginx.md", "title": "Nginx Guide"},
                    relevance_score=0.92,
                ),
            ],
            token_usage=TokenUsage(prompt_tokens=100, completion_tokens=20, total_tokens=120),
            latency_ms=450.0,
        )

    def ingest_directory(self, path: str, default_role: str = "user", glob_pattern: str = "**/*") -> IngestResponse:  # noqa: ARG002
        return IngestResponse(task_id="mock-task-id", status="completed", source=path)

    def ingest_file(self, path: str, allowed_roles: list[str] | None = None) -> IngestResponse:  # noqa: ARG002
        return IngestResponse(task_id="mock-task-id", status="completed", source=path)

    def get_ingestion_status(self, task_id: str) -> IngestStatusResponse:  # noqa: ARG002
        return IngestStatusResponse(
            task_id="mock-task-id",
            status="completed",
            source="test",
            result={"num_added": 3, "num_updated": 0, "num_skipped": 0, "num_deleted": 0},
        )

    def create_key(self, name: str, role: str = "user") -> CreateKeyResponse:

        return CreateKeyResponse(
            key="rfr_mockkey1234567890abcdef1234567890abcdef1234",
            key_prefix="rfr_mockke",
            name=name,
            role=role,
            created_at=datetime.now(UTC),
        )

    def list_keys(self) -> KeyListResponse:

        return KeyListResponse(
            keys=[
                KeyInfo(
                    prefix="rfr_abc123",
                    name="test-key",
                    role="admin",
                    is_active=True,
                    created_at=datetime.now(UTC),
                    last_used_at=datetime.now(UTC),
                ),
            ],
        )

    def revoke_key(self, prefix: str) -> DeactivateKeyResponse:
        return DeactivateKeyResponse(deactivated=True, prefix=prefix)

    def list_documents(self, source: str | None = None, limit: int = 20, offset: int = 0) -> DocumentListResponse:  # noqa: ARG002
        return DocumentListResponse(items=[], total=0, limit=limit, offset=offset)

    def delete_document(self, doc_id: str) -> DeleteDocumentResponse:
        return DeleteDocumentResponse(deleted=True, doc_id=doc_id, chunks_removed=0)

    def list_sources(self) -> SourceListResponse:
        return SourceListResponse(sources=[])

    def close(self) -> None:
        pass


class TestCli:
    """Verify CLI commands register and produce expected output."""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    def _invoke(self, args: list[str]) -> "Result":
        """Invoke CLI with RfrClient mocked."""
        with patch("rfr.cli.client.RfrClient", return_value=_MockClient()):
            return self.runner.invoke(cli, args)

    def test_version(self) -> None:
        """--version should print the package version."""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0a1" in result.output

    def test_help(self) -> None:
        """--help should show command list."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "ring-fenced rag" in result.output.lower()

    def test_init(self) -> None:
        """Init command should succeed."""
        result = self.runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert "Initializing" in result.output

    def test_config_show(self) -> None:
        """Config show should print configuration table."""
        result = self.runner.invoke(cli, ["config", "show"])
        assert result.exit_code == 0
        assert "ollama" in result.output

    def test_query(self) -> None:
        """Query command should accept a question and use the API."""
        result = self._invoke(["query", "How do I restart Nginx?"])
        assert result.exit_code == 0, result.output
        assert "restart nginx" in result.output.lower()

    def test_ingest(self) -> None:
        """Ingest command should accept a path."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._invoke(["ingest", tmpdir])
            assert result.exit_code == 0, result.output
            assert "Ingesting" in result.output

    def test_keys_create(self) -> None:
        """Keys create should accept a name."""
        result = self._invoke(["keys", "create", "test-key"])
        assert result.exit_code == 0, result.output
        assert "test-key" in result.output

    def test_keys_list(self) -> None:
        """Keys list should show API keys."""
        result = self._invoke(["keys", "list"])
        assert result.exit_code == 0, result.output
        assert "test-key" in result.output

    def test_status(self) -> None:
        """Status should show component health."""
        result = self._invoke(["status"])
        assert result.exit_code == 0, result.output
        assert "connected" in result.output
