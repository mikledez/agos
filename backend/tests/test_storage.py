import pytest

from services import storage

def test_new_image_names_are_unique_and_keep_the_extension():
    original, annotated = storage.new_image_names(1, "Runner.PNG")
    assert original.startswith("users/1/images/")
    assert original.endswith(".png")
    assert annotated == f"{original.removesuffix('.png')}_annotated.jpg"
    assert storage.new_image_names(1, "Runner.PNG")[0] != original

def test_unsupported_extension_is_rejected():
    with pytest.raises(ValueError):
        storage.new_image_names(1, "animation.gif")

def test_media_type_for_known_and_unknown():
    assert storage.media_type_for("a.jpg") == "image/jpeg"
    assert storage.media_type_for("a.webp") == "image/webp"
    assert storage.media_type_for("a.bin") == "application/octet-stream"
