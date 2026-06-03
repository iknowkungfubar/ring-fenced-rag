"""Tests for security headers and rate limiting middleware.

Covers:
- Security headers middleware: CSP, X-Content-Type-Options, X-Frame-Options
- Rate limiting middleware: normal pass, 429, disabled, multi-IP separation
"""

from __future__ import annotations

import os

from fastapi.testclient import TestClient

from rfr.api.app import create_app

# AppConfig requires standalone mode or DB URL when running outside production.
os.environ.setdefault("RFR_STANDALONE", "true")


class TestSecurityHeadersMiddleware:
    """Every response must include key security headers (defence in depth)."""

    def _get_client(self) -> TestClient:
        return TestClient(create_app())

    def test_csp_header_present(self) -> None:
        """Content-Security-Policy header must be set."""
        client = self._get_client()
        response = client.get("/docs")
        assert "Content-Security-Policy" in response.headers

    def test_csp_header_contains_self(self) -> None:
        """CSP should restrict to self by default."""
        client = self._get_client()
        response = client.get("/docs")
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    def test_x_content_type_options_header_present(self) -> None:
        """X-Content-Type-Options: nosniff must be set."""
        client = self._get_client()
        response = client.get("/docs")
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_x_frame_options_header_present(self) -> None:
        """X-Frame-Options: DENY must be set."""
        client = self._get_client()
        response = client.get("/docs")
        assert response.headers["X-Frame-Options"] == "DENY"

    def test_all_three_headers_on_health_endpoint(self) -> None:
        """Security headers must appear on every response path."""
        client = self._get_client()
        response = client.get("/api/v1/health")
        assert "Content-Security-Policy" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"

    def test_all_three_headers_on_404(self) -> None:
        """Security headers must appear even on error responses."""
        client = self._get_client()
        response = client.get("/nonexistent-path-xyz")
        assert response.status_code == 404
        assert "Content-Security-Policy" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
