"""Extended tests for auth module — bearer token extraction, key operations."""

from __future__ import annotations

from unittest.mock import MagicMock

from rfr.api.auth import extract_bearer_token, generate_api_key, hash_api_key, verify_key


class TestExtractBearerToken:
    """Verify bearer token extraction works correctly."""

    def test_valid_bearer_token(self) -> None:
        """A valid Bearer token should be extracted."""
        request = MagicMock()
        request.headers = {"Authorization": "Bearer rfr_test12345"}
        result = extract_bearer_token(request)
        assert result == "rfr_test12345"

    def test_missing_header(self) -> None:
        """Missing Authorization header should return None."""
        request = MagicMock()
        request.headers = {}
        result = extract_bearer_token(request)
        assert result is None

    def test_non_bearer_auth(self) -> None:
        """Non-Bearer Authorization should return None."""
        request = MagicMock()
        request.headers = {"Authorization": "Basic dXNlcjpwYXNz"}
        result = extract_bearer_token(request)
        assert result is None

    def test_empty_bearer(self) -> None:
        """Bearer with no token should return empty string."""
        request = MagicMock()
        request.headers = {"Authorization": "Bearer "}
        result = extract_bearer_token(request)
        assert result == ""

    def test_malformed_header(self) -> None:
        """Completely malformed header should return None."""
        request = MagicMock()
        request.headers = {"Authorization": "NotEvenAnAuth"}
        result = extract_bearer_token(request)
        assert result is None


class TestKeyOperations:
    """Verify key generation, hashing, and verification."""

    def test_generate_returns_three_values(self) -> None:
        """generate_api_key should return raw, hash, and prefix."""
        raw, key_hash, prefix = generate_api_key()
        assert isinstance(raw, str)
        assert isinstance(key_hash, str)
        assert isinstance(prefix, str)
        assert len(key_hash) == 64  # SHA-256 hex
        assert prefix == raw[:10]

    def test_hash_is_sha256(self) -> None:
        """Key hash should be a 64-char hex string (SHA-256)."""
        raw, _, _ = generate_api_key()
        h = hash_api_key(raw)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_verify_correct_key(self) -> None:
        """verify_key should return True for matching key/hash."""
        raw, key_hash, _ = generate_api_key()
        assert verify_key(raw, key_hash)

    def test_verify_wrong_key(self) -> None:
        """verify_key should return False for wrong key."""
        raw, key_hash, _ = generate_api_key()
        wrong_key = raw[:-1] + ("x" if raw[-1] != "x" else "y")
        assert not verify_key(wrong_key, key_hash)

    def test_verify_different_hash(self) -> None:
        """verify_key should return False with different hash."""
        raw, _, _ = generate_api_key()
        _, other_hash, _ = generate_api_key()
        assert not verify_key(raw, other_hash)
