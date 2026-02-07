"""
Uvicorn entry point. Run from project root with:
  python -m app.run
Optional env: HOST (default 0.0.0.0), PORT (default 8000), RELOAD (default true for dev).
"""
import os
import uvicorn

_HOST = os.getenv("HOST", "0.0.0.0")
_PORT = int(os.getenv("PORT", "8000"))
_RELOAD = os.getenv("RELOAD", "true").lower() in ("true", "1", "yes")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=_HOST,
        port=_PORT,
        reload=_RELOAD,
    )
