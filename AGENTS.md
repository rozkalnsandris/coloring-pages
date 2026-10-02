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

## FAST-LANE v2.3 — lightweight adoption

This repository adopts the shared FAST-LANE v2.3 / Agent Work Cycle behavior from
`rozkalnsandris/ops-workflows@94187cc447fc80757db10ac25d49717d00dc8430`.

Canonical shared surfaces at that accepted revision:

- `docs/AGENT_WORK_CYCLE_V1.md`
- `docs/GITHUB_API_ACCESS_V1.md`
- `docs/WRITE_PREFLIGHT_COMPACT_V1.md`
- `docs/BOOTSTRAP_MANIFEST_V1.md`

Use the lightweight profile deliberately:

- `AGENTS.md` stays the compact repository-local routing and rules surface.
- Do not add a local `.github/agent-bootstrap.json` merely for fleet uniformity while this file remains small and unambiguous; the shared bootstrap contract explicitly permits repository-local fallback.
- Do not add AUTO-RUN FULL state/controllers, Queue mode, GITHUB-ONLY compatibility state or copied shared policy files unless a concrete repository need is separately reviewed.
- Current automation profile is FAST source work only. Planned SIMPLE-DEPLOY is not activated by this adoption.
- Repository-local rules in this file remain authoritative when they are stricter than shared policy.

Command behavior:

- `START coloring-pages` — freshly read minimum-sufficient GitHub state, select exactly one current lane, and continue all immediately safe same-scope source work until a genuine owner gate, external wait, fail-closed error/drift/ambiguity, or DONE.
- `SYNC coloring-pages` — incrementally refresh only the selected/current lane and mutable GitHub evidence needed for it.
- `turpini` — continue the exact same safe scope; it creates no merge, LIVE, retry, rollback, cleanup, credential, permission, settings or runtime authority.
- `AUDIT-HANDOFF coloring-pages` — explicit deeper continuity audit; do not turn ordinary START/SYNC into a repo-wide historical scan.

GitHub write discipline:

- Before a branch, PR, issue, comment or metadata write, use minimum-sufficient read-only preflight and reconcile an already-existing exact intended object instead of blindly duplicating it.
- Conflicting branch/PR identity, stale writer state or ambiguous post-dispatch outcome is a STOP; do not force, recreate, retry through another path or silently choose a different target.
- Before merge, refresh exact PR head, mergeability, required CI/status, reviews/threads and the exact owner authorization binding.
- Merge remains an explicit owner decision and never implies LIVE.

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
