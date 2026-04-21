"""
API key and JWT Bearer authentication. When API_KEY is set, requests (except
public paths) must include either Authorization: Bearer <jwt> or X-API-Key.
When API_KEY is not set, no authentication is required (e.g. local development).
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.auth_jwt import verify_token
from app.config import API_KEY
from app.errors import build_error_payload

API_KEY_HEADER = "X-API-Key"


# Paths that do not require auth (method-sensitive where needed).


def _is_public_path(path: str, method: str) -> bool:
    if path == "/" and method == "GET":
        return True
    if path == "/health" and method == "GET":
        return True
    if path == "/auth/login" and method == "POST":
        return True
    if path.startswith("/uploads/") and method == "GET":
        return True

    # FastAPI docs/OpenAPI endpoints
    if method == "GET" and path in {
        "/docs",
        "/openapi.json",
        "/redoc",
        "/docs/oauth2-redirect",
    }:
        return True

    return False


# APIKeyMiddleware is a class that is used to authenticate the request
class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Require either valid Bearer JWT or X-API-Key when API_KEY is set.
    GET /, GET /health, POST /auth/login are always allowed.
    """

    # call_next is a function that is used to call the next middleware or endpoint

    async def dispatch(self, request: Request, call_next):
        if _is_public_path(request.url.path, request.method):
            return await call_next(request)

        if not API_KEY:
            return await call_next(request)

        # Accept Bearer token
        auth = request.headers.get("Authorization") or request.headers.get(
            "authorization"
        )
        if auth and auth.startswith("Bearer "):
            token = auth[7:].strip()
            if token and verify_token(token):
                return await call_next(request)

        # Accept API key
        key = request.headers.get(API_KEY_HEADER) or request.headers.get("x-api-key")
        if key == API_KEY:
            return await call_next(request)

        return JSONResponse(
            status_code=401,
            content=build_error_payload(
                code="UNAUTHORIZED",
                message=(
                    "Invalid or missing authentication. Use Authorization: "
                    "Bearer <token> or X-API-Key header."
                ),
                details=None,
            ),
        )
