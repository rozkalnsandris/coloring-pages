# coloring-pages

Static, mobile-first coloring-page catalogue for `coloring.rozkalns.net`.

## V1 content model

Application source and media content are deliberately separated:

- **GitHub** is canonical for HTML/CSS/JavaScript, importer/tooling, schemas, tests, Docker/nginx source and operational documentation.
- **RPi5 content store** is canonical for coloring-page PNG originals, generated web/print derivatives and the live `catalog.json`.
- Production coloring-page image binaries are **not committed to GitHub**.

Daily content flow:

```text
generate PNG
→ copy to /srv/coloring-pages-content/inbox/
→ run coloring-pages-import
→ catalogue entry becomes visible
```

The application keeps the simple V1 journey:

**find → preview → print**

## Media standard

See [Coloring Pages Media Standard v1](docs/MEDIA_STANDARD_V1.md).

The source artwork is preserved as the generated PNG. V1 does not require vector tracing or a mandatory 2480×3508 upscale. The importer creates lightweight WebP browsing derivatives and an A4 portrait PDF.

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

Only `public/` is mounted into the nginx container, read-only. `inbox/`, `originals/` and `state/` remain host-side and are not web-served.

## Project documents

- [V1 project plan](docs/PROJECT_PLAN.md)
- [Media Standard v1](docs/MEDIA_STANDARD_V1.md)
- [SIMPLE-DEPLOY publication contract](docs/SIMPLE_DEPLOY.md)
- [UI mockups](docs/mockups/README.md)

## Authorization boundary

GitHub source work, merge, application deployment, RPi5 content-store mutation and public ingress are separate authority boundaries. A source merge never authorizes content import or any LIVE mutation.
