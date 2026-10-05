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
generate or edit PNG draft page(s) in ChatGPT
→ owner PUBLISH approval of the exact latest draft or ordered draft set
→ PUBLISH prepares every A4 print-master deterministically
→ PUBLISH validates every prepared print master before mutation
→ determine one valid category from metadata/categories.json
→ allocate and freeze one random seven-digit activity ID
→ freeze every prepared print-master SHA-256 + byte size
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
REMAKE           # same subject, new composition
EDIT <change>    # edit latest draft
PUBLISH           # approve latest draft/set; prepare, validate, bind and ingest
```

`UPSCALE-PRINT` and `VALIDATE-PRINT` remain optional manual inspection/debug commands. They are not required owner steps in the normal publication path because `PUBLISH` performs both gates internally before any Drive/content mutation.

See [Chat image commands v1](docs/CHAT_IMAGE_COMMANDS_V1.md). `PUBLISH` does not weaken the exact activity/page SHA-256/byte-size binding or any existing owner/runtime boundary. `OK` is not a publication command. Before Drive staging, one category must be bound from the canonical registry in `metadata/categories.json`; an unknown category is rejected rather than silently published outside the visible filters.

Multi-page activities use the production-activated [Chat-to-Drive ingestion v2](docs/CHAT_TO_DRIVE_INGESTION_V2.md) path. The shared v1/v2 host publish operator is verified at `RPi5_main@7e3e6b6d6574c1dc5199618dbb974b1fae83eaf5` with installed blob `399df72159479c405166d011f140a967bdb749a5` and newest-first importer image `sha256:53801684e0ce5a30d195d3436220a71b350112fc6e6fdc6fe107779d13c857ba`. Each activity still requires fresh exact owner `PUBLISH` approval.

Application release is a separate lane. An owner-authorized merge that changes an approved application-image input (Dockerfile, importer, nginx, HTML, CSS, JavaScript or assets) publishes an immutable GHCR image and may proceed through the existing bounded RPi5 SIMPLE-DEPLOY reconciler to LIVE automatically. Content-contract/docs/tests changes do not mint or redeploy an application image.

The application keeps the simple V1 journey:

**find → preview → print**

Multi-page activities use the same journey: one gallery item may contain an ordered `pages[]` set, the detail view switches between page previews, and one A4 print action prints the complete set. Existing one-page catalogue entries and media paths remain backward compatible.

## Media standard

See [Coloring Pages Media Standard v1](docs/MEDIA_STANDARD_V1.md).

The approved publication source artwork is preserved byte-for-byte only as the private `originals/<id>/source.png` master. For new Chat-generated publication, that source is the exact `2480×3508` portrait or `3508×2480` landscape validated print master produced by `PUBLISH` before the first Drive/content mutation; the lower-resolution generation draft is not the production master. The CPU-only preparation step uses Pillow/LANCZOS, conservative unsharp masking and exact-white normalization, with 300 DPI metadata. This resampling does not recreate missing native detail. The importer itself still performs no upscale and remains backward-compatible with its broader accepted source geometry. Published media URLs are immutable; if an existing derivative must be corrected, the corrected bytes receive new full-SHA-256 content-addressed filenames and the no-cache catalogue switches to those URLs instead of requiring a CDN purge. The importer publishes one color-preserving `print.png` derivative at the approved source dimensions as the canonical printable/downloadable file. The hidden `print.html` infers each PNG orientation and uses named CSS `@page` rules for A4 portrait (`210 × 297 mm`) or A4 landscape (`297 × 210 mm`) before calling `window.print()` without recoloring the pixels. The detail page downloads the same `print.png` directly.

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

Authority is intentionally narrow. An owner-authorized eligible application merge grants only the reviewed auto-LIVE flow for `coloring-pages-public-rpi5`. A fresh explicit `PUBLISH` approval of the exact latest draft or ordered draft set authorizes only one bounded content-publication chain; that chain must prepare and validate the print master(s), then bind the activity ID and every page SHA-256/byte size before the first Drive/content mutation, and may then perform only Drive staging + verified RPi5 ingest/import + public verification. Cloudflare/network, secrets/permissions, Drive archive/delete, overwrite, manual/alternate deploy and unrelated host mutations remain separately owner-gated.
