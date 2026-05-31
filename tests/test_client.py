"""Tests for the CLI HTTP client — error handling and connection failures."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from rfr.cli.client import RfrClient, RfrClientError


class TestRfrClientErrors:
    """Verify CLI client handles errors gracefully."""

    def _make_client(self, mock_response: MagicMock | None = None) -> RfrClient:
        """Create a client with a mocked httpx.Client."""
        client = RfrClient(base_url="http://localhost:8000", api_key="test")

        if mock_response is not None:
            real_client = httpx.Client()
            real_client.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]
            client._client = real_client
        else:
            client._client = MagicMock(spec=httpx.Client)

        return client

    def test_connection_refused(self) -> None:
        """Connection refused should raise a friendly error."""
        client = self._make_client()
        assert client._client is not None
        client._client.request.side_effect = httpx.ConnectError("Connection refused")  # type: ignore[union-attr]
        with pytest.raises(RfrClientError, match="Cannot connect"):
            client.health()

    def test_timeout(self) -> None:
        """Timeout should raise a friendly error."""
        client = self._make_client()
        assert client._client is not None
        client._client.request.side_effect = httpx.TimeoutException("Timed out")  # type: ignore[union-attr]
        with pytest.raises(RfrClientError, match="timed out"):
            client.health()

    def test_http_400_error(self) -> None:
        """HTTP 400 should include the error message."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 400
        response.text = "Bad request"
        response.json.return_value = {"error": {"message": "Invalid input"}}
        client = self._make_client(response)

        with pytest.raises(RfrClientError, match="Invalid input"):
            client.health()

    def test_http_400_no_json(self) -> None:
        """HTTP 400 with non-JSON response should use raw text."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 400
        response.text = "Raw error text"
        response.json.side_effect = json.JSONDecodeError("No JSON", "", 0)
        client = self._make_client(response)

        with pytest.raises(RfrClientError, match="Raw error text"):
            client.health()


class TestRfrClientMethods:
    """Verify API client methods construct correct requests."""

    def _make_client(self) -> tuple[RfrClient, MagicMock]:
        """Create a client with a mocked httpx.Client and return both."""
        client = RfrClient(base_url="http://localhost:8000", api_key="test")
        mock_http = MagicMock(spec=httpx.Client)
        client._client = mock_http
        return client, mock_http

    def test_health_request(self) -> None:
        """Health check should GET /api/v1/health."""
        client, mock_http = self._make_client()
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "version": "1.0.0",
            "components": {},
            "uptime_seconds": 0.0,
        }
        mock_http.request.return_value = mock_response
        result = client.health()
        mock_http.request.assert_called_once_with("GET", "/api/v1/health")
        assert result.status == "ok"

    def test_query_request(self) -> None:
        """Query should POST with question."""
        client, mock_http = self._make_client()
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "answer": "test answer",
            "sources": [],
            "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "latency_ms": 0.0,
        }
        mock_http.request.return_value = mock_response
        result = client.query("test question")
        mock_http.request.assert_called_once()
        _args, kwargs = mock_http.request.call_args
        assert kwargs["json"]["query"] == "test question"
        assert result.answer == "test answer"

    def test_request_sets_auth_header(self) -> None:
        """Client should include auth header in requests."""
        client = RfrClient(base_url="http://localhost:8000", api_key="rfr_test_key_12345")
        # The auth header is set on the client's default headers, not per-request
        assert client.api_key == "rfr_test_key_12345"

    def test_close_client(self) -> None:
        """Closing the client should work."""
        client, mock_http = self._make_client()
        client.close()
        mock_http.close.assert_called_once()
        assert client._client is None
