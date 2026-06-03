"""Tests for __about__ version info module."""

from __future__ import annotations

from rfr.__about__ import __git_commit__, __title__, __version__, version_info


class TestVersionInfo:
    """Verify version info returns correct structure."""

    def test_version_is_string(self) -> None:
        """Version should be a non-empty string."""
        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_git_commit_is_string(self) -> None:
        """Git commit should be a string (either SHA or 'unknown')."""
        assert isinstance(__git_commit__, str)
        assert len(__git_commit__) > 0

    def test_title_is_correct(self) -> None:
        """Title should match the package name."""
        assert __title__ == "ring-fenced-rag"

    def test_version_info_returns_dict(self) -> None:
        """version_info() should return a dict with required keys."""
        info = version_info()
        assert isinstance(info, dict)
        assert "version" in info
        assert "git_commit" in info
        assert "python" in info
        assert "platform" in info
        assert "title" in info

    def test_version_info_values_are_strings(self) -> None:
        """All version_info values should be strings."""
        info = version_info()
        for key, value in info.items():
            assert isinstance(value, str), f"{key} should be str, got {type(value)}"

    def test_version_info_includes_title(self) -> None:
        """version_info should include the title."""
        info = version_info()
        assert info["title"] == "ring-fenced-rag"

    def test_version_matches_static_format(self) -> None:
        """Version should match semver-like format."""
        import re

        assert re.match(r"^\d+\.\d+\.\d+", __version__), f"Version '{__version__}' not semver"
