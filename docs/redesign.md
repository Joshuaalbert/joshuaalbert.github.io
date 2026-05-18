# Portfolio Redesign

This repository is moving from a Beautiful Jekyll CV-style site to a Python-generated static portfolio for photography, essays, and research. The generated site is deployed from `dist/` by GitHub Actions and keeps source content in human-editable TOML, Markdown, and image files.

## Content Model

Photography albums live under `photography/albums/`. Each album has `photography/albums/<album_slug>.toml` with `name` and `description`, plus a matching directory containing photo files and same-stem TOML metadata. Photo metadata requires `date_taken`, `name`, `description`, and `location`; `alt` and `comment_id` are optional.

Essays and research entries use matching Markdown/TOML pairs:

```text
essays/<slug>/<slug>.md
essays/<slug>/<slug>.toml
research/<slug>/<slug>.md
research/<slug>/<slug>.toml
```

Writing TOML requires `title` and `date_published`. Lists sort newest-first, then alphabetically for matching dates.

## Rendering

The generator validates content strictly, renders Markdown to HTML, keeps LaTeX delimiters for client-side KaTeX rendering, generates web photo derivatives, and emits static routes under `dist/`. Photos are never visually blurred. Text/list surfaces use a subtle pointer and keyboard focus defocus effect.

## Comments

giscus provides GitHub-backed comments and reactions through Discussions in `Joshuaalbert/joshuaalbert.github.io`. Production builds require the `Comments` category ID in `site_config.toml`.

Before comments work publicly, enable GitHub Pages from Actions, enable Discussions on the site repository, install the giscus GitHub App for that repository, create a `Comments` discussion category, and copy the generated category ID into `site_config.toml`. Until then, normal builds deploy the site with a placeholder comments message; `python scripts/build_site.py --production` remains the strict giscus readiness check.
