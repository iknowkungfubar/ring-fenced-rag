"""Document chunking — split documents into semantically coherent pieces."""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_document(
    documents: list[Document],
    chunk_size: int = 512,
    chunk_overlap: int = 50,
) -> list[Document]:
    """Split documents into chunks using recursive character splitting.

    Validates that every chunk retains the required 'allowed_roles' metadata.
    If any chunk lacks 'allowed_roles', a ValueError is raised.

    Args:
        documents: List of source Document objects with metadata.
        chunk_size: Target chunk size in characters (not tokens).
        chunk_overlap: Overlap between consecutive chunks.

    Returns:
        List of chunked Document objects with preserved metadata.

    Raises:
        ValueError: If any chunk is missing 'allowed_roles' metadata.

    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
    )

    chunked = splitter.split_documents(documents)

    for chunk in chunked:
        if "allowed_roles" not in chunk.metadata:
            msg = (
                f"Document missing required 'allowed_roles' metadata: "
                f"{chunk.metadata.get('source', 'unknown')}"
            )
            raise ValueError(msg)

    return chunked
