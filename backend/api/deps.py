from __future__ import annotations

from fastapi import Depends, Header, HTTPException

from services import auth as auth_service


def get_current_user_id(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> int:
    try:
        return auth_service.authenticate(authorization)["id"]
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def get_current_user(user_id: int = Depends(get_current_user_id)) -> dict:
    from db import repository as repo

    user = repo.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Unknown user")
    return user
