import pytest

from services import storage

@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "UPLOAD_DIR", tmp_path)
    return tmp_path

def test_save_and_delete_original_and_annotated():
    stored = storage.save_original(1, b"original-bytes", "Runner.PNG")
    assert stored.startswith("users/1/images/")
    assert stored.endswith(".png")
    assert storage.resolve(stored).read_bytes() == b"original-bytes"

    annotated = storage.save_annotated(1, b"annotated-bytes", stored)
    assert annotated.endswith("_annotated.jpg")
    assert storage.resolve(annotated).read_bytes() == b"annotated-bytes"

    storage.delete_paths([stored, annotated])
    assert not storage.resolve(stored).exists()
    assert not storage.resolve(annotated).exists()

def test_unsupported_extension_is_rejected():
    with pytest.raises(ValueError):
        storage.save_original(1, b"x", "animation.gif")

def test_resolve_rejects_path_traversal():
    with pytest.raises(ValueError):
        storage.resolve("../../etc/passwd")

def test_delete_paths_ignores_missing_and_none():
    storage.delete_paths(["users/1/images/missing.jpg", None])

def test_media_type_for_known_and_unknown():
    assert storage.media_type_for("a.jpg") == "image/jpeg"
    assert storage.media_type_for("a.webp") == "image/webp"
    assert storage.media_type_for("a.bin") == "application/octet-stream"
