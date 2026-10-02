# Coloring Pages — V1 Project Plan

## Goal

Build a modern, very simple children’s coloring-page website that works well on mobile and desktop.

Primary user journey:

**open → find → preview → print A4**

Planned public hostname:

`https://coloring.rozkalns.net`

The V1 target is deliberately small, static, fast, and easy to maintain.

---

## V1 technology stack

Use only:

- HTML
- CSS
- vanilla JavaScript
- JSON
- a small Python build script
- Docker
- `nginx-unprivileged`
- Raspberry Pi 5 runtime
- the existing shared Cloudflare Tunnel

Do **not** add for V1:

- Hugo
- Astro
- React / Next.js
- Node.js / npm
- Tailwind / Bootstrap
- WordPress or another CMS
- database
- backend API
- Cloudflare Workers / Pages / R2 / D1

The reason is simple: this project is a static media catalogue with search, filters, preview, download and printing. A framework or database would add maintenance without improving the core result.

---

## Architecture

```text
GitHub
│
│ source + original images + metadata
│
▼
Python build_catalog.py
│
├── validate originals
├── normalize A4 / 300 DPI
├── generate WebP thumbnails
├── generate WebP previews
├── generate printable PNG
├── generate PDF
└── generate catalog.json
│
▼
dist/
│
├── index.html
├── css/
├── js/
├── catalog.json
└── media/
│   ├── thumbnails
│   ├── previews
│   ├── print PNG
│   └── PDF
│
▼
Docker image
│
▼
nginx-unprivileged on RPi5
│
▼
existing shared cloudflared.service
│
▼
coloring.rozkalns.net
```

Cloudflare is only the public HTTPS / tunnel transport layer.

---

## Source of truth and storage

### GitHub

GitHub is the canonical source of truth.

Store:

- original master PNG files
- metadata
- HTML/CSS/JS source
- Python build tooling
- tests and deployment source

Generated WebP previews and PDFs can be produced during the build instead of being permanently committed.

### Raspberry Pi 5

RPi5 stores the deployed production copy inside the static Docker image.

For V1, do **not** create a separate `/srv/.../media` storage system. Keep deployment simple.

If the catalogue later becomes large enough that image size materially affects the repository or image deployment, media storage can be separated then.

### Google Drive

Google Drive remains an archive / backup / convenient browsing location.

```text
GitHub = canonical source
RPi5   = LIVE runtime copy
Drive  = archive / backup
```

---

## Coloring-page quality standard

Default target:

```text
Paper:         A4 portrait
Resolution:    300 DPI
Dimensions:    2480 × 3508 px
Color:         black and white
Background:    white
Outline:       thick and clean
Small details: minimal
```

Primary age group: **3–6 years**.

Design priorities:

- large coloring areas
- clear contours
- few objects
- simple shapes
- minimal tiny decorative details
- printer-friendly black-and-white output

Future difficulty levels may be:

```text
Easy       3–4
Normal     4–6
Detailed   6+
```

---

## Image pipeline

One master image produces the web and print variants:

```text
original.png
2480 × 3508 / 300 DPI
       │
       ├── thumb.webp      ~400 px
       ├── preview.webp    ~1000 px
       ├── print.png       A4 / 300 DPI
       └── print.pdf       A4
```

The gallery should never load the full 300 DPI image unless the user explicitly prints or downloads it.

This keeps mobile browsing fast.

---

## Catalogue model

The website reads one generated `catalog.json`.

Example:

```json
{
  "id": "ben-001",
  "title": "Ben hilft einem Kind",
  "character": "Ben",
  "category": "rettungshunde",
  "age": "3-6",
  "difficulty": "easy",
  "language": "de",
  "thumb": "/media/ben/001-thumb.webp",
  "preview": "/media/ben/001-preview.webp",
  "print": "/media/ben/001.png",
  "pdf": "/media/ben/001.pdf"
}
```

No database is required.

The frontend JavaScript uses this catalogue for:

- rendering cards
- search
- filters
- sorting
- detail view
- print/download actions

---

## Initial repository layout

