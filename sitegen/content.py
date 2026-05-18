"""Compatibility helpers around the stricter manifest loader."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable

from .loader import _load_photography, _load_text_collection
from .markdown import render_markdown
from .models import TextEntry

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ContentError(ValueError):
    """Raised by compatibility content helpers."""


@dataclass
class GiscusConfig:
    repo: str = ""
    repo_id: str = ""
    category: str = "Comments"
    category_id: str = ""
    theme: str = "noborder_light"

    @property
    def configured(self) -> bool:
        return all([self.repo, self.repo_id, self.category, self.category_id])


@dataclass
class SiteConfig:
    title: str = "Portfolio of Joshua G. Albert"
    base_url: str = ""
    giscus: GiscusConfig = field(default_factory=GiscusConfig)


@dataclass
class Photo:
    slug: str
    album_slug: str
    name: str
    description: str
    location: str
    date_taken: date
    source_path: Path
    metadata_path: Path
    alt: str
    comment_id: str
    derivatives: dict[str, str] = field(default_factory=dict)

    @property
    def giscus_term(self) -> str:
        return f"[photo/comments] {self.comment_id}"


@dataclass
class Album:
    slug: str
    name: str
    description: str
    metadata_path: Path
    source_dir: Path
    photos: list[Photo] = field(default_factory=list)

    @property
    def year_label(self) -> str:
        years = sorted({photo.date_taken.year for photo in self.photos})
        if not years:
            return ""
        if years[0] == years[-1]:
            return str(years[0])
        return f"{years[0]}-{years[-1]}"


@dataclass
class Writing:
    section: str
    slug: str
    title: str
    date_published: date
    markdown_path: Path
    metadata_path: Path
    html: str
    excerpt: str
    comment_id: str

    @property
    def giscus_term(self) -> str:
        kind = "essay" if self.section == "essays" else "research"
        return f"[{kind}/comments] {self.comment_id}"

    @property
    def body_html(self) -> str:
        return self.html

    @property
    def summary(self) -> str:
        return self.excerpt


@dataclass
class SiteData:
    config: SiteConfig
    albums: list[Album]
    essays: list[Writing]
    research: list[Writing]


def parse_iso_date(value: str, field_name: str, path: Path) -> date:
    if not DATE_RE.fullmatch(value):
        raise ContentError(f"{path} field {field_name!r} must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ContentError(f"{path} field {field_name!r} must be a valid date") from exc


def summarize(text: str, limit: int = 42) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def collect_writings(
    root: Path,
    section: str,
    renderer: Callable[[str], str] = render_markdown,
    seen_comment_ids: set[str] | None = None,
) -> list[Writing]:
    kind = "essay" if section == "essays" else "research"
    errors: list[str] = []
    comment_ids: dict[str, str] = {}
    root = Path(root).resolve()
    items = _load_text_collection(root, section, kind, errors, comment_ids)
    if errors:
        raise ContentError("\n".join(errors))
    writings: list[Writing] = []
    seen_comment_ids = seen_comment_ids if seen_comment_ids is not None else set()
    for item in items:
        if item.comment_id in seen_comment_ids:
            raise ContentError(f"duplicate comment_id `{item.comment_id}`")
        seen_comment_ids.add(item.comment_id)
        markdown_path = root / item.markdown_path
        rendered = renderer(
            markdown_path.read_text(encoding="utf-8"),
            markdown_path,
            section,
            item.slug,
        )
        if isinstance(rendered, tuple):
            html, excerpt = rendered
        else:
            html, excerpt = rendered, item.excerpt
        writings.append(
            Writing(
                section=section,
                slug=item.slug,
                title=item.title,
                date_published=item.date_published,
                markdown_path=markdown_path,
                metadata_path=root / item.metadata_path,
                html=html,
                excerpt=excerpt,
                comment_id=item.comment_id,
            )
        )
    return writings


def collect_albums(root: Path, seen_comment_ids: set[str] | None = None) -> list[Album]:
    root = Path(root).resolve()
    errors: list[str] = []
    comment_ids: dict[str, str] = {}
    loaded = _load_photography(root, errors, comment_ids)
    if errors:
        raise ContentError("\n".join(errors))
    seen_comment_ids = seen_comment_ids if seen_comment_ids is not None else set()
    albums: list[Album] = []
    for album in loaded:
        for photo in album.photos:
            if photo.comment_id in seen_comment_ids:
                raise ContentError(f"duplicate comment_id `{photo.comment_id}`")
            seen_comment_ids.add(photo.comment_id)
        photos = [
            Photo(
                slug=photo.slug,
                album_slug=photo.album_slug,
                name=photo.name,
                description=photo.description,
                location=photo.location,
                date_taken=photo.date_taken,
                source_path=root / photo.source_path,
                metadata_path=root / photo.metadata_path,
                alt=photo.alt,
                comment_id=photo.comment_id,
            )
            for photo in album.photos
        ]
        albums.append(
            Album(
                slug=album.slug,
                name=album.name,
                description=album.description,
                metadata_path=root / album.metadata_path,
                source_dir=root / album.source_dir,
                photos=photos,
            )
        )
    return albums


def load_config(root: Path, production: bool = False) -> SiteConfig:
    config_path = Path(root) / "site_config.toml"
    if not config_path.exists():
        return SiteConfig()
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    site_data = data.get("site", {})
    giscus_data = data.get("giscus", {})
    config = SiteConfig(
        title=str(site_data.get("title", "Portfolio of Joshua G. Albert")),
        base_url=str(site_data.get("base_url", "")),
        giscus=GiscusConfig(
            repo=str(giscus_data.get("repo", "")),
            repo_id=str(giscus_data.get("repo_id", "")),
            category=str(giscus_data.get("category", "Comments")),
            category_id=str(giscus_data.get("category_id", "")),
            theme=str(giscus_data.get("theme", "noborder_light")),
        ),
    )
    if production and not config.giscus.configured:
        raise ContentError("production build requires complete giscus configuration")
    return config
