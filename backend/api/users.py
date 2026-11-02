from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from db import repository as repo

from .deps import get_current_user
from .schemas import UserOut, UserUpdate

router = APIRouter(tags=["users"])

@router.get("/me", response_model=UserOut)
def get_me(user: dict = Depends(get_current_user)) -> repo.Row:
    return user

@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate, user: dict = Depends(get_current_user)
) -> repo.Row:
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="No fields to update")
    return repo.update_user(user["id"], **changes)
