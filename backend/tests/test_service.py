import io
import json
import re
import urllib.error

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


def test_humanization_prompt_describes_positions_without_numbers():
    image = {**_humanization_image(), "stance_knee": 170.0}

    payload = humanization.build_payload(image)
    prompt = humanization.build_prompt(image)

    assert payload["stance_leg"]["fixes"] == [
        {
            "problem": "Knee too straight at landing",
            "fix": "Land with a slight bend in the knee.",
        }
    ]
    assert payload["swing_leg"]["looks_good"] == [
        "thigh position", "knee bend", "ankle and foot"
    ]
    assert payload["thigh_gap_between_legs"] == "looks good"
    assert "touchdown" in prompt
    assert not re.search(r"\d", json.dumps(payload))
    assert "Never state degrees" in prompt


def test_chat_context_keeps_measurements_for_when_numbers_are_asked_for():
    messages = humanization._build_chat_messages(
        _humanization_image(), [], "What was my knee angle?", None
    )
    system = messages[0]["content"]

    assert "Only give degrees or reference ranges when the athlete" in system
    assert '"measurements_only_if_asked"' in system
    assert '"knee": 150.0' in system
    assert messages[-1] == {"role": "user", "content": "What was my knee angle?"}


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
    monkeypatch.setenv("AGOS_GROQ_MAX_COMPLETION_TOKENS", "42")
    monkeypatch.setattr(humanization.urllib.request, "urlopen", fake_urlopen)

    model, prompt, text = humanization.humanize_image(_humanization_image())

    assert model == "groq:test-model"
    assert text == "Drive the knee forward."
    assert captured["url"] == humanization.GROQ_URL
    assert captured["authorization"] == "Bearer test-key"
    assert captured["timeout"] == 30
    assert captured["body"]["model"] == "test-model"
    assert captured["body"]["max_completion_tokens"] == 42
    assert captured["body"]["reasoning_effort"] == "low"
    assert captured["body"]["temperature"] == 0
    assert captured["body"]["messages"][0]["role"] == "system"
    user_content = captured["body"]["messages"][1]["content"]
    assert '"swing_leg"' in user_content
    assert "160" not in user_content
    assert "Position check for this photo" in prompt


def test_groq_humanization_falls_back_when_model_missing(monkeypatch):
    calls = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(
                {"choices": [{"message": {"content": "Fallback feedback."}}]}
            ).encode()

    def fake_urlopen(request, timeout):
        model = json.loads(request.data)["model"]
        calls.append(model)
        if model == "missing-model":
            raise urllib.error.HTTPError(
                request.full_url,
                404,
                "Not Found",
                {},
                io.BytesIO(b'{"error":{"code":"model_not_found"}}'),
            )
        return FakeResponse()

    monkeypatch.setenv("AGOS_HUMANIZATION_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("AGOS_GROQ_MODEL", "missing-model")
    monkeypatch.setenv("AGOS_GROQ_FALLBACK_MODEL", "fallback-model")
    monkeypatch.setattr(humanization.urllib.request, "urlopen", fake_urlopen)

    model, _, text = humanization.humanize_image(_humanization_image())

    assert calls == ["missing-model", "fallback-model"]
    assert model == "groq:fallback-model"
    assert text == "Fallback feedback."
