"""
Login endpoint: POST /auth/login with username/password, returns JWT access token.
GET /auth/me validates Bearer token and returns current user (sub).
Credentials are checked against env AUTH_USERNAME and AUTH_PASSWORD (or AUTH_PASSWORD_HASH).
"""

from fastapi import APIRouter, Depends, HTTPException

from app.auth_jwt import create_token, get_current_user
from app.config import (
    AUTH_PASSWORD,
    AUTH_PASSWORD_HASH,
    AUTH_USERNAME,
    JWT_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


def _verify_password(plain: str) -> bool:
    if AUTH_PASSWORD_HASH:
        from passlib.context import CryptContext

        ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return ctx.verify(plain, AUTH_PASSWORD_HASH)
    if AUTH_PASSWORD is not None:
        return plain == AUTH_PASSWORD
    return False


from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(data: LoginRequest):
    """
    Authenticate with username and password. Returns JWT access token.
    Configure AUTH_USERNAME and AUTH_PASSWORD (or AUTH_PASSWORD_HASH) in .env.
    """
    if not AUTH_USERNAME:
        raise HTTPException(
            status_code=503,
            detail="Login not configured. Set AUTH_USERNAME and AUTH_PASSWORD (or AUTH_PASSWORD_HASH) in .env.",
        )
    if data.username != AUTH_USERNAME or not _verify_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token = create_token(data.username)
    # Actual JWT expiry is set in create_token (auth_jwt) from JWT_EXPIRE_MINUTES.
    # expires_in is in seconds for the client (e.g. to show "Session expires in X" or to auto-logout).
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRE_MINUTES * 60,  # seconds; set JWT_EXPIRE_MINUTES in .env for real expiry
    }


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    """
    Validate Bearer token and return current user. Returns 200 with {"sub": "username"}
    or 401 if token is missing/invalid/expired. Useful for the dashboard to ping and
    confirm the session is still valid without calling business endpoints.
    """
    return {"sub": user["sub"]}


@router.post("/refresh")
def refresh(user: dict = Depends(get_current_user)):
    """
    Issue a new access token while the current one is still valid (e.g. after user
    activity to extend the session). Returns the same shape as login: access_token,
    token_type, expires_in.
    """
    access_token = create_token(user["sub"])
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRE_MINUTES * 60,
    }
