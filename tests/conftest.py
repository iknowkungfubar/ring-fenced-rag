"""Pytest configuration for Ring-Fenced RAG tests."""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture(autouse=True)
def _no_env_pollution(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Prevent test env from polluting real config paths."""
    monkeypatch.delenv("RFR_CONFIG_PATH", raising=False)
    monkeypatch.delenv("RFR_DB__URL", raising=False)
    return None
