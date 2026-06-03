"""HTTP API client for Ring-Fenced RAG.

Wraps all REST endpoints for use by the CLI and other consumers.
Handles auth header injection, error handling, and response parsing.
"""

from __future__ import annotations

import contextlib
import os
from pathlib import Path
from typing import Any

import httpx
from httpx import Client, Response

from rfr.api.schemas import (
    CreateKeyRequest,
    CreateKeyResponse,
    DeactivateKeyResponse,
    DeleteDocumentResponse,
    DocumentListResponse,
    HealthResponse,
    IngestResponse,
    IngestStatusResponse,
    KeyListResponse,
    QueryRequest,
    QueryResponse,
    SourceListResponse,
)


class RfrClientError(Exception):
    """Raised when the API client encounters an error."""


def _get_api_key() -> str | None:
    """Get the API key from the environment or config file."""
    key = os.environ.get("RFR_API_KEY")
    if key:
        return key
    # Check ~/.rfr/config.toml
    config_path = Path.home() / ".rfr" / "config.toml"
    if config_path.exists():
        import tomllib

        try:
            data = tomllib.loads(config_path.read_text())
            return data.get("api_key")
        except (tomllib.TOMLDecodeError, OSError, ValueError):
            pass
    return None


def _default_base_url() -> str:
    """Get the default API base URL from config or env."""
    return os.environ.get("RFR_API_URL", "http://localhost:8000")


