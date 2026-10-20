from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from db import repository as repo

from .deps import get_current_user_id
from .schemas import SessionCreate, SessionOut, SessionUpdate
from .serializers import image_payload

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("", response_model=SessionOut, status_code=201)
def create_session(
    payload: SessionCreate, user_id: int = Depends(get_current_user_id)
) -> repo.Row:
    if payload.parent_id is not None and (
        repo.get_session(payload.parent_id, user_id) is None
    ):
        raise HTTPException(status_code=404, detail="Parent session not found")
    return repo.create_session(user_id, payload.name, parent_id=payload.parent_id)

@router.get("", response_model=list[SessionOut])
def list_sessions(
    user_id: int = Depends(get_current_user_id),
    parent_id: int | None = Query(default=None),
    root: bool = Query(default=False),
    limit: int | None = Query(default=None, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[repo.Row]:
    if root and parent_id is not None:
        raise HTTPException(
            status_code=400, detail="Use either root or parent_id, not both"
        )
    if root:
        session_filter: object = None
    elif parent_id is not None:
        if repo.get_session(parent_id, user_id) is None:
            raise HTTPException(status_code=404, detail="Session not found")
        session_filter = parent_id
    else:
        session_filter = repo.UNSET
    return repo.list_sessions(
        user_id, parent_id=session_filter, limit=limit, offset=offset
    )

@router.get("/{session_id}", response_model=SessionOut)
def get_session(
    session_id: int, user_id: int = Depends(get_current_user_id)
) -> repo.Row:
    session = repo.get_session(session_id, user_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.get("/{session_id}/images")
def list_session_images(
    session_id: int,
    user_id: int = Depends(get_current_user_id),
    limit: int | None = Query(default=None, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    if repo.get_session(session_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    rows = repo.list_images(
        user_id, session_id=session_id, limit=limit, offset=offset
    )
    return [image_payload(row) for row in rows]

@router.patch("/{session_id}", response_model=SessionOut)
def update_session(
    session_id: int,
    payload: SessionUpdate,
    user_id: int = Depends(get_current_user_id),
) -> repo.Row:
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="No fields to update")
    if changes.get("parent_id") is not None and (
        repo.get_session(changes["parent_id"], user_id) is None
    ):
        raise HTTPException(status_code=404, detail="Parent session not found")
    session = repo.update_session(session_id, user_id, **changes)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.delete("/{session_id}", status_code=204)
def delete_session(
    session_id: int, user_id: int = Depends(get_current_user_id)
) -> None:
    from services import image_service

    if not image_service.delete_session(user_id, session_id):
        raise HTTPException(status_code=404, detail="Session not found")
