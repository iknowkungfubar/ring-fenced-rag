"""FastAPI application factory for Ring-Fenced RAG.

Creates and configures the FastAPI app with:
- CORS middleware
- All route handlers
- Error handlers
- Lifecycle hooks (startup/shutdown)
"""

from __future__ import annotations

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
        # Initialize database
        try:
            from rfr.models.database import init_db

            init_db()
            logger.info("Database initialized")
        except Exception as e:
            logger.warning("Database initialization skipped (will retry): %s", e)

    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown() -> None:
        import logging

        logger = logging.getLogger(__name__)
        logger.info("Ring-Fenced RAG shutting down...")

    return app
