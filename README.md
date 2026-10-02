# coloring-pages

Static, mobile-first coloring-page catalogue planned for `coloring.rozkalns.net`.

## Project documents

- [V1 project plan](docs/PROJECT_PLAN.md)
- [UI mockups](docs/mockups/README.md)
- [SIMPLE-DEPLOY publication contract](docs/SIMPLE_DEPLOY.md)

Current phase: **V1 source implementation started**.

Implemented so far:

- responsive desktop/mobile home-page UI in real HTML/CSS
- mobile navigation
- local search/category filtering with automatic `catalog.json` hydration when entries exist
- catalogue-driven detail page and dedicated A4 print page
- canonical metadata contract under `metadata/`
- deterministic Python catalogue validator/generator
- deterministic A4/WebP/PDF media derivative generator from canonical PNG masters
- hardened static Docker runtime source using `nginx-unprivileged`
- SIMPLE-DEPLOY v1 consumer contract and compose source
- CI coverage for catalogue, UI/runtime source, consumer JSON and Compose validation

Still planned:

- real original coloring-page assets
- first reviewed GHCR image publication after merge of the pinned SIMPLE-DEPLOY caller
- separate RPi5 / Cloudflare LIVE work

The V1 stack remains HTML + CSS + vanilla JavaScript + JSON + a small Python build script, served as static files by `nginx-unprivileged` on RPi5.

No LIVE deployment or Cloudflare change is part of the current source work.
