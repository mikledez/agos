import os
import threading
from datetime import datetime, timedelta, timezone

import cv2
import jwt
import numpy as np
import pytest
from fastapi.testclient import TestClient

import main
from db import repository as repo
from db.connection import get_pool
from services import humanization, image_service, storage


def auth_headers(email: str) -> dict[str, str]:
    token = jwt.encode(
        {
            "sub": email,
            "email": email,
            "name": "Test User",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        os.environ["AGOS_INTERNAL_SECRET"],
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}

FAKE_RESULT = {
    "phase": "toe_off",
    "swing_leg": {
        "hip_angle": 105.0,
        "knee_angle": 70.0,
        "ankle_angle": 100.0,
        "feedback": "Good positions",
    },
    "stance_leg": {
        "hip_angle": 198.0,
        "knee_angle": 145.0,
        "ankle_angle": 130.0,
        "feedback": "Good positions",
    },
    "thigh_thigh_angle": None,
    "feedback": "Good positions",
}

@pytest.fixture
def client():
    return TestClient(main.app)

@pytest.fixture
def fake_analysis(monkeypatch):
    def fake_analyze(
        user_id, *, contents, original_filename, phase, direction,
        session_id=None,
    ):
        stored, annotated = storage.new_image_names(user_id, original_filename)
        row = repo.create_image_from_analysis(
            user_id,
            original_filename=original_filename,
            stored_filename=stored,
            phase=phase,
            direction=direction,
            result=FAKE_RESULT,
            session_id=session_id,
            annotated_path=annotated,
        )
        repo.save_image_files(
            row["id"], user_id, original=contents, annotated=b"annotated"
        )
        return row, FAKE_RESULT, "QUJD"

    monkeypatch.setattr(image_service, "analyze_and_store", fake_analyze)

def _upload(client, session_id=None, filename="run.png"):
    data = {"phase": "toe_off", "direction": "ltr"}
    if session_id is not None:
        data["session_id"] = str(session_id)
    return client.post(
        "/analyze",
        files={"file": (filename, b"original-bytes", "image/png")},
        data=data,
    )

def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "database": "ok"}

def test_analyze_persists_and_serves_files(client, fake_analysis):
    response = _upload(client)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["image_id"] > 0
    assert body["swing_leg"]["hip_angle"] == 105.0
    assert body["annotated_image"] == "data:image/jpeg;base64,QUJD"
    assert body["original_url"] == f"/images/{body['image_id']}/file"

    image_id = body["image_id"]
    original = client.get(body["original_url"])
    assert original.status_code == 200
    assert original.content == b"original-bytes"

    annotated = client.get(body["annotated_url"])
    assert annotated.status_code == 200
    assert annotated.content == b"annotated"

    detail = client.get(f"/images/{image_id}").json()
    assert detail["image"]["id"] == image_id
    assert detail["humanization"] is None
    assert detail["image"]["swing_hip"] == 105.0

def test_analyze_requires_a_session_owned_by_the_user(client, fake_analysis):
    assert _upload(client, session_id=9999).status_code == 404

def test_sessions_crud_and_cycle_prevention(client):
    root = client.post("/sessions", json={"name": "Root"}).json()
    child = client.post(
        "/sessions", json={"name": "Child", "parent_id": root["id"]}
    ).json()

    assert [s["id"] for s in client.get("/sessions?root=true").json()] == [
        root["id"]
    ]
    assert [
        s["id"] for s in client.get(f"/sessions?parent_id={root['id']}").json()
    ] == [child["id"]]

    assert client.patch(
        f"/sessions/{child['id']}", json={"name": "Renamed"}
    ).json()["name"] == "Renamed"
    assert client.patch(
        f"/sessions/{child['id']}", json={"parent_id": None}
    ).json()["parent_id"] is None
    assert client.get("/sessions?root=true").json()[0]["id"] in {
        root["id"],
        child["id"],
    }

    assert client.patch(
        f"/sessions/{root['id']}", json={"parent_id": root["id"]}
    ).status_code == 400
    assert client.post(
        "/sessions", json={"name": "Orphan", "parent_id": 9999}
    ).status_code == 404

