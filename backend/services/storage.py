from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = Path(
    os.getenv("AGOS_UPLOAD_DIR", BASE_DIR / "uploads")
).expanduser().resolve()

ALLOWED_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})
_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

def resolve(relative_path: str | os.PathLike[str]) -> Path:

    path = (UPLOAD_DIR / relative_path).resolve()
    if not path.is_relative_to(UPLOAD_DIR):
        raise ValueError(f"path escapes upload directory: {relative_path!r}")
    return path

def _write(relative_path: str, contents: bytes) -> Path:
    path = resolve(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(contents)
    return path

def save_original(
    user_id: int, contents: bytes, original_filename: str
) -> str:

    extension = Path(original_filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(
            f"unsupported image type {extension or '(none)'}; allowed: {allowed}"
        )

    relative_path = (
        f"users/{user_id}/images/{uuid.uuid4().hex}{extension}"
    )
    _write(relative_path, contents)
    return relative_path

def save_annotated(
    user_id: int, contents: bytes, stored_filename: str
) -> str:

    stem = Path(stored_filename).stem
    relative_path = f"users/{user_id}/images/{stem}_annotated.jpg"
    _write(relative_path, contents)
    return relative_path

def delete_paths(paths: Iterable[str | None]) -> None:

    for relative_path in paths:
        if not relative_path:
            continue
        try:
            resolve(relative_path).unlink(missing_ok=True)
        except (OSError, ValueError) as exc:
            logger.warning("could not delete %s: %s", relative_path, exc)

def media_type_for(relative_path: str | os.PathLike[str]) -> str:
    return _MEDIA_TYPES.get(
        Path(relative_path).suffix.lower(), "application/octet-stream"
    )
