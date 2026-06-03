"""Shared fixtures for ring-fenced-rag tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _standalone_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure standalone mode for all tests unless explicitly overridden."""
    monkeypatch.setenv("RFR_STANDALONE", "true")
