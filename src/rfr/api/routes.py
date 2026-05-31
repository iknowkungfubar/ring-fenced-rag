"""FastAPI router with all Ring-Fenced RAG endpoints.

Implements the API contracts from 05-API.md:
- Health, Query, Ingest, Documents, Auth/Keys, Admin
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from rfr import __version__
from rfr.api.auth import generate_api_key, get_current_role, require_admin_role
from rfr.api.pipeline import RAGExecutionError, execute_rag_query
from rfr.api.schemas import (
    CreateKeyRequest,
    CreateKeyResponse,
    DeactivateKeyResponse,
    DeleteDocumentResponse,
    DirectorySource,
    DocumentListResponse,
    FileSource,
    HealthResponse,
    IngestResponse,
    IngestStatusResponse,
    KeyInfo,
    KeyListResponse,
    QueryRequest,
    QueryResponse,
    RawSource,
    ReindexResponse,
    SourceListResponse,
)
from rfr.config import AppConfig

router = APIRouter(prefix="/api/v1")

# Track server start time for uptime
_server_start = time.time()


# ── Health ──


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health() -> HealthResponse:
    """Health check. Returns service status and component connectivity."""
    from rfr.models.database import get_engine

    db_status = "disconnected"
    try:
        engine = get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text

            conn.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        version=__version__,
        components={
            "database": db_status,
            "redis": "not_connected",
            "llm": "configured" if AppConfig().llm.provider != "none" else "not_configured",
        },
        uptime_seconds=time.time() - _server_start,
    )


# ── Query ──


@router.post("/query", response_model=QueryResponse, tags=["Query"])
async def query(
    body: QueryRequest,
    role: str = Depends(get_current_role),
) -> QueryResponse:
    """Execute a RAG query. Returns generated answer with source citations."""
    if not body.query.strip():
        raise HTTPException(status_code=422, detail="Query cannot be empty")

    try:
        result = execute_rag_query(
            query=body.query,
            user_role=role,
            top_k=body.top_k,
        )
        return result
    except RAGExecutionError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


# ── Ingestion ──


@router.post("/ingest", response_model=IngestResponse, status_code=202, tags=["Ingestion"])
async def trigger_ingestion(
    body: DirectorySource | FileSource | RawSource,
    _admin: str = Depends(require_admin_role),
) -> IngestResponse:
    """Trigger async document ingestion from a source."""
    source_desc = body.path if hasattr(body, "path") else "raw"
    # TODO: Enqueue Celery task with source config
    return IngestResponse(
        task_id="00000000-0000-0000-0000-000000000000",
        status="pending",
        source=source_desc,
    )


@router.get("/ingest/{task_id}", response_model=IngestStatusResponse, tags=["Ingestion"])
async def get_ingestion_status(
    task_id: str = Path(..., description="Task ID from ingestion trigger"),
    _: str = Depends(get_current_role),
) -> IngestStatusResponse:
    """Poll the status of an async ingestion task."""
    # TODO: Look up task in ingestion_jobs table
    return IngestStatusResponse(
        task_id=task_id,
        status="completed",
        source="unknown",
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        result={"num_added": 0, "num_updated": 0, "num_skipped": 0, "num_deleted": 0},
    )


# ── Documents ──


@router.get("/documents", response_model=DocumentListResponse, tags=["Documents"])
async def list_documents(
    source: str | None = Query(None, description="Filter by source"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    role: str = Depends(get_current_role),
) -> DocumentListResponse:
    """List indexed documents (metadata only, filtered by user role)."""
    # TODO: Query document_chunks table grouped by doc_id
    return DocumentListResponse(items=[], total=0, limit=limit, offset=offset)


@router.delete("/documents/{doc_id}", response_model=DeleteDocumentResponse, tags=["Documents"])
async def delete_document(
    doc_id: str = Path(..., description="Document ID to delete"),
    _admin: str = Depends(require_admin_role),
) -> DeleteDocumentResponse:
    """Delete all chunks for a specific document."""
    # TODO: Delete from document_chunks + SQLRecordManager
    return DeleteDocumentResponse(deleted=True, doc_id=doc_id, chunks_removed=0)


@router.get("/documents/sources", response_model=SourceListResponse, tags=["Documents"])
async def list_sources(
    _: str = Depends(get_current_role),
) -> SourceListResponse:
    """List distinct document sources."""
    # TODO: Query distinct sources from document_chunks
    return SourceListResponse(sources=[])


# ── Auth / API Keys ──


@router.post("/auth/keys", response_model=CreateKeyResponse, status_code=201, tags=["Auth"])
async def create_api_key(
    body: CreateKeyRequest,
    _admin: str = Depends(require_admin_role),
) -> CreateKeyResponse:
    """Create a new API key. Returns the raw key once (shown only here)."""
    raw_key, key_hash, key_prefix = generate_api_key()

    from rfr.models.database import create_session
    from rfr.models.orm import ApiKey

    with create_session() as session:
        key = ApiKey(
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=body.name,
            role=body.role,
        )
        session.add(key)
        session.commit()

    return CreateKeyResponse(
        key=raw_key,
        key_prefix=key_prefix,
        name=body.name,
        role=body.role,
        created_at=datetime.now(UTC),
    )


@router.get("/auth/keys", response_model=KeyListResponse, tags=["Auth"])
async def list_api_keys(
    _admin: str = Depends(require_admin_role),
) -> KeyListResponse:
    """List all API keys (hashes only, no raw keys)."""
    from rfr.models.database import create_session
    from rfr.models.orm import ApiKey

    with create_session() as session:
        keys = session.query(ApiKey).all()
        return KeyListResponse(
            keys=[
                KeyInfo(
                    prefix=k.key_prefix,
                    name=k.name,
                    role=k.role,
                    is_active=k.is_active,
                    created_at=k.created_at,
                    last_used_at=k.last_used_at,
                )
                for k in keys
            ],
        )


@router.delete("/auth/keys/{prefix}", response_model=DeactivateKeyResponse, tags=["Auth"])
async def deactivate_api_key(
    prefix: str = Path(..., description="Key prefix to deactivate"),
    _admin: str = Depends(require_admin_role),
) -> DeactivateKeyResponse:
    """Deactivate an API key by its prefix."""
    from rfr.models.database import create_session
    from rfr.models.orm import ApiKey

    with create_session() as session:
        key = session.query(ApiKey).filter(ApiKey.key_prefix == prefix).first()
        if key is None:
            raise HTTPException(status_code=404, detail=f"No key found with prefix '{prefix}'")
        key.is_active = False
        session.commit()

    return DeactivateKeyResponse(deactivated=True, prefix=prefix)


# ── Admin ──


@router.post("/admin/reindex", response_model=ReindexResponse, status_code=202, tags=["Admin"])
async def trigger_reindex(
    _admin: str = Depends(require_admin_role),
) -> ReindexResponse:
    """Re-index all documents (clears existing vectors, re-runs ingestion)."""
    # TODO: Clear all chunks + upsertion records, re-ingest known sources
    return ReindexResponse(
        task_id="00000000-0000-0000-0000-000000000000",
        status="pending",
        message="Full re-index started.",
    )
