"""Retrieval functions — role-filtered retriever, secure retriever factory, mock retriever."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.documents import Document

from rfr.api.pipeline.store import create_vector_store
from rfr.config import AppConfig

logger = logging.getLogger(__name__)


def create_role_filtered_retriever(
    vector_store: Any,  # type: ignore[explicit-any]
    user_role: str,
    top_k: int,
) -> Any:  # type: ignore[explicit-any]
    """Create a retriever that enforces role-based access at the database level.

    Uses the PostgreSQL JSONB ``@>`` containment operator via SQLAlchemy's
    ``.contains()`` method to filter documents where the ``allowed_roles``
    array includes the user's role.  This is a **database-level** filter -- the
    ring-fence cannot be bypassed from the application layer.

    Args:
        vector_store: A ``PGVector`` instance (from ``langchain_postgres``).
        user_role: The role to filter by.
        top_k: Number of documents to retrieve.

    Returns:
        A callable that takes a query string and returns ``list[Document]``.

    """
    from sqlalchemy import func, select

    embedding_store_cls = vector_store.EmbeddingStore
    # ``distance_strategy`` is a ``@property`` that returns a bound method
    # such as ``embedding_store_cls.embedding.cosine_distance`` which is then
    # called with the query embedding vector.
    distance_fn = vector_store.distance_strategy

    def retrieve(query: str) -> list[Document]:
        """Embed the query and run a secure pgvector similarity search."""
        try:
            query_embedding = vector_store.embedding_function.embed_query(query)
        except Exception:
            logger.exception("Failed to embed query")
            return []

        with vector_store._make_sync_session() as session:
            collection = vector_store.get_collection(session)
            if collection is None:
                logger.warning(
                    "PGVector collection '%s' not found -- is the DB initialized?",
                    vector_store.collection_name,
                )
                return []

            # JSONB containment:
            #   ``cmetadata @> '{"allowed_roles": ["<role>"]}'::jsonb``
            # Only chunks whose ``allowed_roles`` array contains the
            # user's role will be returned.
            role_filter = {"allowed_roles": [user_role]}

            stmt = (
                select(
                    embedding_store_cls,
                    distance_fn(query_embedding).label("distance"),
                )
                .filter(
                    embedding_store_cls.collection_id == collection.uuid,
                    embedding_store_cls.cmetadata.contains(role_filter),
                )
                .order_by(func.asc("distance"))
                .limit(top_k)
            )

            try:
                results = session.execute(stmt).all()
            except Exception:
                logger.exception("Vector similarity query failed")
                return []

            docs: list[Document] = []
            for row in results:
                es = row.embedding_store_cls
                metadata = dict(es.cmetadata) if es.cmetadata else {}
                metadata["relevance_score"] = 1.0 - float(row.distance)
                docs.append(
                    Document(
                        page_content=es.document,
                        metadata=metadata,
                    )
                )
            return docs

    return retrieve


def create_secure_retriever(
    user_role: str,
    top_k: int = 3,
    vector_store: Any | None = None,  # type: ignore[explicit-any]
) -> Any:  # type: ignore[explicit-any]
    """Create a secure retriever that filters by user role.

    The ring-fence is enforced at the **database level**: the pgvector
    similarity query includes a JSONB ``@>`` containment filter so that
    only chunks whose ``allowed_roles`` array includes the user's role
    are considered.

    Resolution order:
    1. If *vector_store* is provided -> wrap it with role filtering.
    2. If a real database is configured -> create a ``PGVector`` store.
    3. Otherwise -> return a mock retriever for standalone / dev mode.

    Args:
        user_role: The role to filter by.
        top_k: Number of documents to retrieve.
        vector_store: A LangChain ``VectorStore`` instance. If ``None``, one
            is created from the app config (or a mock is used).

    Returns:
        A callable that takes a query string and returns ``list[Document]``.

    """
    if vector_store is not None:
        return create_role_filtered_retriever(vector_store, user_role, top_k)

    # No explicit store -- try to create one from config
    try:
        cfg = AppConfig()
        if cfg.standalone or not cfg.database.url or "sqlite" in cfg.database.url.lower():
            logger.info("Standalone mode or no pgvector DB configured -- using mock retriever")
            return create_mock_retriever(user_role, top_k)

        store = create_vector_store()
        return create_role_filtered_retriever(store, user_role, top_k)
    except Exception:
        logger.exception("Failed to create real vector store -- falling back to mock")
        return create_mock_retriever(user_role, top_k)


def create_mock_retriever(user_role: str, top_k: int = 3) -> Any:  # type: ignore[explicit-any]
    """Create a mock retriever for development/testing without a DB."""

    def retrieve(query: str) -> list[dict[str, Any]]:
        logger.info("Mock retriever: role=%s query=%s", user_role, query[:50])
        # Return a single mock result to demonstrate the pipeline
        if user_role == "none":
            return []
        return [
            {
                "content": (
                    "To restart the primary Nginx reverse proxy, execute: "
                    "systemctl restart nginx. Ensure you are on the management VPN."
                ),
                "metadata": {
                    "source": "confluence/nginx_guide",
                    "doc_id": "NG-001",
                    "title": "Nginx Restart Procedure",
                    "allowed_roles": ["admin", "senior_engineer"],
                },
            },
        ]

    return retrieve
