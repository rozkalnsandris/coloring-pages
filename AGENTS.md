# AGENTS.md

## Scope

This repository owns the Coloring Pages application source and its static media catalogue.

## Canonical source

- GitHub is the source of truth.
- Original master images, metadata, application source, build tooling, tests and deployment source belong in this repository.
- Google Drive is archive/backup only and must not override GitHub state.
- RPi5 contains the deployed runtime copy, not the canonical source.

## Working model

- Prefer GitHub-native source work: branches, commits, pull requests, reviews and CI.
- Do not mutate `main` directly for normal feature work.
- A pull request must not be merged without explicit owner authorization for that PR.
- `MERGE coloring-pages #N` authorizes only that exact merge.
- A merge never authorizes RPi5 deployment, Cloudflare/DNS/tunnel changes, restarts or other LIVE mutations.
- LIVE/runtime work requires a separate, explicit authorization with the exact target and scope.
- Use RPi5-local/remote-desktop tooling only when host-local execution or observation is genuinely required and is not supported through GitHub.
- If runtime state is uncertain, do not infer it from source; stop and require fresh authorized evidence.

## Secrets and protected data

- Never commit secrets, tokens, credentials, private keys, environment files or protected runtime configuration.
- Do not read secrets merely to prove configuration state.
- Keep deployment and verification evidence sanitized to classes, booleans, counts, hashes or other non-secret facts when possible.

## V1 architecture

V1 intentionally uses:

- HTML
- CSS
- vanilla JavaScript
- JSON
- a small Python build pipeline
- Docker
- `nginx-unprivileged`
- RPi5 runtime behind the existing shared Cloudflare Tunnel

Do not add a framework, CMS, database or backend API without a documented need.

## Source/generated boundary

- `originals/` contains canonical master artwork.
- `metadata/` contains canonical catalogue metadata.
- `tools/build_catalog.py` will validate inputs and generate web/print derivatives.
- `dist/` is generated output and is not canonical source.
- `dist/catalog.json` is generated from canonical metadata; do not hand-edit it.
- Generated thumbnails, previews and PDFs should be reproducible from canonical inputs.

## Coloring-page standard

Default V1 artwork standard:

- A4 portrait
- 300 DPI
- 2480 × 3508 px
- black and white
- white background
- thick, clean outlines
- large coloring areas
- few small details
- primary age group 3–6 years

## Public-content rule

- Publish original characters and original illustrations.
- Generic roles/themes are acceptable.
- Do not build the public catalogue from direct copies of protected branded characters.
- Mockups are design references only; implement the product with real HTML/CSS and real catalogue assets rather than slicing mockup images.

## Deployment ownership

- This repository owns the application origin.
- `rozkalnsandris/RPi5_main` owns shared RPi5 ingress/tunnel policy and runtime coordination.
- Planned public hostname: `coloring.rozkalns.net`.
- Desired public origin class: loopback.
- Until fresh authorized runtime evidence exists, do not claim a current LIVE origin state.

## V1 product priority

Keep the primary journey simple:

**find → preview → print**

Avoid adding accounts, login, ratings, comments, CMS, browser uploads, on-site AI generation, ads or advanced analytics in V1 unless the project plan is explicitly changed.
