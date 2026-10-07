# Coloring Pages — V1 Project Plan

## Goal

Build a simple, fast, mobile-first coloring-page website whose primary journey is:

**open → find → preview → print A4**

Public hostname: `https://coloring.rozkalns.net`.

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

No framework, CMS or RPi5-hosted database/backend API is required. The only approved analytics exception is a small Cloudflare edge layer: Web Analytics for aggregate traffic plus Worker/D1 for print-intent counts, reversible likes, Popular and 7-day Trending.

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
- portrait / approximately A4 aspect ratio
- preserve intentional source colors; ordinary coloring pages may be black-and-white while learning worksheets may use color
- thick, clean, high-contrast outlines where line art is used
- large coloring areas
- minimal tiny details
- primary age target 3–6
- no JPEG
- no watermark
- no mandatory vectorization
- new Chat-generated publication uses `PUBLISH` as the single normal command; it internally prepares and validates the A4 print master(s) before any Drive/content mutation, while `UPSCALE-PRINT` and `VALIDATE-PRINT` remain optional manual inspection/debug commands
- the validated Chat print master is exact `2480×3508` PNG with approximately 300×300 DPI metadata and an exact-white outer border
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

1. validates PNG and safe A4-like portrait geometry;
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
