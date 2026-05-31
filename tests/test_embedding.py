"""Tests for the embedding module."""


from rfr.ingestion.embedding import LocalEmbeddings


class TestLocalEmbeddings:
    """Verify the embedding wrapper works correctly."""

    def test_embed_query_returns_list_of_floats(self) -> None:
        """Embedding a query should return a list of floats."""
        emb = LocalEmbeddings()
        vector = emb.embed_query("How do I restart Nginx?")
        assert isinstance(vector, list)
        assert len(vector) > 0
        assert all(isinstance(v, float) for v in vector)

    def test_embed_documents_returns_list_of_vectors(self) -> None:
        """Embedding documents should return a list of vectors."""
        emb = LocalEmbeddings()
        vectors = emb.embed_documents(["doc one", "doc two"])
        assert len(vectors) == 2
        assert len(vectors[0]) > 0
        assert len(vectors[1]) > 0

    def test_embedding_dimension_matches_model(self) -> None:
        """The dimension property should match the model output."""
        emb = LocalEmbeddings()
        vector = emb.embed_query("test")
        assert emb.dimension == len(vector)
        assert emb.dimension == 384  # all-MiniLM-L6-v2 is 384d

    def test_model_name_propagates(self) -> None:
        """A custom model name should be used."""
        emb = LocalEmbeddings("all-MiniLM-L6-v2")
        vector = emb.embed_query("test")
        assert len(vector) == 384

    def test_different_texts_different_vectors(self) -> None:
        """Semantically different texts should produce different vectors."""
        emb = LocalEmbeddings()
        v1 = emb.embed_query("How to restart Nginx")
        v2 = emb.embed_query("The weather is nice today")
        assert v1 != v2

    def test_same_text_same_vector(self) -> None:
        """The same text should produce the same vector (deterministic)."""
        emb = LocalEmbeddings()
        v1 = emb.embed_query("restart nginx server")
        v2 = emb.embed_query("restart nginx server")
        assert v1 == v2