class RfrClient:
    """HTTP client for the Ring-Fenced RAG API.

    Usage:
        client = RfrClient(base_url="http://localhost:8000", api_key="rfr_...")
        health = client.health()
        result = client.query("How do I restart Nginx?")
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the API client.

        Args:
            base_url: API base URL. Defaults to $RFR_API_URL or http://localhost:8000.
            api_key: API key for authentication. Defaults to $RFR_API_KEY or config file.
            timeout: Request timeout in seconds.

        """
        self.base_url = (base_url or _default_base_url()).rstrip("/")
        self.api_key = api_key or _get_api_key()
        self.timeout = timeout
        self._client: Client | None = None

    @property
    def client(self) -> Client:
        """Get or create the HTTP client session."""
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = Client(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
            )
        return self._client

    def _request(self, method: str, path: str, **kwargs: Any) -> Response:
        """Make an HTTP request and handle errors.

        Args:
            method: HTTP method.
            path: URL path (e.g., "/api/v1/query").
            **kwargs: Additional request arguments.

        Returns:
            HTTP response.

        Raises:
            RfrClientError: On connection or HTTP errors.

        """
        try:
            response = self.client.request(method, path, **kwargs)
            if response.status_code >= 400:
                detail = response.text
                with contextlib.suppress(ValueError, TypeError):
                    detail = response.json().get("error", {}).get("message", detail)
                raise RfrClientError(
                    f"API error ({response.status_code}): {detail}",
                )
            return response
        except httpx.ConnectError as e:
            raise RfrClientError(
                f"Cannot connect to {self.base_url}. Is the server running? "
                "Start with 'rfr up' or 'rfr standalone'."
            ) from e
        except httpx.TimeoutException as e:
            raise RfrClientError(f"Request timed out after {self.timeout}s") from e

    # ── Health ──

    def health(self) -> HealthResponse:
        """Check API server health.

        Returns:
            HealthResponse with component status.

        """
        response = self._request("GET", "/api/v1/health")
        return HealthResponse(**response.json())

    # ── Query ──

    def query(self, question: str, top_k: int = 3) -> QueryResponse:
        """Execute a RAG query.

        Args:
            question: The user's question.
            top_k: Number of documents to retrieve.

        Returns:
            QueryResponse with answer and sources.

        """
        body = QueryRequest(query=question, top_k=top_k)
        response = self._request("POST", "/api/v1/query", json=body.model_dump())
        return QueryResponse(**response.json())

    # ── Ingestion ──

    def ingest_directory(
        self,
        path: str,
        default_role: str = "user",
        glob_pattern: str = "**/*",
    ) -> IngestResponse:
        """Trigger ingestion from a directory.

        Args:
            path: Path to the directory.
            default_role: Default role for documents.
            glob_pattern: File glob pattern.

        Returns:
            IngestResponse with task_id.

        """
        body = {
            "type": "directory",
            "path": path,
            "default_role": default_role,
            "glob_pattern": glob_pattern,
        }
        response = self._request("POST", "/api/v1/ingest", json=body)
        return IngestResponse(**response.json())

    def ingest_file(self, path: str, allowed_roles: list[str] | None = None) -> IngestResponse:
        """Trigger ingestion from a single file.

        Args:
            path: Path to the file.
            allowed_roles: Roles allowed to access this document.

        Returns:
            IngestResponse with task_id.

        """
        body = {
            "type": "file",
            "path": path,
            "allowed_roles": allowed_roles or ["user"],
        }
        response = self._request("POST", "/api/v1/ingest", json=body)
        return IngestResponse(**response.json())

    def get_ingestion_status(self, task_id: str) -> IngestStatusResponse:
        """Poll ingestion task status.

        Args:
            task_id: Task ID from ingest response.

        Returns:
            IngestStatusResponse with current status.

        """
        response = self._request("GET", f"/api/v1/ingest/{task_id}")
        return IngestStatusResponse(**response.json())

    # ── Documents ──

    def list_documents(
        self, source: str | None = None, limit: int = 20, offset: int = 0
    ) -> DocumentListResponse:
        """List indexed documents.

        Args:
            source: Optional source filter.
            limit: Max items per page.
            offset: Pagination offset.

        Returns:
            DocumentListResponse with items.

        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if source:
            params["source"] = source
        response = self._request("GET", "/api/v1/documents", params=params)
        return DocumentListResponse(**response.json())

    def delete_document(self, doc_id: str) -> DeleteDocumentResponse:
        """Delete a document by its ID.

        Args:
            doc_id: Document ID to delete.

        Returns:
            DeleteDocumentResponse.

        """
        response = self._request("DELETE", f"/api/v1/documents/{doc_id}")
        return DeleteDocumentResponse(**response.json())

    def list_sources(self) -> SourceListResponse:
        """List distinct document sources.

        Returns:
            SourceListResponse.

        """
        response = self._request("GET", "/api/v1/documents/sources")
        return SourceListResponse(**response.json())

    # ── API Keys ──

    def create_key(self, name: str, role: str = "user") -> CreateKeyResponse:
        """Create a new API key.

        Args:
            name: Human-readable key name.
            role: Role to assign.

        Returns:
            CreateKeyResponse with the raw key (shown once).

        """
        body = CreateKeyRequest(name=name, role=role)
        response = self._request("POST", "/api/v1/auth/keys", json=body.model_dump())
        return CreateKeyResponse(**response.json())

    def list_keys(self) -> KeyListResponse:
        """List all API keys.

        Returns:
            KeyListResponse.

        """
        response = self._request("GET", "/api/v1/auth/keys")
        return KeyListResponse(**response.json())

    def revoke_key(self, prefix: str) -> DeactivateKeyResponse:
        """Revoke an API key by its prefix.

        Args:
            prefix: Key prefix to revoke.

        Returns:
            DeactivateKeyResponse.

        """
        response = self._request("DELETE", f"/api/v1/auth/keys/{prefix}")
        return DeactivateKeyResponse(**response.json())

    # ── Admin ──

    def reindex(self) -> dict[str, Any]:
        """Trigger full re-index.

        Returns:
            Response dict with task_id.

        """
        response = self._request("POST", "/api/v1/admin/reindex")
        return response.json()  # type: ignore[return-value]

    def close(self) -> None:
        """Close the HTTP client session."""
        if self._client is not None:
            self._client.close()
            self._client = None
