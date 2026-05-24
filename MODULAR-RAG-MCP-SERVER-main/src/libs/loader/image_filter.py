"""Shared image filtering helpers for embedded document images."""

from __future__ import annotations

import io
from typing import Iterable, Optional

MIN_EMBEDDED_IMAGE_DIMENSION = 80
MIN_EMBEDDED_IMAGE_AREA = 6400
PERCEPTUAL_DUPLICATE_DISTANCE = 5


def is_decorative_image(width: int, height: int) -> bool:
    """Return True for tiny embedded images that are likely layout decoration."""
    if width <= 0 or height <= 0:
        return False
    return (
        width < MIN_EMBEDDED_IMAGE_DIMENSION
        or height < MIN_EMBEDDED_IMAGE_DIMENSION
        or width * height < MIN_EMBEDDED_IMAGE_AREA
    )


def average_hash(image_bytes: bytes) -> Optional[int]:
    """Compute a small perceptual hash without extra dependencies."""
    try:
        from PIL import Image

        with Image.open(io.BytesIO(image_bytes)) as img:
            gray = img.convert("L").resize((8, 8), Image.Resampling.LANCZOS)
            pixels = list(gray.tobytes())
    except Exception:
        return None

    avg = sum(pixels) / len(pixels)
    bits = 0
    for idx, pixel in enumerate(pixels):
        if pixel >= avg:
            bits |= 1 << idx
    return bits


def hamming_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def is_near_duplicate(
    image_hash: Optional[int],
    seen_hashes: Iterable[int],
    max_distance: int = PERCEPTUAL_DUPLICATE_DISTANCE,
) -> bool:
    if image_hash is None:
        return False
    return any(hamming_distance(image_hash, seen) <= max_distance for seen in seen_hashes)
