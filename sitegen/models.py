"""Typed manifest models for generated site templates."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal


@dataclass(frozen=True)
class Photo:
    slug: str
    album_slug: str
    name: str
    description: str
    location: str
    date_taken: date
    source_path: str
    metadata_path: str
    alt: str
    comment_id: str
    camera: str = ""
    lens: str = ""
    focal_length: str = ""
    aperture: str = ""
    shutter_speed: str = ""
    iso: str = ""

    @property
    def comment_term(self) -> str:
        return f"[photo/comments] {self.comment_id}"

    @property
    def exif_label(self) -> str:
        return " · ".join(
            part
            for part in [
                self.camera,
                self.lens,
                self.focal_length,
                self.aperture,
                self.shutter_speed,
                self.iso,
            ]
            if part
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "album_slug": self.album_slug,
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "date_taken": self.date_taken.isoformat(),
            "source_path": self.source_path,
            "metadata_path": self.metadata_path,
            "alt": self.alt,
            "comment_id": self.comment_id,
            "camera": self.camera,
            "lens": self.lens,
            "focal_length": self.focal_length,
            "aperture": self.aperture,
            "shutter_speed": self.shutter_speed,
            "iso": self.iso,
            "exif_label": self.exif_label,
            "comment_term": self.comment_term,
        }


@dataclass(frozen=True)
class Album:
    slug: str
    name: str
    description: str
    metadata_path: str
    source_dir: str
    photos: tuple[Photo, ...] = field(default_factory=tuple)

    @property
    def year_label(self) -> str:
        years = sorted({photo.date_taken.year for photo in self.photos})
        if not years:
            return ""
        if years[0] == years[-1]:
            return str(years[0])
        return f"{years[0]}-{years[-1]}"

    @property
    def sort_date(self) -> date:
        if not self.photos:
            return date.min
        return max(photo.date_taken for photo in self.photos)

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "metadata_path": self.metadata_path,
            "source_dir": self.source_dir,
            "year_label": self.year_label,
            "photos": [photo.to_dict() for photo in self.photos],
        }


@dataclass(frozen=True)
class TextEntry:
    kind: Literal["essay", "research"]
    slug: str
    title: str
    date_published: date
    markdown_path: str
    metadata_path: str
    html: str
    excerpt: str
    comment_id: str

    @property
    def comment_term(self) -> str:
        return f"[{self.kind}/comments] {self.comment_id}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "slug": self.slug,
            "title": self.title,
            "date_published": self.date_published.isoformat(),
            "markdown_path": self.markdown_path,
            "metadata_path": self.metadata_path,
            "html": self.html,
            "excerpt": self.excerpt,
            "comment_id": self.comment_id,
            "comment_term": self.comment_term,
        }


@dataclass(frozen=True)
class BuildManifest:
    photography: tuple[Album, ...] = field(default_factory=tuple)
    essays: tuple[TextEntry, ...] = field(default_factory=tuple)
    research: tuple[TextEntry, ...] = field(default_factory=tuple)
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "photography": [album.to_dict() for album in self.photography],
            "essays": [entry.to_dict() for entry in self.essays],
            "research": [entry.to_dict() for entry in self.research],
        }
