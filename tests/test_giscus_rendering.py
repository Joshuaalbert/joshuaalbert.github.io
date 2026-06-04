from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from sitegen.content import Album, GiscusConfig, Photo, SiteConfig, Writing


ROOT = Path(__file__).resolve().parents[1]


class GiscusRenderingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.env = Environment(
            loader=FileSystemLoader(ROOT / "site" / "templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )
        self.site = SiteConfig(
            giscus=GiscusConfig(
                repo="owner/repo",
                repo_id="repo-id",
                category="Comments",
                category_id="category-id",
            )
        )

    def test_photo_comments_match_unique_html_title(self) -> None:
        photo = Photo(
            slug="photo-01",
            album_slug="cannon-d60",
            name="Photo 1",
            description="",
            location="Ingersoll, ON Canada",
            date_taken=date(2016, 9, 3),
            source_path=ROOT / "photo.jpg",
            metadata_path=ROOT / "photo.toml",
            alt="Photo 1",
            comment_id="photography/albums/cannon-d60/photo-01",
            derivatives={"full": "/assets/photo.jpg", "full_webp": ""},
        )
        album = Album(
            slug="cannon-d60",
            name="Cannon D60",
            description="Album",
            metadata_path=ROOT / "album.toml",
            source_dir=ROOT,
            photos=[photo],
        )

        html = self.env.get_template("photo.html").render(
            site=self.site,
            active="photography",
            album=album,
            photo=photo,
            previous_photo=None,
            next_photo=None,
            current_index=0,
        )

        self.assertIn("<title>[photo/comments] photography/albums/cannon-d60/photo-01</title>", html)
        self.assertIn('class="giscus"', html)
        self.assertIn('data-input-position="top"', html)
        self.assertIn('data-loading="lazy"', html)
        self.assertIn('data-mapping="title"', html)
        self.assertIn('data-theme="noborder_light"', html)
        self.assertIn('data-light-theme="noborder_light"', html)
        self.assertIn('data-dark-theme="noborder_dark"', html)
        self.assertNotIn("data-term=", html)
        self.assertIn(
            'data-giscus-title="[photo/comments] photography/albums/cannon-d60/photo-01"',
            html,
        )

    def test_writing_comments_match_unique_html_title(self) -> None:
        item = Writing(
            section="essays",
            slug="hello",
            title="Hello",
            date_published=date(2026, 1, 1),
            markdown_path=ROOT / "hello.md",
            metadata_path=ROOT / "hello.toml",
            html="<p>Hello.</p>",
            excerpt="Hello.",
            comment_id="essays/hello",
        )

        html = self.env.get_template("writing_detail.html").render(
            site=self.site,
            active="essays",
            section="essays",
            title="Essays",
            item=item,
        )

        self.assertIn("<title>[essay/comments] essays/hello</title>", html)
        self.assertIn('data-mapping="title"', html)
        self.assertNotIn("data-term=", html)


if __name__ == "__main__":
    unittest.main()
