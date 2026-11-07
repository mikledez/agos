from __future__ import annotations

import math
from contextlib import contextmanager
from typing import Any, Iterator

from psycopg.errors import UniqueViolation
from psycopg.rows import dict_row

from .connection import get_pool

PHASES = ("toe_off", "mid_stance", "touchdown")
DIRECTIONS = ("ltr", "rtl")

Row = dict[str, Any]
_UNSET = object()

UNSET = _UNSET

class ValidationError(ValueError):
    pass

class ConflictError(ValueError):
    pass

@contextmanager
def _cursor() -> Iterator[Any]:
    with get_pool().connection() as conn:
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise

def _limit_offset(limit: int | None, offset: int) -> tuple[int | None, int]:
    if limit is not None and limit < 0:
        raise ValidationError("limit must be >= 0")
    if offset < 0:
        raise ValidationError("offset must be >= 0")
    return limit, offset

def _clean_email(email: str) -> str:
    if not isinstance(email, str) or not email.strip():
        raise ValidationError("email is required")
    return email.strip().lower()

def _clean_name(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValidationError("name is required")
    return name.strip()

def _validate_phase(phase: str) -> None:
    if phase not in PHASES:
        raise ValidationError(f"unknown phase: {phase!r}")

def _validate_direction(direction: str) -> None:
    if direction not in DIRECTIONS:
        raise ValidationError(f"unknown direction: {direction!r}")

def _finite_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None

def _update_row(
    cur,
    table: str,
    id_column: str,
    id_value: Any,
    changes: dict[str, Any],
    allowed: frozenset[str],
    user_id: int | None = None,
) -> Row | None:
    updates = {key: value for key, value in changes.items() if key in allowed}
    if not updates:
        raise ValidationError("no updatable fields were provided")

    assignments = ", ".join(f"{column} = %s" for column in updates)
    params: list[Any] = list(updates.values())
    params.append(id_value)
    where = f"{id_column} = %s"
    if user_id is not None:
        where += " AND user_id = %s"
        params.append(user_id)

    cur.execute(
        f"UPDATE {table} SET {assignments} WHERE {where} RETURNING *",
        params,
    )
    return cur.fetchone()

_USER_UPDATABLE = frozenset({"email", "name", "image", "email_verified"})

def create_user(
    email: str,
    *,
    name: str | None = None,
    image: str | None = None,
    email_verified: Any = None,
) -> Row:
    email = _clean_email(email)
    try:
        with _cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, name, image, email_verified)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (email, name, image, email_verified),
            )
            return cur.fetchone()
    except UniqueViolation as exc:
        raise ConflictError(f"user with email {email!r} already exists") from exc

