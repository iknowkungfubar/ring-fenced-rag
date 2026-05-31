"""Version information for Ring-Fenced RAG.

Derives the version from git tags when available, falling back
to the static version string. The git tag version is preferred
because it always reflects the actual release state.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__title__ = "ring-fenced-rag"
__author__ = "Turin"

# Static fallback version (updated manually for each release)
_STATIC_VERSION = "1.0.0a1"


def _get_git_version() -> str | None:
    """Try to derive version from the most recent git tag.

    Returns:
        Version string like '1.0.0a1' or '1.0.0a1-3-gdeadbeef'
        (with commit count and hash when not exactly on a tag),
        or None if git is not available or not a git repo.
    """
    try:
        repo_root = Path(__file__).resolve().parent.parent.parent
        result = subprocess.run(
            ["git", "-C", str(repo_root), "describe", "--tags", "--dirty=-dirty"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            # Strip leading 'v' if present (e.g. v1.0.0 → 1.0.0)
            if version.startswith("v"):
                version = version[1:]
            return version
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def _get_version() -> str:
    """Get the current version.

    Checks, in order:
    1. Git tag (via git describe)
    2. Static fallback version

    Returns:
        Version string.
    """
    git_version = _get_git_version()
    if git_version:
        return git_version
    return _STATIC_VERSION


def _get_git_commit() -> str:
    """Get the short SHA of the current git commit.

    Returns:
        7-char commit hash, or 'unknown' if git is unavailable.
    """
    try:
        repo_root = Path(__file__).resolve().parent.parent.parent
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return "unknown"


__version__ = _get_version()
__git_commit__ = _get_git_commit()


def version_info() -> dict[str, str]:
    """Return a dictionary of version metadata for display.

    Returns:
        Dict with keys: version, git_commit, python, platform, title.
    """
    return {
        "title": __title__,
        "version": __version__,
        "git_commit": __git_commit__,
        "python": sys.version.split()[0],
        "platform": sys.platform,
    }
