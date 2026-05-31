"""Tests for the CLI module."""

from click.testing import CliRunner

from rfr.cli import cli


class TestCli:
    """Verify CLI commands register and produce expected output."""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    def test_version(self) -> None:
        """--version should print the package version."""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0a1" in result.output

    def test_help(self) -> None:
        """--help should show command list."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "ring-fenced rag" in result.output.lower()

    def test_init(self) -> None:
        """Init command should succeed."""
        result = self.runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert "Initializing" in result.output

    def test_config_show(self) -> None:
        """Config show should print configuration table."""
        result = self.runner.invoke(cli, ["config", "show"])
        assert result.exit_code == 0
        assert "ollama" in result.output

    def test_query(self) -> None:
        """Query command should accept a question."""
        result = self.runner.invoke(cli, ["query", "How do I restart Nginx?"])
        assert result.exit_code == 0
        assert "Querying" in result.output

    def test_ingest(self) -> None:
        """Ingest command should accept a path."""
        result = self.runner.invoke(cli, ["ingest", "/tmp"])
        assert result.exit_code == 0
        assert "Ingesting" in result.output

    def test_keys_create(self) -> None:
        """Keys create should accept a name."""
        result = self.runner.invoke(cli, ["keys", "create", "test-key"])
        assert result.exit_code == 0

    def test_keys_list(self) -> None:
        """Keys list should succeed."""
        result = self.runner.invoke(cli, ["keys", "list"])
        assert result.exit_code == 0

    def test_status(self) -> None:
        """Status should show component health."""
        result = self.runner.invoke(cli, ["status"])
        assert result.exit_code == 0
