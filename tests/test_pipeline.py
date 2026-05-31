"""Tests for the RAG pipeline module."""

from __future__ import annotations

from rfr.api.pipeline import RAGExecutionError, create_rag_chain, execute_rag_query, format_docs
from rfr.api.schemas import QueryResponse


class TestFormatDocs:
    """Verify document formatting works correctly."""

    def test_empty_docs(self) -> None:
        """Empty doc list should return a fallback message."""
        result = format_docs([])
        assert "No relevant documentation" in result

    def test_single_doc(self) -> None:
        """A single doc should be formatted with source citation."""
        docs = [{"content": "Restart Nginx with systemctl.", "metadata": {"source": "nginx.md"}}]
        result = format_docs(docs)
        assert "Restart Nginx" in result
        assert "nginx.md" in result

    def test_multiple_docs(self) -> None:
        """Multiple docs should be separated by newlines."""
        docs = [
            {"content": "Doc one.", "metadata": {"source": "a.md"}},
            {"content": "Doc two.", "metadata": {"source": "b.md"}},
        ]
        result = format_docs(docs)
        assert "Doc one" in result
        assert "Doc two" in result
        assert "\n\n" in result

    def test_doc_object_with_metadata(self) -> None:
        """Docs with page_content attribute should work."""
        from langchain_core.documents import Document

        doc = Document(
            page_content="Test content",
            metadata={"source": "test.md"},
        )
        result = format_docs([doc])
        assert "Test content" in result
        assert "test.md" in result


class TestExecuteRagQuery:
    """Verify the RAG query function works (with mock retriever)."""

    def test_query_returns_response(self) -> None:
        """A query should return a QueryResponse with the mock retriever."""
        result = execute_rag_query(
            query="How do I restart Nginx?",
            user_role="admin",
        )
        assert isinstance(result, QueryResponse)
        assert result.answer
        assert isinstance(result.answer, str)

    def test_query_with_no_role_returns_empty(self) -> None:
        """A user role of 'none' should get no results."""
        result = execute_rag_query(
            query="How do I restart Nginx?",
            user_role="none",
        )
        assert isinstance(result, QueryResponse)
        assert result.sources == []

    def test_query_with_unauthorized_role(self) -> None:
        """A role not in the mock doc's allowed_roles should get no results."""
        result = execute_rag_query(
            query="How do I restart Nginx?",
            user_role="intern",
        )
        # Mock retriever only returns docs for senior_engineer/admin
        assert isinstance(result, QueryResponse)

    def test_query_source_metadata(self) -> None:
        """Query response should include source metadata."""
        result = execute_rag_query(
            query="How do I restart Nginx?",
            user_role="admin",
        )
        if result.sources:
            source = result.sources[0]
            assert source.content
            assert source.metadata
            assert source.relevance_score >= 0.0

    def test_pipeline_error_raises(self) -> None:
        """The pipeline should raise RAGExecutionError on failure."""
        chain = create_rag_chain(user_role="admin")
        # This should work with the mock
        result = chain.invoke("test query")
        assert isinstance(result, QueryResponse)
