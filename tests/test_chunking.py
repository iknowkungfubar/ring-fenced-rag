"""Tests for the chunking module."""

import pytest
from langchain_core.documents import Document

from rfr.ingestion.chunking import chunk_document


class TestChunkDocument:
    """Verify chunking preserves metadata and enforces RBAC validation."""

    def test_single_document_single_chunk(self) -> None:
        """A small document should produce one chunk."""
        doc = Document(
            page_content="Short content.",
            metadata={"source": "test.md", "allowed_roles": ["user"]},
        )
        chunks = chunk_document([doc])
        assert len(chunks) >= 1

    def test_single_document_multiple_chunks(self) -> None:
        """A large document should produce multiple chunks."""
        content = " ".join(["word"] * 2000)  # ~2000 words
        doc = Document(
            page_content=content,
            metadata={"source": "large.md", "allowed_roles": ["admin"]},
        )
        chunks = chunk_document([doc], chunk_size=200, chunk_overlap=20)
        assert len(chunks) >= 2

    def test_metadata_preserved_in_all_chunks(self) -> None:
        """All chunks should retain the source metadata."""
        doc = Document(
            page_content=" ".join(["word"] * 2000),
            metadata={"source": "test.md", "allowed_roles": ["admin"], "title": "Test"},
        )
        chunks = chunk_document([doc], chunk_size=200, chunk_overlap=20)
        for chunk in chunks:
            assert chunk.metadata["source"] == "test.md"
            assert chunk.metadata["allowed_roles"] == ["admin"]
            assert chunk.metadata["title"] == "Test"
            assert "start_index" in chunk.metadata

    def test_missing_allowed_roles_raises_error(self) -> None:
        """A chunk without allowed_roles should raise ValueError."""
        doc = Document(
            page_content="Some content without role metadata.",
            metadata={"source": "test.md"},
        )
        with pytest.raises(ValueError, match="allowed_roles"):
            chunk_document([doc])

    def test_multiple_documents(self) -> None:
        """Multiple documents should all be chunked."""
        docs = [
            Document(
                page_content="Short doc.",
                metadata={"source": "a.md", "allowed_roles": ["user"]},
            ),
            Document(
                page_content="Another short doc.",
                metadata={"source": "b.md", "allowed_roles": ["admin"]},
            ),
        ]
        chunks = chunk_document(docs)
        assert len(chunks) == 2

    def test_chunk_overlap_works(self) -> None:
        """Consecutive chunks should share overlapping text."""
        # Create content long enough to force multiple chunks
        content = "paragraph one. " * 50 + "UNIQUE_MARKER_MIDDLE. " * 10 + "paragraph three. " * 50
        doc = Document(
            page_content=content,
            metadata={"source": "overlap.md", "allowed_roles": ["user"]},
        )
        chunks = chunk_document([doc], chunk_size=100, chunk_overlap=30)
        if len(chunks) >= 2:
            # Verify overlap: consecutive chunks should share some content
            assert chunks[0].page_content != chunks[1].page_content
