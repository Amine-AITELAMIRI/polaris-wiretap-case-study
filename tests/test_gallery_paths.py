import pytest

from gallery_paths import resolve_gallery_image


def test_accepts_bundled_image(tmp_path):
    gallery = tmp_path / "gallery"
    gallery.mkdir()
    image = gallery / "Shannon.webp"
    image.write_bytes(b"example")

    assert resolve_gallery_image(gallery, "Shannon.webp") == image


@pytest.mark.parametrize("filename", ["../outside.webp", "subdir/image.webp", "..\\outside.webp", ".hidden.webp", "notes.txt", "missing.webp"])
def test_rejects_invalid_selection(tmp_path, filename):
    gallery = tmp_path / "gallery"
    gallery.mkdir()

    with pytest.raises(ValueError, match="Invalid gallery image"):
        resolve_gallery_image(gallery, filename)


def test_rejects_symlink_outside_gallery(tmp_path):
    gallery = tmp_path / "gallery"
    gallery.mkdir()
    outside = tmp_path / "outside.webp"
    outside.write_bytes(b"example")
    (gallery / "linked.webp").symlink_to(outside)

    with pytest.raises(ValueError, match="Invalid gallery image"):
        resolve_gallery_image(gallery, "linked.webp")
