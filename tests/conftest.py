"""Shared test fixtures and configuration for Ring-Fenced RAG tests.

Following the testing-strategy pattern:
- Session-scoped: DB connection, embedding model (shared across tests)
- Factory fixtures: create test data with overridable defaults
- Auto-use: env isolation to prevent test pollution
"""

from __future__ import annotations

from typing import Any

import pytest

from rfr.config import AppConfig

# ── Environment Isolation ──


@pytest.fixture(autouse=True)
def _no_env_pollution(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent test env from polluting real config paths."""
    monkeypatch.delenv("RFR_CONFIG_PATH", raising=False)
    monkeypatch.delenv("RFR_DB__URL", raising=False)
    monkeypatch.delenv("RFR_API_KEY", raising=False)


# ── Configuration Fixtures ──


@pytest.fixture
def test_config() -> AppConfig:
    """Provide a clean AppConfig for testing."""
    return AppConfig()


@pytest.fixture
def sqlite_db_url() -> str:
    """Provide an in-memory SQLite URL for model tests."""
    return "sqlite://"


# ── Factory Fixtures ──


@pytest.fixture
def document_factory() -> Any:
    """Factory fixture: create Document objects with overridable defaults.

    Usage:
        doc = document_factory(content="Custom text", roles=["admin"])
    """
    from langchain_core.documents import Document

    def _create_doc(
        content: str = "Test document content for RAG ingestion.",
        source: str = "test/source.md",
        doc_id: str = "doc-001",
        roles: list[str | None] | None = None,
        **metadata: Any,
    ) -> Document:
        meta = {
            "source": source,
            "doc_id": doc_id,
            "allowed_roles": roles or ["user"],
            "title": source.rsplit("/", maxsplit=1)[-1].replace(".md", "").replace("_", " ").title(),
        }
        meta.update(metadata)
        return Document(page_content=content, metadata=meta)

    return _create_doc


@pytest.fixture
def api_key_factory() -> Any:
    """Factory fixture: create ApiKey model instances.

    Usage:
        key = api_key_factory(role="admin", name="test-admin")
    """
    import hashlib

    from rfr.models.orm import ApiKey

    def _create_key(
        name: str = "test-key",
        role: str = "user",
        prefix: str = "rfr_test01",
    ) -> ApiKey:
        raw = f"rfr_{hashlib.md5(name.encode()).hexdigest()}"
        key_hash = hashlib.sha256(raw.encode()).hexdigest()
        return ApiKey(
            key_hash=key_hash,
            key_prefix=prefix,
            name=name,
            role=role,
        )

    return _create_key


@pytest.fixture
def chunk_factory() -> Any:
    """Factory fixture: create document chunks with embedding vectors.

    Usage:
        chunks = chunk_factory(["text one", "text two"], roles=["admin"])
    """
    from rfr.ingestion.chunking import chunk_document
    from rfr.ingestion.embedding import LocalEmbeddings

    embeddings = LocalEmbeddings()
    splitter_kwargs: dict[str, int] = {"chunk_size": 200, "chunk_overlap": 20}

    def _create_chunks(
        texts: list[str],
        source: str = "test/source.md",
        roles: list[str] | None = None,
    ) -> Any:
        from langchain_core.documents import Document

        docs = [
            Document(
                page_content=t,
                metadata={"source": source, "allowed_roles": roles or ["user"]},
            )
            for t in texts
        ]
        return chunk_document(docs, **splitter_kwargs)

    return _create_chunks


# ── Embedding Fixture (cached module-scoped) ──


@pytest.fixture(scope="module")
def embeddings() -> Any:
    """Cached embedding model — loaded once per module, shared across tests."""
    from rfr.ingestion.embedding import LocalEmbeddings

    return LocalEmbeddings()
