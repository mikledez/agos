from __future__ import annotations

import os

from fastapi import Depends, Header, HTTPException

from db import repository as repo

DEV_USER_EMAIL = os.getenv("AGOS_DEV_USER_EMAIL", "dev@local")
_ALLOW_DEV_USER = os.getenv("AGOS_ALLOW_DEV_USER", "1").lower() not in {
    "0",
    "false",
    "no",
}

def get_current_user_id(
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> int:
    if x_user_id is not None:
        if repo.get_user(x_user_id) is None:
            raise HTTPException(status_code=401, detail="Unknown user")
        return x_user_id

    if not _ALLOW_DEV_USER:
        raise HTTPException(status_code=401, detail="Authentication required")

    user = repo.upsert_user(DEV_USER_EMAIL, name="Dev User")
    return user["id"]

def get_current_user(user_id: int = Depends(get_current_user_id)) -> dict:
    user = repo.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Unknown user")
    return user
