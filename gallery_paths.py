"""Resolve images selected from the bundled, local demonstration gallery."""

from pathlib import Path


ALLOWED_IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".webp"}


def resolve_gallery_image(gallery_dir, filename):
    """Return an existing gallery image, rejecting paths outside the gallery."""
    if (
        not filename
        or filename.startswith(".")
        or "/" in filename
        or "\\" in filename
        or Path(filename).suffix.lower() not in ALLOWED_IMAGE_SUFFIXES
    ):
        raise ValueError("Invalid gallery image")

    gallery = Path(gallery_dir).resolve()
    candidate = gallery / filename
    resolved = candidate.resolve()
    if resolved.parent != gallery or not candidate.is_file():
        raise ValueError("Invalid gallery image")
    return resolved
