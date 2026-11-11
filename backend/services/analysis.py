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
    n1 = np.linalg.norm(ba)
    n2 = np.linalg.norm(bc)
    if n1 < 1e-6 or n2 < 1e-6:
        return float("nan")
    cosine = np.dot(ba, bc) / (n1 * n2)
    angle = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
    return angle


def _thigh_angle(thigh_np):
    vertical_vector = np.array([0, 1])
    n = np.linalg.norm(thigh_np)
    if n < 1e-6:
        return float("nan")
    cosine = np.dot(thigh_np, vertical_vector) / (n * np.linalg.norm(vertical_vector))
    raw = float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))
    if thigh_np[0] < 0:
        return -raw
    return raw


def _vector(a, b):
    return np.array([b.x - a.x, b.y - a.y])


def _angle_between(u, v):
    n1 = np.linalg.norm(u)
    n2 = np.linalg.norm(v)
    if n1 < 1e-6 or n2 < 1e-6:
        return float("nan")
    cosine = np.dot(u, v) / (n1 * n2)
    return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))


MIN_VISIBILITY = 0.5


def _is_visible(p):
    if p is None:
        return False
    if getattr(p, "visibility", 1.0) < MIN_VISIBILITY:
        return False
    if p.x == -1 and p.y == -1:
        return False
    return True


def _measure_leg(points):
    if not all(_is_visible(p) for p in points):
        return {"hip_angle": float("nan"), "knee_angle": float("nan"), "ankle_angle": float("nan")}
    hip, knee, ankle, heel, foot = points
    hip_angle = 180 - _thigh_angle(_vector(hip, knee))
    knee_angle = float(calculate_angle(hip, knee, ankle))
    shin_vector = _vector(ankle, knee)
    foot_vector = _vector(heel, foot)
    n1 = np.linalg.norm(shin_vector)
    n2 = np.linalg.norm(foot_vector)
    if n1 < 1e-6 or n2 < 1e-6:
        ankle_angle = float("nan")
    else:
        cosine_ankle = np.dot(shin_vector, foot_vector) / (n1 * n2)
        ankle_angle = float(np.degrees(np.arccos(np.clip(cosine_ankle, -1.0, 1.0))))
    return {
        "hip_angle": round(hip_angle, 1) if hip_angle == hip_angle else float("nan"),
        "knee_angle": round(knee_angle, 1) if knee_angle == knee_angle else float("nan"),
        "ankle_angle": round(ankle_angle, 1) if ankle_angle == ankle_angle else float("nan"),
    }


JOINTS = ("hip", "knee", "ankle")
_JOINT_NAMES = {
    "hip": "Thigh",
    "knee": "Knee",
    "ankle": "Ankle",
    "thigh_thigh": "Thigh gap",
}

# Plain-language (problem, fix cue) per side of the target range.
# Hip: lower value = thigh further forward/up. Knee: lower = more bent.
# Ankle: lower = toes pulled up / shin over the foot, higher = toes pointing down.
_MESSAGES = {
    ("swing", "hip"): {
        "low": ("Thigh too high", "Drive the knee forward rather than up."),
        "high": ("Thigh too low", "Drive the knee forward and up sooner."),
    },
    ("swing", "knee"): {
        "low": ("Knee too bent", "Let the lower leg open out a little more."),
        "high": (
            "Knee too straight",
            "Bend the knee more and bring the heel up toward the hip.",
        ),
    },
    ("swing", "ankle"): {
        "low": (
            "Toes pulled up too far",
            "Relax the ankle slightly; keep the foot firm but not cranked up.",
        ),
        "high": (
            "Toes pointing down",
            "Pull the toes up toward the shin as the leg swings through.",
        ),
    },
    ("stance", "knee"): {
        "low": (
            "Knee too bent",
            "Stay tall and stiff through the leg so it doesn't collapse under you.",
        ),
        "high": (
            "Knee too straight",
            "Keep a slight bend in the knee instead of locking it.",
        ),
    },
}

