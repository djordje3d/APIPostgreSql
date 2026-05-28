"""Compatibility package that points `app.*` imports to `api/app`.

This keeps existing absolute imports (`from app...`) working after moving the
backend under `api/`.
"""

from pathlib import Path

__path__ = [str(Path(__file__).resolve().parent.parent / "api" / "app")]
