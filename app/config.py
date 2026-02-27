"""
Application configuration. Use environment variables to choose whether
fee calculation and payment status updates are done in the API or by the DB.

- When using a database that has triggers: set both to false (default).
- When using a database without those triggers: set both to true so the API
  computes ticket fee on exit and updates ticket payment_status after payments.

- API key: When API_KEY is set, all requests except GET /health must send
  header X-API-Key. When API_KEY is not set, no authentication is required.
  .env is loaded from the project root (parent of app/) so it is found
  regardless of the process current working directory.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]

# Load .env from project root (parent of app/) so it works even when the server
# is started from a different directory (e.g. python -m app.run from project root).
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

_log = logging.getLogger(__name__)

def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return default


# Optional API key. When set: auth middleware requires X-API-Key or Bearer JWT on every
# request except GET /, GET /health, POST /auth/login (401 otherwise). When not set: no auth required.
# Read once at startup so the middleware does not read env on every request.
API_KEY: str | None = os.getenv("API_KEY") or None

# JWT token auth (used for login; middleware accepts Bearer token or X-API-Key).
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES: int = _env_int("JWT_EXPIRE_MINUTES", 60 * 24)  # 24 hours

# Single-user login (env-only). When set, POST /auth/login accepts these credentials.
# For hashed password, set AUTH_PASSWORD_HASH (bcrypt) and leave AUTH_PASSWORD unset.
AUTH_USERNAME: str | None = os.getenv("AUTH_USERNAME") or None
AUTH_PASSWORD: str | None = os.getenv("AUTH_PASSWORD") or None
AUTH_PASSWORD_HASH: str | None = os.getenv("AUTH_PASSWORD_HASH") or None


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name, "false" if not default else "true").lower()
    return value in ("true", "1", "yes")


def _is_valid_cors_origin(origin: str) -> bool:
    """Origin must be http(s) only, no path, no spaces, no wildcard."""
    if not origin or " " in origin or "*" in origin:
        return False
    if not (origin.startswith("http://") or origin.startswith("https://")):
        return False
    # No path: after "://", rest must be host[:port] only (no slash)
    after_scheme = origin.split("://", 1)[-1]
    if "/" in after_scheme:
        return False
    return True


def _normalize_and_validate_cors_origins(raw: str) -> tuple[list[str], list[str]]:
    """Parse CORS_ORIGINS, normalize (strip), validate. Returns (valid, invalid)."""
    entries = [o.strip() for o in raw.split(",") if o.strip()]
    valid: list[str] = []
    invalid: list[str] = []
    seen: set[str] = set()
    for o in entries:
        normalized = o.rstrip("/")
        if not _is_valid_cors_origin(normalized):
            invalid.append(o)
            continue
        if normalized not in seen:
            seen.add(normalized)
            valid.append(normalized)
    return valid, invalid


# If True, API computes ticket fee and sets ticket_state to CLOSED on exit.
# If False, API only sets exit_time; fee/state expected from a DB trigger.
USE_API_FEE_CALCULATION: bool = _env_bool("USE_API_FEE_CALCULATION", default=False)

# If True, API recalculates ticket.payment_status after create/update/delete.
# If False, payment_status is expected to be updated by a DB trigger.
USE_API_PAYMENT_STATUS: bool = _env_bool("USE_API_PAYMENT_STATUS", default=False)

# CORS: set CORS_DISABLED=true to skip adding CORSMiddleware (server-only/same-origin).
CORS_DISABLED: bool = _env_bool("CORS_DISABLED", default=False)

# CORS: origins allowed for browser requests (CORS_ORIGINS env, comma-sep).
# Each origin must start with http:// or https://, no path, no spaces/wildcards.
# Invalid entries are skipped with a log warning; in production, invalid entries
# cause startup to fail. In production, CORS_ORIGINS must be set (no default).
_is_production = os.getenv("ENVIRONMENT", "").lower() in (
    "production",
    "prod",
) or os.getenv("ENV", "").lower() in ("production", "prod")
_cors_raw = os.getenv("CORS_ORIGINS", "").strip()
if _is_production and not CORS_DISABLED and not _cors_raw:
    raise ValueError(
        "In production, CORS_ORIGINS must be set to your frontend origin(s). "
        "Set ENVIRONMENT=production or ENV=production only when CORS_ORIGINS is set, "
        "or set CORS_DISABLED=true if you do not need CORS."
    )
_cors_valid, _cors_invalid = _normalize_and_validate_cors_origins(_cors_raw)
for inv in _cors_invalid:
    _log.warning(
        "CORS: invalid origin skipped (use http:// or https://, no path): %r",
        inv,
    )
if _cors_invalid and _is_production:
    raise ValueError(
        "CORS_ORIGINS has invalid entries in production; fix or remove them: "
        + ", ".join(repr(e) for e in _cors_invalid)
    )
_DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
CORS_ORIGINS: list[str] = _cors_valid if _cors_valid else _DEFAULT_CORS_ORIGINS

# Preflight cache (seconds). Browsers cache OPTIONS for this long.
CORS_MAX_AGE: int = _env_int("CORS_MAX_AGE", 600)

# Methods and headers allowed in CORS (explicit is safer than "*").
CORS_ALLOW_METHODS: list[str] = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]
CORS_ALLOW_HEADERS: list[str] = [
    "Content-Type",
    "Accept",
    "Authorization",
    "X-API-Key",
]
