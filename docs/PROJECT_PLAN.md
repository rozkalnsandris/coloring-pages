# Coloring Pages — V1 Project Plan

## Goal

Build a simple, fast, mobile-first coloring-page website whose primary journey is:

**open → find → preview → print A4**

Canonical hostname in application source: `https://ausmalwiese.de/`. The legacy `coloring.rozkalns.net` redirect is separately owner-gated; actual routing and availability require fresh LIVE verification.

## Technology

V1 remains intentionally small:

- semantic HTML5
- plain CSS
- vanilla JavaScript
- JSON catalogue
- Python/Pillow importer embedded in the immutable application image
- Docker
- `nginx-unprivileged`
- Raspberry Pi 5 runtime

No framework, CMS or RPi5-hosted database/backend API is required. The only approved analytics exception is a small Cloudflare edge layer: Web Analytics for aggregate traffic plus Worker/D1 for print-intent counts, aggregate hearts (the owner-selected new frontend target), Popular and 7-day Trending. Historical reversible likes and visitor-recognition paths must be reconciled separately; this source direction alone is not LIVE proof.

## Current continuity handoff (audited 2026-10-23)

This is a **dated source-work locator**, not a stored current SHA, CI/review, release, Cloudflare, or RPi5/LIVE receipt. On continuation, freshly read `main`, the selected issue/PR's exact head/checks/reviews/threads, and independently authorized LIVE evidence when actual deployment matters. A merged source PR or a green SIMPLE-DEPLOY workflow alone does not prove installed ADMIN/importer compatibility, public endpoint health, or completed Cloudflare/D1 changes.

