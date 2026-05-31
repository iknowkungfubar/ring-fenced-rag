"""Document ingestion pipeline — parsing, chunking, embedding, and idempotent indexing."""

from rfr.ingestion.chunking import chunk_document
from rfr.ingestion.embedding import LocalEmbeddings
from rfr.ingestion.parsing import parse_directory, parse_document
from rfr.ingestion.pipeline import ingest_documents

__all__ = [
    "LocalEmbeddings",
    "chunk_document",
    "ingest_documents",
    "parse_directory",
    "parse_document",
]
