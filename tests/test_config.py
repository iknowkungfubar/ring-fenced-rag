"""Tests for the configuration module."""

from pathlib import Path

import pytest

from rfr.config import AppConfig, LLMConfig, load_config


class TestAppConfig:
    """Verify config module loads and validates correctly."""

    def test_default_config_loads(self) -> None:
        """Default config should have sensible defaults."""
        cfg = AppConfig()
        assert cfg.llm.provider == "ollama"
        assert cfg.llm.base_url == "http://localhost:11434/v1"
        assert cfg.embedding.model == "all-MiniLM-L6-v2"
        assert cfg.embedding.dimension == 384
        assert cfg.ingestion.chunk_size == 512
        # In standalone mode the DB URL is empty — must be set via RFR_DB__URL
        assert cfg.database.url == "", "DB URL must be set explicitly in production"
        assert cfg.server.port == 8000

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Environment variables should override defaults."""
        monkeypatch.setenv("RFR_LLM__PROVIDER", "vllm")
        monkeypatch.setenv("RFR_LLM__BASE_URL", "http://localhost:8000/v1")
        monkeypatch.setenv("RFR_EMBEDDING__MODEL", "BAAI/bge-small-en-v1.5")

        cfg = AppConfig()
        assert cfg.llm.provider == "vllm"
        assert cfg.llm.base_url == "http://localhost:8000/v1"
        assert cfg.embedding.model == "BAAI/bge-small-en-v1.5"

    def test_llm_config_validates_temperature(self) -> None:
        """Temperature should be clamped to [0, 2]."""
        LLMConfig(temperature=0.0)
        LLMConfig(temperature=2.0)
        with pytest.raises(Exception):
            LLMConfig(temperature=-0.1)
        with pytest.raises(Exception):
            LLMConfig(temperature=2.1)

    def test_load_config_no_file(self, tmp_path: Path) -> None:
        """load_config should work without a config file."""
        cfg = load_config()
        assert isinstance(cfg, AppConfig)

    def test_save_and_load_config(self, tmp_path: Path) -> None:
        """Config should round-trip through save/load."""
        cfg = AppConfig()
        cfg.llm.provider = "vllm"  # type: ignore[assignment]
        config_path = tmp_path / "config.toml"
        cfg.save(config_path)
        assert config_path.exists()
        content = config_path.read_text()
        assert "vllm" in content

    def test_data_dir_created(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """data_dir should be created automatically."""
        test_dir = str(tmp_path / "rfr_data")
        monkeypatch.setenv("RFR_DATA_DIR", test_dir)
        cfg = AppConfig()
        assert Path(cfg.data_dir).exists()
