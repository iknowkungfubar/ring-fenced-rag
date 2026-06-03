"""Final edge cases — parsing error paths, providers abstract method."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rfr.ingestion.parsing import parse_directory

if TYPE_CHECKING:
    from pathlib import Path


class TestParsingEdgeCases:
    """Error paths in document parsing."""

    def test_parse_directory_skips_binary_file(self, tmp_path: Path) -> None:
        """Binary files should be skipped, not crash the pipeline."""
        d = tmp_path / "sub"
        d.mkdir()
        bin_file = d / "binary.bin"
        bin_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe")
        txt_file = d / "good.txt"
        txt_file.write_text("Hello world")

        docs = parse_directory(str(tmp_path), glob_pattern="**/*")
        assert len(docs) >= 1
        assert any("good.txt" in doc.metadata.get("source", "") for doc in docs)

    def test_parse_directory_skips_unsupported_type(self, tmp_path: Path) -> None:
        """Unsupported file types should be skipped."""
        d = tmp_path / "mixed"
        d.mkdir()
        (d / "data.csv").write_text("a,b,c\n1,2,3")
        (d / "readme.md").write_text("# Hello")

        docs = parse_directory(str(tmp_path), glob_pattern="**/*")
        assert len(docs) == 1
        assert docs[0].metadata["file_type"] == "md"

    def test_parse_directory_empty_pattern(self, tmp_path: Path) -> None:
        """No matching files should return empty list."""
        (tmp_path / "readme.md").write_text("# Hello")
        docs = parse_directory(str(tmp_path), glob_pattern="**/*.xyz")
        assert docs == []
