"""Upload endpoints (e.g. ticket image).

Client resizes before upload; server only validates and stores.
"""

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile

from app.config import UPLOAD_DIR, UPLOAD_TICKET_IMAGE_MAX_BYTES
from app.errors import api_error

router = APIRouter(tags=["Upload"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
CONTENT_TYPE_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
TICKET_IMAGE_SUBDIR = "tickets"


def _ext_from_content_type(content_type: str | None) -> str:
    if (
        content_type
        and content_type.split(";")[0].strip().lower() in CONTENT_TYPE_TO_EXT
    ):
        return CONTENT_TYPE_TO_EXT[content_type.split(";")[0].strip().lower()]
    return ".jpg"


def _safe_ext(filename: str | None) -> str:
    if not filename or "." not in filename:
        return ".jpg"
    ext = "." + filename.rsplit(".", 1)[-1].lower()
    return ext if ext in ALLOWED_EXTENSIONS else ".jpg"


@router.post("/ticket-image")
async def upload_ticket_image(
    file: UploadFile = File(
        ...,
        description="Image (JPEG/PNG/WebP); client resizes before upload",
    ),
):
    """
    Upload a ticket image. Returns URL path to use as ticket image_url.
    Max size: UPLOAD_TICKET_IMAGE_MAX_BYTES. Allowed: JPEG, PNG, WebP.
    """
    content_type = (file.content_type or "").split(";")[0].strip().lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise api_error(
            422,
            "INVALID_IMAGE_FORMAT",
            "Invalid image type.",
            details={"allowed_types": sorted(ALLOWED_CONTENT_TYPES)},
        )

    content = await file.read()
    if len(content) > UPLOAD_TICKET_IMAGE_MAX_BYTES:
        raise api_error(
            422,
            "IMAGE_TOO_LARGE",
            "Image exceeds maximum allowed size.",
            details={"max_bytes": UPLOAD_TICKET_IMAGE_MAX_BYTES},
        )

    ext = _ext_from_content_type(file.content_type) or _safe_ext(file.filename)
    filename = f"ticket_{uuid4().hex}{ext}"
    subdir = Path(UPLOAD_DIR) / TICKET_IMAGE_SUBDIR
    subdir.mkdir(parents=True, exist_ok=True)
    target = subdir / filename
    target.write_bytes(content)

    return {"url": f"/uploads/{TICKET_IMAGE_SUBDIR}/{filename}"}
