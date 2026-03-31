"""
Login endpoint: POST /auth/login with username/password, returns JWT access token.
GET /auth/me validates Bearer token and returns current user (sub).
Credentials are checked against env AUTH_USERNAME and AUTH_PASSWORD (or AUTH_PASSWORD_HASH).
"""

from fastapi import APIRouter, Depends

from app.auth_jwt import create_token, get_current_user
from app.config import (
    AUTH_PASSWORD,
    AUTH_PASSWORD_HASH,
    AUTH_USERNAME,
    AUTH_PREFERRED_LANGUAGE,
    JWT_EXPIRE_MINUTES,
)
from app.errors import api_error

router = APIRouter(prefix="/auth", tags=["Auth"])


def _verify_password(plain: str) -> bool:
    if AUTH_PASSWORD_HASH:
        from passlib.context import (
            CryptContext,
        )  # passlib je biblioteka za hashovanje i verifikaciju lozinki

        # CryptContext je klasa koja se koristi za hashovanje i verifikaciju lozinki
        # schemes je lista hash algoritama koje passlib podržava
        # deprecated je opcija koja omogućava korišćenje starijih hash algoritama
        # auto je opcija koja omogućava automatsko odabiranje najboljeg hash algoritma

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
    # LoginRequest je Pydantic model koji se koristi za validaciju ulaznih podataka
    """
    Authenticate with username and password. Returns JWT access token.
    Configure AUTH_USERNAME and AUTH_PASSWORD (or AUTH_PASSWORD_HASH) in .env.
    """
    if not AUTH_USERNAME:
        raise api_error(
            status_code=503,
            code="AUTH_NOT_CONFIGURED",
            message="Login not configured. Set AUTH_USERNAME and AUTH_PASSWORD (or AUTH_PASSWORD_HASH) in .env.",
            details=None,
        )
    if data.username != AUTH_USERNAME or not _verify_password(data.password):
        raise api_error(
            status_code=401,
            code="INVALID_CREDENTIALS",
            message="Invalid username or password.",
            details=None,
        )
    access_token = create_token(data.username)
    # Actual JWT expiry is set in create_token (auth_jwt) from JWT_EXPIRE_MINUTES.
    # expires_in is in seconds for the client (e.g. to show "Session expires in X" or to auto-logout).
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRE_MINUTES
        * 60,  # seconds; set JWT_EXPIRE_MINUTES in .env for real expiry
        "preferred_language": AUTH_PREFERRED_LANGUAGE,
    }


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    """
    Validate Bearer token and return current user. Returns 200 with {"sub": "username"}
    or 401 if token is missing/invalid/expired. Useful for the dashboard to ping and
    confirm the session is still valid without calling business endpoints.
    """
    return {"sub": user["sub"], "preferred_language": AUTH_PREFERRED_LANGUAGE}


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
