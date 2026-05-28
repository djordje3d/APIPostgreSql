from typing import Any

from fastapi import HTTPException


def build_error_payload(
    code: str,
    message: str,
    details: Any = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }


def api_error(
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=build_error_payload(
            code=code,
            message=message,
            details=details,
        ),
    )
