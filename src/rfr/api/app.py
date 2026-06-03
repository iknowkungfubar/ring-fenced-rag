"""FastAPI application factory for Ring-Fenced RAG.

Creates and configures the FastAPI app with:
- CORS middleware
- All route handlers
- Error handlers
- Lifecycle hooks (startup/shutdown)
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from rfr import __version__
from rfr.api.routes import router
from rfr.config import AppConfig


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.

    """
    cfg = AppConfig()

    app = FastAPI(
        title="Ring-Fenced RAG",
        description="Self-hosted, zero-trust RAG with role-based access control",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        contact={
            "name": "Ring-Fenced RAG",
            "url": "https://github.com/iknowkungfubar/ring-fenced-rag",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.server.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # CSP + security headers on every response (defence in depth)
    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
            "form-action 'self'; base-uri 'self'; frame-ancestors 'none';"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    # Rate limiting
    if cfg.server.rate_limit_per_minute > 0:
        import logging as _rate_logging

        _rate_requests: dict[str, list[float]] = defaultdict(list)
        _rate_logger = _rate_logging.getLogger("rfr.api.rate_limit")

        @app.middleware("http")
        async def rate_limit_middleware(request: Request, call_next):
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            window_start = now - 60.0

            # Prune old requests outside the 60-second window
            timestamps = _rate_requests[client_ip]
            _rate_requests[client_ip] = [t for t in timestamps if t > window_start]

            if len(_rate_requests[client_ip]) >= cfg.server.rate_limit_per_minute:
                _rate_logger.warning(
                    "Rate limit hit: ip=%s path=%s limit=%d/min",
                    client_ip,
                    request.url.path,
                    cfg.server.rate_limit_per_minute,
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMITED",
                            "message": f"Rate limit exceeded: max {cfg.server.rate_limit_per_minute} requests per minute",
                            "details": {},
                        },
                    },
                )

            _rate_requests[client_ip].append(now)
            return await call_next(request)

    # Register routers
    app.include_router(router)

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch unhandled exceptions and return a sanitized error."""
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred. Please try again.",
                    "details": {},
                },
            },
        )

    # Startup event
    @app.on_event("startup")
    async def startup() -> None:
        import logging

        logger = logging.getLogger(__name__)
        logger.info("Ring-Fenced RAG v%s starting...", __version__)

        # 🟢 Auth status check
        if not cfg.auth.enabled:
            logger.warning(
                "🔴 AUTH IS DISABLED! Set RFR_AUTH__ENABLED=true in production. "
                "Without authentication, any user can access all endpoints."
            )
        else:
            logger.info("✅ Authentication enabled")

        # Initialize database
        try:
            from rfr.models.database import init_db

            init_db()
            logger.info("Database initialized")
        except Exception as e:  # noqa: BLE001
            logger.warning("Database initialization skipped (will retry): %s", e)

    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown() -> None:
        import logging

        logger = logging.getLogger(__name__)
        logger.info("Ring-Fenced RAG shutting down...")

    return app
