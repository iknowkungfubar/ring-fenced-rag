"""SQLAlchemy ORM models for Ring-Fenced RAG.

Defines the core data entities:
- DocumentChunk: vector + metadata + RBAC
- ApiKey: authentication
- IngestionJob: async task tracking
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


# ---------------------------------------------------------------------------
# Vector type (custom, wraps a list[float] as the DB type varies by backend)
# ---------------------------------------------------------------------------


class VectorType(TypeDecorator[list[float]]):
    """Custom type for pgvector embeddings.

    Stores as a pgvector-compatible string in raw SQL mode.
    The actual vector type is handled by pgvector's SQL type system.
    For ORM/schema creation, we use a JSON string fallback.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: list[float] | None, dialect) -> str | None:  # type: ignore[no-untyped-def]
        if value is None:
            return None
        return "[" + ",".join(str(v) for v in value) + "]"

    def process_result_value(self, value: str | None, dialect) -> list[float] | None:  # type: ignore[no-untyped-def]
        if value is None:
            return None
        # Strip brackets and split
        inner = value.strip("[]")
        return [float(x) for x in inner.split(",")] if inner else []


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class DocumentChunk(Base):
    """A single chunk of a source document with its embedding vector and RBAC metadata.

    The ring-fence is enforced by querying this table with JSONB @> containment
    on the 'allowed_roles' field inside the metadata column.
    """

    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        VectorType,
        nullable=False,
        comment="Vector embedding — dimension depends on model (384 for all-MiniLM)",
    )
    rbac_metadata: Mapped[dict[str, object]] = mapped_column(
        "metadata",
        JSON(none_as_null=False),
        nullable=False,
        default=dict,
        comment="JSONB with allowed_roles, source, title, tags, etc.",
    )
    source: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        comment="Document origin path/URL",
    )
    doc_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Document ID within the source system",
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Position of this chunk in the source document",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_doc_chunks_doc_id", "doc_id"),
        Index(
            "idx_doc_chunks_metadata_roles",
            rbac_metadata,
            postgresql_using="gin",
            postgresql_ops={"rbac_metadata": "jsonb_path_ops"},
        ),
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk id={self.id} source={self.source!r} idx={self.chunk_index}>"


class ApiKey(Base):
    """API key for authentication.

    The raw key is shown once at creation time and stored as a SHA-256 hash.
    The key prefix (first 8 chars) is used for identification in listings.
    """

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    key_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="SHA-256 hash of the raw API key",
    )
    key_prefix: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="First 8 chars of the raw key, for identification",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable key name",
    )
    role: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Role this key grants (admin, senior_engineer, etc.)",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        Index("idx_api_keys_key_hash", key_hash, unique=True),
    )

    def __repr__(self) -> str:
        return f"<ApiKey prefix={self.key_prefix!r} role={self.role!r}>"


class IngestionJob(Base):
    """Tracks the state of async document ingestion tasks."""

    __tablename__ = "ingestion_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Path, URL, or description of ingested source",
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "running",
            "completed",
            "failed",
            name="ingestion_status",
        ),
        nullable=False,
        default="pending",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    result: Mapped[dict | None] = mapped_column(
        JSON(none_as_null=False),
        nullable=True,
        comment="Result stats: num_added, num_updated, num_skipped, num_deleted",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    __table_args__ = (
        Index("idx_ingestion_jobs_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<IngestionJob id={self.id} status={self.status!r}>"
