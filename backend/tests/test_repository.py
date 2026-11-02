import math

import pytest

from db import repository as repo

def make_user(email="a@example.com", name="Alice"):
    return repo.create_user(email, name=name)

def make_session(user_id, name="Session", parent_id=None):
    return repo.create_session(user_id, name, parent_id=parent_id)

def make_analysis():
    return {
        "phase": "touchdown",
        "swing_leg": {
            "hip_angle": 160.0,
            "knee_angle": 45.0,
            "ankle_angle": 120.0,
            "feedback": "Good positions",
        },
        "stance_leg": {
            "hip_angle": 146.0,
            "knee_angle": 150.0,
            "ankle_angle": 100.0,
            "feedback": "Good positions",
        },
        "thigh_thigh_angle": 15.0,
        "feedback": "Good positions",
    }

def make_image(user_id, **overrides):
    kwargs = dict(
        original_filename="runner.jpg",
        stored_filename="uuid-runner.jpg",
        phase="toe_off",
        direction="ltr",
        session_id=None,
        annotated_path="uuid-runner-annotated.jpg",
        swing_hip=105.0,
        swing_knee=70.0,
        swing_ankle=100.0,
        stance_hip=198.0,
        stance_knee=145.0,
        stance_ankle=130.0,
        feedback="Good positions",
        swing_feedback="Good positions",
        stance_feedback="Good positions",
    )
    kwargs.update(overrides)
    return repo.create_image(user_id, **kwargs)

def test_create_and_fetch_user():
    user = repo.create_user("Alice@Example.com", name="Alice")
    assert user["email"] == "alice@example.com"
    assert user["name"] == "Alice"
    assert repo.get_user(user["id"])["email"] == "alice@example.com"
    assert repo.get_user_by_email("ALICE@example.com")["id"] == user["id"]

def test_duplicate_email_is_a_conflict():
    make_user("alice@example.com")
    with pytest.raises(repo.ConflictError):
        make_user("ALICE@EXAMPLE.COM")

def test_upsert_user_updates_only_supplied_fields():
    user = make_user("alice@example.com", name="Alice")
    updated = repo.upsert_user("alice@example.com", name="Alicia")
    assert updated["id"] == user["id"]
    assert updated["name"] == "Alicia"
    assert repo.get_user_by_email("alice@example.com")["name"] == "Alicia"

def test_update_user_and_delete_cascades():
    user = make_user()
    session = make_session(user["id"])
    image = make_image(user["id"], session_id=session["id"])
    repo.upsert_humanization(image["id"], user["id"], model="gemma",
                             humanized_text="text")

    updated = repo.update_user(user["id"], name="Bob")
    assert updated["name"] == "Bob"
    assert updated["updated_at"] >= user["updated_at"]

    assert repo.delete_user(user["id"]) is True
    assert repo.get_user(user["id"]) is None
    assert repo.get_session(session["id"], user["id"]) is None
    assert repo.get_image(image["id"], user["id"]) is None
    assert repo.get_humanization(image["id"], user["id"]) is None

def test_nested_sessions_and_listing():
    user = make_user()
    root = make_session(user["id"], "Root")
    child = make_session(user["id"], "Child", root["id"])

    roots = repo.list_sessions(user["id"], parent_id=None)
    children = repo.list_sessions(user["id"], parent_id=root["id"])
    everything = repo.list_sessions(user["id"])

    assert [s["id"] for s in roots] == [root["id"]]
    assert [s["id"] for s in children] == [child["id"]]
    assert {s["id"] for s in everything} == {root["id"], child["id"]}

def test_session_ownership_is_enforced():
    alice = make_user("alice@example.com")
    bob = make_user("bob@example.com")
    session = make_session(alice["id"])

    assert repo.get_session(session["id"], bob["id"]) is None
    assert repo.update_session(session["id"], bob["id"], name="Hijacked") is None
    assert repo.delete_session(session["id"], bob["id"]) is False
    with pytest.raises(repo.ValidationError):
        repo.create_session(bob["id"], "Child", parent_id=session["id"])

def test_session_cannot_be_moved_into_itself_or_descendant():
    user = make_user()
    root = make_session(user["id"], "Root")
    child = make_session(user["id"], "Child", root["id"])
    grandchild = make_session(user["id"], "Grandchild", child["id"])

    with pytest.raises(repo.ValidationError):
        repo.update_session(root["id"], user["id"], parent_id=root["id"])
    with pytest.raises(repo.ValidationError):
        repo.update_session(root["id"], user["id"], parent_id=grandchild["id"])

    moved = repo.update_session(grandchild["id"], user["id"], parent_id=root["id"])
    assert moved["parent_id"] == root["id"]

def test_rename_and_delete_session_cascades_children_and_images():
    user = make_user()
    root = make_session(user["id"], "Root")
    child = make_session(user["id"], "Child", root["id"])
    image = make_image(user["id"], session_id=child["id"])

    renamed = repo.update_session(root["id"], user["id"], name="Renamed")
    assert renamed["name"] == "Renamed"

    assert repo.delete_session(root["id"], user["id"]) is True
    assert repo.get_session(child["id"], user["id"]) is None
    assert repo.get_image(image["id"], user["id"]) is None