def test_delete_session_removes_nested_images_and_files(client, fake_analysis):
    root = client.post("/sessions", json={"name": "Root"}).json()
    child = client.post(
        "/sessions", json={"name": "Child", "parent_id": root["id"]}
    ).json()
    body = _upload(client, session_id=child["id"]).json()

    image = repo.get_image(body["image_id"], repo.get_user_by_email("dev@local")["id"])
    assert repo.get_original_file(image["id"], image["user_id"]) is not None

    assert client.delete(f"/sessions/{root['id']}").status_code == 204
    assert repo.get_image(body["image_id"], image["user_id"]) is None
    assert repo.get_original_file(image["id"], image["user_id"]) is None
    assert repo.get_annotated_file(image["id"], image["user_id"]) is None

def test_delete_image_removes_files(client, fake_analysis):
    body = _upload(client).json()
    user_id = repo.get_user_by_email("dev@local")["id"]

    assert client.delete(f"/images/{body['image_id']}").status_code == 204
    assert repo.get_original_file(body["image_id"], user_id) is None
    assert client.get(f"/images/{body['image_id']}").status_code == 404

def _age_image(image_id, *, hours):
    with get_pool().connection() as conn:
        conn.execute(
            """
            UPDATE image_files
            SET last_activity_at = now() - make_interval(hours => %s)
            WHERE image_id = %s
            """,
            (hours, image_id),
        )
        conn.commit()

def _image_exists(image_id):
    user_id = repo.get_user_by_email("dev@local")["id"]
    return repo.get_image(image_id, user_id) is not None

def test_purge_deletes_only_images_idle_past_the_limit(client, fake_analysis):
    folder = client.post("/sessions", json={"name": "Keep me"}).json()
    idle = _upload(client, session_id=folder["id"]).json()["image_id"]
    recent = _upload(client).json()["image_id"]
    user_id = repo.get_user_by_email("dev@local")["id"]
    repo.upsert_humanization(idle, user_id, model="m", humanized_text="text")
    _age_image(idle, hours=49)
    _age_image(recent, hours=47)

    assert image_service.purge_inactive_images() == 1

    assert not _image_exists(idle)
    assert repo.get_original_file(idle, user_id) is None
    assert repo.get_humanization(idle, user_id) is None
    assert _image_exists(recent)
    assert client.get(f"/sessions/{folder['id']}").status_code == 200

def test_purge_keeps_older_images_without_stored_bytes(client):
    client.get("/me")
    user_id = repo.get_user_by_email("dev@local")["id"]
    legacy = repo.create_image(
        user_id,
        original_filename="old.jpg",
        stored_filename="users/1/images/old.jpg",
        phase="toe_off",
        direction="ltr",
    )

    assert image_service.purge_inactive_images() == 0
    assert _image_exists(legacy["id"])
    assert client.get(f"/images/{legacy['id']}/file").status_code == 404

def test_lost_image_cleanup_only_removes_old_records_without_bytes(
    client, fake_analysis
):
    client.get("/me")
    user_id = repo.get_user_by_email("dev@local")["id"]
    make_record = lambda name: repo.create_image(
        user_id,
        original_filename=name,
        stored_filename=f"users/1/images/{name}",
        phase="toe_off",
        direction="ltr",
    )["id"]
    lost = make_record("lost.jpg")
    still_saving = make_record("saving.jpg")
    stored = _upload(client).json()["image_id"]
    repo.upsert_humanization(lost, user_id, model="m", humanized_text="text")
    with get_pool().connection() as conn:
        conn.execute(
            """
            UPDATE images SET created_at = now() - interval '2 hours'
            WHERE id = ANY(%s)
            """,
            ([lost, stored],),
        )
        conn.commit()

    assert repo.count_images_without_files() == 1
    assert _image_exists(lost)

    assert repo.delete_images_without_files() == 1

    assert not _image_exists(lost)
    assert repo.get_humanization(lost, user_id) is None
    assert _image_exists(still_saving)
    assert _image_exists(stored)

@pytest.mark.parametrize(
    "keep_alive",
    [
        lambda client, image_id: client.get(f"/images/{image_id}"),
        lambda client, image_id: client.patch(
            f"/images/{image_id}", json={"original_filename": "new.png"}
        ),
        lambda client, image_id: client.put(
            f"/images/{image_id}/humanization",
            json={"model": "m", "humanized_text": "text"},
        ),
    ],
    ids=["open", "rename", "feedback"],
)
def test_activity_resets_the_inactivity_clock(client, fake_analysis, keep_alive):
    image_id = _upload(client).json()["image_id"]
    _age_image(image_id, hours=49)

    assert keep_alive(client, image_id).status_code == 200

    assert image_service.purge_inactive_images() == 0
    assert _image_exists(image_id)

