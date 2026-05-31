"""Database session management and engine setup for Ring-Fenced RAG."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from rfr.config import AppConfig
from rfr.models.orm import Base

# Global engine and session factory — initialized once
_engine: Any = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine(db_url: str | None = None, **kwargs: Any) -> Any:  # noqa: ANN401
    """Get or create the SQLAlchemy engine.

    Args:
        db_url: Database URL. If None, uses the default from config.
        **kwargs: Additional engine arguments.

    Returns:
        SQLAlchemy Engine instance.
    """
    global _engine
    if _engine is None:
        url = db_url or AppConfig().database.url
        if db_url:
            # Explicit URL → no default pool config (handles SQLite etc.)
            _engine = create_engine(url, **kwargs)
        else:
            cfg = AppConfig().database
            _engine = create_engine(
                url,
                pool_size=cfg.pool_size,
                max_overflow=cfg.max_overflow,
                echo=cfg.echo,
                **kwargs,
            )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Get or create the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _SessionLocal


@contextmanager
def create_session() -> Generator[Session, None, None]:
    """Create a new database session.

    Yields:
        SQLAlchemy Session.

    Example:
        with create_session() as session:
            results = session.query(DocumentChunk).all()
    """
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


async def get_async_session() -> AsyncGenerator[Any, None]:  # noqa: ANN401
    """FastAPI dependency for database sessions."""
    for session in create_session():
        yield session


def init_db(db_url: str | None = None) -> None:
    """Create all tables if they don't exist.

    Args:
        db_url: Database URL. If None, uses the default from config.
    """
    engine = get_engine(db_url)
    Base.metadata.create_all(bind=engine)


def drop_db(db_url: str | None = None) -> None:
    """Drop all tables. USE WITH EXTREME CAUTION."""
    engine = get_engine(db_url)
    Base.metadata.drop_all(bind=engine)


def reset_engine() -> None:
    """Reset the global engine and session factory (for testing)."""
    global _engine, _SessionLocal
    _engine = None
    _SessionLocal = None
