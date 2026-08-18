#!/usr/bin/env bash
set -euo pipefail

# Official OpenMMLab onnx_sdk exports, mirrored on Hugging Face
# (download.openmmlab.com no longer serves the model zoo).
# Detector: YOLOX-nano person detector (HumanArt), 416x416 input,
#           NMS already baked in -> outputs dets [1, N, 5].
# Pose:     RTMPose-M (body7 / halpe26), 256x192 input,
#           SimCC outputs -> simcc_x [1, 26, 384], simcc_y [1, 26, 512].

BASE_URL="https://huggingface.co/Tau-J/RTMPose/resolve/main/rtmposev1/onnx_sdk"
MODEL_DIR="$(cd "$(dirname "$0")/.." && pwd)/models"
mkdir -p "$MODEL_DIR"

echo "Downloading ONNX models into $MODEL_DIR"

curl -fL --retry 3 -o /tmp/yolox_nano.zip \
  "$BASE_URL/yolox_nano_8xb8-300e_humanart-40f6f0d0.zip"
unzip -o -j -q /tmp/yolox_nano.zip "*/end2end.onnx" -d "$MODEL_DIR/.tmp"
mv "$MODEL_DIR/.tmp/end2end.onnx" "$MODEL_DIR/yolox-nano_person.onnx"

curl -fL --retry 3 -o /tmp/rtmpose_m.zip \
  "$BASE_URL/rtmpose-m_simcc-body7_pt-body7-halpe26_700e-256x192-4d3e73dd_20230605.zip"
unzip -o -j -q /tmp/rtmpose_m.zip "*/end2end.onnx" -d "$MODEL_DIR/.tmp"
mv "$MODEL_DIR/.tmp/end2end.onnx" "$MODEL_DIR/rtmpose-m_halpe26.onnx"

rmdir "$MODEL_DIR/.tmp" 2>/dev/null || true
rm -f /tmp/yolox_nano.zip /tmp/rtmpose_m.zip

echo "Done."
ls -la "$MODEL_DIR"