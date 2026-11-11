"""Draw plain-language form feedback on top of an analyzed sprint photo.

Each joint that is outside its target range gets a shaded green "target zone"
showing where that body segment should point, the segment itself is drawn in
red, and a numbered badge links it to a short list in the corner of the photo.
Segments in range are drawn green.
"""

from __future__ import annotations

import math

import cv2
import numpy as np

from .analysis import JOINTS, RANGES, _is_visible, thigh_gap_to_show
from .pose import _SKELETON, MIN_KEYPOINT_CONFIDENCE

# BGR colors
GOOD = (90, 200, 70)
BAD = (60, 60, 235)
TARGET = (110, 230, 110)
NEUTRAL = (225, 225, 225)
WHITE = (255, 255, 255)

ZONE_ALPHA = 0.35
ZONE_STEPS = 24
_LEG_POINTS = ("hip", "knee", "ankle", "heel", "toe")
_SEGMENTS = {"hip": ("hip", "knee"), "knee": ("knee", "ankle"), "ankle": ("heel", "toe")}


def _xy(point) -> np.ndarray:
    return np.array([point.x, point.y], dtype=float)


def _unit(vector: np.ndarray) -> np.ndarray | None:
    norm = float(np.linalg.norm(vector))
    return None if norm < 1e-6 else vector / norm


def _rotate(vector: np.ndarray, degrees: float) -> np.ndarray:
    theta = math.radians(degrees)
    c, s = math.cos(theta), math.sin(theta)
    return np.array([vector[0] * c - vector[1] * s, vector[0] * s + vector[1] * c])


def _side(reference: np.ndarray, actual: np.ndarray) -> float:
    """+1 or -1: which way ``actual`` turns from ``reference``."""
    cross = reference[0] * actual[1] - reference[1] * actual[0]
    return 1.0 if cross >= 0 else -1.0


def _rotated_arc(pivot, reference, actual, length, lo, hi):
    unit = _unit(reference)
    if unit is None or length < 1e-6:
        return None
    side = _side(reference, actual)
    return [
        pivot + length * _rotate(unit, side * angle)
        for angle in np.linspace(lo, hi, ZONE_STEPS)
    ]


def target_zone(joint, leg, value_range, *, direction="ltr", other_leg=None):
    """Return ``(pivot, arc_points)`` for a joint's target range, or None.

    ``leg`` maps hip/knee/ankle/heel/toe to points in image coordinates. The
    arc points are where the distal end of the segment would sit at each
    angle across the range, using the same angle definitions as ``analysis``.
    """
    lo, hi = value_range
    p = {name: _xy(point) for name, point in leg.items()}

    if joint == "hip":
        length = float(np.linalg.norm(p["knee"] - p["hip"]))
        if length < 1e-6:
            return None
        mirror = -1.0 if direction == "rtl" else 1.0
        arc = []
        for hip_angle in np.linspace(lo, hi, ZONE_STEPS):
            from_vertical = math.radians(180 - hip_angle)
            arc.append(
                p["hip"]
                + length
                * np.array([mirror * math.sin(from_vertical), math.cos(from_vertical)])
            )
        return p["hip"], arc

    if joint == "knee":
        shin = p["ankle"] - p["knee"]
        arc = _rotated_arc(
            p["knee"], p["hip"] - p["knee"], shin,
            float(np.linalg.norm(shin)), lo, hi,
        )
        return None if arc is None else (p["knee"], arc)

    if joint == "ankle":
        foot = p["toe"] - p["heel"]
        arc = _rotated_arc(
            p["heel"], p["knee"] - p["ankle"], foot,
            float(np.linalg.norm(foot)), lo, hi,
        )
        return None if arc is None else (p["heel"], arc)

    if joint == "thigh_thigh" and other_leg is not None:
        o = {name: _xy(point) for name, point in other_leg.items()}
        thigh = p["knee"] - p["hip"]
        arc = _rotated_arc(
            p["hip"], o["knee"] - o["hip"], thigh,
            float(np.linalg.norm(thigh)), lo, hi,
        )
        return None if arc is None else (p["hip"], arc)

    return None


def _pt(vector) -> tuple[int, int]:
    return int(round(vector[0])), int(round(vector[1]))


def _visible(leg, names) -> bool:
    return all(_is_visible(leg[name]) for name in names)