def upsert_user(
    email: str,
    *,
    name: str | None = None,
    image: str | None = None,
    email_verified: Any = None,
) -> Row:

    email = _clean_email(email)
    with _cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (email, name, image, email_verified)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO UPDATE SET
                name = COALESCE(EXCLUDED.name, users.name),
                image = COALESCE(EXCLUDED.image, users.image),
                email_verified = COALESCE(EXCLUDED.email_verified, users.email_verified)
            RETURNING *
            """,
            (email, name, image, email_verified),
        )
        return cur.fetchone()

def get_user(user_id: int) -> Row | None:
    with _cursor() as cur:
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return cur.fetchone()

def get_user_by_email(email: str) -> Row | None:
    email = _clean_email(email)
    with _cursor() as cur:
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cur.fetchone()

def list_users(limit: int | None = None, offset: int = 0) -> list[Row]:
    limit, offset = _limit_offset(limit, offset)
    with _cursor() as cur:
        cur.execute(
            "SELECT * FROM users ORDER BY id LIMIT %s OFFSET %s",
            (limit, offset),
        )
        return cur.fetchall()

def update_user(user_id: int, **changes: Any) -> Row | None:
    if "email" in changes:
        changes["email"] = _clean_email(changes["email"])
    with _cursor() as cur:
        return _update_row(
            cur, "users", "id", user_id, changes, _USER_UPDATABLE
        )

def delete_user(user_id: int) -> bool:
    with _cursor() as cur:
        cur.execute("DELETE FROM users WHERE id = %s RETURNING id", (user_id,))
        return cur.fetchone() is not None

_session_row = "SELECT * FROM sessions WHERE id = %s AND user_id = %s"

def _ensure_session(cur, session_id: int, user_id: int) -> None:
    cur.execute("SELECT 1 FROM sessions WHERE id = %s AND user_id = %s",
                (session_id, user_id))
    if cur.fetchone() is None:
        raise ValidationError(f"session {session_id} not found")

def _has_ancestor(cur, node_id: int, ancestor_id: int, user_id: int) -> bool:

    cur.execute(
        """
        WITH RECURSIVE ancestors AS (
            SELECT id, parent_id FROM sessions WHERE id = %s AND user_id = %s
            UNION ALL
            SELECT s.id, s.parent_id
            FROM sessions s
            JOIN ancestors a ON s.id = a.parent_id
        )
        SELECT 1 FROM ancestors WHERE id = %s
        """,
        (node_id, user_id, ancestor_id),
    )
    return cur.fetchone() is not None

def create_session(
    user_id: int, name: str, parent_id: int | None = None
) -> Row:
    name = _clean_name(name)
    with _cursor() as cur:
        if parent_id is not None:
            _ensure_session(cur, parent_id, user_id)
        cur.execute(
            """
            INSERT INTO sessions (user_id, parent_id, name)
            VALUES (%s, %s, %s)
            RETURNING *
            """,
            (user_id, parent_id, name),
        )
        return cur.fetchone()

def get_session(session_id: int, user_id: int) -> Row | None:
    with _cursor() as cur:
        cur.execute(_session_row, (session_id, user_id))
        return cur.fetchone()

def list_sessions(
    user_id: int,
    *,
    parent_id: int | None | object = _UNSET,
    limit: int | None = None,
    offset: int = 0,
) -> list[Row]:

    limit, offset = _limit_offset(limit, offset)
    query = "SELECT * FROM sessions WHERE user_id = %s"
    params: list[Any] = [user_id]
    if parent_id is None:
        query += " AND parent_id IS NULL"
    elif parent_id is not _UNSET:
        query += " AND parent_id = %s"
        params.append(parent_id)
    query += " ORDER BY created_at, id LIMIT %s OFFSET %s"
    params.extend((limit, offset))
    with _cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()

def update_session(
    session_id: int,
    user_id: int,
    *,
    name: str | object = _UNSET,
    parent_id: int | None | object = _UNSET,
) -> Row | None:
    changes: dict[str, Any] = {}
    if name is not _UNSET:
        changes["name"] = _clean_name(name)

    with _cursor() as cur:
        cur.execute(_session_row + " FOR UPDATE", (session_id, user_id))
        existing = cur.fetchone()
        if existing is None:
            return None

        if parent_id is not _UNSET:
            if parent_id is not None:
                if parent_id == session_id:
                    raise ValidationError("a session cannot be its own parent")
                _ensure_session(cur, parent_id, user_id)
                if _has_ancestor(cur, parent_id, session_id, user_id):
                    raise ValidationError(
                        "a session cannot be moved into its own descendant"
                    )
            changes["parent_id"] = parent_id

        if not changes:
            return existing
        return _update_row(
            cur,
            "sessions",
            "id",
            session_id,
            changes,
            frozenset({"name", "parent_id"}),
            user_id=user_id,
        )

def delete_session(session_id: int, user_id: int) -> bool:
    with _cursor() as cur:
        cur.execute(
            "DELETE FROM sessions WHERE id = %s AND user_id = %s RETURNING id",
            (session_id, user_id),
        )
        return cur.fetchone() is not None

_IMAGE_UPDATABLE = frozenset(
    {
        "session_id",
        "original_filename",
        "stored_filename",
        "annotated_path",
        "phase",
        "direction",
        "swing_hip",
        "swing_knee",
        "swing_ankle",
        "stance_hip",
        "stance_knee",
        "stance_ankle",
        "thigh_thigh",
        "feedback",
        "swing_feedback",
        "stance_feedback",
    }
)

def _ensure_image(cur, image_id: int, user_id: int) -> None:
    cur.execute("SELECT 1 FROM images WHERE id = %s AND user_id = %s",
                (image_id, user_id))
    if cur.fetchone() is None:
        raise ValidationError(f"image {image_id} not found")

def create_image(
    user_id: int,
    *,
    original_filename: str,
    stored_filename: str,
    phase: str,
    direction: str,
    session_id: int | None = None,
    annotated_path: str | None = None,
    swing_hip: float | None = None,
    swing_knee: float | None = None,
    swing_ankle: float | None = None,
    stance_hip: float | None = None,
    stance_knee: float | None = None,
    stance_ankle: float | None = None,
    thigh_thigh: float | None = None,
    feedback: str | None = None,
    swing_feedback: str | None = None,
    stance_feedback: str | None = None,
) -> Row:
    if not original_filename or not original_filename.strip():
        raise ValidationError("original_filename is required")
    if not stored_filename or not stored_filename.strip():
        raise ValidationError("stored_filename is required")
    _validate_phase(phase)
    _validate_direction(direction)

    with _cursor() as cur:
        if session_id is not None:
            _ensure_session(cur, session_id, user_id)
        cur.execute(
            """
            INSERT INTO images (
                user_id, session_id, original_filename, stored_filename,
                annotated_path, phase, direction,
                swing_hip, swing_knee, swing_ankle,
                stance_hip, stance_knee, stance_ankle,
                thigh_thigh, feedback, swing_feedback, stance_feedback
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s
            )
            RETURNING *
            """,
            (
                user_id,
                session_id,
                original_filename,
                stored_filename,
                annotated_path,
                phase,
                direction,
                swing_hip,
                swing_knee,
                swing_ankle,
                stance_hip,
                stance_knee,
                stance_ankle,
                thigh_thigh,
                feedback,
                swing_feedback,
                stance_feedback,
            ),
        )
        return cur.fetchone()

def create_image_from_analysis(
    user_id: int,
    *,
    original_filename: str,
    stored_filename: str,
    phase: str,
    direction: str,
    result: dict[str, Any],
    session_id: int | None = None,
    annotated_path: str | None = None,
) -> Row:

    swing = result.get("swing_leg") or {}
    stance = result.get("stance_leg") or {}
    return create_image(
        user_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        phase=phase,
        direction=direction,
        session_id=session_id,
        annotated_path=annotated_path,
        swing_hip=_finite_or_none(swing.get("hip_angle")),
        swing_knee=_finite_or_none(swing.get("knee_angle")),
        swing_ankle=_finite_or_none(swing.get("ankle_angle")),
        stance_hip=_finite_or_none(stance.get("hip_angle")),
        stance_knee=_finite_or_none(stance.get("knee_angle")),
        stance_ankle=_finite_or_none(stance.get("ankle_angle")),
        thigh_thigh=_finite_or_none(result.get("thigh_thigh_angle")),
        feedback=result.get("feedback"),
        swing_feedback=swing.get("feedback"),
        stance_feedback=stance.get("feedback"),
    )

def get_image(image_id: int, user_id: int) -> Row | None:
    with _cursor() as cur:
        cur.execute(
            "SELECT * FROM images WHERE id = %s AND user_id = %s",
            (image_id, user_id),
        )
        return cur.fetchone()

def get_image_by_stored_filename(
    user_id: int, stored_filename: str
) -> Row | None:
    with _cursor() as cur:
        cur.execute(
            """
            SELECT * FROM images
            WHERE user_id = %s AND stored_filename = %s
            """,
            (user_id, stored_filename),
        )
        return cur.fetchone()

def list_images(
    user_id: int,
    *,
    session_id: int | None | object = _UNSET,
    limit: int | None = None,
    offset: int = 0,
) -> list[Row]:

    limit, offset = _limit_offset(limit, offset)
    query = "SELECT * FROM images WHERE user_id = %s"
    params: list[Any] = [user_id]
    if session_id is None:
        query += " AND session_id IS NULL"
    elif session_id is not _UNSET:
        query += " AND session_id = %s"
        params.append(session_id)
    query += " ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s"
    params.extend((limit, offset))
    with _cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()

def update_image(image_id: int, user_id: int, **changes: Any) -> Row | None:
    if "phase" in changes:
        _validate_phase(changes["phase"])
    if "direction" in changes:
        _validate_direction(changes["direction"])
    for field in ("original_filename", "stored_filename"):
        if field in changes:
            if not isinstance(changes[field], str) or not changes[field].strip():
                raise ValidationError(f"{field} is required")
            changes[field] = changes[field].strip()

    with _cursor() as cur:
        if changes.get("session_id") is not None:
            _ensure_session(cur, changes["session_id"], user_id)
        return _update_row(
            cur,
            "images",
            "id",
            image_id,
            changes,
            _IMAGE_UPDATABLE,
            user_id=user_id,
        )

def delete_image(image_id: int, user_id: int) -> bool:
    with _cursor() as cur:
        cur.execute(
            "DELETE FROM images WHERE id = %s AND user_id = %s RETURNING id",
            (image_id, user_id),
        )
        return cur.fetchone() is not None

def save_image_files(
    image_id: int, user_id: int, *, original: bytes, annotated: bytes | None
) -> None:
    with _cursor() as cur:
        cur.execute(
            """
            INSERT INTO image_files (image_id, user_id, original, annotated)
            VALUES (%s, %s, %s, %s)
            """,
            (image_id, user_id, original, annotated),
        )

def _get_image_file(image_id: int, user_id: int, column: str) -> bytes | None:
    with _cursor() as cur:
        cur.execute(
            f"""
            SELECT {column} AS contents FROM image_files
            WHERE image_id = %s AND user_id = %s
            """,
            (image_id, user_id),
        )
        row = cur.fetchone()
    if row is None or row["contents"] is None:
        return None
    return bytes(row["contents"])

def get_original_file(image_id: int, user_id: int) -> bytes | None:
    return _get_image_file(image_id, user_id, "original")

def get_annotated_file(image_id: int, user_id: int) -> bytes | None:
    return _get_image_file(image_id, user_id, "annotated")

def touch_image_activity(image_id: int, user_id: int) -> None:
    with _cursor() as cur:
        cur.execute(
            """
            UPDATE image_files SET last_activity_at = now()
            WHERE image_id = %s AND user_id = %s
            """,
            (image_id, user_id),
        )

_NO_STORED_FILES = """
    NOT EXISTS (SELECT 1 FROM image_files AS f WHERE f.image_id = i.id)
    AND i.created_at < now() - interval '1 hour'
