"""Ring-Fenced RAG — test placeholder."""


def test_import() -> None:
    """Verify the package can be imported."""
    import rfr  # noqa: F401


def test_version() -> None:
    """Verify version string is set."""
    from rfr import __version__

    assert __version__ == "1.0.0a1"
