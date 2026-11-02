from __future__ import annotations

from typing import Any

def image_payload(row: dict[str, Any]) -> dict[str, Any]:
    data = dict(row)
    data["original_url"] = f"/images/{row['id']}/file"
    data["annotated_url"] = (
        f"/images/{row['id']}/annotated" if row.get("annotated_path") else None
    )
    return data
