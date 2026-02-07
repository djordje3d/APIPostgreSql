"""
API key authentication. When API_KEY is set in the environment, all requests
(except GET /health) must include header: X-API-Key: <API_KEY>.
When API_KEY is not set, no authentication is required (e.g. local development).
Uses API_KEY from app.config (read once at startup) to avoid reading env on every request.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import API_KEY

API_KEY_HEADER = "X-API-Key"


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Require X-API-Key header when API_KEY is set in config; GET /health is always allowed."""

    async def dispatch(self, request: Request, call_next):
        if not API_KEY:
            return await call_next(request)

        if request.url.path == "/health" and request.method == "GET":
            return await call_next(request)

        key = request.headers.get(API_KEY_HEADER) or request.headers.get("x-api-key")
        if key != API_KEY:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key. Set X-API-Key header."},
            )
        return await call_next(request)
