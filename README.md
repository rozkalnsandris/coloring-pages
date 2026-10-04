# coloring-pages

Static, mobile-first coloring-page catalogue for `coloring.rozkalns.net`.

## V1 content model

Application source and media content are deliberately separated:

- **GitHub** is canonical for HTML/CSS/JavaScript, importer/tooling, schemas, tests, Docker/nginx source and operational documentation.
- **RPi5 content store** is canonical for coloring-page PNG originals, generated web/print derivatives and the live `catalog.json`.
- Production coloring-page image binaries are **not committed to GitHub**.
- **Google Drive** may be used only as a bounded transport/staging queue for owner-approved ChatGPT-generated PNGs; it is not a production source of truth.

Daily content flow:

```text
generate PNG page(s) in ChatGPT
→ UPSCALE-PRINT exact draft page(s) into A4 print-master PNGs
→ VALIDATE-PRINT every print master
→ owner PUBLISH approval of the exact validated page or ordered page set
→ determine one valid category from metadata/categories.json
→ freeze every approved print-master SHA-256 + byte size
→ fully materialize + validate the manifest before any Drive write
→ stage exact PNG page(s), then the prebuilt manifest last in Google Drive
→ trusted RPi5 publish operator pulls and verifies every page
→ publish the verified activity into /srv/coloring-pages-content/inbox/
→ directly run the immutable importer image once
→ verify catalogue, derivatives and public URLs
```

This path is production-activated. The first owner-authorized end-to-end import passed on 2026-10-03. That activation record is historical continuity only: each future content import remains separately owner-authorized and exact-ID/hash/size bound.

For normal ChatGPT use, the convenience command layer is:

```text
MAKE <subject>   # generate one draft candidate
REMAKE           # same subject, new composition; invalidates prior validation
EDIT <change>    # edit latest draft; invalidates prior validation
UPSCALE-PRINT     # CPU/Pillow white-clean + A4 print-master preparation
VALIDATE-PRINT    # read-only exact print-master validation
PUBLISH           # approve exact validated print master, bind category, ingest
```

See [Chat image commands v1](docs/CHAT_IMAGE_COMMANDS_V1.md). `PUBLISH` does not weaken the exact activity/page SHA-256/byte-size binding or any existing owner/runtime boundary. `OK` is not a publication command. Before Drive staging, one category must be bound from the canonical registry in `metadata/categories.json`; an unknown category is rejected rather than silently published outside the visible filters.

Multi-page activities use the reviewed [Chat-to-Drive ingestion v2](docs/CHAT_TO_DRIVE_INGESTION_V2.md) path. The shared v1/v2 host publish operator is currently in a repin transition: reviewed target source is `RPi5_main@7e3e6b6d6574c1dc5199618dbb974b1fae83eaf5`, but the new operator must still be installed and verified on the RPi5 before any new `PUBLISH` may mutate Drive/content. Each activity still requires fresh exact owner `PUBLISH` approval after that activation.

Application release is a separate lane. An owner-authorized merge that changes an approved application-image input (Dockerfile, importer, nginx, HTML, CSS, JavaScript or assets) publishes an immutable GHCR image and may proceed through the existing bounded RPi5 SIMPLE-DEPLOY reconciler to LIVE automatically. Content-contract/docs/tests changes do not mint or redeploy an application image.

The application keeps the simple V1 journey:

**find → preview → print**

Multi-page activities use the same journey: one gallery item may contain an ordered `pages[]` set, the detail view switches between page previews, and one A4 print action prints the complete set. Existing one-page catalogue entries and media paths remain backward compatible.

## Media standard

See [Coloring Pages Media Standard v1](docs/MEDIA_STANDARD_V1.md).

The approved publication source artwork is preserved byte-for-byte only as the private `originals/<id>/source.png` master. For new Chat-generated publication, that source is the exact `2480×3508` validated print master produced before `PUBLISH`; the lower-resolution generation draft is not the production master. The CPU-only preparation step uses Pillow/LANCZOS, conservative unsharp masking and exact-white normalization, with 300 DPI metadata. This resampling does not recreate missing native detail. The importer itself still performs no upscale and remains backward-compatible with its broader accepted source geometry. Published media URLs are immutable; if an existing derivative must be corrected, the corrected bytes receive new full-SHA-256 content-addressed filenames and the no-cache catalogue switches to those URLs instead of requiring a CDN purge. The importer publishes one color-preserving `print.png` derivative at the approved source dimensions as the canonical printable/downloadable file. The hidden `print.html` uses that PNG with CSS `@page` fixed to A4 portrait (`210 × 297 mm`) and calls `window.print()` without recoloring the pixels. The detail page downloads the same `print.png` directly.

## Runtime content layout

```text
/srv/coloring-pages-content/
├── inbox/
├── originals/
├── public/
│   ├── catalog.json
│   └── media/
└── state/
```

Only `public/` is exposed to the nginx container, read-only. The consumer contract names this persistence surface `coloring_pages_content`; the exact mapping from that stable identity to `/srv/coloring-pages-content/public` belongs to the trusted `RPi5_main` adapter. `inbox/`, `originals/` and `state/` remain host-side and are not web-served.

## Project documents

- [V1 project plan](docs/PROJECT_PLAN.md)
- [Media Standard v1](docs/MEDIA_STANDARD_V1.md)
- [Importer Runtime v1](docs/IMPORTER_RUNTIME_V1.md)
- [Chat-to-Drive ingestion v1](docs/CHAT_TO_DRIVE_INGESTION_V1.md)
- [Chat-to-Drive ingestion v2 — multi-page source contract](docs/CHAT_TO_DRIVE_INGESTION_V2.md)
- [Chat image commands v1](docs/CHAT_IMAGE_COMMANDS_V1.md)
- [SIMPLE-DEPLOY publication contract](docs/SIMPLE_DEPLOY.md)
- [UI mockups](docs/mockups/README.md)

## Authorization boundary

Authority is intentionally narrow. An owner-authorized eligible application merge grants only the reviewed auto-LIVE flow for `coloring-pages-public-rpi5`. Explicit approval of one exact page or ordered page set (after activity ID and every page SHA-256/byte size are frozen) grants only its Drive staging + verified RPi5 ingest/import + public verification. Cloudflare/network, secrets/permissions, Drive archive/delete, overwrite, manual/alternate deploy and unrelated host mutations remain separately owner-gated.
