"""Tests for the API auth module."""

from __future__ import annotations

from rfr.api.auth import generate_api_key, hash_api_key, verify_key


class TestGenerateApiKey:
    """Verify API key generation works correctly."""

    def test_key_format(self) -> None:
        """Generated keys should start with 'rfr_' and be hex."""
        raw, key_hash, prefix = generate_api_key()
        assert raw.startswith("rfr_")
        assert len(raw) > 10
        assert len(key_hash) == 64  # SHA-256 hex
        assert prefix == raw[:10]

    def test_key_hash_is_deterministic(self) -> None:
        """The same key should produce the same hash."""
        raw, _, _ = generate_api_key()
        h1 = hash_api_key(raw)
        h2 = hash_api_key(raw)
        assert h1 == h2

    def test_different_keys_different_hashes(self) -> None:
        """Different keys should produce different hashes."""
        raw1, _, _ = generate_api_key()
        raw2, _, _ = generate_api_key()
        assert hash_api_key(raw1) != hash_api_key(raw2)

    def test_verify_key_matches(self) -> None:
        """verify_key should return True for matching keys."""
        raw, key_hash, _ = generate_api_key()
        assert verify_key(raw, key_hash)

    def test_verify_key_fails_for_wrong_key(self) -> None:
        """verify_key should return False for wrong keys."""
        raw, key_hash, _ = generate_api_key()
        assert not verify_key(raw + "tampered", key_hash)

    def test_verify_key_constant_time(self) -> None:
        """verify_key should not leak timing with wrong length keys."""
        raw, key_hash, _ = generate_api_key()
        assert not verify_key("short", key_hash)
        assert not verify_key(raw.upper(), key_hash)
