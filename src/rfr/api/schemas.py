"""Pydantic models for API request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str = "1.0.0a1"
    components: dict[str, str] = Field(
        default_factory=lambda: {
            "database": "not_connected",
            "redis": "not_connected",
            "llm": "not_configured",
        },
    )
    uptime_seconds: float = 0.0


# ── Query ──


class QueryRequest(BaseModel):
    """Request to execute a RAG query."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
        description="The user's question",
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Number of documents to retrieve",
    )
    stream: bool = Field(
        default=False,
        description="Enable streaming response (v2 feature, placeholder)",
    )


class SourceInfo(BaseModel):
    """A single source document referenced in the answer."""

    content: str = Field(..., description="Retrieved chunk content")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Document metadata (source, title, roles)",
    )
    relevance_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Cosine similarity score",
    )


class TokenUsage(BaseModel):
    """Token usage statistics."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class QueryResponse(BaseModel):
    """Response from a RAG query."""

    answer: str = Field(..., description="Generated answer text")
    sources: list[SourceInfo] = Field(
        default_factory=list,
        description="Retrieved source documents",
    )
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    latency_ms: float = Field(
        default=0.0,
        description="End-to-end latency in milliseconds",
    )


# ── Ingestion ──


class DirectorySource(BaseModel):
    """Source configuration for directory ingestion."""

    type: str = Field(default="directory", pattern="^(directory)$")
    path: str = Field(..., description="Path to the directory")
    glob_pattern: str = Field(
        default="**/*",
        description="Glob pattern for file matching",
    )
    default_role: str = Field(
        default="user",
        description="Default role for documents without explicit role metadata",
    )


class FileSource(BaseModel):
    """Source configuration for single file ingestion."""

    type: str = Field(default="file", pattern="^(file)$")
    path: str = Field(..., description="Path to the file")
    allowed_roles: list[str] = Field(
        default_factory=lambda: ["user"],
        description="Roles allowed to access this document",
    )


class RawSource(BaseModel):
    """Source configuration for raw text ingestion."""

    type: str = Field(default="raw", pattern="^(raw)$")
    content: str = Field(..., description="Raw text content")
    metadata: dict[str, Any] = Field(
        default_factory=lambda: {"allowed_roles": ["user"], "source": "raw"},
        description="Document metadata including allowed_roles and source",
    )


IngestRequest = DirectorySource | FileSource | RawSource


class IngestResponse(BaseModel):
    """Response after triggering ingestion."""

    task_id: str = Field(..., description="Task ID for status polling")
    status: str = "pending"
    source: str = Field(..., description="Source description")


class IngestStatusResponse(BaseModel):
    """Status of an ingestion task."""

    task_id: str
    status: str
    source: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error_message: str | None = None


# ── Documents ──


class DocumentInfo(BaseModel):
    """Metadata about an indexed document."""

    doc_id: str
    source: str
    title: str = ""
    chunk_count: int = 0
    allowed_roles: list[str] = Field(default_factory=list)
    ingested_at: datetime | None = None


class DocumentListResponse(BaseModel):
    """Paginated list of indexed documents."""

    items: list[DocumentInfo] = Field(default_factory=list)
    total: int = 0
    limit: int = 20
    offset: int = 0


class DeleteDocumentResponse(BaseModel):
    """Response from document deletion."""

    deleted: bool = True
    doc_id: str
    chunks_removed: int = 0


class SourceListResponse(BaseModel):
    """List of distinct document sources."""

    sources: list[str] = Field(default_factory=list)


# ── Auth / API Keys ──


class CreateKeyRequest(BaseModel):
    """Request to create a new API key."""

    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="user", max_length=100)


class CreateKeyResponse(BaseModel):
    """Response after creating an API key (raw key shown once)."""

    key: str
    key_prefix: str
    name: str
    role: str
    created_at: datetime


class KeyInfo(BaseModel):
    """Public info about an API key (no raw key)."""

    prefix: str
    name: str
    role: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None = None


class KeyListResponse(BaseModel):
    """List of API keys."""

    keys: list[KeyInfo] = Field(default_factory=list)


class DeactivateKeyResponse(BaseModel):
    """Response from key deactivation."""

    deactivated: bool = True
    prefix: str


# ── Admin ──


class ReindexResponse(BaseModel):
    """Response from triggering full re-index."""

    task_id: str
    status: str = "pending"
    message: str = "Full re-index started."
