"""Tests for the directory parsing module."""

from pathlib import Path

from rfr.ingestion.parsing import parse_directory


class TestParseDirectory:
    """Verify directory parsing works correctly."""

    def test_parse_empty_directory(self, tmp_path: Path) -> None:
        """An empty directory should return an empty list."""
        docs = parse_directory(str(tmp_path))
        assert docs == []

    def test_parse_directory_with_files(self, tmp_path: Path) -> None:
        """A directory with files should return documents."""
        (tmp_path / "readme.md").write_text("# Readme\n\nHello.")
        (tmp_path / "notes.txt").write_text("Some notes.")
        docs = parse_directory(str(tmp_path))
        assert len(docs) == 2

    def test_parse_with_glob_filter(self, tmp_path: Path) -> None:
        """Only files matching the glob should be parsed."""
        (tmp_path / "doc.md").write_text("# MD")
        (tmp_path / "doc.txt").write_text("TXT")
        (tmp_path / "doc.pdf").write_text("PDF")
        docs = parse_directory(str(tmp_path), glob_pattern="**/*.md")
        assert len(docs) == 1
        assert docs[0].metadata["file_type"] == "md"

    def test_parse_with_default_role(self, tmp_path: Path) -> None:
        """Default role should be added to all parsed docs."""
        (tmp_path / "doc.md").write_text("# Test")
        docs = parse_directory(str(tmp_path), default_role="admin")
        assert docs[0].metadata["allowed_roles"] == ["admin"]

    def test_parse_nonexistent_directory(self) -> None:
        """A nonexistent directory should raise NotADirectoryError."""
        import pytest

        with pytest.raises(NotADirectoryError):
            parse_directory("/nonexistent/path")

    def test_parse_skips_binary_files(self, tmp_path: Path) -> None:
        """Binary files that fail parsing should be skipped (not crash)."""
        (tmp_path / "binary.bin").write_bytes(b"\x00\x01\x02\x03")
        (tmp_path / "good.md").write_text("# Good")
        docs = parse_directory(str(tmp_path), glob_pattern="**/*")
        assert len(docs) >= 1
