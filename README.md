# coloring-pages

Static, mobile-first coloring-page catalogue planned for `coloring.rozkalns.net`.

## Project documents

- [V1 project plan](docs/PROJECT_PLAN.md)
- [UI mockups](docs/mockups/README.md)

Current phase: **V1 source implementation started**.

Implemented so far:

- responsive home-page shell in real HTML/CSS
- mobile navigation
- local search and category filtering over the initial placeholder cards
- mobile-first 2-column gallery behavior
- canonical metadata contract under `metadata/`
- deterministic Python catalogue validator/generator
- CI coverage for catalogue validation and unit tests

Still planned:

- real original coloring-page assets and generated WebP/PNG/PDF derivatives
- detail view and dedicated print view
- Docker image and SIMPLE-DEPLOY consumer contract
- separate RPi5 / Cloudflare LIVE work

The V1 stack remains HTML + CSS + vanilla JavaScript + JSON + a small Python build script, served as static files by `nginx-unprivileged` on RPi5.

No LIVE deployment or Cloudflare change is part of the current source work.
