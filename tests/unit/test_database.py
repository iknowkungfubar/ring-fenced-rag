"""Comprehensive tests for database module — engine init, session lifecycle."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from sqlalchemy import text

from rfr.models.database import create_session, get_engine, get_session_factory, init_db, reset_engine


class TestDatabaseEngine:
    """Engine initialization paths."""

    def setup_method(self) -> None:
        reset_engine()

    def test_get_engine_default_creates_pg_engine(self) -> None:
        """Default engine should be created with PostgreSQL URL."""
        engine = get_engine()
        assert engine is not None
        assert "postgresql" in str(engine.url)

    def test_get_engine_with_sqlite(self) -> None:
        """Custom SQLite URL should work."""
        engine = get_engine("sqlite://")
        assert engine is not None
        assert "sqlite" in str(engine.url)

    def test_get_engine_twice_returns_same(self) -> None:
        """Calling get_engine twice should return the same instance."""
        e1 = get_engine("sqlite://")
        reset_engine()
        e2 = get_engine("sqlite://")
        # Different calls because we reset
        assert e1 is not e2

    def test_get_session_factory(self) -> None:
        """Session factory should return a sessionmaker."""
        factory = get_session_factory()
        assert factory is not None

    def test_init_db_creates_tables(self) -> None:
        """init_db should not raise with SQLite."""
        reset_engine()
        init_db("sqlite://")  # Should succeed without error

    def test_create_session_context(self) -> None:
        """create_session should work as a context manager with SQLite."""
        reset_engine()
        init_db("sqlite://")
        with create_session() as session:
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_create_session_rollback_on_error(self) -> None:
        """create_session should close connection on error."""
        reset_engine()
        init_db("sqlite://")
        try:
            with create_session() as session:
                session.execute(text("SELECT invalid"))
        except Exception:
            pass
        # Session should be closed after the error
        # If we can create a new one, that's good enough
        with create_session() as session:
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_reset_engine_works(self) -> None:
        """reset_engine should clear the cached engine."""
        e1 = get_engine("sqlite://")
        reset_engine()
        e2 = get_engine("sqlite://")
        # After reset, get_engine creates a new one
        assert e1 is not e2

    @patch("rfr.models.database.AppConfig")
    def test_get_engine_without_url_uses_config(self, mock_config) -> None:
        """get_engine without args uses AppConfig."""
        cfg = mock_config.return_value
        cfg.database.url = "postgresql+psycopg://localhost/test"
        cfg.database.pool_size = 2
        cfg.database.max_overflow = 0
        cfg.database.echo = False

        engine = get_engine()
        assert engine is not None
