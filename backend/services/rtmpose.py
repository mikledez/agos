"""RTMPose keypoint estimation via ONNX Runtime.

The model is the official OpenMMLab ONNX SDK export of RTMPose-M
(256x192, HalPE26 keypoint layout). It outputs SimCC representations
(``simcc_x``, ``simcc_y``) that are decoded and mapped back to the input
image coordinates. Pre/post-processing mirrors rtmlib's implementation
(https://github.com/Tau-J/rtmlib, MIT license), which is validated
against these exact export files.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .preprocess import get_top_down_affine, keypoints_to_image

INPUT_SIZE = (192, 256)  # (w, h)
MEAN = np.array([123.675, 116.28, 103.53], dtype=np.float32)
STD = np.array([58.395, 57.12, 57.375], dtype=np.float32)
NUM_KEYPOINTS = 26

_MODEL = "rtmpose-m_halpe26.onnx"


class RTMPose:

    def __init__(self, model_dir: Path | str):
        import onnxruntime as ort

        model_path = Path(model_dir) / _MODEL
        if not model_path.exists():
            raise FileNotFoundError(
                f"pose model not found at {model_path}; run "
                "scripts/download_models.sh")
        self._session = ort.InferenceSession(
            str(model_path), providers=["CPUExecutionProvider"])

    def estimate(self, image: np.ndarray,
                 bbox: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Estimate keypoints for one person crop.

        Args:
            image: BGR image.
            bbox: (x1, y1, x2, y2) person box in image coordinates.

        Returns:
            (keypoints, scores): arrays shaped (26, 2) and (26,) with
            keypoints in image coordinates and per-keypoint confidences.
        """
        cropped, center, scale = get_top_down_affine(INPUT_SIZE, bbox, image)
        normed = (cropped.astype(np.float32) - MEAN) / STD
        tensor = normed.transpose(2, 0, 1)[None, :, :, :]
        outputs = self._session.run(
            None, {self._session.get_inputs()[0].name: tensor})
        return self._postprocess(outputs, center, scale)

    def _postprocess(self, outputs: list[np.ndarray], center: np.ndarray,
                     scale: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        simcc_x, simcc_y = outputs
        locs, scores = get_simcc_maximum(simcc_x, simcc_y)
        keypoints = keypoints_to_image(locs, INPUT_SIZE, center, scale)
        return keypoints[0], scores[0]


def get_simcc_maximum(simcc_x: np.ndarray,
                      simcc_y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Decode SimCC outputs into (locations, scores) in model input space."""
    simcc_x = simcc_x.reshape(-1, simcc_x.shape[-1])
    simcc_y = simcc_y.reshape(-1, simcc_y.shape[-1])

    x_locs = np.argmax(simcc_x, axis=1)
    y_locs = np.argmax(simcc_y, axis=1)
    locs = np.stack((x_locs, y_locs), axis=-1).astype(np.float32)

    max_val_x = np.max(simcc_x, axis=1)
    max_val_y = np.max(simcc_y, axis=1)
    scores = 0.5 * (max_val_x + max_val_y)
    locs[scores <= 0.0] = -1

    return (
        locs.reshape(-1, NUM_KEYPOINTS, 2),
        scores.reshape(-1, NUM_KEYPOINTS),
    )