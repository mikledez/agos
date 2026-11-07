from __future__ import annotations

import os
import uuid
from pathlib import Path

ALLOWED_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})
_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

def new_image_names(user_id: int, original_filename: str) -> tuple[str, str]:
    """Return unique (original, annotated) names for an uploaded image."""

    extension = Path(original_filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(
            f"unsupported image type {extension or '(none)'}; allowed: {allowed}"
        )

    stem = f"users/{user_id}/images/{uuid.uuid4().hex}"
    return f"{stem}{extension}", f"{stem}_annotated.jpg"

def media_type_for(relative_path: str | os.PathLike[str]) -> str:
    return _MEDIA_TYPES.get(
        Path(relative_path).suffix.lower(), "application/octet-stream"
    )
