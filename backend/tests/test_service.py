import json

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


def _humanization_image():
    return {
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


def test_groq_humanization_requires_api_key(monkeypatch):
    monkeypatch.setenv("AGOS_HUMANIZATION_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(
        humanization.HumanizationUnavailable, match="GROQ_API_KEY"
    ):
        humanization.humanize_image(_humanization_image())


def test_groq_humanization_posts_metadata_only(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(
                {"choices": [{"message": {"content": " Drive the knee forward. "}}]}
            ).encode()

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data)
        captured["authorization"] = request.headers["Authorization"]
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setenv("AGOS_HUMANIZATION_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("AGOS_GROQ_MODEL", "test-model")
    monkeypatch.setenv("AGOS_HUMANIZATION_MAX_TOKENS", "42")
    monkeypatch.setattr(humanization.urllib.request, "urlopen", fake_urlopen)

    model, prompt, text = humanization.humanize_image(_humanization_image())

    assert model == "groq:test-model"
    assert text == "Drive the knee forward."
    assert captured["url"] == humanization.GROQ_URL
    assert captured["authorization"] == "Bearer test-key"
    assert captured["timeout"] == 30
    assert captured["body"]["model"] == "test-model"
    assert captured["body"]["max_tokens"] == 42
    assert captured["body"]["temperature"] == 0
    assert captured["body"]["messages"][0]["role"] == "system"
    assert '"hip": 160.0' in captured["body"]["messages"][1]["content"]
    assert '"reference_ranges"' in prompt
