"""Tests for FastAPI middleware: security headers and rate limiting."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from rfr.api.app import create_app


@pytest.fixture(autouse=True)
def _middleware_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure standalone mode and disable auth so route handlers don't hit DB."""
    monkeypatch.setenv("RFR_STANDALONE", "true")
    monkeypatch.setenv("RFR_AUTH__ENABLED", "false")


def _make_app_rate_limited(limit: int = 60) -> TestClient:
    """Create a TestClient with rate limiting enabled."""
    with patch("rfr.api.app.AppConfig") as mock_cfg:
        cfg = mock_cfg.return_value
        cfg.server.rate_limit_per_minute = limit
        cfg.server.cors_origins = ["*"]
        cfg.auth.enabled = False
        cfg.ingestion.default_role = "user"
        cfg.llm.provider = "none"
        cfg.embedding.model = "all-MiniLM-L6-v2"

        app = create_app()
        return TestClient(app)


# ── Issue #20: Security Middleware (CSP, X-Content-Type-Options) ──


class TestSecurityHeadersMiddleware:
    """Every response must include security headers (defence in depth)."""

    SECURITY_HEADERS = {
        "Content-Security-Policy": (
            "default-src 'self'; script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; font-src 'self'; "
            "connect-src 'self'; form-action 'self'; "
            "base-uri 'self'; frame-ancestors 'none';"
        ),
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
    }

    def test_security_headers_present_on_health(self) -> None:
        """Health endpoint should include all security headers."""
        client = _make_app_rate_limited(limit=0)
        response = client.get("/api/v1/health")
        for header, expected_value in self.SECURITY_HEADERS.items():
            assert header in response.headers, f"Missing security header: {header}"
            assert response.headers[header] == expected_value, (
                f"Security header {header} has unexpected value: "
                f"{response.headers[header]!r} != {expected_value!r}"
            )

    def test_security_headers_present_on_404(self) -> None:
        """Even 404 responses should include security headers."""
        client = _make_app_rate_limited(limit=0)
        response = client.get("/nonexistent/route")
        assert response.status_code == 404
        for header in self.SECURITY_HEADERS:
            assert header in response.headers, f"Missing security header on 404: {header}"

    def test_security_headers_present_on_error(self) -> None:
        """Error responses should also carry security headers."""
        client = _make_app_rate_limited(limit=0)
        # A request that triggers an auth gate (401) since auth is enabled by default
        response = client.post("/api/v1/query", json={"query": "test"})
        for header in self.SECURITY_HEADERS:
            assert header in response.headers, f"Missing security header on error: {header}"

    def test_csp_prevents_scripts_from_foreign_origins(self) -> None:
        """CSP default-src 'self' blocks inline/foreign scripts."""
        client = _make_app_rate_limited(limit=0)
        response = client.get("/api/v1/health")
        csp = response.headers.get("Content-Security-Policy", "")
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "unsafe-inline" in csp  # allowed for styles only

    def test_x_content_type_options_nosniff(self) -> None:
        """X-Content-Type-Options must be 'nosniff' to prevent MIME sniffing."""
        client = _make_app_rate_limited(limit=0)
        response = client.get("/api/v1/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options_deny(self) -> None:
        """X-Frame-Options must be 'DENY' to prevent clickjacking."""
        client = _make_app_rate_limited(limit=0)
        response = client.get("/api/v1/health")
        assert response.headers.get("X-Frame-Options") == "DENY"


# ── Issue #19: Rate Limiting Middleware ──


class TestRateLimitMiddleware:
    """Rate limiting should key by API key when available, fall back to IP."""

    def test_rate_limit_not_applied_when_disabled(self) -> None:
        """When rate_limit_per_minute=0, no rate limiting should occur."""
        client = _make_app_rate_limited(limit=0)

        for _ in range(10):
            response = client.post("/api/v1/query", json={"query": "test"})
            # Should NOT get 429 (rate limit) — auth is disabled so gets 503/500
            assert response.status_code != 429

    def test_rate_limit_applies_at_threshold(self) -> None:
        """When rate_limit_per_minute=3, the 4th request in the window gets 429."""
        client = _make_app_rate_limited(limit=3)

        for _ in range(3):
            resp = client.post("/api/v1/query", json={"query": "test"})
            assert resp.status_code != 429, "Request within limit should not be rate limited"

        # 4th request — over limit
        resp = client.post("/api/v1/query", json={"query": "test"})
        assert resp.status_code == 429, f"Expected 429 rate limit, got {resp.status_code}"
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "RATE_LIMITED"

    def test_rate_limit_keys_by_api_key_not_ip(self) -> None:
        """Rate limiting keys by API key, so two requests with same key share
        the limit even from different client states.
        """
        client = _make_app_rate_limited(limit=2)
        shared_token = "Bearer rfr_testsharedkey1234567890abcdef"

        # 1st request with the key
        resp = client.post(
            "/api/v1/query",
            json={"query": "test"},
            headers={"Authorization": shared_token},
        )
        assert resp.status_code != 429

        # 2nd request with the same key
        resp = client.post(
            "/api/v1/query",
            json={"query": "test"},
            headers={"Authorization": shared_token},
        )
        assert resp.status_code != 429

        # 3rd request with the same key — should hit limit
        resp = client.post(
            "/api/v1/query",
            json={"query": "test"},
            headers={"Authorization": shared_token},
        )
        assert resp.status_code == 429, (
            f"Third request with same key should be rate limited, got {resp.status_code}"
        )

    def test_different_api_keys_have_separate_limits(self) -> None:
        """Two different API keys should have independent rate limit counters."""
        client = _make_app_rate_limited(limit=2)

        key_a = "Bearer rfr_key_a_abc123"
        key_b = "Bearer rfr_key_b_def456"

        # Exhaust key A's limit
        for _ in range(2):
            resp = client.post(
                "/api/v1/query",
                json={"query": "test"},
                headers={"Authorization": key_a},
            )
            assert resp.status_code != 429

        # Key A should now be limited
        resp = client.post(
            "/api/v1/query",
            json={"query": "test"},
            headers={"Authorization": key_a},
        )
        assert resp.status_code == 429

        # Key B should still have its full quota
        resp = client.post(
            "/api/v1/query",
            json={"query": "test"},
            headers={"Authorization": key_b},
        )
        assert resp.status_code != 429, (
            f"Key B should not be rate limited by key A's usage, got {resp.status_code}"
        )

    def test_no_auth_falls_back_to_ip(self) -> None:
        """Without an API key, rate limiting should fall back to IP address."""
        client = _make_app_rate_limited(limit=2)

        for _ in range(2):
            resp = client.post("/api/v1/query", json={"query": "test"})
            assert resp.status_code != 429

        # 3rd request without auth — IP should be throttled
        resp = client.post("/api/v1/query", json={"query": "test"})
        assert resp.status_code == 429

    def test_rate_limit_logs_warning_on_hit(self, caplog: pytest.LogCaptureFixture) -> None:
        """When rate limit is hit, a warning should be logged."""
        caplog.set_level(os.environ.get("RFR_LOG_LEVEL", "WARNING"), logger="rfr.api.rate_limit")

        client = _make_app_rate_limited(limit=1)

        # Use up the limit
        resp = client.post("/api/v1/query", json={"query": "test"})
        assert resp.status_code != 429

        # Hit the limit
        resp = client.post("/api/v1/query", json={"query": "test"})
        assert resp.status_code == 429

        # Verify log contains the warning
        assert any("Rate limit hit" in record.getMessage() for record in caplog.records), (
            "Expected 'Rate limit hit' in log records"
        )
