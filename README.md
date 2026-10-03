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
generate PNG in ChatGPT
→ owner approves exact image
→ stage exact PNG + SHA-256 manifest in Google Drive
→ trusted RPi5 operator pulls and verifies it
→ atomically publish verified PNG into /srv/coloring-pages-content/inbox/
→ run coloring-pages-import
→ verify catalogue, derivatives and public URLs
```

This path is production-activated. The first owner-authorized end-to-end import passed on 2026-10-03. That activation record is historical continuity only: each future content import remains separately owner-authorized and exact-ID/hash/size bound.

The application keeps the simple V1 journey:

**find → preview → print**

## Media standard

See [Coloring Pages Media Standard v1](docs/MEDIA_STANDARD_V1.md).

The source artwork is preserved as the generated PNG. V1 does not require vector tracing or a mandatory 2480×3508 upscale. The importer creates lightweight WebP browsing derivatives and an A4 portrait PDF. The importer runtime is embedded in the immutable Coloring Pages image, so the RPi5 host does not need Python/Pillow installed.

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
- [SIMPLE-DEPLOY publication contract](docs/SIMPLE_DEPLOY.md)
- [UI mockups](docs/mockups/README.md)

## Authorization boundary

GitHub source work, merge, Drive staging, RPi5 content-store mutation, application deployment and public ingress are separate authority boundaries. A source merge never authorizes a Drive upload, content import or any other LIVE mutation.
