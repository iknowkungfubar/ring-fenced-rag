"""Tests for embedding error paths."""

from __future__ import annotations

import pytest

from rfr.ingestion.embedding import LocalEmbeddings


class TestEmbeddingErrors:
    """Error paths in embedding module."""

    def test_invalid_model_name(self) -> None:
        """An invalid model name should raise RuntimeError."""
        with pytest.raises(RuntimeError, match="Failed to load embedding model"):
            LocalEmbeddings("nonexistent-model-12345xyz")

    def test_unknown_model_raises(self) -> None:
        """A completely unknown model should raise an error."""
        with pytest.raises(RuntimeError):
            LocalEmbeddings("this-model-definitely-does-not-exist-99999")
