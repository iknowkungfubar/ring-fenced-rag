"""Embedding function creation — HuggingFace sentence-transformers from config."""

from __future__ import annotations

import logging
from typing import Any

from rfr.config import AppConfig

logger = logging.getLogger(__name__)


def create_embedding_function() -> Any:  # type: ignore[explicit-any]
    """Create a HuggingFace sentence-transformers embedding function from config.

    Returns:
        A LangChain Embeddings instance.

    """
    from langchain_community.embeddings import HuggingFaceEmbeddings

    cfg = AppConfig().embedding
    logger.info("Creating embedding function: model=%s device=%s", cfg.model, cfg.device)
    return HuggingFaceEmbeddings(
        model_name=cfg.model,
        model_kwargs={"device": cfg.device},
    )
