import numpy as np
from types import SimpleNamespace

def calculate_angle(a, b, c):
    a = np.array([a.x, a.y])
    b = np.array([b.x, b.y])
    c = np.array([c.x, c.y])

    ba = a - b
    bc = c - b

    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))

    return angle


def analyze_angles(landmarks):
    hip = landmarks[24]
    knee = landmarks[26]
    ankle = landmarks[28]
    heel = landmarks[30]
    foot = landmarks[32]

    # Convert to numpy
    hip_np = np.array([hip.x, hip.y])
    knee_np = np.array([knee.x, knee.y])
    ankle_np = np.array([ankle.x, ankle.y])
    heel_np = np.array([heel.x, heel.y])
    foot_np = np.array([foot.x, foot.y])

    
    thigh_vector = knee_np - hip_np
    vertical_vector = np.array([0, 1])  

    cosine_hip = np.dot(thigh_vector, vertical_vector) / (
        np.linalg.norm(thigh_vector) * np.linalg.norm(vertical_vector)
    )
    raw_hip_angle = np.degrees(np.arccos(np.clip(cosine_hip, -1.0, 1.0)))
    
    hip_angle = 180 - raw_hip_angle

    knee_angle = calculate_angle(hip, knee, ankle)


    shin_vector = knee_np - ankle_np
    foot_vector = foot_np - heel_np

    cosine_ankle = np.dot(shin_vector, foot_vector) / (
        np.linalg.norm(shin_vector) * np.linalg.norm(foot_vector)
    )
    ankle_angle = np.degrees(np.arccos(np.clip(cosine_ankle, -1.0, 1.0)))

    
    hip_good = 97 <= hip_angle <= 113
    knee_good = 58 <= knee_angle <= 80
    ankle_good = 96 <= ankle_angle <= 104

    issues = []
    if not hip_good:
        issues.append("Hip")
    if not knee_good:
        issues.append("Knee")
    if not ankle_good:
        issues.append("Ankle")

    if issues:
        feedback = f"{', '.join(issues)} outside optimal range"
    else:
        feedback = "Good positions"

    return {
        "knee_angle": round(knee_angle, 1),
        "hip_angle": round(hip_angle, 1),
        "ankle_angle": round(ankle_angle, 1),
        "feedback": feedback,
        "hip_feedback": feedback,
        "knee_feedback": feedback,
        "ankle_feedback": feedback
    }