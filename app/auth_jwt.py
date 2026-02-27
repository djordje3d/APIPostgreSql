"""
JWT create/verify and FastAPI dependencies for token auth.
Used by auth middleware (Bearer token) and by login endpoint (create_token).
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Request
from jose import JWTError, jwt

from app.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET_KEY

TOKEN_SUB_KEY = "sub"  # username in payload


def create_token(username: str) -> str:
    """Create a signed JWT with expiry. Payload includes sub=username."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        TOKEN_SUB_KEY: username,
        "exp": expire,
        "iat": now,
    }
    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def verify_token(token: str) -> dict[str, Any] | None:
    """
    Decode and validate JWT. Returns payload (with 'sub') or None if
    invalid/expired.
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        if not payload.get(TOKEN_SUB_KEY):
            return None
        return payload
    except JWTError:
        return None


def get_bearer_token(request: Request) -> str | None:
    """Extract Bearer token from Authorization header."""
    auth = (
        request.headers.get("Authorization")
        or request.headers.get("authorization")
    )
    if not auth or not auth.startswith("Bearer "):
        return None
    return auth[7:].strip() or None


def get_current_user_optional(request: Request) -> dict[str, Any] | None:
    """
    FastAPI dependency: return JWT payload (with 'sub') if valid Bearer token present, else None.
    """
    token = get_bearer_token(request)
    if not token:
        return None
    return verify_token(token)


def get_current_user(request: Request) -> dict[str, Any]:
    """
    FastAPI dependency: return JWT payload; raise 401 if no valid Bearer token.
    """
    from fastapi import HTTPException

    user = get_current_user_optional(request)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid or missing token. Use Authorization: Bearer <token> "
                "or X-API-Key."
            ),
        )
    return user
