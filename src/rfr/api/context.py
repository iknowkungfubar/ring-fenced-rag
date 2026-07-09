"""Context formatting and metadata filtering helpers for the RAG pipeline.

Extracted from api/pipeline.py to make execute_rag_query composable.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class MetadataFilter:
    """Role-based metadata filtering for document retrieval."""

    def __init__(self, role: str | None = None):
        self.role = role

    def filter_docs(self, docs: list[Document]) -> list[Document]:
        """Filter documents by allowed roles."""
        if not self.role:
            return docs
        return [
            d
            for d in docs
            if not d.metadata.get("allowed_roles") or self.role in d.metadata["allowed_roles"]
        ]


class ContextFormatter:
    """Context deduplication, token counting, and truncation."""

    def __init__(self, max_tokens: int = 4096):
        self.max_tokens = max_tokens

    def deduplicate(self, docs: list[Document]) -> list[Document]:
        """Remove duplicate documents by source."""
        seen: set[str] = set()
        unique: list[Document] = []
        for doc in docs:
            source = doc.metadata.get("source", "")
            if source and source in seen:
                continue
            if source:
                seen.add(source)
            unique.append(doc)
        return unique

    def format_context(self, docs: list[Document]) -> str:
        """Format documents into a context string with citations."""
        parts = []
        for i, doc in enumerate(docs):
            source = doc.metadata.get("source", "unknown")
            parts.append(f"[{i + 1}] Source: {source}\n{doc.page_content}")
        return "\n\n".join(parts)

    def truncate_to_budget(self, context: str) -> str:
        """Truncate context to fit within the token budget."""
        # Rough estimate: 1 token ~= 4 chars
        max_chars = self.max_tokens * 4
        if len(context) <= max_chars:
            return context
        logger.warning("Truncating context from %d to %d chars", len(context), max_chars)
        return context[:max_chars] + "\n[...truncated]"