_PHASE_MESSAGES = {
    ("toe_off", "swing", "hip"): {
        "low": (
            "Thigh too high",
            "Aim for the thigh about level with the hips; drive forward, not up.",
        ),
        "high": (
            "Thigh too low",
            "Drive the knee up toward hip height as you push off.",
        ),
    },
    ("touchdown", "swing", "hip"): {
        "low": (
            "Knee too far forward",
            "Time the knee drive so the knee is just in front of the hips as "
            "the other foot lands.",
        ),
        "high": (
            "Knee trailing behind",
            "Bring the knee through faster so it is level with the hips when "
            "the other foot lands.",
        ),
    },
    ("toe_off", "stance", "hip"): {
        "low": (
            "Leg not extended back enough",
            "Push all the way through the ground until the leg is extended "
            "behind you.",
        ),
        "high": (
            "Leg too far behind",
            "Lift the foot off sooner and start bringing the leg through.",
        ),
    },
    ("mid_stance", "stance", "hip"): {
        "low": (
            "Foot too far in front of the hips",
            "Let the foot land closer under your hips.",
        ),
        "high": (
            "Hips too far ahead of the foot",
            "Keep the hips stacked over the foot as you pass over it.",
        ),
    },
    ("touchdown", "stance", "hip"): {
        "low": (
            "Foot landing too far in front",
            "You are overstriding; land with the foot closer under your hips.",
        ),
        "high": (
            "Foot landing too close under the body",
            "Let the foot land slightly in front of your hips.",
        ),
    },
    ("mid_stance", "stance", "knee"): {
        "high": (
            "Knee too straight",
            "Keep a slight bend in the knee to absorb the landing.",
        ),
    },
    ("touchdown", "stance", "knee"): {
        "high": (
            "Knee too straight at landing",
            "Land with a slight bend in the knee.",
        ),
    },
    ("toe_off", "stance", "ankle"): {
        "low": (
            "Not pushing through the toes",
            "Finish the push through the ball of the foot and toes.",
        ),
        "high": (
            "Ankle over-extended",
            "Don't over-point the toes; push through the ball of the foot.",
        ),
    },
    ("mid_stance", "stance", "ankle"): {
        "low": (
            "Ankle collapsing",
            "Stay up on the ball of the foot and keep the ankle stiff.",
        ),
        "high": (
            "Toes pointing down too much",
            "Let the ankle flex a little as your body passes over the foot.",
        ),
    },
    ("touchdown", "stance", "ankle"): {
        "low": (
            "Toes pulled up at landing",
            "Land on the ball of the foot, not the heel.",
        ),
        "high": (
            "Toes pointing down at landing",
            "Pull the toes up slightly before the foot hits the ground.",
        ),
    },
    ("touchdown", None, "thigh_thigh"): {
        "low": (
            "Thighs too close together",
            "Let the landing leg reach a little further in front of the "
            "swing knee.",
        ),
        "high": (
            "Swing knee trailing behind",
            "Bring the swing knee through faster so the knees are close "
            "together when the foot lands.",
        ),
    },
}


def _messages(phase, role, joint):
    return {
        **_MESSAGES.get((role, joint), {}),
        **_PHASE_MESSAGES.get((phase, role, joint), {}),
    }


def assess_joint(phase, role, joint, value):
    """Return {status, problem, cue} for one joint.

    ``status`` is ``good``, ``low`` (below the target range), ``high`` (above
    it), or ``unclear`` (not measured).
    """
    spec = RANGES[phase]
    lo, hi = spec["thigh_thigh"] if joint == "thigh_thigh" else spec[role][joint]
    if value is None or value != value:
        name = _JOINT_NAMES[joint]
        return {
            "status": "unclear",
            "problem": f"{name} not clearly visible",
            "cue": "Retake the photo with the whole leg in frame.",
        }
    if lo <= value <= hi:
        return {"status": "good", "problem": None, "cue": None}
    status = "low" if value < lo else "high"
    problem, cue = _messages(phase, role, joint)[status]
    return {"status": status, "problem": problem, "cue": cue}


