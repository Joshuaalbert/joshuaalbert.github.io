from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from sitegen.content import Album, Photo, SiteConfig


ROOT = Path(__file__).resolve().parents[1]


class PhotographyRenderingTests(unittest.TestCase):
    def test_album_preview_renders_every_photo(self) -> None:
        env = Environment(
            loader=FileSystemLoader(ROOT / "site" / "templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )
        photos = [
            Photo(
                slug=f"photo-{index:02d}",
                album_slug="cannon-d60",
                name=f"Photo {index}",
                description="",
                location="Birch Island",
                date_taken=date(2016, 8, index),
                source_path=ROOT / f"photo-{index:02d}.jpg",
                metadata_path=ROOT / f"photo-{index:02d}.toml",
                alt=f"Photo {index}",
                comment_id=f"photography/albums/cannon-d60/photo-{index:02d}",
                derivatives={
                    "preview": f"/assets/photos/cannon-d60/photo-{index:02d}-preview.jpg",
                    "preview_webp": "",
                    "full": f"/assets/photos/cannon-d60/photo-{index:02d}-full.jpg",
                },
            )
            for index in range(1, 7)
        ]
        album = Album(
            slug="cannon-d60",
            name="Cannon D60",
            description="Album",
            metadata_path=ROOT / "cannon-d60.toml",
            source_dir=ROOT,
            photos=photos,
        )

        html = env.get_template("photography.html").render(
            site=SiteConfig(),
            active="photography",
            albums=[album],
        )

        self.assertEqual(html.count("album-preview-frame"), 6)
        self.assertIn("/photography/albums/cannon-d60/photo-01/", html)


if __name__ == "__main__":
    unittest.main()
