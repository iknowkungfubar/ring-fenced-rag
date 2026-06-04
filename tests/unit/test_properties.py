"""Property-based tests for pure functions using Hypothesis.

Tests the properties that must hold for ALL inputs, not just
specific examples. Covers schemas, validation, and data models.

Note: Embedding property tests are excluded from the default run
because they load the ML model for each generated example.
Use: pytest tests/unit/test_properties.py -k embedding --slow
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from rfr.api.schemas import QueryRequest, QueryResponse, SourceInfo, TokenUsage


class TestQueryRequestProperties:
    """Property-based tests for QueryRequest validation."""

    @given(
        query=st.text(min_size=1, max_size=100),
        top_k=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=50)
    def test_valid_query_always_accepted(self, query: str, top_k: int) -> None:
        """Any non-empty query with valid top_k should be accepted."""
        req = QueryRequest(query=query, top_k=top_k)
        assert req.query == query
        assert req.top_k == top_k

    @given(
        query=st.text(max_size=0),
    )
    @settings(max_examples=10)
    def test_empty_query_rejected(self, query: str) -> None:
        """Empty queries should raise validation error."""
        import pytest

        with pytest.raises(Exception):
            QueryRequest(query=query)

    @given(top_k=st.integers(min_value=21, max_value=1000))
    @settings(max_examples=20)
    def test_top_k_too_large_rejected(self, top_k: int) -> None:
        """top_k > 20 should be rejected."""
        import pytest

        with pytest.raises(Exception):
            QueryRequest(query="test", top_k=top_k)

    @given(top_k=st.integers(min_value=-1000, max_value=0))
    @settings(max_examples=20)
    def test_top_k_too_small_rejected(self, top_k: int) -> None:
        """top_k < 1 should be rejected."""
        import pytest

        with pytest.raises(Exception):
            QueryRequest(query="test", top_k=top_k)


class TestQueryResponseProperties:
    """Property-based tests for QueryResponse structure."""

    @settings(max_examples=30)
    @given(
        answer=st.text(),
        score=st.floats(min_value=0.0, max_value=1.0),
        prompt_tokens=st.integers(min_value=0, max_value=100000),
        completion_tokens=st.integers(min_value=0, max_value=100000),
    )
    def test_response_always_has_answer(
        self,
        answer: str,
        score: float,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        """A QueryResponse should always have an answer string."""
        resp = QueryResponse(
            answer=answer,
            sources=[
                SourceInfo(
                    content="source content",
                    metadata={"source": "test.md"},
                    relevance_score=score,
                ),
            ],
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            latency_ms=100.0,
        )
        assert isinstance(resp.answer, str)
        assert resp.token_usage.total_tokens == prompt_tokens + completion_tokens
        assert 0.0 <= resp.sources[0].relevance_score <= 1.0

    @settings(max_examples=20)
    @given(n_sources=st.integers(min_value=0, max_value=20))
    def test_response_sources_length(self, n_sources: int) -> None:
        """Response can have any number of sources (0 to 20)."""
        sources = [
            SourceInfo(
                content=f"source {i}",
                metadata={"source": f"{i}.md"},
                relevance_score=0.5,
            )
            for i in range(n_sources)
        ]
        resp = QueryResponse(answer="test", sources=sources)
        assert len(resp.sources) == n_sources


# Embedding property tests are marked slow because they load the ML model.
# Run with: pytest tests/unit/test_properties.py -k embedding --slow


import pytest

embedding_test = pytest.mark.slow


@embedding_test
class TestEmbeddingProperties:
    """Property-based tests for embedding behavior (slow — ML model load)."""

    @settings(max_examples=10, deadline=None)
    @given(text=st.text(min_size=1, max_size=100))
    def test_embedding_always_returns_vector(self, text: str) -> None:
        """Any non-empty text should produce a vector."""
        from rfr.ingestion.embedding import LocalEmbeddings

        emb = LocalEmbeddings()
        vector = emb.embed_query(text)
        assert isinstance(vector, list)
        assert len(vector) > 0
        assert all(isinstance(v, float) for v in vector)

    @settings(max_examples=5, deadline=None)
    @given(text=st.text(max_size=0))
    def test_empty_text_returns_vector(self, text: str) -> None:
        """Even empty text should produce a vector (model encodes it)."""
        from rfr.ingestion.embedding import LocalEmbeddings

        emb = LocalEmbeddings()
        vector = emb.embed_query(text)
        assert isinstance(vector, list)
        assert len(vector) == emb.dimension

    @settings(max_examples=10, deadline=None)
    @given(text=st.text(min_size=1, max_size=100))
    def test_same_text_same_vector_property(self, text: str) -> None:
        """The same text should always produce the same vector (deterministic)."""
        from rfr.ingestion.embedding import LocalEmbeddings

        emb = LocalEmbeddings()
        v1 = emb.embed_query(text)
        v2 = emb.embed_query(text)
        assert v1 == v2
