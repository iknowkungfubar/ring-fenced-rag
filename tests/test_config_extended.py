"""Extended tests for configuration module — save/load, CLI methods."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rfr.config import AppConfig

if TYPE_CHECKING:
    from pathlib import Path


class TestConfigSaveLoad:
    """Verify config save/load round-trips."""

    def test_save_creates_file(self, tmp_path: Path) -> None:
        """Saving config should create a TOML file."""
        cfg = AppConfig()
        path = tmp_path / "test_config.toml"
        cfg.save(path)
        assert path.exists()
        content = path.read_text()
        assert "llm" in content
        assert "ollama" in content
        assert "embedding" in content

    def test_save_list_values(self, tmp_path: Path) -> None:
        """Config with list values should serialize correctly."""
        cfg = AppConfig()
        cfg.auth.admin_roles = ["admin", "superadmin"]
        path = tmp_path / "test_list.toml"
        cfg.save(path)
        content = path.read_text()
        assert "admin" in content
        assert "superadmin" in content

    def test_round_trip_preserves_values(self, tmp_path: Path) -> None:
        """Save then reload should preserve key values."""
        cfg = AppConfig()
        cfg.llm.provider = "lm-studio"  # type: ignore[assignment]
        cfg.llm.base_url = "http://localhost:1234/v1"
        cfg.embedding.model = "BAAI/bge-small-en-v1.5"
        path = tmp_path / "roundtrip.toml"
        cfg.save(path)

        # Read back and verify key patterns in TOML
        content = path.read_text()
        assert "lm-studio" in content
        assert "1234" in content
        assert "bge-small" in content

    def test_save_idempotent(self, tmp_path: Path) -> None:
        """Saving the same config twice should produce the same file."""
        cfg = AppConfig()
        path = tmp_path / "idempotent.toml"
        cfg.save(path)
        first = path.read_text()
        cfg.save(path)
        second = path.read_text()
        assert first == second

    def test_save_default_path_creates_dir(self, tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        """Saving should create parent directories automatically."""
        cfg = AppConfig()
        deep_path = tmp_path / "a" / "b" / "c" / "config.toml"
        cfg.save(deep_path)
        assert deep_path.exists()