def test_create_image_from_analysis_maps_all_fields():
    user = make_user()
    session = make_session(user["id"])

    image = repo.create_image_from_analysis(
        user["id"],
        original_filename="runner.jpg",
        stored_filename="uuid.jpg",
        annotated_path="uuid-annotated.jpg",
        phase="touchdown",
        direction="rtl",
        result=make_analysis(),
        session_id=session["id"],
    )

    assert image["session_id"] == session["id"]
    assert image["original_filename"] == "runner.jpg"
    assert image["stored_filename"] == "uuid.jpg"
    assert image["annotated_path"] == "uuid-annotated.jpg"
    assert image["phase"] == "touchdown"
    assert image["direction"] == "rtl"
    assert image["swing_hip"] == 160.0
    assert image["swing_knee"] == 45.0
    assert image["swing_ankle"] == 120.0
    assert image["stance_hip"] == 146.0
    assert image["stance_knee"] == 150.0
    assert image["stance_ankle"] == 100.0
    assert image["thigh_thigh"] == 15.0
    assert image["feedback"] == "Good positions"

    assert repo.get_image(image["id"], user["id"])["id"] == image["id"]
    assert repo.get_image_by_stored_filename(user["id"], "uuid.jpg")["id"] == image["id"]

def test_nan_angles_are_stored_as_null():
    user = make_user()
    nan = float("nan")
    result = {
        "swing_leg": {
            "hip_angle": nan,
            "knee_angle": 45.0,
            "ankle_angle": math.inf,
            "feedback": "Hip (low confidence)",
        },
        "stance_leg": {},
        "thigh_thigh_angle": None,
    }
    image = repo.create_image_from_analysis(
        user["id"],
        original_filename="runner.jpg",
        stored_filename="uuid.jpg",
        phase="mid_stance",
        direction="ltr",
        result=result,
    )
    assert image["swing_hip"] is None
    assert image["swing_ankle"] is None
    assert image["stance_hip"] is None
    assert image["thigh_thigh"] is None

def test_image_listing_filters_root_and_session():
    user = make_user()
    session = make_session(user["id"])
    root_image = make_image(user["id"], stored_filename="root.jpg")
    session_image = make_image(
        user["id"], stored_filename="session.jpg", session_id=session["id"]
    )

    root_ids = [i["id"] for i in repo.list_images(user["id"], session_id=None)]
    session_ids = [
        i["id"] for i in repo.list_images(user["id"], session_id=session["id"])
    ]
    all_ids = {i["id"] for i in repo.list_images(user["id"])}

    assert root_ids == [root_image["id"]]
    assert session_ids == [session_image["id"]]
    assert all_ids == {root_image["id"], session_image["id"]}

def test_image_validation_and_ownership():
    alice = make_user("alice@example.com")
    bob = make_user("bob@example.com")
    bob_session = make_session(bob["id"])
    image = make_image(alice["id"])

    with pytest.raises(repo.ValidationError):
        repo.create_image(
            alice["id"],
            original_filename="x.jpg",
            stored_filename="x.jpg",
            phase="bogus",
            direction="ltr",
        )
    with pytest.raises(repo.ValidationError):
        make_image(alice["id"], stored_filename="other.jpg",
                   session_id=bob_session["id"])

    assert repo.get_image(image["id"], bob["id"]) is None
    assert repo.update_image(image["id"], bob["id"], feedback="x") is None
    assert repo.delete_image(image["id"], bob["id"]) is False

def test_update_image_can_change_analysis_and_move_session():
    user = make_user()
    session = make_session(user["id"])
    image = make_image(user["id"])

    updated = repo.update_image(
        image["id"],
        user["id"],
        session_id=session["id"],
        phase="touchdown",
        direction="rtl",
        swing_hip=159.0,
        feedback="Updated",
    )
    assert updated["session_id"] == session["id"]
    assert updated["phase"] == "touchdown"
    assert updated["direction"] == "rtl"
    assert updated["swing_hip"] == 159.0
    assert updated["feedback"] == "Updated"
    assert updated["updated_at"] >= image["updated_at"]

    moved_to_root = repo.update_image(image["id"], user["id"], session_id=None)
    assert moved_to_root["session_id"] is None

def test_delete_image_cascades_humanization():
    user = make_user()
    image = make_image(user["id"])
    repo.upsert_humanization(image["id"], user["id"], model="gemma",
                             humanized_text="text")

    assert repo.delete_image(image["id"], user["id"]) is True
    assert repo.get_humanization(image["id"], user["id"]) is None

def test_humanization_upsert_get_and_update():
    user = make_user()
    image = make_image(user["id"])

    first = repo.upsert_humanization(
        image["id"], user["id"], model="gemma-2-2b",
        prompt="explain", humanized_text="First text",
    )
    second = repo.upsert_humanization(
        image["id"], user["id"], model="gemma-2-2b",
        humanized_text="Second text",
    )
    assert second["id"] == first["id"]
    assert second["prompt"] is None
    assert repo.get_humanization(image["id"], user["id"])["humanized_text"] == "Second text"

    updated = repo.update_humanization(
        image["id"], user["id"], humanized_text="Third text"
    )
    assert updated["humanized_text"] == "Third text"
    assert updated["updated_at"] >= second["updated_at"]

    assert len(repo.list_humanizations(user["id"])) == 1

def test_humanization_requires_owned_image():
    alice = make_user("alice@example.com")
    bob = make_user("bob@example.com")
    image = make_image(alice["id"])

    with pytest.raises(repo.ValidationError):
        repo.upsert_humanization(image["id"], bob["id"], model="gemma",
                                 humanized_text="text")
    assert repo.get_humanization(image["id"], bob["id"]) is None
    assert repo.delete_humanization(image["id"], bob["id"]) is False
