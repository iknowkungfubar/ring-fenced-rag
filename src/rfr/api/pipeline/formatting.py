"""Document formatting and normalization."""

from __future__ import annotations

from typing import Any


def format_docs(docs: list[Any]) -> str:  # type: ignore[explicit-any]
    """Format retrieved documents into a single context string with source citations.

    Args:
        docs: List of Documents (or dicts with 'content' and 'metadata').

    Returns:
        Formatted string with source citations.

    """
    if not docs:
        return "No relevant documentation found for this query."

    parts = []
    for i, doc in enumerate(docs):
        if isinstance(doc, dict):
            content = doc.get("content", "")
            source = doc.get("metadata", {}).get("source", "Unknown")
        else:
            content = getattr(doc, "page_content", str(doc))
            source = (
                doc.metadata.get("source", "Unknown") if hasattr(doc, "metadata") else "Unknown"
            )

        parts.append(f"[Source {i + 1}: {source}]\n{content}")

    return "\n\n".join(parts)


def normalize_docs(docs: list[Any]) -> list[dict[str, Any]]:  # type: ignore[explicit-any]
    """Normalize various document formats into a list of dicts."""
    result = []
    for doc in docs:
        if isinstance(doc, dict):
            result.append(doc)
        elif hasattr(doc, "page_content"):
            result.append(
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata if hasattr(doc, "metadata") else {},
                    "distance": getattr(doc, "distance", 0.0),
                }
            )
        else:
            result.append({"content": str(doc), "metadata": {}})
    return result
