import io

from PIL import Image

from src.libs.loader.image_filter import average_hash, is_decorative_image, is_near_duplicate


def test_decorative_image_filter_skips_tiny_images():
    assert is_decorative_image(24, 24) is True
    assert is_decorative_image(120, 40) is True


def test_decorative_image_filter_keeps_large_or_unknown_images():
    assert is_decorative_image(400, 300) is False
    assert is_decorative_image(0, 0) is False


def test_perceptual_hash_detects_near_duplicate_images():
    original = io.BytesIO()
    Image.new("RGB", (200, 200), color="white").save(original, format="PNG")

    resized = io.BytesIO()
    Image.new("RGB", (210, 210), color="white").save(resized, format="PNG")

    first_hash = average_hash(original.getvalue())
    second_hash = average_hash(resized.getvalue())

    assert first_hash is not None
    assert second_hash is not None
    assert is_near_duplicate(second_hash, [first_hash]) is True
