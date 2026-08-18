"""YOLOX person detection via ONNX Runtime.

The model is the official OpenMMLab mmdeploy SDK export of YOLOX-nano
(HumanArt). NMS is baked into the graph: the output ``dets`` is already a
list of final (x1, y1, x2, y2, score) boxes in the 416x416 letterboxed
input space, so we only need to scale them back to the original image.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

INPUT_SIZE = (416, 416)  # (w, h)
PAD_VALUE = 114
SCORE_THRESHOLD = 0.3

_MODEL = "yolox-nano_person.onnx"


class PersonDetector:

    def __init__(self, model_dir: Path | str,
                 score_threshold: float = SCORE_THRESHOLD):
        import onnxruntime as ort

        model_path = Path(model_dir) / _MODEL
        if not model_path.exists():
            raise FileNotFoundError(
                f"detector model not found at {model_path}; run "
                "scripts/download_models.sh")
        self.score_threshold = score_threshold
        self._session = ort.InferenceSession(
            str(model_path), providers=["CPUExecutionProvider"])

    def detect(self, image: np.ndarray) -> list[np.ndarray]:
        """Return a list of person bounding boxes (xyxy) in image coords."""
        padded, ratio = self._preprocess(image)
        outputs = self._session.run(
            None, {self._session.get_inputs()[0].name: padded})
        boxes = self._postprocess(outputs, ratio)
        return boxes

    def _preprocess(self, image: np.ndarray) -> tuple[np.ndarray, float]:
        h, w = image.shape[:2]
        ratio = min(INPUT_SIZE[0] / h, INPUT_SIZE[1] / w)
        resized = cv2.resize(
            image,
            (int(w * ratio), int(h * ratio)),
            interpolation=cv2.INTER_LINEAR,
        ).astype(np.uint8)
        padded = np.full((INPUT_SIZE[1], INPUT_SIZE[0], 3), PAD_VALUE,
                         dtype=np.uint8)
        padded[: int(h * ratio), : int(w * ratio)] = resized
        tensor = padded.transpose(2, 0, 1)[None, :, :, :].astype(np.float32)
        return tensor, ratio

    def _postprocess(self, outputs: list[np.ndarray],
                     ratio: float) -> list[np.ndarray]:
        dets = outputs[0][0]  # [N, 5]: x1, y1, x2, y2, score
        if dets.size == 0:
            return []
        boxes = dets[..., :4] / ratio
        scores = dets[..., 4]
        keep = scores > self.score_threshold
        return [box.astype(np.float32) for box in boxes[keep]]