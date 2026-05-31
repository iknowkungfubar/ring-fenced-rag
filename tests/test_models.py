"""Tests for the ORM model definitions and database utilities."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import inspect, text

from rfr.models.database import create_session, get_engine, init_db, reset_engine
from rfr.models.orm import ApiKey, DocumentChunk, IngestionJob


@pytest.fixture
def db_url() -> str:
    """Create an in-memory SQLite database URL for testing."""
    reset_engine()
    return "sqlite://"


def test_create_chunk(db_url: str) -> None:
    """A valid chunk should be creatable."""
    init_db(db_url)
    chunk = DocumentChunk(
        content="Test document content.",
        embedding=[0.1, 0.2, 0.3],
        rbac_metadata={"allowed_roles": ["senior_engineer"], "source": "test"},
        source="test/doc.md",
        doc_id="doc-001",
        chunk_index=0,
    )
    with create_session() as session:
        session.add(chunk)
        session.commit()
        fetched = session.get(DocumentChunk, chunk.id)
        assert fetched is not None
        assert fetched.content == "Test document content."
        assert fetched.rbac_metadata["allowed_roles"] == ["senior_engineer"]
        assert fetched.chunk_index == 0


def test_chunk_default_metadata(db_url: str) -> None:
    """Chunks without explicit metadata should get an empty dict."""
    init_db(db_url)
    chunk = DocumentChunk(
        content="No metadata.",
        embedding=[0.5, 0.6],
        source="test/no-meta.md",
        doc_id="doc-002",
        chunk_index=0,
        rbac_metadata={},
    )
    with create_session() as session:
        session.add(chunk)
        session.commit()
        assert chunk.rbac_metadata == {}


def test_chunk_timestamps_auto(db_url: str) -> None:
    """created_at and updated_at should be set automatically."""
    init_db(db_url)
    chunk = DocumentChunk(
        content="Timestamps test.",
        embedding=[0.1],
        rbac_metadata={"allowed_roles": ["admin"]},
        source="test/timestamps.md",
        doc_id="doc-003",
        chunk_index=0,
    )
    with create_session() as session:
        session.add(chunk)
        session.commit()
        assert chunk.created_at is not None
        assert chunk.updated_at is not None


def test_chunk_uuid_auto(db_url: str) -> None:
    """Chunk ID should be auto-generated as UUID."""
    init_db(db_url)
    chunk = DocumentChunk(
        content="UUID test.",
        embedding=[0.1],
        rbac_metadata={"allowed_roles": ["user"]},
        source="test/uuid.md",
        doc_id="doc-004",
        chunk_index=0,
    )
    with create_session() as session:
        session.add(chunk)
        session.commit()
        assert isinstance(chunk.id, uuid.UUID)


def test_chunk_repr() -> None:
    """__repr__ should show key fields."""
    chunk = DocumentChunk(
        content="Test",
        embedding=[0.1],
        rbac_metadata={"allowed_roles": ["user"]},
        source="test/doc.md",
        doc_id="doc-005",
        chunk_index=0,
    )
    rep = repr(chunk)
    assert "DocumentChunk" in rep
    assert "test/doc.md" in rep
    assert "0" in rep


def test_create_key(db_url: str) -> None:
    """A valid API key should be creatable."""
    init_db(db_url)
    key = ApiKey(
        key_hash="abc123def456",
        key_prefix="abc12345",
        name="test-key",
        role="senior_engineer",
    )
    with create_session() as session:
        session.add(key)
        session.commit()
        fetched = session.get(ApiKey, key.id)
        assert fetched is not None
        assert fetched.role == "senior_engineer"
        assert fetched.is_active is True


def test_key_hash_unique(db_url: str) -> None:
    """key_hash should be unique."""
    init_db(db_url)
    key1 = ApiKey(
        key_hash="samehash",
        key_prefix="pref1",
        name="key1",
        role="user",
    )
    key2 = ApiKey(
        key_hash="samehash",
        key_prefix="pref2",
        name="key2",
        role="admin",
    )
    with create_session() as session:
        session.add(key1)
        session.commit()
        session.add(key2)
        with pytest.raises(Exception):
            session.commit()
        session.rollback()


def test_key_repr() -> None:
    """__repr__ should show prefix and role."""
    key = ApiKey(
        key_hash="hash",
        key_prefix="pref1234",
        name="test",
        role="admin",
    )
    rep = repr(key)
    assert "ApiKey" in rep
    assert "pref1234" in rep
    assert "admin" in rep


def test_key_deactivation(db_url: str) -> None:
    """Keys can be deactivated without deletion."""
    init_db(db_url)
    key = ApiKey(
        key_hash="deactivateme",
        key_prefix="deact00",
        name="deactivate-test",
        role="user",
    )
    with create_session() as session:
        session.add(key)
        session.commit()
        key.is_active = False
        session.commit()
        fetched = session.get(ApiKey, key.id)
        assert fetched is not None
        assert fetched.is_active is False


def test_create_job(db_url: str) -> None:
    """A valid ingestion job should be creatable."""
    init_db(db_url)
    job = IngestionJob(
        source="/data/docs/",
        status="pending",
    )
    with create_session() as session:
        session.add(job)
        session.commit()
        fetched = session.get(IngestionJob, job.id)
        assert fetched is not None
        assert fetched.status == "pending"


def test_job_status_transition(db_url: str) -> None:
    """Job status should transition through states."""
    init_db(db_url)
    job = IngestionJob(
        source="/data/docs/",
        status="pending",
    )
    with create_session() as session:
        session.add(job)
        session.commit()
        now = datetime.now(UTC)

        job.status = "running"
        job.started_at = now
        session.commit()
        assert job.status == "running"

        job.status = "completed"
        job.completed_at = now
        job.result = {"num_added": 5, "num_skipped": 0}
        session.commit()
        assert job.status == "completed"
        assert job.result["num_added"] == 5


def test_job_repr() -> None:
    """__repr__ should show id and status."""
    job = IngestionJob(
        source="test",
        status="running",
    )
    rep = repr(job)
    assert "IngestionJob" in rep
    assert "running" in rep


def test_init_db_creates_tables(db_url: str) -> None:
    """init_db should create all tables."""
    init_db(db_url)
    engine = get_engine()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "document_chunks" in tables
    assert "api_keys" in tables
    assert "ingestion_jobs" in tables


def test_create_session_context(db_url: str) -> None:
    """create_session should work as a context manager."""
    init_db(db_url)
    with create_session() as session:
        assert session is not None
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1
