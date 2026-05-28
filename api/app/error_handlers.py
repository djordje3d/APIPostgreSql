from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.errors import build_error_payload


def _legacy_detail_to_fields(detail: list[dict]) -> list[dict[str, str]]:
    fields: list[dict[str, str]] = []
    for err in detail:
        loc = [str(x) for x in err.get("loc", []) if x != "body"]
        fields.append(
            {
                "field": ".".join(loc) or "body",
                "message": err.get("msg", "Invalid value"),
            }
        )
    return fields


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=build_error_payload(
                code="HTTP_ERROR",
                message=str(exc.detail),
                details=None,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return JSONResponse(
            status_code=422,
            content=build_error_payload(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details={"fields": _legacy_detail_to_fields(exc.errors())},
            ),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=build_error_payload(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected server error occurred.",
                details=None,
            ),
        )
