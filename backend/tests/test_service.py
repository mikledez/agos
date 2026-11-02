import pytest

from services import humanization, image_service

def test_rejects_unknown_phase_before_touching_models():
    with pytest.raises(ValueError, match="unknown phase"):
        image_service.analyze_and_store(
            1,
            contents=b"whatever",
            original_filename="a.png",
            phase="bogus",
            direction="ltr",
        )

def test_rejects_unknown_direction():
    with pytest.raises(ValueError, match="unknown direction"):
        image_service.analyze_and_store(
            1,
            contents=b"whatever",
            original_filename="a.png",
            phase="toe_off",
            direction="sideways",
        )

def test_rejects_corrupt_image():
    with pytest.raises(ValueError, match="Invalid image file"):
        image_service.analyze_and_store(
            1,
            contents=b"not-an-image",
            original_filename="a.png",
            phase="toe_off",
            direction="ltr",
        )

def test_rejects_oversized_upload():
    oversized = b"x" * (image_service.MAX_UPLOAD_BYTES + 1)
    with pytest.raises(ValueError, match="larger than"):
        image_service.analyze_and_store(
            1,
            contents=oversized,
            original_filename="a.png",
            phase="toe_off",
            direction="ltr",
        )


def test_humanization_prompt_uses_metadata_and_reference_ranges():
    prompt = humanization.build_prompt(
        {
            "phase": "touchdown",
            "direction": "ltr",
            "swing_hip": 160.0,
            "swing_knee": 45.0,
            "swing_ankle": 120.0,
            "swing_feedback": "Good positions",
            "stance_hip": 146.0,
            "stance_knee": 150.0,
            "stance_ankle": 100.0,
            "stance_feedback": "Good positions",
            "thigh_thigh": 15.0,
            "feedback": "Good positions",
        }
    )
    assert "touchdown" in prompt
    assert '"hip": 160.0' in prompt
    assert '"thigh_thigh": 15.0' in prompt
    assert '"reference_ranges"' in prompt
