"""Pose estimation service backed by RTMPose ONNX (HalPE26 layout).

Drop-in replacement for the MediaPipe-based service: exposes the same
``get_pose_landmarks`` / ``draw_landmarks_on_image`` interface so
``main.py`` and ``analysis.py`` are unchanged.

RTMPose outputs 26 HalPE26 keypoints (COCO-compatible for the first 17).
Leg keypoints are mapped onto the slot indices ``analysis`` expects
(MediaPipe convention): right leg 24/26/28/30/32, left leg 23/25/27/29/31.

Models are the official OpenMMLab ONNX SDK exports mirrored on Hugging
Face (Tau-J/RTMPose); fetch them with ``scripts/download_models.sh``.
"""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np

from .detector import PersonDetector
from .rtmpose import RTMPose

MODEL_DIR = Path(
    os.getenv("AGOS_MODEL_DIR",
              Path(__file__).resolve().parent.parent / "models"))

SLOT_RIGHT_HIP = 24
SLOT_RIGHT_KNEE = 26
SLOT_RIGHT_ANKLE = 28
SLOT_RIGHT_HEEL = 30
SLOT_RIGHT_FOOT = 32

SLOT_LEFT_HIP = 23
SLOT_LEFT_KNEE = 25
SLOT_LEFT_ANKLE = 27
SLOT_LEFT_HEEL = 29
SLOT_LEFT_FOOT = 31

HALPE_RIGHT_HIP = 12
HALPE_RIGHT_KNEE = 14
HALPE_RIGHT_ANKLE = 16
HALPE_RIGHT_HEEL = 25
HALPE_RIGHT_BIG_TOE = 21

HALPE_LEFT_HIP = 11
HALPE_LEFT_KNEE = 13
HALPE_LEFT_ANKLE = 15
HALPE_LEFT_HEEL = 24
HALPE_LEFT_BIG_TOE = 20

_SLOT_TO_HALPE = {
    SLOT_RIGHT_HIP: HALPE_RIGHT_HIP,
    SLOT_RIGHT_KNEE: HALPE_RIGHT_KNEE,
    SLOT_RIGHT_ANKLE: HALPE_RIGHT_ANKLE,
    SLOT_RIGHT_HEEL: HALPE_RIGHT_HEEL,
    SLOT_RIGHT_FOOT: HALPE_RIGHT_BIG_TOE,
    SLOT_LEFT_HIP: HALPE_LEFT_HIP,
    SLOT_LEFT_KNEE: HALPE_LEFT_KNEE,
    SLOT_LEFT_ANKLE: HALPE_LEFT_ANKLE,
    SLOT_LEFT_HEEL: HALPE_LEFT_HEEL,
    SLOT_LEFT_FOOT: HALPE_LEFT_BIG_TOE,
}

# skeleton edges (HalPE26 / COCO ids) used for the overlay
_SKELETON = [
    (15, 13), (13, 11), (16, 14), (14, 12), (11, 12), (5, 11), (6, 12),
    (5, 6), (5, 7), (6, 8), (7, 9), (8, 10), (1, 2), (0, 1), (0, 2),
    (1, 3), (2, 4), (17, 0), (18, 17), (20, 24), (21, 25),
]

MIN_KEYPOINT_CONFIDENCE = 0.5


def _detector() -> PersonDetector:
    return PersonDetector(MODEL_DIR)


def _rtmpose() -> RTMPose:
    return RTMPose(MODEL_DIR)


def get_pose_landmarks(image):
    """Run person detection + RTMPose estimation on one image.

    Returns ``(landmarks, pose_landmarks)``. ``landmarks`` is a
    MediaPipe-style list where the leg slots expected by
    ``analysis.analyze_angles`` are filled (see module docstring);
    ``pose_landmarks`` carries the raw keypoints for drawing. Returns
    ``(None, None)`` when no person is detected.
    """
    detector = _detector()
    rtmpose = _rtmpose()
    boxes = detector.detect(image)
    if not boxes:
        return None, None

    bbox = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
    keypoints, scores = rtmpose.estimate(image, bbox)

    info = {"keypoints": keypoints, "scores": scores}

    landmarks = [None] * 33
    for slot, halpe in _SLOT_TO_HALPE.items():
        x, y = keypoints[halpe]
        landmarks[slot] = SimpleNamespace(
            x=float(x),
            y=float(y),
            visibility=float(scores[halpe]),
        )
    return landmarks, info


def draw_landmarks_on_image(image, pose_landmarks):
    """Draw the detected skeleton on a copy of ``image``."""
    keypoints = pose_landmarks["keypoints"]
    scores = pose_landmarks["scores"]
    image_with_landmarks = image.copy()

    for i, j in _SKELETON:
        if scores[i] < MIN_KEYPOINT_CONFIDENCE or \
                scores[j] < MIN_KEYPOINT_CONFIDENCE:
            continue
        pt1 = tuple(map(int, keypoints[i]))
        pt2 = tuple(map(int, keypoints[j]))
        cv2.line(image_with_landmarks, pt1, pt2, (0, 255, 0), 2)

    for halpe in _SLOT_TO_HALPE.values():
        if scores[halpe] < MIN_KEYPOINT_CONFIDENCE:
            continue
        pt = tuple(map(int, keypoints[halpe]))
        cv2.circle(image_with_landmarks, pt, 5, (0, 0, 255), -1)

    return image_with_landmarks