**Audit snapshot 2026-10-23 (refresh before any action):** `coloring-pages/main@a910b39a7a8617c1589069a12b0c7c2243b26543` had **4/4 successful completed exact-main checks** (source CI, GitHub-first policy, SIMPLE-DEPLOY source validation and GHCR publication). Shared policy `ops-workflows/main@4e89b75d7f496dfb43fd9c1eb10a995fad53fdd8` matches the adopted repo-local GitHub-first reference. `RPi5_main/main@3edd9bc55e4a6c9a9f4048e5a1a998037efcc520` is **host source state only**, not installed runtime evidence. The AUTO-RUN FULL controller [#5](https://github.com/rozkalnsandris/coloring-pages/issues/5) was **IDLE**; the historical DONE run in #206 covers a prior bounded PR #340, not acceptance of the entire print basket. This audit makes no new LIVE, ADMIN/importer, Cloudflare, D1, or PUBLISH claims.

- **Preferred publication:** [README](../README.md) and `AGENTS.md` specify `MAKE/EDIT/REMAKE → ZIP → protected ADMIN upload → ADMIN A4 prepare/validate → import and public verification` for independent single-page drafts. ZIP is an artwork handoff only, not publication approval. Ordered multi-page activities retain their separate validated publication path until reviewed ADMIN multi-page ZIP support exists. The supported *source contract* for direct Chat `PUBLISH` is [the simple bridge](PUBLISH_SIMPLE_BRIDGE_274.md): prepare and validate all A4 PNG masters and manifests **before** writes; stage only exact PNG bytes using connected Drive top-level `file_uri` inputs; then hand off prebuilt manifest metadata through the bounded RPi5 request bridge to the trusted Drive ingest/import operator. Production eligibility requires fresh connector, exact pending-folder, installed dispatcher/operator/importer and LIVE catalogue evidence; this document asserts no successful publication. [#258 / Draft #259](https://github.com/rozkalnsandris/coloring-pages/pull/259), [#266 / Draft #267](https://github.com/rozkalnsandris/coloring-pages/pull/267) and [#270 / Draft #273](https://github.com/rozkalnsandris/coloring-pages/pull/273) remain offline research, not alternate production upload authority.
- **Discovery and seasonal UI:** source merges [#332](https://github.com/rozkalnsandris/coloring-pages/pull/332) (`Essen & Natur` derived discovery collection, **not** a new canonical category/ADMIN allowlist), [#330](https://github.com/rozkalnsandris/coloring-pages/pull/330) (visual calendar), [#317](https://github.com/rozkalnsandris/coloring-pages/pull/317) (automatic weekly highlight) and [#316](https://github.com/rozkalnsandris/coloring-pages/pull/316) (age/difficulty filters) have merged. Issues [#331](https://github.com/rozkalnsandris/coloring-pages/issues/331), [#196](https://github.com/rozkalnsandris/coloring-pages/issues/196), [#205](https://github.com/rozkalnsandris/coloring-pages/issues/205) and [#201](https://github.com/rozkalnsandris/coloring-pages/issues/201) remain tracker/acceptance surfaces; a source merge does not prove final LIVE QA. Weekly choice follows [WEEKLY_FEATURE_V1](WEEKLY_FEATURE_V1.md): Monday 00:10 `Europe/Berlin` at next homepage reload using validated `published_at` only. Actual ADMIN/importer timestamp emission and historical coverage require separate LIVE evidence; never guess legacy publication dates. Calendar source contract: [AUSMAL_KALENDER_V1](AUSMAL_KALENDER_V1.md).
- **Print basket:** [#206](https://github.com/rozkalnsandris/coloring-pages/issues/206) remains **open**. In addition to merged foundations #325/#326/#327, source PRs [#340](https://github.com/rozkalnsandris/coloring-pages/pull/340) (cross-page selection), [#341](https://github.com/rozkalnsandris/coloring-pages/pull/341) (accessible basket dialog), [#342](https://github.com/rozkalnsandris/coloring-pages/pull/342) (gated full-resolution PNG ZIP), [#343](https://github.com/rozkalnsandris/coloring-pages/pull/343) (cross-activity print plan), [#344](https://github.com/rozkalnsandris/coloring-pages/pull/344) (bounded A4 PNG media preflight) and [#345](https://github.com/rozkalnsandris/coloring-pages/pull/345) (sequential image decode and cleanup) have **merged**. #345's exact-head CI was **2/2 PASS**, zero reviews/unresolved threads. The visitor-facing multi-activity **`Alles drucken` is still inactive** pending final composition, print-to-file/physical Firefox/Chromium tests, mixed-orientation A4, QR/footer, cancellation/memory, and ordinary review/release gates. Do not confuse source tests with end-to-end browser or LIVE evidence. Preserve 5 actual A4 sheets, ordered atomic multi-page activities, unchanged public `print.png` bytes and client-only privacy.
- **Privacy and engagement:** [#256](https://github.com/rozkalnsandris/coloring-pages/issues/256) targets aggregate hearts/Print without persistent visitor recognition; backend [#262](https://github.com/rozkalnsandris/coloring-pages/pull/262) is merged. Frontend [#263](https://github.com/rozkalnsandris/coloring-pages/pull/263) remains **open, not mergeable and merge/release HELD** pending independent evidence for the production Stats Worker endpoint, required D1 schema and application release compatibility. Its audit-time exact head `ccd78a348ecaa6388350197453ad40676d3a99af` had **2/2 PASS** source/policy checks, **0 reviews and 0 unresolved threads**; that does not lift the hold. Legal [#158](https://github.com/rozkalnsandris/coloring-pages/pull/158) is still Draft. Preserve legacy records/totals until a separate authorized transition; CI does not prove LIVE/D1.
- **Social presence:** [#337](https://github.com/rozkalnsandris/coloring-pages/pull/337) merged the shared mobile-friendly `Folge uns` footer on 11 public pages, using owner-provided Instagram and **one exact Facebook `/share/...` URL**; the latter is not independently proven to be a stable profile permalink. No external Meta SDK/tracker was included; the print-only page was excluded. On **2026-10-23**, owner-provided RPi5 **read-only** observations recorded `SOCIAL_JS=PASS`, `HOME_FOOTER=PASS`, `/health=200`, `/ready=200` for that deployed release. This is historical evidence and **not** fresh verification of any later application image or destination links in a browser. Marketing research [#198](https://github.com/rozkalnsandris/coloring-pages/issues/198) is still open; drafts grant no account access, external posting or scheduling authority.
- **Fehler melden:** source improvements [#285](https://github.com/rozkalnsandris/coloring-pages/pull/285) and [#286](https://github.com/rozkalnsandris/coloring-pages/pull/286) are merged; [#240](https://github.com/rozkalnsandris/coloring-pages/issues/240) remains the feature tracker. Mock tests/config do **not** prove a live Cloudflare Email Service binding or mail delivery. See [REPORT_ERRORS_V1](REPORT_ERRORS_V1.md).
- **Domain/SEO:** `ausmalwiese.de` is the source canonical target. Sitemap/Worker and old-host 301 cutover remain separately owner-gated under [DOMAIN_CANONICAL_CUTOVER_V1](DOMAIN_CANONICAL_CUTOVER_V1.md) and [RPi5_main#996](https://github.com/rozkalnsandris/RPi5_main/issues/996). Verify actual edge/host behavior before reporting completion.
- **Cut & Paste:** see `AGENTS.md` and [CUT_PASTE_PLAYBOOK_V1](CUT_PASTE_PLAYBOOK_V1.md) for geometry, A4 and physical QA; source/raster checks never substitute for exact-version `PUBLISH` approval.
- **AUTO-RUN FULL:** [controller #5](https://github.com/rozkalnsandris/coloring-pages/issues/5) is **IDLE** at audit, the GitHub lock/pointer for explicitly activated single-issue runs, never durable CI/release/authorization evidence. Issue #206's previous run marked `DONE` for merged PR #340 only; #206 remains open. Source-level audit does not activate FULL.

## Source/content architecture

```text
GitHub
├── HTML/CSS/JS
├── importer + tests
├── Docker/nginx source
└── docs/contracts
        │
        │ reviewed source
        ▼
RPi5 application container
        │
        ├── static application files
        │
        └── read-only content mount
                │
                ▼
/srv/coloring-pages-content/public
├── catalog.json
└── media/
```

Coloring-page binary media does not live in GitHub.

## RPi5 content store

Canonical LIVE content layout:

```text
/srv/coloring-pages-content/
├── inbox/
├── originals/
│   └── <activity-id>/
│       ├── source.png              # single-page
│       └── source-1.png ...        # multi-page
├── public/
│   ├── catalog.json
│   └── media/
│       └── <activity-id>/
│           ├── thumb.webp
│           ├── preview.webp        # single-page
│           ├── print.png           # single-page
│           ├── preview-1.webp ...  # multi-page
│           └── print-1.png ...     # multi-page
└── state/
```

Responsibilities:

- `inbox/`: operator drop location; never public.
- `originals/`: preserved canonical source PNGs; never public directly.
- `public/`: the only directory mounted into nginx.
- `state/`: importer staging/work state; never public.

## Coloring Pages Media Standard v1

See `docs/MEDIA_STANDARD_V1.md`.

V1 source requirements:

- PNG
- portrait or landscape A4-like aspect ratio, including legacy 2:3 / 3:2 generator inputs
- preserve intentional source colors; ordinary coloring pages may be black-and-white while learning worksheets may use color
- thick, clean, high-contrast outlines where line art is used
- large coloring areas
- minimal tiny details
- primary age target 3–6
- no JPEG
- no watermark
- no mandatory vectorization
- new Chat-generated publication uses `PUBLISH` as the single normal command; it internally prepares and validates the A4 print master(s) before any Drive/content mutation, while `UPSCALE-PRINT` and `VALIDATE-PRINT` remain optional manual inspection/debug commands
- the validated Chat print master is exact `2480×3508` portrait or `3508×2480` landscape PNG, matching source orientation, with approximately 300×300 DPI metadata, exact-white outer border and the current 15 mm artwork-safe margin
- the importer remains backward compatible with its broader accepted A4/2:3 source geometry and does not perform the upscale itself

The exact validated print-master PNG bytes are preserved as the canonical source: `source.png` for single-page activities or ordered `source-1.png`, `source-2.png`, … for multi-page activities.

## Daily content import

Repository source tool: `tools/coloring-pages-import`.

The production path is activated and uses one reviewed RPi5 publish operator. Activation history is not current runtime proof: before the first Drive mutation, `PUBLISH` must freshly verify installed-operator identity and importer-source alignment according to `deploy/chat-to-drive-ingestion.json` / `deploy/chat-to-drive-ingestion-v2.json`; any mismatch fails closed and requires a separately reviewed `RPi5_main` repin/install.

The operator verifies the exact staged manifest, byte size and SHA-256, atomically publishes the PNG into `inbox/`, then directly runs the immutable Coloring Pages importer image under the isolation contract in `deploy/importer-runtime.json`.

The first end-to-end production import passed on 2026-10-03. That is historical activation evidence only. For each future activity, the owner's fresh explicit `PUBLISH` command for the exact latest draft page or ordered draft set authorizes one bounded content-publication chain. That chain prepares and validates every print master, then freezes the activity ID and every page SHA-256 + byte size before the first Drive/content mutation; its authority is limited to staging, verified ingest/import and public verification.

Host Python/Pillow installation is not required. Installing/replacing the publish operator and executing production imports remain outside source-only authority.

The importer may accept metadata flags, but manifest metadata keeps the normal Drive-ingest path explicit and deterministic. Category is mandatory and must match the canonical registry in `metadata/categories.json`; unknown/free-text categories fail closed before publication.

The importer requires the pre-created content-store layout and accepts only direct files from `inbox/`.

The importer:

1. validates PNG and safe A4-like portrait or landscape geometry, including backward-compatible accepted source ratios;
2. derives/validates a stable lowercase-hyphen page ID;
3. rejects duplicate IDs;
4. preserves the approved source page(s) under `originals/<activity-id>/`;
5. creates one `thumb.webp` plus ordered lossless preview derivative(s);
6. creates ordered public print PNG derivative(s) that preserve source colors and source dimensions, without publishing the exact private source PNG bytes;
7. keeps top-level `preview`/`print` compatible with page 1 and adds ordered `pages[]` for multi-page activities;
8. stages a new catalogue;
9. atomically replaces `catalog.json` only after all derivatives are ready.

Validation/generation failure must not modify the currently published catalogue.

## Catalogue contract

Example:

```json
{
  "id": "fire-pup-001",
  "title": "Fire Pup 001",
  "character": "",
  "category": "tiere",
  "age": "3-6",
  "difficulty": "easy",
  "language": "de",
  "thumb": "/media/fire-pup-001/thumb.webp",
  "preview": "/media/fire-pup-001/preview.webp",
  "print": "/media/fire-pup-001/print.png"
}
```

The existing frontend keeps fetching `catalog.json`. New content therefore does not require an HTML/JS edit, GitHub PR, image rebuild or application redeploy. Single-page entries keep their legacy top-level `preview`/`print` fields. Multi-page entries add ordered `pages[]` while keeping the top-level fields pointed at page 1 for backward compatibility. The detail-page `A4 drucken` action sends all ordered print PNG pages through the hidden HTML print document and one normal browser/system print flow; direct download targets the selected page's print PNG.

## Runtime mount

The SIMPLE-DEPLOY consumer contract exposes one stable persistence identity:

```text
coloring_pages_content
→ /var/lib/coloring-pages/public
→ read-only
```

The consumer manifest intentionally does not carry an arbitrary host path. The trusted `RPi5_main` adapter must separately map `coloring_pages_content` to the approved host content path:

```text
/srv/coloring-pages-content/public
```

That RPi5-side mapping is a separate source/LIVE boundary.

nginx maps:

- `/catalog.json` → mounted runtime catalogue
- `/media/...` → mounted runtime media

The container gets no access to `inbox/`, `originals/` or `state/`.

## Caching

- `catalog.json`: `no-cache`
- published media: long-lived immutable cache
- existing-media corrections never overwrite an immutable media identity; corrected bytes use full-SHA-256 content-addressed filenames and an atomic no-cache catalogue URL switch

V1 rejects duplicate IDs; replacement semantics require a separate reviewed workflow.

## Backup

Critical content to back up:

- `originals/`
- `public/catalog.json`

Web derivatives can be regenerated if needed.

## V1 exclusions

Do not add yet:

- accounts/login
- ratings/comments
- CMS
- browser uploads
- on-site AI generation
- database
- ads
- RPi5-hosted analytics/database/backend (the approved exception is the small Cloudflare Web Analytics + Worker/D1 engagement layer documented in `docs/CLOUDFLARE_STATS_V1.md`)

## Authority boundary

The repository owns source contracts and importer code. Two bounded production paths are authorized by the project policy:

- owner-authorized eligible application merge → immutable image → existing RPi5 SIMPLE-DEPLOY auto-LIVE flow for `coloring-pages-public-rpi5`;
- owner `PUBLISH` of the exact latest draft page or ordered draft set → internal print-master preparation/validation → activity ID + every page SHA/size binding before the first Drive/content mutation → Drive staging → verified RPi5 ingest/import → public verification.

Everything outside those paths—Cloudflare/DNS/tunnel, secrets/credentials, permissions, host packages, manual/alternate deploys, Drive archive/delete, production overwrite, cleanup or rollback—requires separate explicit owner authorization.
