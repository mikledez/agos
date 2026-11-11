import re
from types import SimpleNamespace

import numpy as np
import pytest

from services import analysis, overlay, pose

# Toe-off, runner moving right: swing leg uses the right-side slots.
TOE_OFF_POINTS = {
    24: (500, 400), 26: (650, 430), 28: (720, 600), 30: (690, 620), 32: (760, 640),
    23: (490, 405), 25: (420, 560), 27: (330, 700), 29: (300, 690), 31: (350, 760),
}
LEG_NAMES = ("hip", "knee", "ankle", "heel", "toe")


def _landmarks(direction="ltr", width=1000):
    landmarks = [None] * 33
    for slot, (x, y) in TOE_OFF_POINTS.items():
        if direction == "rtl":
            x = width - x
        landmarks[slot] = SimpleNamespace(x=float(x), y=float(y), visibility=0.9)
    return landmarks


def _pose_info(landmarks):
    keypoints = np.zeros((26, 2))
    scores = np.zeros(26)
    for slot, halpe in pose._SLOT_TO_HALPE.items():
        keypoints[halpe] = (landmarks[slot].x, landmarks[slot].y)
        scores[halpe] = 0.9
    return {"keypoints": keypoints, "scores": scores}


def _leg(landmarks, slots):
    return dict(zip(LEG_NAMES, (landmarks[slot] for slot in slots)))


def _point(vector):
    return SimpleNamespace(x=float(vector[0]), y=float(vector[1]), visibility=0.9)


@pytest.mark.parametrize("phase", sorted(analysis.RANGES))
def test_every_joint_has_wording_for_both_sides_of_its_range(phase):
    keys = [(role, joint) for role in ("swing", "stance") for joint in analysis.JOINTS]
    if "thigh_thigh" in analysis.RANGES[phase]:
        keys.append((None, "thigh_thigh"))
    for role, joint in keys:
        messages = analysis._messages(phase, role, joint)
        assert set(messages) == {"low", "high"}, (phase, role, joint)
        for problem, cue in messages.values():
            assert problem and cue.endswith(".")


@pytest.mark.parametrize(
    ("phase", "role", "joint", "value", "status", "problem"),
    [
        ("toe_off", "swing", "knee", 120.0, "high", "Knee too straight"),
        ("toe_off", "swing", "knee", 40.0, "low", "Knee too bent"),
        ("toe_off", "swing", "hip", 130.0, "high", "Thigh too low"),
        ("touchdown", "stance", "knee", 170.0, "high", "Knee too straight at landing"),
        ("touchdown", "stance", "hip", 130.0, "low", "Foot landing too far in front"),
        ("touchdown", None, "thigh_thigh", 40.0, "high", "Swing knee trailing behind"),
        ("mid_stance", "stance", "ankle", 70.0, "low", "Ankle collapsing"),
    ],
)
def test_assess_joint_says_which_way_it_is_off(phase, role, joint, value, status, problem):
    check = analysis.assess_joint(phase, role, joint, value)
    assert check["status"] == status
    assert check["problem"] == problem


def test_assess_joint_in_range_and_unclear():
    assert analysis.assess_joint("toe_off", "swing", "knee", 70.0)["status"] == "good"
    unclear = analysis.assess_joint("toe_off", "swing", "knee", float("nan"))
    assert unclear["status"] == "unclear"
    assert unclear["problem"] == "Knee not clearly visible"


def test_analysis_feedback_is_plain_language_without_numbers():
    result = analysis.analyze_angles(_landmarks(), "toe_off", "ltr")

    assert result["swing_leg"]["feedback"].startswith(
        "Knee too straight – bend the knee more"
    )
    assert result["feedback"] == (
        "Swing leg: knee too straight, toes pointing down. "
        "Stance leg: leg too far behind, knee too straight."
    )
    for text in (result["feedback"], result["swing_leg"]["feedback"], result["stance_leg"]["feedback"]):
        assert not re.search(r"\d", text)
    assert result["slots"]["swing"] == analysis.SWING_POINTS