def _sentence(check):
    cue = check["cue"]
    return f"{check['problem']} – {cue[0].lower()}{cue[1:]}"


def leg_feedback(checks):
    issues = [checks[j] for j in JOINTS if checks[j]["status"] != "good"]
    if not issues:
        return "Good position."
    return " ".join(_sentence(check) for check in issues)


def thigh_gap_to_show(checks):
    """The thigh-gap check, unless the swing thigh check already says the same.

    At touchdown a trailing (or over-driven) swing thigh also widens (or
    narrows) the gap, so showing both would repeat one problem twice.
    """
    gap = checks.get("thigh_thigh")
    if gap is None or gap["status"] not in ("low", "high"):
        return gap
    if checks["swing"]["hip"]["status"] == gap["status"]:
        return None
    return gap


def overall_feedback(swing_checks, stance_checks, thigh_check=None):
    parts = []
    for label, checks in (
        ("Swing leg", swing_checks),
        ("Stance leg", stance_checks),
    ):
        problems = [
            checks[j]["problem"].lower()
            for j in JOINTS
            if checks[j]["status"] != "good"
        ]
        parts.append(
            f"{label}: {', '.join(problems)}." if problems
            else f"{label}: good position."
        )
    if thigh_check is not None and thigh_check["status"] != "good":
        parts.append(f"{_sentence(thigh_check)}")
    return " ".join(parts)


def assess(phase, swing, stance, thigh_thigh=None):
    """Plain-language checks for stored or freshly measured angles.

    ``swing``/``stance`` map hip/knee/ankle to degrees (or None).
    """
    checks = {
        role: {
            joint: assess_joint(phase, role, joint, angles.get(joint))
            for joint in JOINTS
        }
        for role, angles in (("swing", swing), ("stance", stance))
    }
    checks["thigh_thigh"] = (
        assess_joint(phase, None, "thigh_thigh", thigh_thigh)
        if "thigh_thigh" in RANGES[phase]
        else None
    )
    return checks


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
        if value != value:
            total += 1e6
            continue
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
    for swing_slots, stance_slots in candidates:
        swing_pts, stance_pts = swing_slots, stance_slots
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
                "slots": {"swing": swing_slots, "stance": stance_slots},
            }

    if best is None or best["penalty"] >= 1e6:
        raise ValueError("Low confidence pose: keypoints not visible")
    swing = best["swing"]
    stance = best["stance"]
    swing_points = best["swing_points"]
    stance_points = best["stance_points"]

    result = {
        "phase": phase,
        "swing_leg": swing,
        "stance_leg": stance,
        "slots": best["slots"],
    }

    thigh_thigh_angle = None
    if "thigh_thigh" in spec:
        if all(_is_visible(p) for p in swing_points[:2] + stance_points[:2]):
            front_thigh = _vector(swing_points[0], swing_points[1])
            back_thigh = _vector(stance_points[0], stance_points[1])
            measured = _angle_between(front_thigh, back_thigh)
            if measured == measured:
                thigh_thigh_angle = round(measured, 1)
        result["thigh_thigh_angle"] = thigh_thigh_angle

    checks = assess(
        phase,
        {joint: swing[f"{joint}_angle"] for joint in JOINTS},
        {joint: stance[f"{joint}_angle"] for joint in JOINTS},
        thigh_thigh_angle,
    )
    swing["feedback"] = leg_feedback(checks["swing"])
    stance["feedback"] = leg_feedback(checks["stance"])
    result["checks"] = checks
    result["feedback"] = overall_feedback(
        checks["swing"], checks["stance"], thigh_gap_to_show(checks)
    )

    return result
