# Redesign Tickets

## 1. Scaffold

Add `sitegen/`, `site/`, `docs/`, `environment.yml`, dependency files, ignore rules, and GitHub Actions deployment.

## 2. Generator

Implement strict TOML schema validation, newest-first ordering, Markdown rendering, Codecogs-to-LaTeX conversion, route rendering, and manifest output.

## 3. Images

Generate photo thumbnails, previews, full-size JPEG/WebP derivatives, and handle TIFF as source-only. Preserve animated GIF display.

## 4. Interface

Build the creamy minimalist landing page, photography albums, full-screen photo viewer, writing indexes/details, defocus effect, reduced-motion fallback, and giscus mount.

## 5. Migration

Copy existing `_posts/` and `inprep_posts/` into `research/`, strip Jekyll front matter, convert Codecogs links to LaTeX, and archive old CV/theme material in `old_content/`.

## 6. Review

Run generator tests, static build, visual smoke checks, content migration review, image review, giscus setup review, and deployment review before accepting.

