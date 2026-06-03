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


class TestRateLimitingMiddleware:
    """Rate limiting middleware must enforce per-IP limits."""

    def test_normal_request_passes(self) -> None:
        """A single request under the limit should return 200."""
        client = TestClient(create_app())
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_exceeding_rate_limit_returns_429(self) -> None:
        """Requests exceeding the rate limit should get 429."""
        os.environ["RFR_SERVER__RATE_LIMIT_PER_MINUTE"] = "5"
        app = create_app()
        del os.environ["RFR_SERVER__RATE_LIMIT_PER_MINUTE"]

        client = TestClient(app)
        # Exhaust the limit of 5
        responses = [client.get("/api/v1/health") for _ in range(10)]
        statuses = [r.status_code for r in responses]
        # At least one should be 429
        assert 429 in statuses, f"Expected at least one 429, got {statuses}"
        # The first request should be 200
        assert responses[0].status_code == 200

    def test_rate_limit_disabled_passes_all(self) -> None:
        """When rate_limit_per_minute is 0, all requests must pass."""
        os.environ["RFR_SERVER__RATE_LIMIT_PER_MINUTE"] = "0"
        app = create_app()
        del os.environ["RFR_SERVER__RATE_LIMIT_PER_MINUTE"]

        client = TestClient(app)
        for _ in range(100):
            response = client.get("/api/v1/health")
            assert response.status_code == 200, (
                f"Expected 200 with limit disabled, got {response.status_code}"
            )

    def test_multiple_ips_get_separate_buckets(self) -> None:
        """Different IPs must have independent rate limit counters."""
        os.environ["RFR_SERVER__RATE_LIMIT_PER_MINUTE"] = "3"
        app = create_app()
        del os.environ["RFR_SERVER__RATE_LIMIT_PER_MINUTE"]

        # Create two clients with different ASGI client addresses
        client_a = TestClient(app, client=("10.0.0.1", 50000))
        client_b = TestClient(app, client=("10.0.0.2", 50001))

        # Exhaust limit for client_a
        for _ in range(3):
            resp = client_a.get("/api/v1/health")
            assert resp.status_code == 200

        # client_a's next request should be blocked
        resp = client_a.get("/api/v1/health")
        assert resp.status_code == 429

        # client_b (different IP) should still pass
        resp = client_b.get("/api/v1/health")
        assert resp.status_code == 200
