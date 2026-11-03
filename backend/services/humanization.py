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

from .analysis import RANGES

LOCAL_DEFAULT_MODEL = "HuggingFaceTB/SmolLM2-1.7B-Instruct"
GROQ_DEFAULT_MODEL = "openai/gpt-oss-20b"
GROQ_FALLBACK_MODEL = "openai/gpt-oss-120b"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = (
    "You are a sprint biomechanics coach. You receive measured lower-limb "
    "joint angles, the reference range for the sprint phase, and rule-based "
    "feedback. Write 2-3 short, concrete sentences telling the athlete what "
    "is good and what to adjust. Use plain text only, no markdown or lists. "
    "Do not invent measurements or give medical advice."
)


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


def build_payload(image: dict[str, Any]) -> dict[str, Any]:
    phase = image["phase"]
    return {
        "phase": phase,
        "direction": image["direction"],
        "swing_leg": {
            "hip": image.get("swing_hip"),
            "knee": image.get("swing_knee"),
            "ankle": image.get("swing_ankle"),
            "feedback": image.get("swing_feedback"),
        },
        "stance_leg": {
            "hip": image.get("stance_hip"),
            "knee": image.get("stance_knee"),
            "ankle": image.get("stance_ankle"),
            "feedback": image.get("stance_feedback"),
        },
        "thigh_thigh": image.get("thigh_thigh"),
        "overall_feedback": image.get("feedback"),
        "reference_ranges": RANGES[phase],
    }


def build_user_prompt(image: dict[str, Any]) -> str:
    payload = build_payload(image)
    return (
        "Analysis metadata (angles in degrees):\n"
        f"{json.dumps(payload, ensure_ascii=True)}\n\n"
        "Coach feedback:"
    )


def build_prompt(image: dict[str, Any]) -> str:
    return f"{SYSTEM_PROMPT}\n\n{build_user_prompt(image)}"


class _GroqModelNotFound(Exception):
    pass


def _post_groq(
    api_key: str, model_id: str, image: dict[str, Any]
) -> tuple[str, str]:
    body = json.dumps(
        {
            "model": model_id,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(image)},
            ],
            "temperature": 0,
            "max_completion_tokens": _groq_max_completion_tokens(),
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


def _generate_groq(image: dict[str, Any]) -> tuple[str, str]:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise HumanizationUnavailable(
            "GROQ_API_KEY is not configured for hosted humanization."
        )

    last_error = ""
    for model_id in _groq_model_candidates():
        try:
            return _post_groq(api_key, model_id, image)
        except _GroqModelNotFound as exc:
            last_error = str(exc)
    raise HumanizationUnavailable(
        f"No configured Groq model is available: {last_error}"
    )


def _generate_local(image: dict[str, Any], model_id: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(image)},
    ]
    try:
        generator = _generator(model_id)
        tokenizer = generator.tokenizer
        if getattr(tokenizer, "chat_template", None):
            text_input = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        else:
            text_input = f"{SYSTEM_PROMPT}\n\n{build_user_prompt(image)}\n"

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
            f"local model failed to generate feedback: {exc}"
        ) from exc

    generated = output[0].get("generated_text", "") if output else ""
    if isinstance(generated, list):
        generated = generated[-1].get("content", "")
    text = str(generated).strip()
    if not text:
        raise HumanizationUnavailable("local model returned an empty response")
    return text


def humanize_image(image: dict[str, Any]) -> tuple[str, str, str]:
    """Return ``(model_id, prompt, humanized_text)`` for one stored image."""
    prompt = build_prompt(image)
    provider = _provider()

    if provider == "groq":
        model_id, text = _generate_groq(image)
        return f"groq:{model_id}", prompt, text

    model_id = f"local:{_local_model_id()}"
    return model_id, prompt, _generate_local(image, _local_model_id())
