"""Extended tests for CLI client — all API methods and edge cases."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from rfr.cli.client import RfrClient, RfrClientError


def _make_client() -> tuple[RfrClient, MagicMock]:
    """Create a client with mocked httpx.Client."""
    client = RfrClient(base_url="http://localhost:8000", api_key="test")
    mock_http = MagicMock(spec=httpx.Client)
    client._client = mock_http
    return client, mock_http


def _make_response(status_code: int = 200, json_data: dict | None = None) -> MagicMock:
    """Create a mock HTTP response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.text = str(json_data) if json_data else "{}"
    response.json.return_value = json_data or {}
    return response


class TestClientIngestionMethods:
    """Verify client ingestion methods."""

    def test_ingest_directory(self) -> None:
        """ingest_directory should POST with directory type."""
        client, mock = _make_client()
        mock.request.return_value = _make_response(
            202,
            {
                "task_id": "task-123",
                "status": "pending",
                "source": "/path",
            },
        )
        result = client.ingest_directory("/path", default_role="admin")
        assert result.task_id == "task-123"
        call_args = mock.request.call_args
        assert call_args[0][1] == "/api/v1/ingest"
        assert call_args[1]["json"]["type"] == "directory"
        assert call_args[1]["json"]["path"] == "/path"

    def test_ingest_file(self) -> None:
        """ingest_file should POST with file type."""
        client, mock = _make_client()
        mock.request.return_value = _make_response(
            202,
            {
                "task_id": "task-456",
                "status": "pending",
                "source": "/file.md",
            },
        )
        result = client.ingest_file("/file.md", allowed_roles=["admin"])
        assert result.task_id == "task-456"
        call_args = mock.request.call_args
        assert call_args[1]["json"]["type"] == "file"
        assert call_args[1]["json"]["allowed_roles"] == ["admin"]

    def test_ingest_file_default_role(self) -> None:
        """ingest_file without roles should default to ['user']."""
        client, mock = _make_client()
        mock.request.return_value = _make_response(
            202,
            {
                "task_id": "t",
                "status": "pending",
                "source": "/f.md",
            },
        )
        client.ingest_file("/f.md")
        call_args = mock.request.call_args
        assert call_args[1]["json"]["allowed_roles"] == ["user"]

    def test_get_ingestion_status(self) -> None:
        """get_ingestion_status should GET by task ID."""
        client, mock = _make_client()
        mock.request.return_value = _make_response(
            200,
            {
                "task_id": "task-123",
                "status": "completed",
                "source": "/path",
                "result": {"num_added": 5},
            },
        )
        result = client.get_ingestion_status("task-123")
        assert result.status == "completed"
        assert result.result["num_added"] == 5
        mock.request.assert_called_with("GET", "/api/v1/ingest/task-123")


class TestClientDocumentMethods:
    """Verify client document methods."""

    def test_list_documents(self) -> None:
        """list_documents should GET with params."""
        client, mock = _make_client()
        mock.request.return_value = _make_response(
            200,
            {
                "items": [],
                "total": 0,
                "limit": 20,
                "offset": 0,
            },
        )
        result = client.list_documents(source="confluence")
        assert result.total == 0
        mock.request.assert_called_once()
        _args, kwargs = mock.request.call_args
        assert kwargs["params"]["source"] == "confluence"

    def test_delete_document(self) -> None:
        """delete_document should DELETE by doc_id."""
        client, mock = _make_client()
        mock.request.return_value = _make_response(
            200,
            {
                "deleted": True,
                "doc_id": "NG-001",
                "chunks_removed": 3,
            },
        )
        result = client.delete_document("NG-001")
        assert result.deleted
        assert result.chunks_removed == 3

    def test_list_sources(self) -> None:
        """list_sources should GET sources endpoint."""
        client, mock = _make_client()
        mock.request.return_value = _make_response(
            200,
            {
                "sources": ["confluence/doc1", "confluence/doc2"],
            },
        )
        result = client.list_sources()
        assert len(result.sources) == 2

    def test_reindex(self) -> None:
        """reindex should POST admin/reindex."""
        client, mock = _make_client()
        mock.request.return_value = _make_response(
            202,
            {
                "task_id": "reindex-1",
                "status": "pending",
            },
        )
        result = client.reindex()
        assert result["task_id"] == "reindex-1"
        mock.request.assert_called_with("POST", "/api/v1/admin/reindex")


class TestClientKeyMethods:
    """Verify client API key methods."""

    def test_create_key(self) -> None:
        """create_key should POST with name and role."""
        client, mock = _make_client()
        mock.request.return_value = _make_response(
            201,
            {
                "key": "rfr_newkey123",
                "key_prefix": "rfr_newkey",
                "name": "test",
                "role": "admin",
                "created_at": "2025-01-01T00:00:00Z",
            },
        )
        result = client.create_key("test", role="admin")
        assert result.key == "rfr_newkey123"
        assert result.role == "admin"

    def test_list_keys(self) -> None:
        """list_keys should GET keys endpoint."""
        client, mock = _make_client()
        mock.request.return_value = _make_response(
            200,
            {
                "keys": [
                    {
                        "prefix": "rfr_abc",
                        "name": "test",
                        "role": "user",
                        "is_active": True,
                        "created_at": "2025-01-01T00:00:00Z",
                    }
                ],
            },
        )
        result = client.list_keys()
        assert len(result.keys) == 1
        assert result.keys[0].prefix == "rfr_abc"

    def test_revoke_key(self) -> None:
        """revoke_key should DELETE by prefix."""
        client, mock = _make_client()
        mock.request.return_value = _make_response(
            200,
            {
                "deactivated": True,
                "prefix": "rfr_abc",
            },
        )
        result = client.revoke_key("rfr_abc")
        assert result.deactivated
        mock.request.assert_called_with("DELETE", "/api/v1/auth/keys/rfr_abc")


class TestClientEdgeCases:
    """Verify edge cases in the client."""

    def test_client_close(self) -> None:
        """Closing should release the HTTP client."""
        client, mock = _make_client()
        client.close()
        mock.close.assert_called_once()
        assert client._client is None

    def test_client_double_close(self) -> None:
        """Double close should not error."""
        client, mock = _make_client()
        client.close()
        client.close()  # second close should be no-op
        assert client._client is None

    def test_client_base_url_trailing_slash(self) -> None:
        """Trailing slash on base_url should be stripped."""
        client = RfrClient(base_url="http://localhost:8000/", api_key="test")
        assert not client.base_url.endswith("/")

    def test_client_default_api_key(self) -> None:
        """Client with no API key should not fail."""
        client = RfrClient(base_url="http://localhost:8000")
        assert client.api_key is None
        # Auth header just won't be set

    def test_request_json_decode_error(self) -> None:
        """JSON decode error in _request should raise RfrClientError."""
        client, mock = _make_client()
        response = MagicMock(spec=httpx.Response)
        response.status_code = 500
        response.text = "Internal Server Error"
        response.json.side_effect = ValueError("No JSON")
        mock.request.return_value = response
        with pytest.raises(RfrClientError, match="Internal Server Error"):
            client.health()

    def test_ingest_file_no_roles(self) -> None:
        """ingest_file with None roles should use default."""
        client, mock = _make_client()
        mock.request.return_value = _make_response(
            202,
            {
                "task_id": "t",
                "status": "pending",
                "source": "/f.md",
            },
        )
        result = client.ingest_file("/f.md", allowed_roles=None)
        assert result.task_id == "t"
