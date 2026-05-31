"""Initial database schema.

Revision ID: 001
Revises:
Create Date: 2025-05-31

Creates the core RFR schema:
- pgvector extension
- document_chunks table (vectors + RBAC metadata)
- api_keys table
- ingestion_jobs table
- Indexes (GIN, BTREE, HNSW)
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the initial schema."""
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── document_chunks ──
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "embedding",
            sa.String(),  # Stored as string representation for portability
            nullable=False,
            comment="Vector embedding (dimension depends on model)",
        ),
        sa.Column(
            "metadata",
            sa.dialects.postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="JSONB with allowed_roles, source, title, tags",
        ),
        sa.Column("source", sa.String(500), nullable=False),
        sa.Column("doc_id", sa.String(255), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Standard indexes
    op.create_index("idx_doc_chunks_source", "document_chunks", ["source"])
    op.create_index("idx_doc_chunks_doc_id", "document_chunks", ["doc_id"])
    op.create_index(
        "idx_doc_chunks_metadata_roles",
        "document_chunks",
        [sa.text("metadata jsonb_path_ops")],
        postgresql_using="gin",
    )

    # HNSW vector index (run after data is loaded for speed)
    # op.execute(
    #     "CREATE INDEX idx_doc_chunks_embedding_hnsw "
    #     "ON document_chunks USING hnsw (embedding vector_cosine_ops) "
    #     "WITH (m = 16, ef_construction = 200)"
    # )

    # ── api_keys ──
    op.create_table(
        "api_keys",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column("key_prefix", sa.String(10), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash"),
    )
    op.create_index("idx_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)

    # ── ingestion_jobs ──
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("source", sa.String(500), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "failed", name="ingestion_status"),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ingestion_jobs_status", "ingestion_jobs", ["status"])


def downgrade() -> None:
    """Drop the initial schema."""
    op.drop_table("ingestion_jobs")
    op.execute("DROP TYPE IF EXISTS ingestion_status")
    op.drop_table("api_keys")
    op.drop_table("document_chunks")
    # Optionally: op.execute("DROP EXTENSION IF EXISTS vector")