"""

def count_images_without_files() -> int:
    with _cursor() as cur:
        cur.execute(
            f"SELECT count(*) AS total FROM images AS i WHERE {_NO_STORED_FILES}"
        )
        return cur.fetchone()["total"]

def delete_images_without_files() -> int:
    """One-off cleanup; the age check protects uploads that are still saving."""

    with _cursor() as cur:
        cur.execute(f"DELETE FROM images AS i WHERE {_NO_STORED_FILES}")
        return cur.rowcount

def delete_inactive_images(retention_hours: int) -> int:
    """Delete images idle past the limit; older rows without stored bytes stay."""

    with _cursor() as cur:
        cur.execute(
            """
            DELETE FROM images AS i
            USING image_files AS f
            WHERE f.image_id = i.id
              AND f.last_activity_at < now() - make_interval(hours => %s)
            """,
            (retention_hours,),
        )
        return cur.rowcount

def list_chat_messages(
    image_id: int, user_id: int, limit: int = 50
) -> list[Row]:
    if limit < 1:
        raise ValidationError("limit must be >= 1")
    with _cursor() as cur:
        _ensure_image(cur, image_id, user_id)
        cur.execute(
            """
            SELECT * FROM (
                SELECT * FROM image_chat_messages
                WHERE image_id = %s AND user_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s
            ) recent
            ORDER BY created_at, id
            """,
            (image_id, user_id, limit),
        )
        return cur.fetchall()


def create_chat_exchange(
    image_id: int,
    user_id: int,
    *,
    user_content: str,
    assistant_content: str,
    model: str | None = None,
) -> dict[str, Row]:
    if not isinstance(user_content, str) or not user_content.strip():
        raise ValidationError("user_content is required")
    if not isinstance(assistant_content, str) or not assistant_content.strip():
        raise ValidationError("assistant_content is required")

    with _cursor() as cur:
        _ensure_image(cur, image_id, user_id)
        cur.execute(
            """
            INSERT INTO image_chat_messages (image_id, user_id, role, content)
            VALUES (%s, %s, 'user', %s)
            RETURNING *
            """,
            (image_id, user_id, user_content.strip()),
        )
        user_message = cur.fetchone()
        cur.execute(
            """
            INSERT INTO image_chat_messages (
                image_id, user_id, role, content, model
            )
            VALUES (%s, %s, 'assistant', %s, %s)
            RETURNING *
            """,
            (image_id, user_id, assistant_content.strip(), model),
        )
        assistant_message = cur.fetchone()
        return {
            "user_message": user_message,
            "assistant_message": assistant_message,
        }


def clear_chat_messages(image_id: int, user_id: int) -> int:
    with _cursor() as cur:
        _ensure_image(cur, image_id, user_id)
        cur.execute(
            """
            DELETE FROM image_chat_messages
            WHERE image_id = %s AND user_id = %s
            """,
            (image_id, user_id),
        )
        return cur.rowcount


_HUMANIZATION_UPDATABLE = frozenset({"model", "prompt", "humanized_text"})

def upsert_humanization(
    image_id: int,
    user_id: int,
    *,
    model: str,
    humanized_text: str,
    prompt: str | None = None,
) -> Row:
    if not model or not model.strip():
        raise ValidationError("model is required")
    if not humanized_text or not humanized_text.strip():
        raise ValidationError("humanized_text is required")

    with _cursor() as cur:
        _ensure_image(cur, image_id, user_id)
        cur.execute(
            """
            INSERT INTO image_humanizations (
                image_id, user_id, model, prompt, humanized_text
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (image_id) DO UPDATE SET
                model = EXCLUDED.model,
                prompt = EXCLUDED.prompt,
                humanized_text = EXCLUDED.humanized_text
            RETURNING *
            """,
            (image_id, user_id, model, prompt, humanized_text),
        )
        return cur.fetchone()

def get_humanization(image_id: int, user_id: int) -> Row | None:
    with _cursor() as cur:
        cur.execute(
            """
            SELECT * FROM image_humanizations
            WHERE image_id = %s AND user_id = %s
            """,
            (image_id, user_id),
        )
        return cur.fetchone()

def list_humanizations(
    user_id: int, limit: int | None = None, offset: int = 0
) -> list[Row]:
    limit, offset = _limit_offset(limit, offset)
    with _cursor() as cur:
        cur.execute(
            """
            SELECT * FROM image_humanizations
            WHERE user_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT %s OFFSET %s
            """,
            (user_id, limit, offset),
        )
        return cur.fetchall()

def update_humanization(
    image_id: int, user_id: int, **changes: Any
) -> Row | None:
    for field in ("model", "humanized_text"):
        if field in changes and (
            not isinstance(changes[field], str) or not changes[field].strip()
        ):
            raise ValidationError(f"{field} is required")
    with _cursor() as cur:
        return _update_row(
            cur,
            "image_humanizations",
            "image_id",
            image_id,
            changes,
            _HUMANIZATION_UPDATABLE,
            user_id=user_id,
        )

def delete_humanization(image_id: int, user_id: int) -> bool:
    with _cursor() as cur:
        cur.execute(
            """
            DELETE FROM image_humanizations
            WHERE image_id = %s AND user_id = %s
            RETURNING id
            """,
            (image_id, user_id),
        )
        return cur.fetchone() is not None
