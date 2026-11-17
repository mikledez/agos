from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from db import repository as repo

from .deps import get_current_user_id
from .schemas import Direction, Phase, SearchOut
from .serializers import image_payload

router = APIRouter(tags=["search"])

@router.get("/search", response_model=SearchOut)
def search_library(
    user_id: int = Depends(get_current_user_id),
    q: str = Query(default="", max_length=200),
    phase: Phase | None = Query(default=None),
    direction: Direction | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
) -> dict:
    results = repo.search_library(
        user_id, query=q, phase=phase, direction=direction, limit=limit
    )
    return {
        "folders": results["folders"],
        "images": [image_payload(row) for row in results["images"]],
    }
