# coloring-pages

Static, mobile-first coloring-page catalogue planned for `coloring.rozkalns.net`.

## Project documents

- [V1 project plan](docs/PROJECT_PLAN.md)
- [UI mockups](docs/mockups/README.md)
- [SIMPLE-DEPLOY publication contract](docs/SIMPLE_DEPLOY.md)

Current phase: **V1 application runtime is online on the trusted RPi5 loopback origin; public ingress and real catalogue content are still pending**.

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
- pinned main-push SIMPLE-DEPLOY publication workflow
- reviewed `linux/arm64` GHCR image publication
- RPi5 target registration in `rozkalnsandris/RPi5_main`
- first bounded RPi5 loopback deployment at `127.0.0.1:9191`

Last verified LIVE evidence on 2026-10-03 showed the exact reviewed image healthy on `127.0.0.1:9191`, with `/`, `/health`, and `/ready` returning HTTP 200. Runtime state must still be re-read from RPi5 for any future consequential operation.

Still planned:

- real original coloring-page assets and populated catalogue metadata
- public ingress for `coloring.rozkalns.net`
- Cloudflare tunnel/DNS activation and public verification
- standing generic SIMPLE-DEPLOY adoption/receipt for `coloring-pages-public-rpi5`

The V1 stack remains HTML + CSS + vanilla JavaScript + JSON + a small Python build script, served as static files by `nginx-unprivileged` on RPi5.

Source work, application deployment, standing SIMPLE-DEPLOY adoption, and public ingress remain separate authorization boundaries.