def test_thumbnails_do_not_reset_the_inactivity_clock(client, fake_analysis):
    body = _upload(client).json()
    _age_image(body["image_id"], hours=49)

    assert client.get(body["annotated_url"]).status_code == 200
    assert client.get(body["original_url"]).status_code == 200
    assert client.get("/images").status_code == 200

    assert image_service.purge_inactive_images() == 1

def test_opening_an_image_does_not_change_its_updated_at(client, fake_analysis):
    image_id = _upload(client).json()["image_id"]
    user_id = repo.get_user_by_email("dev@local")["id"]
    before = repo.get_image(image_id, user_id)["updated_at"]

    client.get(f"/images/{image_id}")

    assert repo.get_image(image_id, user_id)["updated_at"] == before

def test_app_startup_runs_the_purge(monkeypatch):
    ran = threading.Event()

    def fake_purge():
        ran.set()
        return 0

    monkeypatch.setattr(image_service, "purge_inactive_images", fake_purge)
    monkeypatch.setattr(main, "close_pool", lambda: None)
    with TestClient(main.app):
        assert ran.wait(timeout=5)

def _analysis_upload(client):
    ok, encoded = cv2.imencode(".jpg", np.zeros((8, 8, 3), np.uint8))
    assert ok
    return client.post(
        "/analyze",
        files={"file": ("run.jpg", encoded.tobytes(), "image/jpeg")},
        data={"phase": "toe_off", "direction": "ltr"},
    ), encoded.tobytes()

@pytest.fixture
def fake_pose(monkeypatch):
    monkeypatch.setattr(
        image_service, "get_pose_landmarks", lambda _image: ([object()], object())
    )
    monkeypatch.setattr(
        image_service, "analyze_angles", lambda *_args: FAKE_RESULT
    )
    monkeypatch.setattr(
        image_service, "draw_landmarks_on_image", lambda image, _landmarks: image
    )

def test_analyze_stores_both_images_in_the_database(client, fake_pose):
    response, contents = _analysis_upload(client)
    assert response.status_code == 200, response.text
    body = response.json()

    original = client.get(body["original_url"])
    assert original.content == contents
    assert original.headers["content-type"] == "image/jpeg"
    annotated = client.get(body["annotated_url"])
    assert annotated.status_code == 200
    assert annotated.content.startswith(b"\xff\xd8")

def test_analyze_removes_the_record_when_saving_images_fails(fake_pose, monkeypatch):
    client = TestClient(main.app, raise_server_exceptions=False)

    def fail(*_args, **_kwargs):
        raise RuntimeError("database full")

    monkeypatch.setattr(repo, "save_image_files", fail)
    response, _contents = _analysis_upload(client)

    assert response.status_code == 500
    assert client.get("/images").json() == []

def test_image_update_moves_between_sessions(client, fake_analysis):
    session = client.post("/sessions", json={"name": "S"}).json()
    body = _upload(client).json()

    moved = client.patch(
        f"/images/{body['image_id']}", json={"session_id": session["id"]}
    )
    assert moved.status_code == 200
    assert moved.json()["session_id"] == session["id"]

    listing = client.get(f"/images?session_id={session['id']}").json()
    assert [i["id"] for i in listing] == [body["image_id"]]

    back_to_root = client.patch(
        f"/images/{body['image_id']}", json={"session_id": None}
    )
    assert back_to_root.json()["session_id"] is None
    assert [
        i["id"] for i in client.get("/images?root=true").json()
    ] == [body["image_id"]]

def test_humanization_crud(client, fake_analysis):
    image_id = _upload(client).json()["image_id"]
    url = f"/images/{image_id}/humanization"

    created = client.put(
        url,
        json={"model": "gemma-2-2b", "humanized_text": "First", "prompt": "p"},
    )
    assert created.status_code == 200
    assert created.json()["humanized_text"] == "First"

    assert client.get(url).json()["humanized_text"] == "First"
    assert client.patch(url, json={"humanized_text": "Second"}).json()[
        "humanized_text"
    ] == "Second"
    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404

def test_users_cannot_see_each_others_images(client, fake_analysis):
    body = _upload(client).json()
    headers = auth_headers("other@example.com")
    repo.upsert_user("other@example.com", name="Other")

    assert client.get(
        f"/images/{body['image_id']}", headers=headers
    ).status_code == 404
    assert client.get(body["original_url"], headers=headers).status_code == 404
    assert client.get("/images", headers=headers).json() == []
    assert client.get("/me", headers=headers).json()["email"] == "other@example.com"


