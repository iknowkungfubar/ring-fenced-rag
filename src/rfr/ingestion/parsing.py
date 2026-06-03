"""Document parsing — extract text and metadata from various source formats.

Includes security controls:
- Path traversal sanitization (rejects paths escaping allowed directories)
- File size limits (configurable via RFR_INGEST__MAX_FILE_SIZE_MB)
- Content-based MIME validation (magic byte checks for known formats)
"""

from __future__ import annotations

import glob as glob_module
import logging
import os
from pathlib import Path

from langchain_core.documents import Document

from rfr.config import AppConfig

logger = logging.getLogger(__name__)

_SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf", ".html", ".json"}

# Magic byte signatures for content-based MIME validation.
# Each entry maps a file extension to a byte prefix or tuple of prefixes
# that the file content must start with.
_MAGIC_SIGNATURES: dict[str, bytes | tuple[bytes, ...]] = {
    ".pdf": b"%PDF",
    ".html": (b"<html", b"<!DOCTYPE"),
    ".json": (b"{", b"["),
}


def _validate_content_magic(filepath: Path) -> None:
    """Verify the file's magic bytes match its extension.

    Reads the first few bytes of the file and checks them against known
    signatures for the file's extension.  Extensions without a known
    signature (e.g. .md, .txt) are skipped.

    Args:
        filepath: Path to the file to validate.

    Raises:
        ValueError: If the file content does not match the expected
                    magic bytes for its extension.

    """
    ext = filepath.suffix.lower()
    if ext not in _MAGIC_SIGNATURES:
        return  # No magic known for this extension — skip validation

    signatures = _MAGIC_SIGNATURES[ext]
    if isinstance(signatures, bytes):
        signatures = (signatures,)

    max_len = max(len(sig) for sig in signatures)
    try:
        with filepath.open("rb") as f:
            header = f.read(max_len)
    except OSError as e:
        raise ValueError(f"Unable to read magic bytes from '{filepath}': {e}") from e

    if not any(header.startswith(sig) for sig in signatures):
        expected = " or ".join(repr(s) for s in signatures)
        actual_repr = repr(header[:max_len])
        raise ValueError(
            f"Content MIME mismatch for '{filepath}': expected header "
            f"starting with {expected}, got {actual_repr}. "
            "The file extension does not match its actual content."
        )


def _resolve_safe_path(path: str, allowed_base: Path | None = None) -> Path:
    """Resolve a path and verify it stays within the allowed base directory.

    Args:
        path: The user-supplied path to resolve.
        allowed_base: The directory that resolved paths must remain under.
                      If None, only basic traversal checks are performed.

    Returns:
        Resolved Path object.

    Raises:
        ValueError: If the path contains '..' traversal that escapes
                    the allowed base directory.

    """
    resolved = Path(path).resolve()

    # Check for path traversal — reject if resolved path contains '..'
    # segments that escape the intended directory
    if ".." in Path(path).parts:
        raise ValueError(
            f"Path traversal detected: '{path}' contains '..' segments. "
            "Refusing to resolve paths outside the intended directory.",
        )

    if allowed_base is not None:
        allowed = allowed_base.resolve()
        try:
            resolved.relative_to(allowed)
        except ValueError:
            raise ValueError(
                f"Path traversal blocked: resolved path '{resolved}' "
                f"is outside the allowed base directory '{allowed}'.",
            ) from None

    return resolved


def _check_file_size(filepath: Path) -> None:
    """Check that a file does not exceed the configured maximum size.

    Args:
        filepath: Path to the file to check.

    Raises:
        ValueError: If the file exceeds the maximum allowed size.

    """
    max_size_mb = AppConfig().ingestion.max_file_size_mb
    max_size_bytes = max_size_mb * 1024 * 1024

    try:
        size = os.path.getsize(str(filepath))
    except OSError as e:
        raise ValueError(f"Unable to determine file size for '{filepath}': {e}") from e

    if size > max_size_bytes:
        raise ValueError(
            f"File '{filepath}' ({size / (1024 * 1024):.1f} MB) exceeds "
            f"the maximum allowed size of {max_size_mb} MB. "
            "Adjust RFR_INGEST__MAX_FILE_SIZE_MB if needed.",
        )


def parse_document(
    path: str,
    default_role: str | None = None,
    allowed_base: Path | None = None,
) -> list[Document]:
    """Parse a single document file into LangChain Document objects.

    Supports: .md, .txt, .pdf, .json, .html

    Security:
        - Path traversal is detected and blocked.
        - File size is checked against the configured limit (default 100 MB).
        - Content-based MIME validation ensures the file's magic bytes
          match its declared extension.

    Args:
        path: Absolute or relative path to the document.
        default_role: Default role to assign if metadata lacks 'allowed_roles'.
        allowed_base: Optional base directory for path traversal checks.

    Returns:
        List of Document objects with content and metadata extracted.

    Raises:
        FileNotFoundError: If the path doesn't exist.
        ValueError: If the file type is unsupported, path traversal is
                    detected, the file exceeds size limits, or its content
                    does not match the expected format.

    """
    # Resolve path with traversal protection
    filepath = _resolve_safe_path(path, allowed_base)

    if not filepath.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    # Check file size before reading
    _check_file_size(filepath)

    # Content-based MIME validation (magic bytes)
    _validate_content_magic(filepath)

    content = filepath.read_text(encoding="utf-8")

    metadata: dict[str, str | list[str]] = {
        "source": str(filepath),
        "doc_id": filepath.stem,
        "title": filepath.stem.replace("_", " ").replace("-", " ").title(),
        "file_type": filepath.suffix.lstrip("."),
    }

    if default_role:
        metadata["allowed_roles"] = [default_role]

    return [Document(page_content=content, metadata=metadata)]


def parse_directory(
    path: str,
    glob_pattern: str = "**/*",
    default_role: str | None = None,
) -> list[Document]:
    """Parse all matching documents in a directory.

    Security:
        - Path traversal is detected and blocked.
        - Each file is checked against the configured size limit (default 100 MB).
        - Content-based MIME validation is applied per file.

    Args:
        path: Root directory to search.
        glob_pattern: Glob pattern for matching files. Supports ** and * wildcards.
                      Brace expansion ({a,b}) is not supported; use separate patterns.
        default_role: Default role for documents without explicit role metadata.

    Returns:
        List of Document objects from all matched files.

    Raises:
        NotADirectoryError: If the given path is not a directory.
        ValueError: If path traversal is detected.

    """
    root = _resolve_safe_path(path)

    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")

    documents: list[Document] = []

    # Use glob.glob for better pattern support (recursive **)
    matched = glob_module.glob(glob_pattern, root_dir=str(root), recursive=True)

    for rel_path in sorted(matched):
        filepath = root / rel_path
        if not filepath.is_file():
            continue
        # Check file extension against supported types
        if filepath.suffix.lower() not in _SUPPORTED_EXTENSIONS:
            continue
        try:
            docs = parse_document(str(filepath), default_role, allowed_base=root)
            documents.extend(docs)
        except ValueError as e:
            logger.warning("Skipping %s: %s", filepath, e)

    return documents
