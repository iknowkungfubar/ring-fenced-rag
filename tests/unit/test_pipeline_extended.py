"""Extended pipeline tests — format_docs edge cases, _normalize_docs."""

from __future__ import annotations

from rfr.api.pipeline import RAGExecutionError, format_docs


class TestFormatDocsExtended:
    """Edge cases for document formatting."""

    def test_format_single_empty_doc(self) -> None:
        """A doc with empty content should still be formatted."""
        docs = [{"content": "", "metadata": {"source": "empty.md"}}]
        result = format_docs(docs)
        assert "empty.md" in result

    def test_format_docs_with_no_metadata(self) -> None:
        """Docs without metadata should use 'Unknown' as source."""
        docs = [{"content": "Some content", "metadata": {}}]
        result = format_docs(docs)
        assert "Unknown" in result
        assert "Some content" in result

    def test_format_docs_with_minimal_metadata(self) -> None:
        """Docs with only some metadata fields should still work."""
        docs = [{"content": "Content here", "metadata": {"doc_id": "123"}}]
        result = format_docs(docs)
        assert "Unknown" in result  # no 'source' key
        assert "Content here" in result

    def test_format_docs_mixed_types(self) -> None:
        """Mix of dict and object docs should both format."""
        from langchain_core.documents import Document

        doc_obj = Document(page_content="Object content", metadata={"source": "object.md"})
        doc_dict = {"content": "Dict content", "metadata": {"source": "dict.md"}}
        result = format_docs([doc_obj, doc_dict])
        assert "Object content" in result
        assert "Dict content" in result
        assert "object.md" in result
        assert "dict.md" in result


class TestRAGExecutionError:
    """Verify RAG execution error behavior."""

    def test_error_is_exception_subclass(self) -> None:
        """RAGExecutionError should be an Exception subclass."""
        assert issubclass(RAGExecutionError, Exception)

    def test_error_with_message(self) -> None:
        """RAGExecutionError should carry a message."""
        err = RAGExecutionError("Retrieval failed")
        assert str(err) == "Retrieval failed"

    def test_error_raised_and_caught(self) -> None:
        """RAGExecutionError should be catchable."""
        try:
            raise RAGExecutionError("test error")
        except RAGExecutionError as e:
            assert "test error" in str(e)
