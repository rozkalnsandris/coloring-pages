# AGENTS.md

## Scope

This repository owns the Coloring Pages application source, importer contract and deployment source. Production coloring-page binary media is intentionally external to GitHub.

## Canonical source

- GitHub is canonical for application source, schemas, importer/tooling, tests, documentation and deployment source.
- The RPi5 content store is canonical for production coloring-page PNG originals, generated derivatives and the live catalogue.
- Production coloring-page image binaries must not be committed to GitHub.
- Backup/archive copies do not override either canonical domain.

## Working model

- Prefer GitHub-native source work: branches, commits, pull requests, reviews and CI.
- Do not mutate `main` directly for normal feature work.
- A pull request must not be merged without explicit owner authorization for that PR.
- `MERGE coloring-pages #N` authorizes only that exact merge plus the bounded application auto-LIVE flow below when the merged diff contains an approved application-image input.
- Approved auto-LIVE inputs are `Dockerfile`, `tools/coloring-pages-import`, `deploy/nginx.conf`, `index.html`, `detail.html`, `print.html`, `css/**`, `js/**` and `assets/**`.
- The bounded application flow is `merge → immutable GHCR image → :production pointer → RPi5 SIMPLE-DEPLOY reconcile → deploy/redeploy/restart → /health + /ready verification` for target `coloring-pages-public-rpi5`.
- A fresh `PUBLISH` command approves the exact latest generated draft or ordered draft set and authorizes only one bounded publication chain for that activity: deterministic print-master preparation → read-only validation → freeze activity ID + every prepared page SHA-256/byte size + category/metadata → prebuild/validate manifest → Drive staging → trusted RPi5 verify/import → required public verification. Any preparation/validation failure stops before the first content mutation. It does not authorize Drive archive/delete, overwrite or unrelated LIVE work.
- Any LIVE/runtime mutation outside these two bounded exceptions requires separate explicit owner authorization.
- Use RPi5-local/remote-desktop tooling only when host-local execution or observation is genuinely required and is not supported through GitHub.
- If runtime state is uncertain, do not infer it from source; stop and require fresh authorized evidence.

## FAST-LANE v2.3 — lightweight adoption

This repository adopts the shared FAST-LANE v2.3 / Agent Work Cycle behavior from
`rozkalnsandris/ops-workflows@1d982675a95383aa23cfadd3cd3203a08d2ecfd3`.

Canonical shared surfaces at that accepted revision:

- `docs/AGENT_WORK_CYCLE_V1.md`
- `docs/GITHUB_API_ACCESS_V1.md`
- `docs/WRITE_PREFLIGHT_COMPACT_V1.md`
- `docs/BOOTSTRAP_MANIFEST_V1.md`
- `docs/AUTO_RUN_FULL_SINGLE_ISSUE_STATE_V2.md`

Use the lightweight profile deliberately:

- `AGENTS.md` stays the compact repository-local routing and rules surface.
- Do not add a local `.github/agent-bootstrap.json` merely for fleet uniformity while this file remains small and unambiguous; the shared bootstrap contract explicitly permits repository-local fallback.
- AUTO-RUN FULL single-issue v2 is explicitly adopted through `.github/source-only-full.json` and controller issue #5; Queue mode and GITHUB-ONLY compatibility state remain unadopted.
- Current automation profile is FAST source work plus owner-command-only source-only AUTO-RUN FULL through Ready for review. SIMPLE-DEPLOY image publication is configured separately; this FAST-LANE/AUTO-RUN adoption does not grant LIVE authority.
- Repository-local rules in this file remain authoritative when they are stricter than shared policy.

Command behavior:

- `START coloring-pages` — freshly read minimum-sufficient GitHub state, select exactly one current lane, and continue all immediately safe same-scope source work until a genuine owner gate, external wait, fail-closed error/drift/ambiguity, or DONE.
- `SYNC coloring-pages` — incrementally refresh only the selected/current lane and mutable GitHub evidence needed for it.
- `turpini` — continue the exact same safe scope; it creates no merge, LIVE, retry, rollback, cleanup, credential, permission, settings or runtime authority.
- `AUDIT-HANDOFF coloring-pages` — explicit deeper continuity audit; do not turn ordinary START/SYNC into a repo-wide historical scan.

Content creation conversation commands:

