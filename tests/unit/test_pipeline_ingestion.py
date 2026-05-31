"""Comprehensive tests for ingestion pipeline — with mocked vector store."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rfr.ingestion.pipeline import IngestionError, ingest_documents


class TestIngestDocuments:
    """All ingest_documents code paths with mocked dependencies."""

    @patch("rfr.ingestion.pipeline.parse_document")
    @patch("rfr.ingestion.pipeline.chunk_document")
    @patch("rfr.ingestion.pipeline.SQLRecordManager")
    @patch("rfr.ingestion.pipeline.index")
    def test_ingest_single_file(
        self,
        mock_index: MagicMock,
        mock_record_mgr: MagicMock,
        mock_chunk: MagicMock,
        mock_parse: MagicMock,
    ) -> None:
        """Ingesting a single file should succeed."""
        mock_parse.return_value = [MagicMock()]
        mock_chunk.return_value = [MagicMock()]
        mock_index.return_value = {
            "num_added": 1,
            "num_updated": 0,
            "num_skipped": 0,
            "num_deleted": 0,
        }

        result = ingest_documents(
            source="/tmp/test.md",
            vector_store=MagicMock(),
            db_url="sqlite://",
        )
        assert result["num_added"] == 1
        mock_parse.assert_called_once()
        mock_chunk.assert_called_once()

    @patch("rfr.ingestion.pipeline.parse_directory")
    @patch("rfr.ingestion.pipeline.chunk_document")
    @patch("rfr.ingestion.pipeline.SQLRecordManager")
    @patch("rfr.ingestion.pipeline.index")
    def test_ingest_directory(
        self,
        mock_index: MagicMock,
        mock_record_mgr: MagicMock,
        mock_chunk: MagicMock,
        mock_parse_dir: MagicMock,
    ) -> None:
        """Ingesting a directory should succeed."""
        mock_parse_dir.return_value = [MagicMock(), MagicMock()]
        mock_chunk.return_value = [MagicMock()]
        mock_index.return_value = {
            "num_added": 1,
            "num_updated": 0,
            "num_skipped": 0,
            "num_deleted": 0,
        }

        with patch("os.path.isdir", return_value=True):
            result = ingest_documents(
                source="/tmp/docs",
                vector_store=MagicMock(),
                db_url="sqlite://",
            )
        assert result["num_added"] == 1

    @patch("rfr.ingestion.pipeline.parse_document")
    def test_ingest_error_raises(self, mock_parse: MagicMock) -> None:
        """When parsing fails, IngestionError should be raised."""
        mock_parse.side_effect = ValueError("Parse failed")

        with pytest.raises(IngestionError):
            ingest_documents(
                source="/tmp/test.md",
                vector_store=MagicMock(),
                db_url="sqlite://",
            )

    @patch("rfr.ingestion.pipeline.parse_document")
    @patch("rfr.ingestion.pipeline.chunk_document")
    @patch("rfr.ingestion.pipeline.SQLRecordManager")
    @patch("rfr.ingestion.pipeline.index")
    def test_empty_documents_skipped(
        self,
        mock_index: MagicMock,
        mock_record_mgr: MagicMock,
        mock_chunk: MagicMock,
        mock_parse: MagicMock,
    ) -> None:
        """Empty documents should return zero counts."""
        mock_parse.return_value = []

        result = ingest_documents(
            source="/tmp/empty.md",
            vector_store=MagicMock(),
            db_url="sqlite://",
        )
        assert result["num_added"] == 0
        mock_chunk.assert_not_called()


class TestIngestionError:
    """IngestionError behavior."""

    def test_error_message(self) -> None:
        err = IngestionError("Test error")
        assert str(err) == "Test error"

    def test_error_is_exception(self) -> None:
        assert issubclass(IngestionError, Exception)
