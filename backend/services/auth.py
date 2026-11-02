"""Verify the short-lived identity token minted by the Next.js frontend.

The browser never talks to FastAPI directly. Next.js authenticates the
user with Auth.js (Google OAuth), mints an HS256 token with the shared
``AGOS_INTERNAL_SECRET`` and forwards it as ``Authorization: Bearer``.
This module verifies that token and upserts the matching local user.
"""

from __future__ import annotations

import os
from typing import Any

import jwt

from db import repository as repo

ALGORITHM = "HS256"
DEV_USER_EMAIL = os.getenv("AGOS_DEV_USER_EMAIL", "dev@local")


class AuthError(ValueError):
    pass


def _internal_secret() -> str:
    secret = os.getenv("AGOS_INTERNAL_SECRET") or os.getenv("SESSION_SECRET")
    if not secret:
        raise AuthError("AGOS_INTERNAL_SECRET is not configured")
    return secret


def _dev_user_allowed() -> bool:
    return os.getenv("AGOS_ALLOW_DEV_USER", "0").lower() in {
        "1",
        "true",
        "yes",
    }


def verify_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            _internal_secret(),
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise AuthError("invalid or expired token") from exc

    email = payload.get("email") or payload.get("sub")
    if not isinstance(email, str) or not email.strip():
        raise AuthError("token is missing an email claim")
    return {
        "email": email,
        "name": payload.get("name"),
        "image": payload.get("picture"),
    }


def authenticate(authorization: str | None) -> repo.Row:
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise AuthError("Authorization header must be a bearer token")
        claims = verify_token(token.strip())
        return repo.upsert_user(
            claims["email"], name=claims["name"], image=claims["image"]
        )

    if _dev_user_allowed():
        return repo.upsert_user(DEV_USER_EMAIL, name="Dev User")

    raise AuthError("authentication required")