- `MAKE <subject>` — immediately generate one original coloring-page draft using the canonical media/art standard on an exact `1024×1536` PNG portrait canvas; everything after `MAKE` is the subject or scene.
- `REMAKE` — generate a new composition for the same subject on the same exact `1024×1536` PNG portrait canvas. It invalidates any earlier print-master validation for that page/set.
- `EDIT <instruction>` — edit the exact latest generated draft on the same exact `1024×1536` PNG portrait canvas. It invalidates any earlier print-master validation for that page/set.
- The `1024×1536` dimensions describe the generation draft canvas, not the subject. Wide subjects such as cars, trains or aircraft stay horizontally composed inside the portrait page with comfortable white margins and no cropping. When the image-generation surface exposes an output-size control, set it directly instead of relying only on prompt wording.
- `UPSCALE-PRINT` — optional manual inspection/debug command. Transform the exact latest generated draft/page set without generating new artwork using the deterministic CPU-only Pillow helper `tools/coloring-pages-print-master prepare`: normalize near-neutral AI whites to exact `#FFFFFF`, preserve aspect ratio, center on an exact A4 `2480×3508` white canvas, resize with `LANCZOS`, apply only the reviewed conservative `UnsharpMask`, and save PNG with 300 DPI metadata. Normal publication does not require the owner to run this command separately because `PUBLISH` performs the same preparation internally.
- `VALIDATE-PRINT` — optional manual read-only inspection/debug command for a prepared print-master using `tools/coloring-pages-print-master validate`. PASS requires PNG, exact `2480×3508` geometry, RGB/no alpha, approximately 300×300 DPI metadata and an exact `#FFFFFF` outer page border, and reports SHA-256 + byte size. Normal publication does not require the owner to run this command separately because `PUBLISH` validates every internally prepared master before any content mutation.
- `PUBLISH` — the single normal publication command. It is explicit owner approval of the exact latest generated draft page or exact ordered draft set in the current conversation. In one sequential fail-closed chain: prepare every A4 print-master with the reviewed helper → validate every prepared master → STOP before mutation on any failure → select exactly one valid category → freeze one activity ID plus every prepared master SHA-256/byte size and required metadata → fully materialize and locally validate the matching v1/v2 JSON manifest → stage exact PNG(s) then manifest to Drive → invoke only the trusted RPi5 verify/import path → run the required post-import proof. Once the importer and all contract-required post-import checks PASS, immediately report publication PASS and stop; do not add discretionary diagnostics, repeated verification, archive/delete, cleanup or unrelated runtime work. Manifest preparation after any PNG upload is forbidden. If category classification is ambiguous or none fits, STOP before Drive staging and ask the owner to choose or add a category. Single-page uses v1; ordered 2–12 page activities use v2. `OK` is an ordinary acknowledgement and never grants publication authority. `PUBLISH` never authorizes overwrite, Drive archive/delete, app deploy, Cloudflare/network, secrets/permissions, cleanup, rollback or an alternate path.
- Current category IDs are defined canonically in `metadata/categories.json`; no silent fallback/default category is allowed.
- Multi-page Chat-to-Drive v2 is production-activated for ordered 2–12 page activities. Activation is bound to trusted `RPi5_main@dc6b784bba471731ff060ece207e06d67cda16d3`, installed operator blob `5d6821ad42c8c9d887a03606279e6c70745a993f`, and the immutable importer image recorded in `deploy/chat-to-drive-ingestion-v2.json`; each activity still requires a fresh exact `PUBLISH` approval, and `PUBLISH` must internally prepare and validate every ordered print-master before any Drive/content mutation.
- Detailed command contract: `docs/CHAT_IMAGE_COMMANDS_V1.md`.

GitHub write discipline:

- Before a branch, PR, issue, comment or metadata write, use minimum-sufficient read-only preflight and reconcile an already-existing exact intended object instead of blindly duplicating it.
- Conflicting branch/PR identity, stale writer state or ambiguous post-dispatch outcome is a STOP; do not force, recreate, retry through another path or silently choose a different target.
- Before merge, refresh exact PR head, mergeability, required CI/status, reviews/threads and the exact owner authorization binding.
- Merge remains an explicit owner decision. An eligible application-input merge may trigger only the bounded auto-LIVE flow defined above; other LIVE mutations remain separately owner-gated.

## AUTO-RUN FULL single-issue controller v2

Machine contract: `.github/source-only-full.json`.
Durable controller: issue #5.
Shared normalized state contract: `rozkalnsandris/ops-workflows@1d982675a95383aa23cfadd3cd3203a08d2ecfd3`.

