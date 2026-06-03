"""Pipeline edge case tests — chain creation, error handling, format_docs."""

from __future__ import annotations

from rfr.api.pipeline import (
    RAGExecutionError,
    create_rag_chain,
    execute_rag_query,
    format_docs,
)


class TestChainCreation:
    """Edge cases in chain creation."""

    def test_create_chain_without_llm(self) -> None:
        """create_rag_chain without llm uses mock generator."""
        chain = create_rag_chain(user_role="admin")
        result = chain.invoke("test query")
        assert result is not None
        assert hasattr(result, "answer")

    def test_create_chain_with_none_role(self) -> None:
        """A role of 'none' should produce empty sources."""
        chain = create_rag_chain(user_role="none")
        result = chain.invoke("test")
        assert len(result.sources) == 0


class TestExecuteRagQuery:
    """execute_rag_query edge cases."""

    def test_query_with_unauthorized_role(self) -> None:
        result = execute_rag_query("How do I restart Nginx?", "intern")
        assert result.answer is not None

    def test_query_empty_context(self) -> None:
        result = execute_rag_query("", "admin")
        assert result.answer is not None


class TestFormatDocsExtended:
    """Document formatting edge cases."""

    def test_format_no_docs(self) -> None:
        assert "No relevant" in format_docs([])

    def test_format_with_object_docs(self) -> None:
        from langchain_core.documents import Document

        doc = Document(page_content="Test", metadata={"source": "test.md"})
        result = format_docs([doc])
        assert "Test" in result
        assert "test.md" in result

    def test_format_with_mixed_types(self) -> None:
        from langchain_core.documents import Document

        docs: list = [
            Document(page_content="Obj", metadata={"source": "a.md"}),
            {"content": "Dict", "metadata": {"source": "b.md"}},
        ]
        result = format_docs(docs)
        assert "Obj" in result
        assert "Dict" in result


class TestRAGExecutionError:
    def test_error_message(self) -> None:
        err = RAGExecutionError("test")
        assert str(err) == "test"

    def test_error_is_exception(self) -> None:
        assert issubclass(RAGExecutionError, Exception)
