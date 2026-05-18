"""Content discovery, TOML validation, and manifest construction."""

from __future__ import annotations

import json
import re
import tomllib
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Literal

from .markdown import markdown_excerpt, render_markdown
from .models import Album, BuildManifest, Photo, TextEntry

IMAGE_EXTENSIONS = {".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class SiteValidationError(Exception):
    """Raised when source content cannot be converted into a valid manifest."""

    def __init__(self, errors: Iterable[str]):
        self.errors = tuple(errors)
        super().__init__("\n".join(self.errors))


def load_site(root: str | Path) -> BuildManifest:
    """Load all supported content under ``root`` into a manifest model."""
    root_path = Path(root).resolve()
    errors: list[str] = []
    comment_ids: dict[str, str] = {}
    photography = _load_photography(root_path, errors, comment_ids)
    essays = _load_text_collection(root_path, "essays", "essay", errors, comment_ids)
    research = _load_text_collection(root_path, "research", "research", errors, comment_ids)
    if errors:
        raise SiteValidationError(errors)
    return BuildManifest(
        photography=tuple(photography),
        essays=tuple(essays),
        research=tuple(research),
    )


def write_manifest(manifest: BuildManifest, path: str | Path, pretty: bool = True) -> None:
    """Write a manifest as JSON for downstream template/rendering code."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {"indent": 2, "sort_keys": True} if pretty else {}
    output.write_text(json.dumps(manifest.to_dict(), **kwargs) + "\n", encoding="utf-8")


def _load_photography(
    root: Path,
    errors: list[str],
    comment_ids: dict[str, str],
) -> list[Album]:
    albums_root = root / "photography" / "albums"
    if not albums_root.exists():
        return []
    if not albums_root.is_dir():
        errors.append(f"{_rel(root, albums_root)} must be a directory")
        return []

    album_dirs = [path for path in albums_root.iterdir() if path.is_dir() and not path.name.startswith(".")]
    album_meta = [path for path in albums_root.glob("*.toml") if path.is_file()]
    _check_duplicate_names(album_dirs, "album directory slug", errors, root)
    _check_duplicate_names(album_meta, "album metadata slug", errors, root, use_stem=True)
    _check_slugs(album_dirs, "album directory slug", errors, root)
    _check_slugs(album_meta, "album metadata slug", errors, root, use_stem=True)

    dir_by_slug = {path.name: path for path in album_dirs}
    meta_by_slug = {path.stem: path for path in album_meta}
    for slug in sorted(set(dir_by_slug) - set(meta_by_slug)):
        errors.append(f"missing album metadata for {_rel(root, dir_by_slug[slug])}: expected {slug}.toml")
    for slug in sorted(set(meta_by_slug) - set(dir_by_slug)):
        errors.append(f"missing album directory for {_rel(root, meta_by_slug[slug])}: expected {slug}/")

    albums: list[Album] = []
    for slug in sorted(set(dir_by_slug) & set(meta_by_slug)):
        metadata_path = meta_by_slug[slug]
        source_dir = dir_by_slug[slug]
        data = _read_toml(metadata_path, errors, root)
        if data is None:
            continue
        name = _required_str(data, "name", metadata_path, errors, root)
        description = _required_str(data, "description", metadata_path, errors, root)
        _reject_unknown_keys(data, {"name", "description"}, metadata_path, errors, root)
        photos = _load_album_photos(root, slug, source_dir, errors, comment_ids)
        if not photos:
            errors.append(f"{_rel(root, source_dir)} must contain at least one photo with paired TOML metadata")
        if name is None or description is None:
            continue
        albums.append(
            Album(
                slug=slug,
                name=name,
                description=description,
                metadata_path=_rel(root, metadata_path),
                source_dir=_rel(root, source_dir),
                photos=tuple(photos),
            )
        )

    return sorted(albums, key=lambda album: (-album.sort_date.toordinal(), album.name.casefold(), album.slug.casefold()))


def _load_album_photos(
    root: Path,
    album_slug: str,
    album_dir: Path,
    errors: list[str],
    comment_ids: dict[str, str],
) -> list[Photo]:
    image_files = [
        path
        for path in album_dir.iterdir()
        if path.is_file() and path.suffix.casefold() in IMAGE_EXTENSIONS
    ]
    meta_files = [path for path in album_dir.glob("*.toml") if path.is_file()]
    _check_duplicate_names(image_files, "photo slug", errors, root, use_stem=True)
    _check_duplicate_names(meta_files, "photo metadata slug", errors, root, use_stem=True)
    _check_slugs(image_files, "photo slug", errors, root, use_stem=True)
    _check_slugs(meta_files, "photo metadata slug", errors, root, use_stem=True)

    images_by_stem: dict[str, Path] = {}
    for path in image_files:
        if path.stem not in images_by_stem:
            images_by_stem[path.stem] = path

    meta_by_stem = {path.stem: path for path in meta_files}
    for slug in sorted(set(images_by_stem) - set(meta_by_stem)):
        errors.append(f"missing photo metadata for {_rel(root, images_by_stem[slug])}: expected {slug}.toml")
    for slug in sorted(set(meta_by_stem) - set(images_by_stem)):
        errors.append(f"missing photo file for {_rel(root, meta_by_stem[slug])}")

    photos: list[Photo] = []
    for slug in sorted(set(images_by_stem) & set(meta_by_stem)):
        metadata_path = meta_by_stem[slug]
        data = _read_toml(metadata_path, errors, root)
        if data is None:
            continue
        _reject_unknown_keys(
            data,
            {
                "alt",
                "aperture",
                "camera",
                "comment_id",
                "date_taken",
                "description",
                "focal_length",
                "iso",
                "lens",
                "location",
                "name",
                "shutter_speed",
            },
            metadata_path,
            errors,
            root,
        )
        name = _required_str(data, "name", metadata_path, errors, root)
        description = _optional_blank_str(data, "description", metadata_path, errors, root) or ""
        location = _required_str(data, "location", metadata_path, errors, root)
        date_taken = _required_date(data, "date_taken", metadata_path, errors, root)
        alt = _optional_str(data, "alt", metadata_path, errors, root) or name
        default_comment_id = f"photography/albums/{album_slug}/{slug}"
        comment_id = _optional_str(data, "comment_id", metadata_path, errors, root) or default_comment_id
        _register_comment_id(comment_ids, comment_id, metadata_path, errors, root)
        if None in (name, location, date_taken):
            continue
        photos.append(
            Photo(
                slug=slug,
                album_slug=album_slug,
                name=name or "",
                description=description or "",
                location=location or "",
                date_taken=date_taken or date.min,
                source_path=_rel(root, images_by_stem[slug]),
                metadata_path=_rel(root, metadata_path),
                alt=alt,
                comment_id=comment_id,
                camera=_optional_str(data, "camera", metadata_path, errors, root) or "",
                lens=_optional_str(data, "lens", metadata_path, errors, root) or "",
                focal_length=_optional_str(data, "focal_length", metadata_path, errors, root) or "",
                aperture=_optional_str(data, "aperture", metadata_path, errors, root) or "",
                shutter_speed=_optional_str(data, "shutter_speed", metadata_path, errors, root) or "",
                iso=_optional_str(data, "iso", metadata_path, errors, root) or "",
            )
        )

    return sorted(photos, key=lambda photo: (photo.date_taken.toordinal(), photo.name.casefold(), photo.slug.casefold()))


def _load_text_collection(
    root: Path,
    directory: Literal["essays", "research"],
    kind: Literal["essay", "research"],
    errors: list[str],
    comment_ids: dict[str, str],
) -> list[TextEntry]:
    collection_root = root / directory
    if not collection_root.exists():
        return []
    if not collection_root.is_dir():
        errors.append(f"{_rel(root, collection_root)} must be a directory")
        return []

    entry_dirs = [
        path
        for path in collection_root.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    ]
    _check_duplicate_names(entry_dirs, f"{kind} slug", errors, root)
    _check_slugs(entry_dirs, f"{kind} slug", errors, root)

    entries: list[TextEntry] = []
    for entry_dir in sorted(entry_dirs, key=lambda path: path.name.casefold()):
        slug = entry_dir.name
        metadata_path = entry_dir / f"{slug}.toml"
        markdown_path = entry_dir / f"{slug}.md"
        if not metadata_path.exists():
            errors.append(f"missing {kind} metadata for {_rel(root, entry_dir)}: expected {slug}.toml")
            continue
        if not markdown_path.exists():
            errors.append(f"missing {kind} markdown for {_rel(root, entry_dir)}: expected {slug}.md")
            continue
        data = _read_toml(metadata_path, errors, root)
        if data is None:
            continue
        _reject_unknown_keys(data, {"comment_id", "date_published", "title"}, metadata_path, errors, root)
        title = _required_str(data, "title", metadata_path, errors, root)
        date_published = _required_date(data, "date_published", metadata_path, errors, root)
        default_comment_id = f"{directory}/{slug}"
        comment_id = _optional_str(data, "comment_id", metadata_path, errors, root) or default_comment_id
        _register_comment_id(comment_ids, comment_id, metadata_path, errors, root)
        if title is None or date_published is None:
            continue
        markdown = markdown_path.read_text(encoding="utf-8")
        entries.append(
            TextEntry(
                kind=kind,
                slug=slug,
                title=title,
                date_published=date_published,
                markdown_path=_rel(root, markdown_path),
                metadata_path=_rel(root, metadata_path),
                html=render_markdown(markdown),
                excerpt=markdown_excerpt(markdown),
                comment_id=comment_id,
            )
        )

    return sorted(entries, key=lambda entry: (-entry.date_published.toordinal(), entry.title.casefold(), entry.slug.casefold()))


def _read_toml(path: Path, errors: list[str], root: Path) -> dict[str, Any] | None:
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        errors.append(f"{_rel(root, path)} has invalid TOML: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{_rel(root, path)} must contain a TOML table")
        return None
    return data


def _reject_unknown_keys(
    data: dict[str, Any],
    allowed: set[str],
    path: Path,
    errors: list[str],
    root: Path,
) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        errors.append(f"{_rel(root, path)} has unsupported keys: {', '.join(unknown)}")


def _required_str(
    data: dict[str, Any],
    key: str,
    path: Path,
    errors: list[str],
    root: Path,
) -> str | None:
    if key not in data:
        errors.append(f"{_rel(root, path)} missing required string field {key!r}")
        return None
    return _string_value(data[key], key, path, errors, root)


def _optional_str(
    data: dict[str, Any],
    key: str,
    path: Path,
    errors: list[str],
    root: Path,
) -> str | None:
    if key not in data:
        return None
    return _string_value(data[key], key, path, errors, root)


def _optional_blank_str(
    data: dict[str, Any],
    key: str,
    path: Path,
    errors: list[str],
    root: Path,
) -> str | None:
    if key not in data:
        return None
    value = data[key]
    if not isinstance(value, str):
        errors.append(f"{_rel(root, path)} field {key!r} must be a string")
        return None
    return value.strip()


def _string_value(
    value: Any,
    key: str,
    path: Path,
    errors: list[str],
    root: Path,
) -> str | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{_rel(root, path)} field {key!r} must be a non-empty string")
        return None
    return value.strip()


def _required_date(
    data: dict[str, Any],
    key: str,
    path: Path,
    errors: list[str],
    root: Path,
) -> date | None:
    if key not in data:
        errors.append(f"{_rel(root, path)} missing required date field {key!r}")
        return None
    value = data[key]
    if isinstance(value, datetime):
        errors.append(f"{_rel(root, path)} field {key!r} must be a YYYY-MM-DD date, not a datetime")
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str) and DATE_RE.fullmatch(value):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    errors.append(f"{_rel(root, path)} field {key!r} must be a valid YYYY-MM-DD date")
    return None


def _register_comment_id(
    comment_ids: dict[str, str],
    comment_id: str,
    path: Path,
    errors: list[str],
    root: Path,
) -> None:
    existing = comment_ids.get(comment_id)
    rel_path = _rel(root, path)
    if existing is not None:
        errors.append(f"duplicate comment_id {comment_id!r}: {existing} and {rel_path}")
        return
    comment_ids[comment_id] = rel_path


def _check_duplicate_names(
    paths: Iterable[Path],
    label: str,
    errors: list[str],
    root: Path,
    use_stem: bool = False,
) -> None:
    seen: dict[str, Path] = {}
    for path in paths:
        value = path.stem if use_stem else path.name
        key = value.casefold()
        if key in seen:
            errors.append(f"duplicate {label} {value!r}: {_rel(root, seen[key])} and {_rel(root, path)}")
        else:
            seen[key] = path


def _check_slugs(
    paths: Iterable[Path],
    label: str,
    errors: list[str],
    root: Path,
    use_stem: bool = False,
) -> None:
    for path in paths:
        value = path.stem if use_stem else path.name
        if not SLUG_RE.fullmatch(value):
            errors.append(
                f"{_rel(root, path)} has invalid {label} {value!r}; "
                "use lowercase letters, numbers, and hyphens"
            )


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()
