"""LCEL RAG pipeline — ring-fenced retrieval + generation.

Exposes the public API of the pipeline package. Split into submodules:
- exceptions: RAGExecutionError
- embeddings: embedding function creation
- store: PGVector store creation
- retrieval: role-filtered retriever, secure retriever factory, mock retriever
- formatting: document formatting and normalization
- chain: RAG chain assembly and query execution
"""

from __future__ import annotations

from rfr.api.pipeline.chain import create_rag_chain, execute_rag_query
from rfr.api.pipeline.exceptions import RAGExecutionError
from rfr.api.pipeline.formatting import format_docs

__all__ = [
    "RAGExecutionError",
    "create_rag_chain",
    "execute_rag_query",
    "format_docs",
]
