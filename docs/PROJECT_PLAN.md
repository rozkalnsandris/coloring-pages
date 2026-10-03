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
- Python/Pillow host-side importer
- Docker
- `nginx-unprivileged`
- Raspberry Pi 5 runtime

No framework, CMS, database or backend API is required.

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
│   └── <page-id>/
│       └── source.png
├── public/
│   ├── catalog.json
│   └── media/
│       └── <page-id>/
│           ├── source.png
│           ├── thumb.webp
│           ├── preview.webp
│           └── print.pdf
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
- black-and-white line art on a white background
- thick, clean, high-contrast outlines
- large coloring areas
- minimal tiny details
- primary age target 3–6
- no JPEG
- no watermark
- no mandatory vectorization
- no mandatory 2480×3508 source upscale

The generated PNG is preserved byte-for-byte as `source.png`.

## One-command import

Repository tool:

```bash
python3 tools/coloring-pages-import /srv/coloring-pages-content/inbox/fire-pup-001.png
```

During LIVE installation this tool may be exposed as the convenience command `coloring-pages-import`; that host installation is outside source-only authority.

The importer may accept metadata flags, but filename-derived defaults keep the one-image path simple.

The importer:

1. validates PNG and safe A4-like portrait geometry;
2. derives/validates a stable lowercase-hyphen page ID;
3. rejects duplicate IDs;
4. preserves `originals/<page-id>/source.png`;
5. creates lossless `thumb.webp` and `preview.webp`;
6. copies the exact source PNG into the public media directory;
7. creates an A4 portrait `print.pdf` without stretching;
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
  "category": "rettungshunde",
  "age": "3-6",
  "difficulty": "easy",
  "language": "de",
  "thumb": "/media/fire-pup-001/thumb.webp",
  "preview": "/media/fire-pup-001/preview.webp",
  "print": "/media/fire-pup-001/source.png",
  "pdf": "/media/fire-pup-001/print.pdf"
}
```

The existing frontend keeps fetching `catalog.json`. New content therefore does not require an HTML/JS edit, GitHub PR, image rebuild or application redeploy.

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
- advanced analytics

## Authority boundary

The repository owns source contracts and importer code. RPi5 filesystem creation, copying images, running the importer against production content, changing Docker runtime mounts, restarting/redeploying and any Cloudflare/DNS/tunnel mutation are separate LIVE operations requiring explicit owner authorization.
