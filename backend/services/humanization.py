"""Coach-feedback humanization with local and hosted providers.

The model receives *metadata only* (phase, measured angles, deterministic
feedback and the reference ranges) -- never image bytes.

Providers (``AGOS_HUMANIZATION_PROVIDER``):

- ``auto``: use Groq when ``GROQ_API_KEY`` is set, otherwise local.
- ``groq``: hosted OpenAI-compatible Groq chat completion.
- ``local``: Hugging Face ``transformers``; requires
  ``backend/requirements-llm.txt``.

Other configuration:
    AGOS_HUMANIZATION_MODEL     local model (default SmolLM2-1.7B-Instruct)
    AGOS_GROQ_MODEL             Groq model (default openai/gpt-oss-20b)
    AGOS_GROQ_FALLBACK_MODEL    used on model_not_found (default gpt-oss-120b)
    AGOS_HUMANIZATION_DEVICE    local device (default cpu)
    AGOS_HUMANIZATION_MAX_TOKENS (default 160)
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from functools import lru_cache
from typing import Any

from .analysis import JOINTS, RANGES, assess, thigh_gap_to_show

LOCAL_DEFAULT_MODEL = "HuggingFaceTB/SmolLM2-1.7B-Instruct"
GROQ_DEFAULT_MODEL = "openai/gpt-oss-20b"
GROQ_FALLBACK_MODEL = "openai/gpt-oss-120b"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

_AUDIENCE = (
    "Your readers range from beginners fixing their own sprint form to "
    "coaches, so lead with simple body-position language and a cue the "
    "athlete can feel or do, while naming the leg, joint, and sprint phase "
    "precisely enough for a coach to use. The swing leg is the leg in the "
    "air; the stance leg is the leg on the ground. "
)

SYSTEM_PROMPT = (
    "You are a sprint coach reviewing one photo. "
    + _AUDIENCE
    + "You receive a plain-language check of each joint: what is off and a "
    "cue to fix it, plus what already looks good. Write 2-4 short sentences: "
    "start with the most important fix, then any other fixes, then briefly "
    "say what looks good. Describe positions in words such as too bent, too "
    "straight, thigh too low, or foot landing too far in front. Never state "
    "degrees, angle numbers, or reference ranges. Use plain text only, no "
    "markdown or lists. Do not invent problems or give medical advice."
)

CHAT_SYSTEM_PROMPT = (
    "You are AGOS, a sprint coach answering questions about one analyzed "
    "sprint photo. "
    + _AUDIENCE
    + "Answer in 2-4 concise sentences of plain text, with no markdown or "
    "lists, using the position check in words and practical cues or drills. "
    "Only give degrees or reference ranges when the athlete explicitly asks "
    "for numbers or angles; then use the supplied measurements and never "
    "invent numbers. Do not provide a medical diagnosis."
)

_PHASE_NAMES = {
    "toe_off": "toe-off (the moment the back foot leaves the ground)",
    "mid_stance": "mid-stance (the body passing over the foot on the ground)",
    "touchdown": "touchdown (the moment the front foot lands)",
}
_CHECK_NAMES = {"hip": "thigh position", "knee": "knee bend", "ankle": "ankle and foot"}

MAX_CHAT_QUESTION_CHARS = 1000
MAX_CHAT_HISTORY_MESSAGES = 12


class HumanizationUnavailable(RuntimeError):
    """Raised when the configured model or provider is not available."""


def _provider() -> str:
    configured = os.getenv("AGOS_HUMANIZATION_PROVIDER", "auto").strip().lower()
    if configured in {"groq", "local"}:
        return configured
    return "groq" if os.getenv("GROQ_API_KEY", "").strip() else "local"


def _local_model_id() -> str:
    return (
        os.getenv("AGOS_HUMANIZATION_MODEL", "").strip()
        or LOCAL_DEFAULT_MODEL
    )


def _groq_model_id() -> str:
    return os.getenv("AGOS_GROQ_MODEL", "").strip() or GROQ_DEFAULT_MODEL


def _groq_model_candidates() -> list[str]:
    primary = _groq_model_id()
    fallback = (
        os.getenv("AGOS_GROQ_FALLBACK_MODEL", "").strip()
        or GROQ_FALLBACK_MODEL
    )
    if fallback == primary:
        return [primary]
    return [primary, fallback]


def _max_new_tokens() -> int:
    return int(os.getenv("AGOS_HUMANIZATION_MAX_TOKENS", "160"))


def _groq_max_completion_tokens() -> int:
    return int(os.getenv("AGOS_GROQ_MAX_COMPLETION_TOKENS", "800"))


@lru_cache(maxsize=1)
def _generator(model_id: str) -> Any:
    try:
        import torch
        from transformers import pipeline
    except ModuleNotFoundError as exc:
        raise HumanizationUnavailable(
            "Local humanization is not installed. Set GROQ_API_KEY for hosted "
            "feedback or run pip install -r backend/requirements-llm.txt."
        ) from exc

    device = os.getenv("AGOS_HUMANIZATION_DEVICE", "cpu")
    return pipeline(
        "text-generation",
        model=model_id,
        device=torch.device(device),
    )


def _leg_angles(image: dict[str, Any], role: str) -> dict[str, float | None]:
    return {joint: image.get(f"{role}_{joint}") for joint in JOINTS}


def _describe_leg(checks: dict[str, dict[str, Any]]) -> dict[str, Any]:
    fixes = []
    looks_good = []
    for joint in JOINTS:
        check = checks[joint]
        if check["status"] == "good":
            looks_good.append(_CHECK_NAMES[joint])
        else:
            fixes.append({"problem": check["problem"], "fix": check["cue"]})
    return {"fixes": fixes, "looks_good": looks_good}


def build_payload(
    image: dict[str, Any], *, include_measurements: bool = False
) -> dict[str, Any]:
    """Describe the analysis in words; angles only when explicitly included."""

    phase = image["phase"]
    checks = assess(
        phase,
        _leg_angles(image, "swing"),
        _leg_angles(image, "stance"),
        image.get("thigh_thigh"),
    )
    payload: dict[str, Any] = {
        "phase": _PHASE_NAMES.get(phase, phase),
        "swing_leg": _describe_leg(checks["swing"]),
        "stance_leg": _describe_leg(checks["stance"]),
    }
    thigh_check = thigh_gap_to_show(checks)
    if checks["thigh_thigh"] is not None and thigh_check is not None:
        payload["thigh_gap_between_legs"] = (
            "looks good"
            if thigh_check["status"] == "good"
            else {"problem": thigh_check["problem"], "fix": thigh_check["cue"]}
        )
    if include_measurements:
        payload["measurements_only_if_asked"] = {
            "angles_degrees": {
                "swing_leg": _leg_angles(image, "swing"),
                "stance_leg": _leg_angles(image, "stance"),
                "thigh_gap": image.get("thigh_thigh"),
            },
            "target_ranges_degrees": RANGES[phase],
        }
    return payload


def build_user_prompt(image: dict[str, Any]) -> str:
    payload = build_payload(image)
    return (
        "Position check for this photo:\n"
        f"{json.dumps(payload, ensure_ascii=True)}\n\n"
        "Coach feedback:"
    )


def build_prompt(image: dict[str, Any]) -> str:
    return f"{SYSTEM_PROMPT}\n\n{build_user_prompt(image)}"


class _GroqModelNotFound(Exception):
    pass


def _post_groq(
    api_key: str,
    model_id: str,
    messages: list[dict[str, str]],
    *,
    max_completion_tokens: int | None = None,
) -> tuple[str, str]:
    body = json.dumps(
        {
            "model": model_id,
            "messages": messages,
            "temperature": 0,
            "max_completion_tokens": (
                max_completion_tokens
                if max_completion_tokens is not None
                else _groq_max_completion_tokens()
            ),
            "reasoning_effort": "low",
            "stream": False,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        GROQ_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "agos-sprint-analyzer/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        if exc.code == 404 and "model_not_found" in detail:
            raise _GroqModelNotFound(detail) from exc
        raise HumanizationUnavailable(
            f"Groq request failed ({exc.code}): {detail}"
        ) from exc
    except (urllib.error.URLError, OSError) as exc:
        raise HumanizationUnavailable(f"Groq request failed: {exc}") from exc

    try:
        choice = payload["choices"][0]
        text = str(choice["message"].get("content") or "").strip()
        finish_reason = choice.get("finish_reason")
    except (KeyError, IndexError, TypeError) as exc:
        raise HumanizationUnavailable(
            "Groq returned an unexpected response."
        ) from exc
    if not text:
        raise HumanizationUnavailable(
            f"Groq returned an empty response (finish_reason={finish_reason})"
        )
    return model_id, text


def _generate_groq_messages(
    messages: list[dict[str, str]],
    *,
    max_completion_tokens: int | None = None,
) -> tuple[str, str]:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise HumanizationUnavailable(
            "GROQ_API_KEY is not configured for hosted humanization."
        )

    last_error = ""
    for model_id in _groq_model_candidates():
        try:
            return _post_groq(
                api_key,
                model_id,
                messages,
                max_completion_tokens=max_completion_tokens,
            )
        except _GroqModelNotFound as exc:
            last_error = str(exc)
    raise HumanizationUnavailable(
        f"No configured Groq model is available: {last_error}"
    )


def _generate_groq(image: dict[str, Any]) -> tuple[str, str]:
    return _generate_groq_messages(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(image)},
        ]
    )


def _generate_local_messages(
    messages: list[dict[str, str]], model_id: str
) -> str:
    try:
        generator = _generator(model_id)
        tokenizer = generator.tokenizer
        if getattr(tokenizer, "chat_template", None):
            text_input = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        else:
            text_input = "\n\n".join(
                f"{message['role']}: {message['content']}"
                for message in messages
            )
            text_input += "\nassistant:"

        output = generator(
            text_input,
            max_new_tokens=_max_new_tokens(),
            do_sample=False,
            return_full_text=False,
            truncation=True,
        )
    except HumanizationUnavailable:
        raise
    except Exception as exc:
        raise HumanizationUnavailable(
            f"local model failed to generate a response: {exc}"
        ) from exc

    generated = output[0].get("generated_text", "") if output else ""
    if isinstance(generated, list):
        generated = generated[-1].get("content", "")
    text = str(generated).strip()
    if not text:
        raise HumanizationUnavailable("local model returned an empty response")
    return text


def _generate_local(image: dict[str, Any], model_id: str) -> str:
    return _generate_local_messages(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(image)},
        ],
        model_id,
    )


def _build_chat_messages(
    image: dict[str, Any],
    messages: list[dict[str, Any]],
    latest_question: str,
    existing_feedback: str | None,
) -> list[dict[str, str]]:
    context = {
        "analysis": build_payload(image, include_measurements=True),
        "existing_ai_feedback": existing_feedback,
    }
    system_content = (
        f"{CHAT_SYSTEM_PROMPT}\n\n"
        "Analysis context:\n"
        f"{json.dumps(context, ensure_ascii=True)}"
    )

    history: list[dict[str, str]] = []
    for message in list(messages or [])[-MAX_CHAT_HISTORY_MESSAGES:]:
        role = message.get("role")
        content = str(message.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            history.append(
                {"role": role, "content": content[:MAX_CHAT_QUESTION_CHARS]}
            )

    question = str(latest_question or "").strip()
    if not question:
        raise HumanizationUnavailable("A question is required.")
    question = question[:MAX_CHAT_QUESTION_CHARS]

    return [
        {"role": "system", "content": system_content},
        *history,
        {"role": "user", "content": question},
    ]


def answer_question(
    image: dict[str, Any],
    messages: list[dict[str, Any]],
    latest_question: str,
    existing_feedback: str | None = None,
) -> tuple[str, str]:
    """Return ``(model_id, answer)`` for one chat question about an image."""
    chat_messages = _build_chat_messages(
        image, messages, latest_question, existing_feedback
    )

    if _provider() == "groq":
        model_id, text = _generate_groq_messages(
            chat_messages, max_completion_tokens=_groq_max_completion_tokens()
        )
        return f"groq:{model_id}", text

    model_id = f"local:{_local_model_id()}"
    return model_id, _generate_local_messages(
        chat_messages, _local_model_id()
    )


def humanize_image(image: dict[str, Any]) -> tuple[str, str, str]:
    """Return ``(model_id, prompt, humanized_text)`` for one stored image."""
    prompt = build_prompt(image)
    provider = _provider()

    if provider == "groq":
        model_id, text = _generate_groq(image)
        return f"groq:{model_id}", prompt, text

    model_id = f"local:{_local_model_id()}"
    return model_id, prompt, _generate_local(image, _local_model_id())
