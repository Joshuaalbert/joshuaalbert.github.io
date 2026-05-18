from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sitegen.loader import SiteValidationError, load_site


class LoaderTests(unittest.TestCase):
    def test_loads_and_sorts_content_newest_first_with_alpha_ties(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            album = root / "photography" / "albums" / "city"
            album.mkdir(parents=True)
            (root / "photography" / "albums" / "city.toml").write_text(
                'name = "City"\ndescription = "Street work."\n',
                encoding="utf-8",
            )
            self._write_photo(album, "b", "Beta", "2020-01-01")
            self._write_photo(album, "a", "Alpha", "2020-01-01")
            self._write_photo(album, "z", "Zed", "2022-05-03")

            self._write_text_entry(root, "essays", "older", "Older", "2021-01-01")
            self._write_text_entry(root, "essays", "alpha", "Alpha", "2023-02-01")
            self._write_text_entry(root, "essays", "beta", "Beta", "2023-02-01")
            self._write_text_entry(root, "research", "paper", "Paper", "2024-01-05")

            manifest = load_site(root)

            self.assertEqual([album.slug for album in manifest.photography], ["city"])
            loaded_album = manifest.photography[0]
            self.assertEqual(loaded_album.year_label, "2020-2022")
            self.assertEqual([photo.slug for photo in loaded_album.photos], ["z", "a", "b"])
            self.assertEqual([entry.slug for entry in manifest.essays], ["alpha", "beta", "older"])
            self.assertIn(r"\(x=1\)", manifest.research[0].html)
            self.assertEqual(
                manifest.research[0].comment_term,
                "[research/comments] research/paper",
            )

    def test_strict_validation_reports_missing_pairs_invalid_dates_and_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            album = root / "photography" / "albums" / "city"
            album.mkdir(parents=True)
            (root / "photography" / "albums" / "city.toml").write_text(
                'name = "City"\ndescription = "Street work."\n',
                encoding="utf-8",
            )
            (album / "lonely.jpg").write_bytes(b"not really an image")
            (album / "bad.jpg").write_bytes(b"not really an image")
            (album / "bad.toml").write_text(
                'name = "Bad"\ndescription = "Bad date."\nlocation = "Nowhere"\n'
                'date_taken = "2020-13-40"\ncomment_id = "same"\n',
                encoding="utf-8",
            )
            (album / "Dup.jpg").write_bytes(b"one")
            (album / "dup.jpg").write_bytes(b"two")
            (album / "Dup.toml").write_text(
                'name = "Dup"\ndescription = "Dup."\nlocation = "Nowhere"\n'
                'date_taken = "2020-01-01"\n',
                encoding="utf-8",
            )
            (album / "dup.toml").write_text(
                'name = "dup"\ndescription = "dup."\nlocation = "Nowhere"\n'
                'date_taken = "2020-01-02"\n',
                encoding="utf-8",
            )
            self._write_text_entry(
                root,
                "essays",
                "same-comment",
                "Same",
                "2020-01-01",
                comment_id="same",
            )

            with self.assertRaises(SiteValidationError) as caught:
                load_site(root)

            message = "\n".join(caught.exception.errors)
            self.assertIn("missing photo metadata", message)
            self.assertIn("valid YYYY-MM-DD date", message)
            self.assertIn("duplicate photo slug", message)
            self.assertIn("duplicate comment_id 'same'", message)

    def test_rejects_non_url_safe_slugs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._write_text_entry(root, "essays", "Bad Slug", "Bad", "2020-01-01")

            with self.assertRaises(SiteValidationError) as caught:
                load_site(root)

            self.assertIn("invalid essay slug", "\n".join(caught.exception.errors))

    def _write_photo(self, album: Path, slug: str, name: str, date_taken: str) -> None:
        (album / f"{slug}.jpg").write_bytes(b"not really an image")
        (album / f"{slug}.toml").write_text(
            f'name = "{name}"\n'
            f'description = "{name} description."\n'
            'location = "Amsterdam"\n'
            f'date_taken = "{date_taken}"\n',
            encoding="utf-8",
        )

    def _write_text_entry(
        self,
        root: Path,
        collection: str,
        slug: str,
        title: str,
        date_published: str,
        comment_id: str | None = None,
    ) -> None:
        entry = root / collection / slug
        entry.mkdir(parents=True)
        comment_line = f'comment_id = "{comment_id}"\n' if comment_id else ""
        (entry / f"{slug}.toml").write_text(
            f'title = "{title}"\n'
            f'date_published = "{date_published}"\n'
            f"{comment_line}",
            encoding="utf-8",
        )
        (entry / f"{slug}.md").write_text(
            "# Heading\n\nFirst paragraph with \\(x=1\\) and enough text for an excerpt.",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
