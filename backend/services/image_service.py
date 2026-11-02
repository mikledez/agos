from __future__ import annotations

import base64
import math
import os
from typing import Any

import cv2
import numpy as np

from db import repository as repo

from . import storage
from .analysis import analyze_angles
from .pose import draw_landmarks_on_image, get_pose_landmarks

MAX_UPLOAD_BYTES = int(os.getenv("AGOS_MAX_UPLOAD_BYTES", 10 * 1024 * 1024))

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

def _file_paths(row: dict[str, Any]) -> list[str | None]:
    return [row.get("stored_filename"), row.get("annotated_path")]

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
    ok, encoded = cv2.imencode(".jpg", annotated)
    if not ok:
        raise ValueError("Could not encode annotated image")
    annotated_bytes = encoded.tobytes()

    stored_filename: str | None = None
    annotated_path: str | None = None
    try:
        stored_filename = storage.save_original(
            user_id, contents, original_filename
        )
        annotated_path = storage.save_annotated(
            user_id, annotated_bytes, stored_filename
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
    except Exception:
        storage.delete_paths([stored_filename, annotated_path])
        raise

    annotated_base64 = base64.b64encode(annotated_bytes).decode("utf-8")
    return row, result, annotated_base64

def delete_image(user_id: int, image_id: int) -> bool:
    row = repo.get_image(image_id, user_id)
    if row is None:
        return False
    if not repo.delete_image(image_id, user_id):
        return False
    storage.delete_paths(_file_paths(row))
    return True

def delete_session(user_id: int, session_id: int) -> bool:
    if repo.get_session(session_id, user_id) is None:
        return False
    files = repo.list_image_files(user_id, session_id=session_id)
    if not repo.delete_session(session_id, user_id):
        return False
    storage.delete_paths(path for row in files for path in _file_paths(row))
    return True

def delete_user(user_id: int) -> bool:
    files = repo.list_image_files(user_id)
    if not repo.delete_user(user_id):
        return False
    storage.delete_paths(path for row in files for path in _file_paths(row))
    return True
