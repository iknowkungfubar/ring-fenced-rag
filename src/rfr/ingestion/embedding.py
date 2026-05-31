"""Local embedding engine — wraps sentence-transformers for LangChain compatibility."""

from __future__ import annotations

from sentence_transformers import SentenceTransformer


class LocalEmbeddings:
    """LangChain-compatible embedding wrapper using local sentence-transformers.

    Runs entirely offline — no data leaves the machine during embedding generation.

    Usage:
        embeddings = LocalEmbeddings("all-MiniLM-L6-v2")
        vector = embeddings.embed_query("How do I restart Nginx?")
        vectors = embeddings.embed_documents(["doc1", "doc2"])
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Initialize the embedding model.

        Args:
            model_name: HuggingFace model identifier for a sentence-transformers model.
                        Downloaded on first use, cached locally thereafter.

        Raises:
            ImportError: If sentence-transformers is not installed.
            Exception: If the model fails to load.

        """
        try:
            self.model: SentenceTransformer = SentenceTransformer(model_name)  # type: ignore[no-untyped-call]
        except Exception as e:
            msg = f"Failed to load embedding model '{model_name}': {e}"
            raise RuntimeError(msg) from e

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        Args:
            texts: List of document text strings to embed.

        Returns:
            List of dense vector embeddings (one per input text).

        """
        return self.model.encode(texts).tolist()  # type: ignore[no-any-return]

    def embed_query(self, text: str) -> list[float]:
        """Generate a single embedding for a query string.

        Args:
            text: The query text to embed.

        Returns:
            Dense vector embedding.

        """
        return self.model.encode(text).tolist()  # type: ignore[no-any-return]

    @property
    def dimension(self) -> int:
        """Return the embedding dimension of the loaded model."""
        return self.model.get_sentence_embedding_dimension()  # type: ignore[no-any-return]
