# Repository Guidelines

## Project Structure & Module Organization

This repository is a Python-generated static portfolio deployed to GitHub Pages. Generator code lives in `sitegen/`, templates and frontend assets in `site/`, and generated output in `dist/` is not committed. Photography content belongs in `photography/albums/` as album TOML plus photo/TOML pairs. Essays and research use paired files under `essays/<slug>/<slug>.md|toml` and `research/<slug>/<slug>.md|toml`. Legacy Jekyll/CV material is archived in `old_content/`; keep `_posts/` and `inprep_posts/` unchanged.

## Build, Test, and Development Commands

Use the `joshuaalbert_py` conda environment for installs and local commands:

```sh
conda activate joshuaalbert_py
```

Install Python dependencies inside that environment before local work:

```sh
conda run -n joshuaalbert_py pip install -r requirements.txt
```

Run a local development server:

```sh
conda run -n joshuaalbert_py python scripts/build_site.py
conda run -n joshuaalbert_py python -m http.server 8000 -d dist
```

Run tests and production validation:

```sh
conda run -n joshuaalbert_py pytest
conda run -n joshuaalbert_py python scripts/build_site.py --production
```

Production builds require the giscus category ID in `site_config.toml`.

## Coding Style & Naming Conventions

Use TOML metadata, Markdown content, and lowercase URL-safe slugs. Keep Markdown prose natural, write math as `\(...\)` or `\[...\]`, and store local essay/research assets beside their Markdown. Python uses standard 4-space indentation and typed dataclasses where useful. Frontend code is vanilla HTML/CSS/JS; preserve the minimalist creamy aesthetic and never apply blur/filter effects to photos.

## Testing Guidelines

Run `pytest` for schema, sorting, and migration helpers. Run `python scripts/build_site.py` before every change is considered complete. For UI changes, preview `dist/` locally and check landing, photography, photo viewer, essays, and research at desktop and mobile widths.

## Commit & Pull Request Guidelines

Recent history uses short imperative messages such as `Update aboutme.md`. Keep commit subjects concise and file- or feature-focused. Pull requests should describe the visible change, list validation performed, link any related issue, and include screenshots for visual changes. Note content schema, giscus, image-pipeline, or deployment changes explicitly.

## Agent-Specific Instructions

Do not commit `dist/`, `_site/`, dependency directories, or generated caches. Preserve source originals and archived legacy content unless the task explicitly asks to change them.
