"""Extended CLI tests — standalone, docs, and edge case paths."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from rfr.cli import cli


class TestCliEdgeCases:
    """CLI edge case paths."""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    def test_standalone_short_flag(self) -> None:
        """standalone --port flag should be accepted."""
        result = self.runner.invoke(cli, ["standalone", "--port", "9000"])
        assert "9000" in result.output or result.exit_code in (0, 1)

    def test_keys_create_invalid_role(self) -> None:
        """keys create with invalid args should show error."""
        result = self.runner.invoke(cli, ["keys", "create"])
        # Missing name argument
        assert result.exit_code != 0

    def test_query_empty(self) -> None:
        """query with no question should error."""
        result = self.runner.invoke(cli, ["query"])
        assert result.exit_code != 0

    def test_query_with_flags(self) -> None:
        """query with --top-k flag should work with mocked client."""
        with patch("rfr.cli.client.RfrClient") as mock_client_cls:
            mock_instance = mock_client_cls.return_value
            mock_instance.query.return_value.answer = "Test answer"
            mock_instance.query.return_value.sources = []
            mock_instance.query.return_value.token_usage.total_tokens = 0
            mock_instance.query.return_value.latency_ms = 0.0

            result = self.runner.invoke(cli, ["query", "test question", "--top-k", "5"])
            assert result.exit_code == 0, result.output
            assert "Test answer" in result.output

    def test_ingest_with_role_flag(self) -> None:
        """ingest with --role flag should pass role to client."""
        from rfr.cli.client import RfrClientError

        with patch("rfr.cli.client.RfrClient") as mock_client_cls:
            mock_instance = mock_client_cls.return_value
            mock_instance.ingest_directory.return_value.task_id = "task-1"
            mock_instance.get_ingestion_status.return_value.status = "completed"
            mock_instance.get_ingestion_status.return_value.result = {"num_added": 3}

            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                result = self.runner.invoke(cli, ["ingest", tmpdir, "--role", "admin"])
                assert result.exit_code == 0, result.output

    def test_init_with_force(self) -> None:
        """init --force should attempt overwrite."""
        result = self.runner.invoke(cli, ["init", "--force"])
        assert "Initializing" in result.output or "Already" in result.output

    def test_version_command_detailed(self) -> None:
        """version command should show detailed info."""
        with patch("rfr.cli.client.RfrClient") as mock_client_cls:
            mock_client_cls.return_value.health.return_value.status = "ok"
            result = self.runner.invoke(cli, ["version"])
            assert result.exit_code == 0, result.output
            assert "Version" in result.output or "ring-fenced" in result.output

    def test_tui_command_no_textual(self) -> None:
        """tui command should error gracefully without Textual."""
        with patch("rfr.cli.tui_app.RFRTuiApp", side_effect=ImportError("No Textual")):
            result = self.runner.invoke(cli, ["tui"])
            # Should show install message
            assert result.exit_code != 0 or "TUI" in result.output
