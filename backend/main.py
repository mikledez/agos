from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import base64
from services.pose import get_pose_landmarks, draw_landmarks_on_image
from services.analysis import analyze_angles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    contents = await file.read()
    np_arr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    landmarks, pose_landmarks = get_pose_landmarks(image)

    if landmarks is None:
        return {"error": "No pose detected"}

    result = analyze_angles(landmarks)

    image_with_landmarks = draw_landmarks_on_image(image, pose_landmarks)
    _, buffer = cv2.imencode(".jpg", image_with_landmarks)
    encoded_image = base64.b64encode(buffer).decode("utf-8")

    result["annotated_image"] = f"data:image/jpeg;base64,{encoded_image}"

    return result