```text
coloring-pages/
├── README.md
├── AGENTS.md
│
├── index.html
├── css/
│   └── app.css
├── js/
│   └── app.js
├── catalog.json
│
├── originals/
│   ├── rettungshunde/
│   ├── alphabet/
│   ├── tiere/
│   ├── fahrzeuge/
│   └── seasonal/
│
├── metadata/
│
├── tools/
│   └── build_catalog.py
│
├── Dockerfile
├── deploy/
│   ├── nginx.conf
│   └── docker-compose.simple.yml
│
├── tests/
└── docs/
    ├── PROJECT_PLAN.md
    └── mockups/
```

This document records the intended structure; V1 implementation files do not need to be created until implementation starts.

---

## UI principles

The site is **mobile-first**.

### Home page

Core elements:

- logo / brand header
- large search field
- category cards
- “Neue Malvorlagen”
- simple coloring-page cards
- age and difficulty badges

Expected category examples:

- Rettungshunde
- Tiere
- Fahrzeuge
- Alphabet
- Lernen
- Jahreszeiten

Mobile target:

- 2 coloring cards per row
- large touch targets
- compact category grid

Desktop target:

- wider hero section
- 4–6 coloring cards per row
- category row or grid
- generous whitespace

---

## Coloring-page detail view

The detail screen contains:

- breadcrumb
- large preview
- title
- age badge
- difficulty badge
- category badge
- character badge where applicable
- short description
- strong primary **A4 drucken** button
- PDF download
- PNG download
- short A4 / 300 DPI note

Primary action order:

1. **A4 drucken**
2. PDF herunterladen
3. PNG herunterladen

---

## Print view

The print flow should be extremely simple.

```text
detail page
↓
A4 drucken
↓
dedicated clean print view
↓
browser print dialog
```

The print view must remove navigation and unrelated UI and show only the A4 page and a print action before the browser dialog opens.

Use standard browser print support with print CSS.

---

## Search and filters

V1 filtering happens entirely in the browser.

Initial filters:

- Alter
- Thema / Kategorie
- Schwierigkeit
- Charakter

Example age values:

- 3–4
- 4–6
- 6+

Example difficulty values:

- Einfach
- Mittel
- Detailliert

No backend request is needed after `catalog.json` is loaded.

---

## Initial content categories

Start with:

- Rettungshunde
- Tiere
- Fahrzeuge
- Alphabet
- Lernen
- Jahreszeiten / Feiertage

The first complete collection can be **Rettungshunde**.

Example original characters:

- Ben — Feuerwehrhund
- Bruno — Polizeihund
- Luna — Hubschrauber-Rettung
- Nala — Wasserrettung
- Kira — Berg-/Schneerettung

---

## IP / content rule

The public site should publish original characters and original illustrations.

Generic roles and themes are fine, for example:

- police puppy
- firefighter puppy
- construction puppy
- water rescue puppy
- helicopter rescue puppy

Do not build the public catalogue around direct copies of protected branded characters.

---

## RPi5 deployment pattern

Use the same lightweight static-container pattern already proven elsewhere in the home infrastructure:

```text
static build
↓
nginxinc/nginx-unprivileged
↓
read-only runtime
↓
no-new-privileges
↓
health endpoint
↓
ready endpoint
```

Application runtime should stay simple and stateless.

---

## Cloudflare / ingress target

Planned future public service:

```text
service_id:       coloring-pages
hostname:         coloring.rozkalns.net
zone:             PUBLIC
origin:           loopback
Cloudflare Access: NONE
LAN exposure:     NONE
runtime owner:    RPi5_main
repository owner: coloring-pages
```

Cloudflare / tunnel / RPi5 LIVE changes are separate deployment actions and are **not** implied by source work or a repository merge.

---

## Content workflow

Typical new-page flow:

```text
generate image
↓
normalize A4 / 300 DPI
↓
add metadata
↓
GitHub branch
↓
build_catalog.py
↓
generate thumbnail / preview / PDF
↓
tests
↓
PR
↓
review
↓
merge after explicit authorization
↓
separate RPi5 deploy
```

Normal source changes should use GitHub. RPi5-local tooling is only for LIVE/runtime work when required.

---

## V1 intentionally excludes

Do not add yet:

- accounts
- login
- favorites
- ratings
- comments
- CMS
- browser uploads
- on-site AI generator
- database
- ads
- advanced analytics

The V1 product should do one thing very well:

> **find → preview → print**

---

## Current status

Planning and UI mockups only.

Not yet implemented:

- production HTML/CSS/JS
- catalogue build pipeline
- Docker image
- RPi5 deployment
- Cloudflare hostname / tunnel route
- LIVE site