def draw_feedback(image, pose_info, landmarks, result, phase, direction):
    """Return a copy of ``image`` with target zones and issue markers."""
    out = image.copy()
    height, width = out.shape[:2]
    scale = max(height, width) / 1000
    thin = max(1, round(1.5 * scale))
    thick = max(2, round(4 * scale))

    keypoints, scores = pose_info["keypoints"], pose_info["scores"]
    for i, j in _SKELETON:
        if min(scores[i], scores[j]) >= MIN_KEYPOINT_CONFIDENCE:
            cv2.line(out, _pt(keypoints[i]), _pt(keypoints[j]), NEUTRAL, thin, cv2.LINE_AA)

    legs = {
        role: dict(zip(_LEG_POINTS, (landmarks[slot] for slot in result["slots"][role])))
        for role in ("swing", "stance")
    }
    checks = result["checks"]
    spec = RANGES[phase]

    zones = []
    segments = []
    issues = []
    for role, label in (("swing", "Swing leg"), ("stance", "Stance leg")):
        leg = legs[role]
        for joint in JOINTS:
            start, end = _SEGMENTS[joint]
            if not _visible(leg, (start, end)):
                continue
            status = checks[role][joint]["status"]
            if status == "good":
                segments.append((leg[start], leg[end], GOOD))
                continue
            if status not in ("low", "high"):
                continue
            segments.append((leg[start], leg[end], BAD))
            if _visible(leg, _LEG_POINTS):
                zone = target_zone(joint, leg, spec[role][joint], direction=direction)
                if zone is not None:
                    zones.append(zone)
            problem = checks[role][joint]["problem"]
            issues.append((leg[start], f"{label}: {problem[0].lower()}{problem[1:]}"))

    thigh_check = thigh_gap_to_show(checks)
    if thigh_check is not None and thigh_check["status"] in ("low", "high"):
        swing, stance = legs["swing"], legs["stance"]
        if _visible(swing, ("hip", "knee")) and _visible(stance, ("hip", "knee")):
            zone = target_zone(
                "thigh_thigh", swing, spec["thigh_thigh"], other_leg=stance
            )
            if zone is not None:
                zones.append(zone)
            issues.append((swing["hip"], thigh_check["problem"]))

    if zones:
        layer = out.copy()
        for pivot, arc in zones:
            polygon = np.array([_pt(pivot)] + [_pt(p) for p in arc], dtype=np.int32)
            cv2.fillPoly(layer, [polygon], TARGET, cv2.LINE_AA)
        out = cv2.addWeighted(layer, ZONE_ALPHA, out, 1 - ZONE_ALPHA, 0)
        for pivot, arc in zones:
            for edge in (arc[0], arc[-1]):
                cv2.line(out, _pt(pivot), _pt(edge), TARGET, thin, cv2.LINE_AA)

    for leg in legs.values():
        if _visible(leg, ("ankle", "heel")):
            cv2.line(out, _pt(_xy(leg["ankle"])), _pt(_xy(leg["heel"])), NEUTRAL, thin, cv2.LINE_AA)
    for start, end, color in segments:
        cv2.line(out, _pt(_xy(start)), _pt(_xy(end)), color, thick, cv2.LINE_AA)
    for leg in legs.values():
        for point in leg.values():
            if _is_visible(point):
                cv2.circle(out, _pt(_xy(point)), thick + 1, WHITE, -1, cv2.LINE_AA)

    _draw_badges(out, issues, scale)
    _draw_legend(out, [text for _, text in issues], scale)
    return out


def _draw_badges(out, issues, scale):
    radius = max(9, round(13 * scale))
    font_scale = 0.5 * radius / 13
    gap = radius * 2.3
    placed: list[tuple[int, int]] = []
    for number, (anchor, _) in enumerate(issues, start=1):
        x, y = _pt(_xy(anchor))
        center = (x - radius * 2, y - radius)
        while any(math.dist(center, other) < gap for other in placed):
            center = (int(center[0] - gap), center[1])
        placed.append(center)
        cv2.circle(out, center, radius, BAD, -1, cv2.LINE_AA)
        cv2.circle(out, center, radius, WHITE, max(1, round(scale)), cv2.LINE_AA)
        _centered_text(out, str(number), center, font_scale, max(1, round(1.5 * scale)))


def _centered_text(out, text, center, font_scale, thickness):
    (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
    origin = (center[0] - w // 2, center[1] + h // 2)
    cv2.putText(out, text, origin, cv2.FONT_HERSHEY_SIMPLEX, font_scale, WHITE, thickness, cv2.LINE_AA)


def _draw_legend(out, lines, scale):
    font_scale = max(0.45, 0.6 * scale)
    thickness = max(1, round(1.5 * scale))
    rows = (
        ["Green zone = target position"]
        + [f"{n}  {text}" for n, text in enumerate(lines, start=1)]
        if lines
        else ["All positions look good"]
    )
    sizes = [
        cv2.getTextSize(row, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
        for row in rows
    ]
    pad = max(6, round(10 * scale))
    line_height = max(h for _, h in sizes) + pad
    width = max(w for w, _ in sizes) + pad * 2
    height = line_height * len(rows) + pad

    layer = out.copy()
    cv2.rectangle(layer, (pad, pad), (pad + width, pad + height), (20, 20, 20), -1)
    cv2.addWeighted(layer, 0.65, out, 0.35, 0, dst=out)
    for index, row in enumerate(rows):
        color = TARGET if index == 0 and lines else WHITE
        y = pad + line_height * (index + 1) - pad // 2
        cv2.putText(out, row, (pad * 2, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)
