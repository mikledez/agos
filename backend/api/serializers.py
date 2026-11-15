from __future__ import annotations

from typing import Any

def image_payload(row: dict[str, Any]) -> dict[str, Any]:
    data = dict(row)
    data["original_url"] = f"/images/{row['id']}/file"
    data["thumbnail_url"] = f"/images/{row['id']}/thumbnail"
    has_photo = row.get("has_photo", True)
    data["has_photo"] = has_photo
    data["annotated_url"] = (
        f"/images/{row['id']}/annotated"
        if row.get("annotated_path") and has_photo
        else None
    )
    return data
