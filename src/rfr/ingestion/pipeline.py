"""Idempotent ingestion pipeline — hash-tracked indexing with deduplication."""

from __future__ import annotations

import logging
from typing import Any

from langchain.indexes import SQLRecordManager, index
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from rfr.ingestion.chunking import chunk_document
from rfr.ingestion.parsing import parse_directory, parse_document

logger = logging.getLogger(__name__)


class IngestionError(Exception):
    """Raised when the ingestion pipeline encounters a fatal error."""


def ingest_documents(  # noqa: PLR0913
    source: str,
    vector_store: VectorStore,
    db_url: str,
    namespace: str = "rfr_ingestion",
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    default_role: str | None = None,
    cleanup_mode: str = "incremental",
) -> dict[str, Any]:
    """Execute idempotent document ingestion from a file or directory.

    Uses LangChain's SQLRecordManager to track content hashes, ensuring
    that running the same ingestion twice produces identical state
    (no duplicate vectors).

    Args:
        source: Path to a file or directory to ingest.
        vector_store: Initialized LangChain VectorStore instance.
        db_url: Database URL for the SQLRecordManager.
        namespace: Namespace for the record manager.
        chunk_size: Target chunk size in characters.
        chunk_overlap: Overlap between consecutive chunks.
        default_role: Default role for documents without explicit role metadata.
        cleanup_mode: SQLRecordManager cleanup mode ('incremental', 'full', 'none').

    Returns:
        Dictionary with 'num_added', 'num_updated', 'num_skipped', 'num_deleted'.

    Raises:
        IngestionError: If ingestion fails at any step.

    """
    import os

    try:
        raw_documents: list[Document]
        if os.path.isdir(source):
            raw_documents = parse_directory(source, default_role=default_role)
        else:
            raw_documents = parse_document(source, default_role=default_role)

        if not raw_documents:
            logger.warning("No documents found at source: %s", source)
            return {"num_added": 0, "num_updated": 0, "num_skipped": 0, "num_deleted": 0}

        chunked_docs = chunk_document(raw_documents, chunk_size, chunk_overlap)

        record_manager = SQLRecordManager(
            namespace=namespace,
            db_url=db_url,
        )
        record_manager.create_schema()

        logger.info(
            "Indexing %d chunks from %d documents (cleanup=%s)",
            len(chunked_docs),
            len(raw_documents),
            cleanup_mode,
        )

        indexing_result = index(
            docs_source=chunked_docs,
            record_manager=record_manager,
            vector_store=vector_store,
            cleanup=cleanup_mode,
            source_id_key="source",
        )

        logger.info("Ingestion result: %s", indexing_result)
        return indexing_result  # type: ignore[return-value]

    except Exception as e:
        logger.exception("Ingestion pipeline failed for source: %s", source)
        raise IngestionError(str(e)) from e