def test_thigh_gap_is_not_repeated_when_the_swing_thigh_says_the_same():
    spec = analysis.RANGES["touchdown"]
    stance = {j: sum(spec["stance"][j]) / 2 for j in analysis.JOINTS}
    swing = {j: sum(spec["swing"][j]) / 2 for j in analysis.JOINTS}

    trailing = analysis.assess("touchdown", {**swing, "hip": 175.0}, stance, 40.0)
    assert analysis.thigh_gap_to_show(trailing) is None
    feedback = analysis.overall_feedback(
        trailing["swing"], trailing["stance"], analysis.thigh_gap_to_show(trailing)
    )
    assert feedback.count("trailing behind") == 1

    gap_only = analysis.assess("touchdown", swing, stance, 40.0)
    assert analysis.thigh_gap_to_show(gap_only)["problem"] == "Swing knee trailing behind"


def test_good_positions_read_as_good():
    good = {joint: None for joint in analysis.JOINTS}
    spec = analysis.RANGES["mid_stance"]
    swing = {j: sum(spec["swing"][j]) / 2 for j in good}
    stance = {j: sum(spec["stance"][j]) / 2 for j in good}
    checks = analysis.assess("mid_stance", swing, stance)

    assert analysis.leg_feedback(checks["swing"]) == "Good position."
    assert analysis.overall_feedback(checks["swing"], checks["stance"]) == (
        "Swing leg: good position. Stance leg: good position."
    )


def _measure(joint, leg, end, direction, other_leg=None):
    """Re-measure a joint after moving its segment's far end to ``end``."""
    end = _point(end)
    if joint == "hip":
        hip, knee = leg["hip"], end
        if direction == "rtl":
            hip, knee = analysis._mirror_landmarks([hip, knee])
        return 180 - analysis._thigh_angle(analysis._vector(hip, knee))
    if joint == "knee":
        return analysis.calculate_angle(leg["hip"], leg["knee"], end)
    if joint == "ankle":
        return analysis._angle_between(
            analysis._vector(leg["ankle"], leg["knee"]),
            analysis._vector(leg["heel"], end),
        )
    return analysis._angle_between(
        analysis._vector(leg["hip"], end),
        analysis._vector(other_leg["hip"], other_leg["knee"]),
    )


@pytest.mark.parametrize("direction", ["ltr", "rtl"])
@pytest.mark.parametrize("role", ["swing", "stance"])
@pytest.mark.parametrize("joint", analysis.JOINTS)
def test_target_zone_edges_match_the_target_range(direction, role, joint):
    landmarks = _landmarks(direction)
    slots = analysis.SWING_POINTS if role == "swing" else analysis.STANCE_POINTS
    leg = _leg(landmarks, slots)
    lo, hi = analysis.RANGES["toe_off"][role][joint]

    pivot, arc = overlay.target_zone(joint, leg, (lo, hi), direction=direction)

    assert _measure(joint, leg, arc[0], direction) == pytest.approx(lo, abs=1e-6)
    assert _measure(joint, leg, arc[-1], direction) == pytest.approx(hi, abs=1e-6)


def test_thigh_gap_zone_edges_match_the_target_range():
    landmarks = _landmarks()
    swing = _leg(landmarks, analysis.SWING_POINTS)
    stance = _leg(landmarks, analysis.STANCE_POINTS)
    lo, hi = analysis.RANGES["touchdown"]["thigh_thigh"]

    _, arc = overlay.target_zone("thigh_thigh", swing, (lo, hi), other_leg=stance)

    assert _measure("thigh_thigh", swing, arc[0], "ltr", stance) == pytest.approx(lo, abs=1e-6)
    assert _measure("thigh_thigh", swing, arc[-1], "ltr", stance) == pytest.approx(hi, abs=1e-6)


@pytest.mark.parametrize("direction", ["ltr", "rtl"])
def test_draw_feedback_marks_up_a_copy(direction):
    landmarks = _landmarks(direction)
    result = analysis.analyze_angles(landmarks, "toe_off", direction)
    image = np.full((1000, 1000, 3), 70, np.uint8)

    annotated = overlay.draw_feedback(
        image, _pose_info(landmarks), landmarks, result, "toe_off", direction
    )

    assert annotated.shape == image.shape
    assert (image == 70).all()
    red = (annotated[:, :, 2] > 200) & (annotated[:, :, 1] < 100)
    assert red.any()


def test_draw_feedback_handles_missing_keypoints():
    landmarks = _landmarks()
    result = analysis.analyze_angles(landmarks, "toe_off", "ltr")
    landmarks[30] = SimpleNamespace(x=-1, y=-1, visibility=0.0)
    image = np.zeros((600, 400, 3), np.uint8)

    annotated = overlay.draw_feedback(
        image, _pose_info(landmarks), landmarks, result, "toe_off", "ltr"
    )

    assert annotated.shape == image.shape
