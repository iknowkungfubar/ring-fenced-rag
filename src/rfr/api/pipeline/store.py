"""Vector store creation — PGVector from app configuration."""

from __future__ import annotations

import logging
from typing import Any

from rfr.api.pipeline.embeddings import create_embedding_function
from rfr.config import AppConfig

logger = logging.getLogger(__name__)


def create_vector_store() -> Any:  # type: ignore[explicit-any]
    """Create a PGVector vector store from the app configuration.

    Uses ``langchain_postgres.vectorstores.PGVector`` which creates proper
    pgvector-native tables (``langchain_pg_embedding`` / ``langchain_pg_collection``)
    with the native ``vector`` column type for efficient HNSW-indexed similarity search.

    Returns:
        A ``PGVector`` instance connected to the configured database.

    """
    from langchain_postgres.vectorstores import PGVector

    cfg = AppConfig()
    embeddings = create_embedding_function()
    logger.info(
        "Creating PGVector store: collection=document_chunks db=%s",
        cfg.database.url.split("@")[-1] if "@" in cfg.database.url else cfg.database.url,
    )
    return PGVector(
        embeddings=embeddings,
        connection=cfg.database.sync_url,
        collection_name="document_chunks",
        use_jsonb=True,
    )
