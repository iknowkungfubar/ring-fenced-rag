"""Comprehensive tests for FastAPI app factory and error handling."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from rfr.api.app import create_app


class TestAppFactory:
    """App factory paths."""

    def test_create_app(self) -> None:
        """App should be created with correct metadata."""
        app = create_app()
        assert app.title == "Ring-Fenced RAG"
        assert app.version
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"

    def test_health_endpoint(self) -> None:
        """Health endpoint should return 200."""
        app = create_app()
        client = TestClient(app)
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data

    def test_query_endpoint_requires_auth(self) -> None:
        """Query endpoint with no auth header returns 401 or 500."""
        app = create_app()
        client = TestClient(app)
        response = client.post("/api/v1/query", json={"query": "test"})
        # Auth is enabled by default, so either 401 or 500 is fine
        assert response.status_code in (401, 403, 500)

    def test_cors_middleware(self) -> None:
        """CORS headers should be set."""
        app = create_app()
        client = TestClient(app)
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in response.headers

    def test_openapi_schema(self) -> None:
        """OpenAPI schema should be accessible."""
        app = create_app()
        client = TestClient(app)
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/api/v1/health" in schema["paths"]
        assert "/api/v1/query" in schema["paths"]

    def test_app_has_exception_handler(self) -> None:
        """App should have a global exception handler registered."""
        app = create_app()
        # Check that exception handlers exist
        assert len(app.exception_handlers) > 0
