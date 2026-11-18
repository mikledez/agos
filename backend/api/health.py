from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from db.connection import get_pool

router = APIRouter(tags=["health"])

@router.get("/health")
def health() -> dict:
    try:
        with get_pool().connection() as conn:
            conn.execute("SELECT 1")
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail="database unavailable"
        ) from exc
    # Render sets RENDER_GIT_COMMIT; the post-deploy check uses it to confirm
    # the new commit is live.
    return {
        "status": "ok",
        "database": "ok",
        "commit": os.environ.get("RENDER_GIT_COMMIT"),
    }

@router.get("/")
def root() -> dict:
    return {
        "name": "Sprint Form Analyzer API",
        "docs": "/docs",
        "health": "/health",
    }