def test_bearer_token_creates_and_reuses_user(client):
    headers = auth_headers("runner@example.com")
    first = client.get("/me", headers=headers).json()
    second = client.get("/me", headers=headers).json()
    assert first["id"] == second["id"]
    assert first["email"] == "runner@example.com"


def test_rejects_invalid_token_and_missing_auth(client, monkeypatch):
    bad = {"Authorization": "Bearer not-a-token"}
    assert client.get("/me", headers=bad).status_code == 401

    monkeypatch.setenv("AGOS_ALLOW_DEV_USER", "0")
    assert client.get("/me").status_code == 401


def test_generate_humanization(client, fake_analysis, monkeypatch):
    image_id = _upload(client).json()["image_id"]

    def fake_humanize(image):
        assert image["id"] == image_id
        return "test-model", "prompt", "Drive the knee forward."

    monkeypatch.setattr(humanization, "humanize_image", fake_humanize)

    response = client.post(f"/images/{image_id}/humanization/generate")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["model"] == "test-model"
    assert body["humanized_text"] == "Drive the knee forward."

    assert client.get(
        f"/images/{image_id}/humanization"
    ).json()["humanized_text"] == "Drive the knee forward."

def test_image_rename_accepts_and_trims_filename(client, fake_analysis):
    image_id = _upload(client).json()["image_id"]

    response = client.patch(
        f"/images/{image_id}", json={"original_filename": "  new-run.jpg  "}
    )
    assert response.status_code == 200, response.text
    assert response.json()["original_filename"] == "new-run.jpg"

    empty = client.patch(
        f"/images/{image_id}", json={"original_filename": "   "}
    )
    assert empty.status_code == 400


def test_chat_persists_and_clears(client, fake_analysis, monkeypatch):
    image_id = _upload(client).json()["image_id"]

    def fake_answer(image, messages, latest_question, existing_feedback=None):
        assert latest_question == "What drills help?"
        return "groq:test-model", "Try high-knee drills."

    monkeypatch.setattr(humanization, "answer_question", fake_answer)

    created = client.post(
        f"/images/{image_id}/messages", json={"content": "What drills help?"}
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["user_message"]["role"] == "user"
    assert body["assistant_message"]["role"] == "assistant"
    assert body["assistant_message"]["model"] == "groq:test-model"

    listing = client.get(f"/images/{image_id}/messages")
    assert listing.status_code == 200
    assert [m["content"] for m in listing.json()] == [
        "What drills help?",
        "Try high-knee drills.",
    ]

    assert client.delete(f"/images/{image_id}/messages").status_code == 204
    assert client.get(f"/images/{image_id}/messages").json() == []


def test_chat_model_failure_does_not_store_user_message(
    client, fake_analysis, monkeypatch
):
    image_id = _upload(client).json()["image_id"]

    def failing_answer(*args, **kwargs):
        raise humanization.HumanizationUnavailable("model offline")

    monkeypatch.setattr(humanization, "answer_question", failing_answer)

    response = client.post(
        f"/images/{image_id}/messages", json={"content": "Explain this."}
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "model offline"
    assert client.get(f"/images/{image_id}/messages").json() == []


def test_chat_rejects_empty_or_too_long_messages(client, fake_analysis):
    image_id = _upload(client).json()["image_id"]

    assert client.post(
        f"/images/{image_id}/messages", json={"content": "   "}
    ).status_code == 400
    assert client.post(
        f"/images/{image_id}/messages", json={"content": "x" * 1001}
    ).status_code == 422


def test_chat_requires_image_ownership(client, fake_analysis):
    image_id = _upload(client).json()["image_id"]
    headers = auth_headers("other@example.com")
    repo.upsert_user("other@example.com", name="Other")

    assert client.get(
        f"/images/{image_id}/messages", headers=headers
    ).status_code == 404
    assert client.post(
        f"/images/{image_id}/messages",
        json={"content": "Hello"},
        headers=headers,
    ).status_code == 404
    assert client.delete(
        f"/images/{image_id}/messages", headers=headers
    ).status_code == 404


def test_upload_size_limit(client, monkeypatch):
    monkeypatch.setattr(image_service, "MAX_UPLOAD_BYTES", 4)
    response = client.post(
        "/analyze",
        files={"file": ("run.png", b"12345", "image/png")},
        data={"phase": "toe_off", "direction": "ltr"},
    )
    assert response.status_code == 413
