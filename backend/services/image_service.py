from __future__ import annotations

import base64
import logging
import math
import os
from typing import Any

import cv2
import numpy as np

from db import repository as repo

from . import storage
from .analysis import analyze_angles
from .pose import draw_landmarks_on_image, get_pose_landmarks

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = int(os.getenv("AGOS_MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
IMAGE_RETENTION_HOURS = int(os.getenv("AGOS_IMAGE_RETENTION_HOURS", 48))
ANNOTATED_JPEG_QUALITY = 85

def _assert_finite(result: dict[str, Any]) -> None:
    message = "Low confidence pose: cannot compute angles"
    for leg_key in ("swing_leg", "stance_leg"):
        leg = result.get(leg_key) or {}
        for angle in ("hip_angle", "knee_angle", "ankle_angle"):
            value = leg.get(angle)
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError(message)
    thigh = result.get("thigh_thigh_angle")
    if isinstance(thigh, float) and not math.isfinite(thigh):
        raise ValueError(message)

def analyze_and_store(
    user_id: int,
    *,
    contents: bytes,
    original_filename: str,
    phase: str,
    direction: str,
    session_id: int | None = None,
) -> tuple[dict[str, Any], dict[str, Any], str]:

    if len(contents) > MAX_UPLOAD_BYTES:
        raise ValueError(
            f"image is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB"
        )
    if phase not in repo.PHASES:
        raise ValueError(f"unknown phase: {phase}")
    if direction not in repo.DIRECTIONS:
        raise ValueError(f"unknown direction: {direction}")

    image = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Invalid image file")

    landmarks, pose_landmarks = get_pose_landmarks(image)
    if landmarks is None:
        raise ValueError("No pose detected")

    try:
        result = analyze_angles(landmarks, phase, direction)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    _assert_finite(result)

    annotated = draw_landmarks_on_image(image, pose_landmarks)
    ok, encoded = cv2.imencode(
        ".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, ANNOTATED_JPEG_QUALITY]
    )
    if not ok:
        raise ValueError("Could not encode annotated image")
    annotated_bytes = encoded.tobytes()

    stored_filename, annotated_path = storage.new_image_names(
        user_id, original_filename
    )
    row = repo.create_image_from_analysis(
        user_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        phase=phase,
        direction=direction,
        result=result,
        session_id=session_id,
        annotated_path=annotated_path,
    )
    try:
        repo.save_image_files(
            row["id"], user_id, original=contents, annotated=annotated_bytes
        )
    except Exception:
        repo.delete_image(row["id"], user_id)
        raise

    annotated_base64 = base64.b64encode(annotated_bytes).decode("utf-8")
    return row, result, annotated_base64

def delete_image(user_id: int, image_id: int) -> bool:
    return repo.delete_image(image_id, user_id)

def delete_session(user_id: int, session_id: int) -> bool:
    return repo.delete_session(session_id, user_id)

def delete_user(user_id: int) -> bool:
    return repo.delete_user(user_id)

def purge_inactive_images() -> int:
    deleted = repo.delete_inactive_images(IMAGE_RETENTION_HOURS)
    if deleted:
        logger.info("deleted %d inactive images", deleted)
    return deleted
