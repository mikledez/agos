from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import base64
from services.pose import get_pose_landmarks, draw_landmarks_on_image
from services.analysis import analyze_angles, RANGES

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    phase: str = Form("toe_off"),
    direction: str = Form("ltr"),
):
    if phase not in RANGES:
        raise HTTPException(status_code=400, detail=f"Unknown phase: {phase}")
    if direction not in ("ltr", "rtl"):
        raise HTTPException(status_code=400, detail=f"Unknown direction: {direction}")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")
    np_arr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    landmarks, pose_landmarks = get_pose_landmarks(image)

    if landmarks is None:
        raise HTTPException(status_code=400, detail="No pose detected")

    try:
        result = analyze_angles(landmarks, phase, direction)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    for k, v in list(result.items()):
        if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
            raise HTTPException(status_code=400, detail="Low confidence pose: cannot compute angles")
        if isinstance(v, dict):
            for kk, vv in v.items():
                if isinstance(vv, float) and (vv != vv or vv in (float("inf"), float("-inf"))):
                    raise HTTPException(status_code=400, detail="Low confidence pose: cannot compute angles")

    image_with_landmarks = draw_landmarks_on_image(image, pose_landmarks)
    _, buffer = cv2.imencode(".jpg", image_with_landmarks)
    encoded_image = base64.b64encode(buffer).decode("utf-8")

    result["annotated_image"] = f"data:image/jpeg;base64,{encoded_image}"

    return result