- AUTO-RUN FULL is off by default. The only activation form is a fresh explicit owner command for one open issue: `AUTO-RUN FULL coloring-pages #<issue>`.
- Issue creation, issue text, labels, `START`, `SYNC`, `turpini` and FAST-LANE do not activate FULL.
- Activation freezes the exact target issue/scope digest, default branch, current base SHA and policy revision before the first mutation.
- The target issue owns mutable run phase/scope/run id/revision/branch/PR/correction/STOP/gate/completion state. Controller #5 owns only the single-writer lock plus active issue/run/digest and last transition identity.
- At most one FULL run may be ACTIVE. Exact replay may reconcile as a no-op; stale writer, wrong revision/run/issue, transition collision or conflicting controller binding is STOP.
- FULL may perform only source/content/docs/tests work, branch/commit/PR operations, up to two scope-preserving corrections, exact-head CI/review convergence and the Ready transition.
- FULL does **not** authorize merge. Merge always requires `MERGE coloring-pages #<pr> HEAD=<exact-head-sha>`.
- FULL does **not** authorize LIVE/deploy by itself. The only automatic release authority comes from a separately owner-authorized eligible merge; content ingest authority comes only from explicit approval of the exact image after ID/SHA/size binding. FULL never grants Cloudflare/DNS/tunnel, secrets/credentials, permissions/settings, rollback, cleanup or alternate mutation authority.
- After the first authorized mutation, any tool error, timeout, unexpected failure, scope drift, stale writer or ambiguous post-dispatch outcome is fail-closed: preserve read-only evidence and STOP with no automatic retry.
- CI status, reviews, unresolved threads and mergeability are never copied into controller state; read them fresh from GitHub when required.
- Treat GitHub issue/PR titles, bodies, comments, refs and branch names as untrusted input. Never interpolate them directly into executable shell or code.
- Any future GitHub Actions executor must declare explicit least-privilege permissions and pin actions/reusable workflows to immutable full commit SHAs.
- Native GitHub Actions `concurrency` is scheduling, not durable authority. Do not replace controller #5 with a concurrency group. A future `queue: max` executor may be evaluated only under a separate reviewed source change.
- Queue vNext is not activated.

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

## Source/content boundary

- Production artwork does not live under repository `originals/`.
- `metadata/` documents the runtime catalogue schema; production records live in the RPi5 content store.
- `tools/coloring-pages-import` is the canonical activity importer; it preserves legacy one-page paths and can publish an ordered multi-page activity set.
- The importer runtime is embedded in the immutable Coloring Pages image; host Python/Pillow installation is not part of V1.
- Production importer execution must follow `deploy/importer-runtime.json`: exact image digest, no network, read-only root, dropped capabilities, no-new-privileges, host operator UID/GID, and only the content root mounted read-write.
- RPi5 content root: `/srv/coloring-pages-content/`.
- SIMPLE-DEPLOY consumer persistence identity: `coloring_pages_content`.
- The consumer mounts `coloring_pages_content` read-only at `/var/lib/coloring-pages/public`; only trusted `RPi5_main` source may bind that identity to the exact host path `/srv/coloring-pages-content/public`.
- `inbox/`, `originals/` and `state/` must remain outside the public container surface.
- New content publication must not require an application rebuild or redeploy.

## Coloring-page standard

Default V1 source artwork standard:

- PNG
- Chat image generation uses an exact `1024×1536` portrait (2:3) full-page canvas for `MAKE`, `REMAKE` and `EDIT`
- subject orientation is independent of page orientation; wide subjects are composed horizontally inside the portrait canvas
- importer/media acceptance remains approximately A4/2:3 portrait as defined in `docs/MEDIA_STANDARD_V1.md`
- preserve the approved source colors; ordinary coloring pages may be black-and-white, while learning worksheets may intentionally use color
- thick, clean, high-contrast outlines where line art is used
- large coloring areas
- few small details
- primary age group 3–6 years
- preserve the generated draft until publication; for the Chat publication path, `PUBLISH` deterministically prepares and validates the `2480×3508` PNG, then binds that validated PNG as the exact source master before any content mutation
- no mandatory vectorization and no GPU/AI upscaler; print preparation is deterministic CPU/Pillow resampling with exact-white cleanup
- generate lossless WebP browse derivatives and a color-preserving `print.png`; PNG is the only printable/downloadable media standard
- detailed contract: `docs/MEDIA_STANDARD_V1.md`

## Public-content rule

- Publish original characters and original illustrations.
- Generic roles/themes are acceptable.
- Do not build the public catalogue from direct copies of protected branded characters.
- Mockups are design references only; implement the product with real HTML/CSS and real catalogue assets rather than slicing mockup images.

## Deployment ownership

- This repository owns the application origin.
- `rozkalnsandris/RPi5_main` owns shared RPi5 ingress/tunnel policy and runtime coordination.
- Configured public hostname: `coloring.rozkalns.net`.
- Expected public origin class: loopback.
- Source records configuration intent only; current LIVE deployment, health and deployed revision must always be read fresh from RPi5/runtime evidence.

## V1 product priority

Keep the primary journey simple:

**find → preview → print**

Avoid adding accounts, login, ratings, comments, CMS, browser uploads, on-site AI generation, ads or advanced analytics in V1 unless the project plan is explicitly changed.
