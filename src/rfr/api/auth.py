"""Authentication module — API key hashing, verification, and role extraction.

Uses BLAKE2b (via hashlib) for key hashing and constant-time HMAC comparison.
Keys are formatted as: rfr_<32-hex-chars>
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from fastapi import HTTPException, Request
from fastapi import status as http_status

from rfr.config import AppConfig


def generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key.

    Returns:
        Tuple of (raw_key, key_hash, key_prefix).
        The raw key should be shown once and then discarded.
        The hash is stored in the database.
        The prefix is used for key identification in listings.

    """
    raw = "rfr_" + secrets.token_hex(32)
    key_hash = hashlib.blake2b(raw.encode(), digest_size=32).hexdigest()
    key_prefix = raw[:10]
    return raw, key_hash, key_prefix


def hash_api_key(raw_key: str) -> str:
    """Hash an API key for storage/comparison.

    Uses BLAKE2b (256-bit digest) — the standard choice for API key hashing
    (GitHub, GitLab, and others use similar keyed-hash constructions for
    their API tokens).

    Args:
        raw_key: The full API key string.

    Returns:
        BLAKE2b hex digest of the key.

    """
    return hashlib.blake2b(raw_key.encode(), digest_size=32).hexdigest()


def verify_key(raw_key: str, stored_hash: str) -> bool:
    """Verify a raw key against a stored hash using constant-time comparison.

    Args:
        raw_key: The raw API key to verify.
        stored_hash: The stored BLAKE2b hash.

    Returns:
        True if the key matches, False otherwise.

    """
    computed = hash_api_key(raw_key)
    return hmac.compare_digest(computed, stored_hash)


def extract_bearer_token(request: Request) -> str | None:
    """Extract Bearer token from the Authorization header.

    Args:
        request: The FastAPI request object.

    Returns:
        The token string, or None if not present or malformed.

    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


async def get_current_role(
    request: Request,
) -> str:
    """Extract and validate the user's role from the API key.

    For v1, this is a simplified implementation that:
    1. Extracts the Bearer token
    2. Hashes it using BLAKE2b
    3. Looks up the hash in the database
    4. Returns the associated role

    If auth is disabled in config, returns a default role.

    Args:
        request: The FastAPI request.
        authorization: The Authorization header.

    Returns:
        The user's role string.

    Raises:
        HTTPException: If the key is invalid, inactive, or missing.

    """
    cfg = AppConfig()

    if not cfg.auth.enabled:
        return cfg.ingestion.default_role

    token = extract_bearer_token(request)
    if token is None:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
        )

    key_hash = hash_api_key(token)

    from rfr.models.database import create_session
    from rfr.models.orm import ApiKey

    with create_session() as session:
        key_record = (
            session.query(ApiKey)
            .filter(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True))
            .first()
        )
        if key_record is None:
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or deactivated API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Update last_used_at
        from datetime import UTC, datetime

        key_record.last_used_at = datetime.now(UTC)
        session.commit()

        return key_record.role


async def require_admin_role(
    request: Request,
) -> str:
    """Require the caller to have an admin role.

    Same as get_current_role, but raises 403 if the role is not in the admin list.
    """
    role = await get_current_role(request)
    cfg = AppConfig()
    if role not in cfg.auth.admin_roles:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=f"Admin role required. Current role: {role}",
        )
    return role
