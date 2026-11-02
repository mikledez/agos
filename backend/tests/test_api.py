import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

import main
from db import repository as repo
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
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "UPLOAD_DIR", tmp_path)
    return TestClient(main.app)

@pytest.fixture
def fake_analysis(monkeypatch):
    def fake_analyze(
        user_id, *, contents, original_filename, phase, direction,
        session_id=None,
    ):
        stored = storage.save_original(user_id, contents, original_filename)
        annotated = storage.save_annotated(user_id, b"annotated", stored)
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
    assert storage.resolve(image["stored_filename"]).exists()

    assert client.delete(f"/sessions/{root['id']}").status_code == 204
    assert repo.get_image(body["image_id"], image["user_id"]) is None
    assert not storage.resolve(image["stored_filename"]).exists()
    assert not storage.resolve(image["annotated_path"]).exists()

def test_delete_image_removes_files(client, fake_analysis):
    body = _upload(client).json()
    user_id = repo.get_user_by_email("dev@local")["id"]
    image = repo.get_image(body["image_id"], user_id)

    assert client.delete(f"/images/{body['image_id']}").status_code == 204
    assert not storage.resolve(image["stored_filename"]).exists()
    assert client.get(f"/images/{body['image_id']}").status_code == 404

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

def test_upload_size_limit(client, monkeypatch):
    monkeypatch.setattr(image_service, "MAX_UPLOAD_BYTES", 4)
    response = client.post(
        "/analyze",
        files={"file": ("run.png", b"12345", "image/png")},
        data={"phase": "toe_off", "direction": "ltr"},
    )
    assert response.status_code == 413
