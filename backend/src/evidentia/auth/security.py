"""Security utilities: password hashing and dual JWT (15m access / 7d refresh)."""

from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from evidentia.config import get_settings


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with 100,000 iterations and 16-byte salt."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against salt$hash representation using constant-time comparison."""
    try:
        salt_hex, hash_hex = hashed_password.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected_dk = bytes.fromhex(hash_hex)
        actual_dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100_000)
        return secrets.compare_digest(actual_dk, expected_dk)
    except Exception:
        return False


def hash_token(raw_token: str) -> str:
    """Hash a raw token string (e.g. refresh token) for safe storage in the database."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """Create a 15-minute access token."""
    settings = get_settings()
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "access",
    })
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> tuple[str, str, datetime]:
    """Create a 7-day refresh token. Returns (raw_token, token_hash, expires_at)."""
    settings = get_settings()
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.refresh_token_expire_days))
    # Add unique jti to ensure refresh tokens are always unique
    jti = secrets.token_urlsafe(32)
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": jti,
        "type": "refresh",
    })
    raw_token = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    token_h = hash_token(raw_token)
    return raw_token, token_h, expire


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
