"""Document parsing — extract text and metadata from various source formats."""

from __future__ import annotations

import glob as glob_module
from pathlib import Path

from langchain_core.documents import Document

_SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf", ".html", ".json"}


def parse_document(path: str, default_role: str | None = None) -> list[Document]:
    """Parse a single document file into LangChain Document objects.

    Supports: .md, .txt, .pdf, .json, .html

    Args:
        path: Absolute or relative path to the document.
        default_role: Default role to assign if metadata lacks 'allowed_roles'.

    Returns:
        List of Document objects with content and metadata extracted.

    Raises:
        FileNotFoundError: If the path doesn't exist.
        ValueError: If the file type is unsupported.

    """
    filepath = Path(path)
    if not filepath.exists():
        raise FileNotFoundError(f"Document not found: {path}")

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

    Args:
        path: Root directory to search.
        glob_pattern: Glob pattern for matching files. Supports ** and * wildcards.
                      Brace expansion ({a,b}) is not supported; use separate patterns.
        default_role: Default role for documents without explicit role metadata.

    Returns:
        List of Document objects from all matched files.

    """
    root = Path(path)
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
            docs = parse_document(str(filepath), default_role)
            documents.extend(docs)
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(
                "Skipping %s: %s", filepath, e
            )

    return documents
