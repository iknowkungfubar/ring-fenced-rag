"""Tests for the document parsing module."""

from pathlib import Path

import pytest

from rfr.ingestion.parsing import parse_document


class TestParseDocument:
    """Verify document parsing works correctly."""

    def test_parse_markdown(self, tmp_path: Path) -> None:
        """A markdown file should be parsed into a Document."""
        f = tmp_path / "test.md"
        f.write_text("# Hello\n\nThis is test content.")
        docs = parse_document(str(f))
        assert len(docs) == 1
        assert "test content" in docs[0].page_content
        assert docs[0].metadata["title"] == "Test"

    def test_parse_with_default_role(self, tmp_path: Path) -> None:
        """Default role should be added to metadata."""
        f = tmp_path / "doc.txt"
        f.write_text("content")
        docs = parse_document(str(f), default_role="senior_engineer")
        assert docs[0].metadata["allowed_roles"] == ["senior_engineer"]

    def test_parse_nonexistent_file(self) -> None:
        """A nonexistent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parse_document("/nonexistent/path.md")

    def test_parse_empty_file(self, tmp_path: Path) -> None:
        """An empty file should produce a Document with empty content."""
        f = tmp_path / "empty.md"
        f.write_text("")
        docs = parse_document(str(f))
        assert len(docs) == 1
        assert docs[0].page_content == ""
