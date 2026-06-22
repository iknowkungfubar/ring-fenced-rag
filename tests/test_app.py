"""Tests for the API application factory."""

from __future__ import annotations

from rfr.api.app import create_app


class TestAppFactory:
    """Verify the FastAPI app factory creates a valid application."""

    def test_create_app_returns_app(self) -> None:
        """create_app should return a FastAPI application."""
        app = create_app()
        assert app is not None
        assert app.title == "Ring-Fenced RAG"

    def test_app_has_routes(self) -> None:
        """The app should have registered routes."""
        app = create_app()
        # Flatten routes — Starlette uses _IncludedRouter for APIRouter includes
        route_paths: list[str] = []
        for r in app.routes:
            path = getattr(r, "path", None)
            if path is not None:
                route_paths.append(path)
            # _IncludedRouter wraps the original APIRouter
            original = getattr(r, "original_router", None)
            if original is not None:
                prefix = getattr(r, "include_context", None)
                prefix = prefix.prefix if prefix is not None else ""
                for sub in getattr(original, "routes", []):
                    sub_path = getattr(sub, "path", None)
                    if sub_path is not None:
                        route_paths.append(prefix + sub_path)
        assert "/api/v1/health" in route_paths
        assert "/api/v1/query" in route_paths
        assert "/api/v1/ingest" in route_paths
        assert "/api/v1/auth/keys" in route_paths
        assert "/api/v1/documents" in route_paths

    def test_app_has_openapi(self) -> None:
        """The app should have OpenAPI docs enabled."""
        app = create_app()
        assert app.openapi_url == "/openapi.json"

    def test_app_has_docs(self) -> None:
        """The app should have Swagger docs enabled."""
        app = create_app()
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"

    def test_app_version_matches(self) -> None:
        """The app version should match the package version."""
        from rfr import __version__

        app = create_app()
        assert app.version == __version__
