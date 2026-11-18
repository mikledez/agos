"""Athlete progress: each image's angles and a form score, oldest first."""

from __future__ import annotations

from typing import Any

from db import repository as repo

from .analysis import RANGES, assess


def _score(phase: str, row: dict[str, Any]) -> tuple[int, int]:
    """(joints in range, joints measured); unclear joints don't count."""

    checks = assess(
        phase,
        {"hip": row["swing_hip"], "knee": row["swing_knee"], "ankle": row["swing_ankle"]},
        {"hip": row["stance_hip"], "knee": row["stance_knee"], "ankle": row["stance_ankle"]},
        row["thigh_thigh"],
    )
    results = [*checks["swing"].values(), *checks["stance"].values()]
    if checks["thigh_thigh"] is not None:
        results.append(checks["thigh_thigh"])
    measured = [r for r in results if r["status"] != "unclear"]
    return sum(r["status"] == "good" for r in measured), len(measured)

def athlete_progress(session_id: int, user_id: int) -> dict[str, Any]:
    points = []
    for row in repo.list_subtree_images(session_id, user_id):
        in_range, measured = _score(row["phase"], row)
        points.append(
            {
                "image_id": row["id"],
                "original_filename": row["original_filename"],
                "phase": row["phase"],
                "created_at": row["created_at"],
                "score": round(100 * in_range / measured) if measured else None,
                "in_range": in_range,
                "measured": measured,
                "swing": {
                    "hip": row["swing_hip"],
                    "knee": row["swing_knee"],
                    "ankle": row["swing_ankle"],
                },
                "stance": {
                    "hip": row["stance_hip"],
                    "knee": row["stance_knee"],
                    "ankle": row["stance_ankle"],
                },
                "thigh_thigh": row["thigh_thigh"],
            }
        )
    return {"points": points, "ranges": RANGES}
