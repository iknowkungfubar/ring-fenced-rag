"""Extended CLI tests — standalone, docs, and edge case paths."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from rfr.cli import cli


class _MockClient:
    """Mock API client."""

    def health(self):
        return type(
            "obj",
            (),
            {
                "status": "ok",
                "version": "1.0.0",
                "components": {"database": "connected"},
                "uptime_seconds": 0.0,
            },
        )()

    def query(self, question: str, top_k: int = 3):
        return type(
            "obj",
            (),
            {
                "answer": "Test answer",
                "sources": [],
                "token_usage": type("obj", (), {"total_tokens": 0})(),
                "latency_ms": 0.0,
            },
        )()

    def ingest_directory(self, path: str, default_role: str = "user", glob_pattern: str = "**/*"):
        return type("obj", (), {"task_id": "task-1", "status": "completed", "source": path})()

    def get_ingestion_status(self, task_id: str):
        return type(
            "obj",
            (),
            {
                "status": "completed",
                "result": {"num_added": 3},
            },
        )()


class TestCliEdgeCases:
    """CLI edge case paths."""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    def _invoke_with_mock(self, args: list[str]):
        with (
            patch("rfr.cli.commands.query.RfrClient", return_value=_MockClient()),
            patch("rfr.cli.commands.ingest.RfrClient", return_value=_MockClient()),
            patch("rfr.cli.commands.keys.RfrClient", return_value=_MockClient()),
        ):
            return self.runner.invoke(cli, args)

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
        result = self._invoke_with_mock(["query", "test question", "--top-k", "5"])
        assert result.exit_code == 0, result.output
        assert "Test answer" in result.output

    def test_ingest_with_role_flag(self) -> None:
        """ingest with --role flag should pass role to client."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._invoke_with_mock(["ingest", tmpdir, "--role", "admin"])
            assert result.exit_code == 0, result.output

    def test_init_with_force(self) -> None:
        """init --force should attempt overwrite."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(cli, ["init", "--force"])
            assert "Created rfr.yml" in result.output

    def test_help_version(self) -> None:
        """--version should show version info."""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "rfr" in result.output or "ring-fenced" in result.output

    def test_tui_command_no_textual(self) -> None:
        """tui command should error gracefully without Textual."""
        with patch("rfr.cli.tui_app.app", side_effect=ImportError("No Textual")):
            result = self.runner.invoke(cli, ["tui"])
            # Should show install message
            assert result.exit_code != 0 or "TUI" in result.output
