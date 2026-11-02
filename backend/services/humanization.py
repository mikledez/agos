"""Local LLM feedback humanization.

The model receives *metadata only* (phase, measured angles, deterministic
feedback and the reference ranges) -- never image bytes. It runs locally
through Hugging Face ``transformers``; the heavy dependencies live in
``requirements-llm.txt`` so the pose API can be installed without torch.

Configure with:
    AGOS_HUMANIZATION_MODEL        (default HuggingFaceTB/SmolLM2-1.7B-Instruct)
    AGOS_HUMANIZATION_DEVICE       (default cpu)
    AGOS_HUMANIZATION_MAX_TOKENS   (default 160)
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any

from .analysis import RANGES

DEFAULT_MODEL = "HuggingFaceTB/SmolLM2-1.7B-Instruct"
MODEL_ID = os.getenv("AGOS_HUMANIZATION_MODEL", DEFAULT_MODEL)
MAX_NEW_TOKENS = int(os.getenv("AGOS_HUMANIZATION_MAX_TOKENS", "160"))
DEVICE = os.getenv("AGOS_HUMANIZATION_DEVICE", "cpu")

SYSTEM_PROMPT = (
    "You are a sprint biomechanics coach. You receive measured lower-limb "
    "joint angles, the reference range for the sprint phase, and rule-based "
    "feedback. Write 2-3 short, concrete sentences telling the athlete what "
    "is good and what to adjust. Use plain text only, no markdown or lists. "
    "Do not invent measurements or give medical advice."
)


class HumanizationUnavailable(RuntimeError):
    """Raised when the optional local model or its dependencies are absent."""


@lru_cache(maxsize=1)
def _generator() -> Any:
    try:
        import torch
        from transformers import pipeline
    except ModuleNotFoundError as exc:
        raise HumanizationUnavailable(
            "Local humanization requires the optional dependencies: "
            "pip install -r requirements-llm.txt"
        ) from exc

    return pipeline(
        "text-generation",
        model=MODEL_ID,
        device=torch.device(DEVICE),
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


def build_prompt(image: dict[str, Any]) -> str:
    payload = build_payload(image)
    return (
        f"{SYSTEM_PROMPT}\n\n"
        "Analysis metadata (angles in degrees):\n"
        f"{json.dumps(payload, ensure_ascii=True)}\n\n"
        "Coach feedback:"
    )


def humanize_image(image: dict[str, Any]) -> tuple[str, str, str]:
    """Return ``(model_id, prompt, humanized_text)`` for one stored image."""
    prompt = build_prompt(image)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    try:
        generator = _generator()
        tokenizer = generator.tokenizer
        if getattr(tokenizer, "chat_template", None):
            text_input = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        else:
            text_input = f"{SYSTEM_PROMPT}\n\n{prompt}\n"

        output = generator(
            text_input,
            max_new_tokens=MAX_NEW_TOKENS,
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
    return MODEL_ID, prompt, text
