"""Affine crop helpers for top-down pose estimation.

Ported from rtmlib (https://github.com/Tau-J/rtmlib, MIT license), which
mirrors the exact preprocessing the official OpenMMLab RTMPose ONNX SDK
exports expect.
"""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np


def bbox_xyxy2cs(bbox: np.ndarray,
                 padding: float = 1.25) -> Tuple[np.ndarray, np.ndarray]:
    """Convert an xyxy bounding box into (center, scale).

    ``scale`` is the box size (w, h) multiplied by the padding factor.
    """
    x1, y1, x2, y2 = bbox.astype(np.float32)
    center = np.array([(x1 + x2) * 0.5, (y1 + y2) * 0.5], dtype=np.float32)
    scale = np.array([(x2 - x1) * padding, (y2 - y1) * padding],
                     dtype=np.float32)
    return center, scale


def _rotate_point(pt: np.ndarray, angle_rad: float) -> np.ndarray:
    sn, cs = np.sin(angle_rad), np.cos(angle_rad)
    rot_mat = np.array([[cs, -sn], [sn, cs]], dtype=np.float32)
    return rot_mat @ pt


def _get_3rd_point(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    direction = a - b
    return b + np.array([-direction[1], direction[0]], dtype=np.float32)


def get_warp_matrix(center: np.ndarray, scale: np.ndarray, rot: float,
                    output_size: Tuple[int, int],
                    inv: bool = False) -> np.ndarray:
    """Affine matrix that warps the bbox area in the input onto the model
    input size (or back, with ``inv=True``)."""
    shift = np.array([0.0, 0.0], dtype=np.float32)
    src_w = scale[0]
    dst_w = output_size[0]
    dst_h = output_size[1]

    rot_rad = np.deg2rad(rot)
    src_dir = _rotate_point(np.array([0.0, src_w * -0.5], dtype=np.float32),
                            rot_rad)
    dst_dir = np.array([0.0, dst_w * -0.5], dtype=np.float32)

    src = np.zeros((3, 2), dtype=np.float32)
    src[0] = center + scale * shift
    src[1] = center + src_dir + scale * shift
    src[2] = _get_3rd_point(src[0], src[1])

    dst = np.zeros((3, 2), dtype=np.float32)
    dst[0] = [dst_w * 0.5, dst_h * 0.5]
    dst[1] = np.array([dst_w * 0.5, dst_h * 0.5]) + dst_dir
    dst[2] = _get_3rd_point(dst[0], dst[1])

    if inv:
        warp_mat = cv2.getAffineTransform(dst, src)
    else:
        warp_mat = cv2.getAffineTransform(src, dst)
    return warp_mat


def get_top_down_affine(input_size: Tuple[int, int], bbox: np.ndarray,
                        image: np.ndarray) -> Tuple[np.ndarray, np.ndarray,
                                                    np.ndarray]:
    """Crop the bbox area of ``image`` into the fixed model input size.

    Returns (cropped image, center, scale) where ``center``/``scale`` can be
    used later to map model-space keypoints back to image coordinates.
    """
    w, h = input_size
    center, scale = bbox_xyxy2cs(bbox, padding=1.25)

    # fix the crop to the model's aspect ratio
    aspect_ratio = w / h
    if scale[0] > scale[1] * aspect_ratio:
        scale[1] = scale[0] / aspect_ratio
    else:
        scale[0] = scale[1] * aspect_ratio

    warp_mat = get_warp_matrix(center, scale, 0, output_size=(w, h))
    cropped = cv2.warpAffine(image, warp_mat, (w, h),
                             flags=cv2.INTER_LINEAR)
    return cropped, center, scale


def keypoints_to_image(keypoints: np.ndarray,
                       model_input_size: Tuple[int, int],
                       center: np.ndarray,
                       scale: np.ndarray) -> np.ndarray:
    """Map model-space keypoint coordinates back to the input image."""
    simcc_split_ratio = 2.0
    kpts = keypoints / simcc_split_ratio
    kpts = kpts / np.array(model_input_size, dtype=np.float32) * scale
    return kpts + center - scale / 2