"""Comprehensive tests for __about__ — git and non-git version paths."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

from rfr.__about__ import _STATIC_VERSION, __git_commit__, __title__, __version__, version_info


class TestVersionInfo:
    """Version info structure."""

    def test_version_is_string(self) -> None:
        assert isinstance(__version__, str) and len(__version__) > 0

    def test_git_commit_is_string(self) -> None:
        assert isinstance(__git_commit__, str)

    def test_title_is_correct(self) -> None:
        assert __title__ == "ring-fenced-rag"

    def test_version_info_has_all_keys(self) -> None:
        info = version_info()
        for key in ("version", "git_commit", "python", "platform", "title"):
            assert key in info
            assert isinstance(info[key], str)


class TestGetGitVersion:
    """Git version detection paths (mocked subprocess)."""

    @patch("rfr.__about__.subprocess.run")
    def test_git_found_with_v_prefix(self, mock_run) -> None:
        """git describe returning 'v1.0.0' should strip the 'v'."""
        mock_result = subprocess.CompletedProcess([], 0, stdout="v1.0.0\n", stderr="")
        mock_run.return_value = mock_result
        from rfr.__about__ import _get_git_version

        result = _get_git_version()
        assert result == "1.0.0"

    @patch("rfr.__about__.subprocess.run")
    def test_git_found_without_v(self, mock_run) -> None:
        """git describe without 'v' prefix should pass through."""
        mock_result = subprocess.CompletedProcess([], 0, stdout="1.0.0a1\n", stderr="")
        mock_run.return_value = mock_result
        from rfr.__about__ import _get_git_version

        result = _get_git_version()
        assert result == "1.0.0a1"

    @patch("rfr.__about__.subprocess.run")
    def test_git_found_with_dirty(self, mock_run) -> None:
        """git describe with --dirty should include the dirty flag."""
        mock_result = subprocess.CompletedProcess([], 0, stdout="1.0.0-dirty\n", stderr="")
        mock_run.return_value = mock_result
        from rfr.__about__ import _get_git_version

        result = _get_git_version()
        assert result == "1.0.0-dirty"

    @patch("rfr.__about__.subprocess.run")
    def test_git_with_commits_since_tag(self, mock_run) -> None:
        """git describe with commits since tag should include count and hash."""
        mock_result = subprocess.CompletedProcess([], 0, stdout="1.0.0-3-gdeadbeef\n", stderr="")
        mock_run.return_value = mock_result
        from rfr.__about__ import _get_git_version

        result = _get_git_version()
        assert result == "1.0.0-3-gdeadbeef"

    @patch("rfr.__about__.subprocess.run")
    def test_git_not_found_returns_none(self, mock_run) -> None:
        """When git fails, return None."""
        mock_run.side_effect = FileNotFoundError("git not found")
        from rfr.__about__ import _get_git_version

        result = _get_git_version()
        assert result is None

    @patch("rfr.__about__.subprocess.run")
    def test_git_timeout_returns_none(self, mock_run) -> None:
        """When git times out, return None."""
        mock_run.side_effect = subprocess.TimeoutExpired("git", 2)
        from rfr.__about__ import _get_git_version

        result = _get_git_version()
        assert result is None


class TestGetGitCommit:
    """Git commit detection paths."""

    @patch("rfr.__about__.subprocess.run")
    def test_commit_found(self, mock_run) -> None:
        """git rev-parse should return the commit hash."""
        mock_result = subprocess.CompletedProcess([], 0, stdout="abc1234\n", stderr="")
        mock_run.return_value = mock_result
        from rfr.__about__ import _get_git_commit

        result = _get_git_commit()
        assert result == "abc1234"

    @patch("rfr.__about__.subprocess.run")
    def test_commit_not_found_returns_unknown(self, mock_run) -> None:
        """When git fails, return 'unknown'."""
        mock_run.side_effect = FileNotFoundError("git not found")
        from rfr.__about__ import _get_git_commit

        result = _get_git_commit()
        assert result == "unknown"


class TestGetVersion:
    """Version resolution paths."""

    @patch("rfr.__about__._get_git_version")
    def test_git_version_used(self, mock_git) -> None:
        """When git version exists, use it."""
        mock_git.return_value = "2.0.0rc1"
        from rfr.__about__ import _get_version

        result = _get_version()
        assert result == "2.0.0rc1"

    @patch("rfr.__about__._get_git_version")
    def test_static_fallback(self, mock_git) -> None:
        """When git fails, use static version."""
        mock_git.return_value = None
        from rfr.__about__ import _get_version

        result = _get_version()
        assert result == _STATIC_VERSION
