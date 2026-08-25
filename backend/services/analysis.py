import numpy as np
from types import SimpleNamespace

SWING_POINTS = (24, 26, 28, 30, 32)
STANCE_POINTS = (23, 25, 27, 29, 31)

RANGES = {
    "toe_off": {
        "swing": {"hip": (97, 113), "knee": (58, 80), "ankle": (96, 104)},
        "stance": {"hip": (193, 204), "knee": (138, 155), "ankle": (110, 147)},
    },
    "mid_stance": {
        "swing": {"hip": (126, 146), "knee": (26, 41), "ankle": (108, 132)},
        "stance": {"hip": (155, 165), "knee": (141, 149), "ankle": (79, 88)},
    },
    "touchdown": {
        "swing": {"hip": (157, 168), "knee": (39, 49), "ankle": (116, 130)},
        "stance": {"hip": (141, 152), "knee": (146, 156), "ankle": (97, 105)},
        "thigh_thigh": (7, 28),
    },
}


def calculate_angle(a, b, c):
    a = np.array([a.x, a.y])
    b = np.array([b.x, b.y])
    c = np.array([c.x, c.y])

    ba = a - b
    bc = c - b

    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))

    return angle


def _thigh_angle(thigh_np):
    vertical_vector = np.array([0, 1])

    cosine = np.dot(thigh_np, vertical_vector) / (
        np.linalg.norm(thigh_np) * np.linalg.norm(vertical_vector)
    )
    raw = float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))

    if thigh_np[0] < 0:
        return -raw
    return raw


def _vector(a, b):
    return np.array([b.x - a.x, b.y - a.y])


def _angle_between(u, v):
    cosine = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v))
    return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))


def _measure_leg(points):
    hip, knee, ankle, heel, foot = points

    hip_np = np.array([hip.x, hip.y])
    knee_np = np.array([knee.x, knee.y])
    ankle_np = np.array([ankle.x, ankle.y])
    heel_np = np.array([heel.x, heel.y])
    foot_np = np.array([foot.x, foot.y])

    hip_angle = 180 - _thigh_angle(_vector(hip, knee))

    knee_angle = float(calculate_angle(hip, knee, ankle))

    shin_vector = _vector(ankle, knee)
    foot_vector = _vector(heel, foot)

    cosine_ankle = np.dot(shin_vector, foot_vector) / (
        np.linalg.norm(shin_vector) * np.linalg.norm(foot_vector)
    )
    ankle_angle = float(np.degrees(np.arccos(np.clip(cosine_ankle, -1.0, 1.0))))

    return {
        "hip_angle": round(hip_angle, 1),
        "knee_angle": round(knee_angle, 1),
        "ankle_angle": round(ankle_angle, 1),
    }


def _check_leg(angles, optimal):
    issues = []
    for angle_key, range_key, label in (
        ("hip_angle", "hip", "Hip"),
        ("knee_angle", "knee", "Knee"),
        ("ankle_angle", "ankle", "Ankle"),
    ):
        lo, hi = optimal[range_key]
        if not lo <= angles[angle_key] <= hi:
            issues.append(label)

    if issues:
        return f"{', '.join(issues)} outside optimal range"
    return "Good positions"


def _mirror_landmarks(landmarks):
    return [
        p
        if p is None
        else SimpleNamespace(
            x=-p.x,
            y=p.y,
            visibility=getattr(p, "visibility", 0.0),
        )
        for p in landmarks
    ]


def _penalty(angles, optimal):
    total = 0.0
    for angle_key, range_key in (
        ("hip_angle", "hip"),
        ("knee_angle", "knee"),
        ("ankle_angle", "ankle"),
    ):
        lo, hi = optimal[range_key]
        value = angles[angle_key]
        if value < lo:
            total += (lo - value) ** 2
        elif value > hi:
            total += (value - hi) ** 2
    return total


def analyze_angles(landmarks, phase="toe_off", direction="ltr"):
    spec = RANGES[phase]
    if direction == "rtl":
        norm = _mirror_landmarks(landmarks)
    else:
        norm = landmarks

    candidates = (
        (SWING_POINTS, STANCE_POINTS),
        (STANCE_POINTS, SWING_POINTS),
    )

    best = None
    for swing_pts, stance_pts in candidates:
        swing_points = [norm[i] for i in swing_pts]
        stance_points = [norm[i] for i in stance_pts]

        swing = _measure_leg(swing_points)
        stance = _measure_leg(stance_points)

        penalty = _penalty(swing, spec["swing"]) + _penalty(
            stance, spec["stance"]
        )
        if best is None or penalty < best["penalty"]:
            best = {
                "penalty": penalty,
                "swing": swing,
                "stance": stance,
                "swing_points": swing_points,
                "stance_points": stance_points,
            }

    swing = best["swing"]
    stance = best["stance"]
    swing_points = best["swing_points"]
    stance_points = best["stance_points"]

    swing["feedback"] = _check_leg(swing, spec["swing"])
    stance["feedback"] = _check_leg(stance, spec["stance"])

    parts = []
    if swing["feedback"] != "Good positions":
        parts.append(f"Swing leg: {swing['feedback']}")
    if stance["feedback"] != "Good positions":
        parts.append(f"Stance leg: {stance['feedback']}")

    result = {
        "phase": phase,
        "swing_leg": swing,
        "stance_leg": stance,
    }

    if "thigh_thigh" in spec:
        front_thigh = _vector(swing_points[0], swing_points[1])
        back_thigh = _vector(stance_points[0], stance_points[1])
        thigh_thigh_angle = round(_angle_between(front_thigh, back_thigh), 1)
        result["thigh_thigh_angle"] = thigh_thigh_angle

        lo, hi = spec["thigh_thigh"]
        if not lo <= thigh_thigh_angle <= hi:
            parts.append("Thighs outside optimal range")

    result["feedback"] = "; ".join(parts) if parts else "Good positions"

    return result
