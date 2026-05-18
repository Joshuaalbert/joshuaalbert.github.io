from __future__ import annotations

from pathlib import Path
import shutil

from PIL import Image, ImageOps

from .content import Photo

JPEG_QUALITY = 88
WEBP_QUALITY = 82
SIZES = {
    "thumb": 600,
    "preview": 1400,
    "full": 2560,
}
PREVIEW_SIZES = {
    "thumb": 600,
    "preview": 1400,
}


def generate_photo_derivatives(photo: Photo, output_root: Path) -> None:
    target_dir = output_root / "assets" / "photos" / photo.album_slug
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = photo.source_path.suffix.lower()
    if suffix == ".gif" and _is_animated_gif(photo.source_path):
        full_path = target_dir / f"{photo.slug}.gif"
        shutil.copy2(photo.source_path, full_path)
        photo.derivatives["full"] = f"/assets/photos/{photo.album_slug}/{photo.slug}.gif"
        _generate_static_derivatives(photo, target_dir, PREVIEW_SIZES, first_frame=True)
        return
    _generate_static_derivatives(photo, target_dir, SIZES, first_frame=False)


def _is_animated_gif(path: Path) -> bool:
    try:
        with Image.open(path) as image:
            return getattr(image, "is_animated", False)
    except OSError:
        return False


def _generate_static_derivatives(
    photo: Photo, target_dir: Path, sizes: dict[str, int], first_frame: bool
) -> None:
    with Image.open(photo.source_path) as original:
        if first_frame:
            original.seek(0)
        image = ImageOps.exif_transpose(original).convert("RGB")
        for label, max_size in sizes.items():
            resized = image.copy()
            resized.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            jpg_path = target_dir / f"{photo.slug}-{label}.jpg"
            webp_path = target_dir / f"{photo.slug}-{label}.webp"
            resized.save(jpg_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
            resized.save(webp_path, "WEBP", quality=WEBP_QUALITY, method=6)
            photo.derivatives[label] = f"/assets/photos/{photo.album_slug}/{photo.slug}-{label}.jpg"
            photo.derivatives[f"{label}_webp"] = (
                f"/assets/photos/{photo.album_slug}/{photo.slug}-{label}.webp"
            )
