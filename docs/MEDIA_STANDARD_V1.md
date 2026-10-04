# Coloring Pages Media Standard v1

## Purpose

Keep new coloring-page publication simple and repeatable while preserving the generated source artwork.

## Source PNG

Required:

- PNG format
- portrait orientation
- A4-like portrait ratio: native A4 (`210:297`) and standard generator `2:3` portrait output are accepted
- minimum safe source geometry: 800 px wide and 1100 px high
- white/light page background
- preserve intentional source colors; ordinary coloring pages may use black/high-contrast line art, while learning worksheets may use color
- thick, clean contours where line art is used
- large coloring regions
- minimal tiny decorative details
- no watermark
- no JPEG input
- primary age target: 3–6

The importer validates file type, portrait geometry, A4-like ratio, minimum geometry and light page corners. The accepted width/height ratio starts at `2/3` (so `1024×1536` is explicitly valid); the upper bound remains the prior A4-side tolerance of `210/297 + 0.04`. This keeps common generated `2:3` pages inside the contract without widening the gate on the opposite side. It accepts production inputs only as direct children of the pre-created content-store `inbox/`. Visual/editorial properties such as clean outlines and lack of unwanted shading remain content-review requirements.

## Original-resolution print

The source PNG is preserved byte-for-byte and is the canonical print artwork.

V1 does **not** require:

- vector tracing
- AI upscale
- a 2480×3508 source raster
- a 300 PPI conversion
- manual enlargement before import

The normal generated source is an exact `1024×1536` PNG. The PNG remains the preserved source master and the catalogue `print` PNG is the canonical browser print/download source. A minimal hidden HTML print document loads that PNG into a canvas, preserves its original pixel colors, centers it on A4 portrait geometry, uses CSS `@page { size: A4 portrait; margin: 0; }`, and calls `window.print()`. The detail page downloads the same `print.png` directly.

## Derivatives

One accepted source creates:

```text
originals/<id>/source.png    private canonical master
public/media/<id>/
├── thumb.webp               max width 400 px, lossless
├── preview.webp             max width 1000 px, lossless
└── print.png                color-preserving original-size derivative
```

The exact approved source PNG bytes are not copied into the public media directory. The public `print.png` keeps the source dimensions and visual colors without grayscale or black-line conversion. The browser uses that same PNG for A4 printing and direct download without recoloring it.

## Stable IDs

IDs must match:

```text
^[a-z0-9]+(?:-[a-z0-9]+)*$
```

Once published, an ID is immutable in V1. Duplicate IDs fail closed. Replacing existing artwork is outside this workflow and requires a separate reviewed contract.

## Public paths

For `fire-pup-001`:

```text
/media/fire-pup-001/thumb.webp
/media/fire-pup-001/preview.webp
/media/fire-pup-001/print.png
```

## Runtime

The importer executes from the immutable Coloring Pages container image under the isolation contract in `docs/IMPORTER_RUNTIME_V1.md`. Host Python/Pillow is not a V1 requirement.

## Quality principle

V1 optimizes for a clean coloring experience and a one-command content workflow. If real printer tests later show that a higher native source resolution is required, that change belongs in this single importer/media contract rather than in per-image manual procedures.

## Existing derivative correction

Already-published media URLs are immutable and must never be overwritten as the normal correction mechanism. If a historical derivative needs correction, the corrected bytes are validated against a separately reviewed exact baseline, then published under a new content-addressed filename containing the full SHA-256. Only after all new media files exist does the workflow atomically switch that catalogue entry's media URL fields. `catalog.json` is `no-cache`, so clients discover the new immutable media URLs without a CDN purge.

Normal new imports keep their existing stable filenames because those bytes are never rewritten. The content-addressed naming rule applies when an already-published immutable media identity needs replacement.

Issue #74 applies this rule to the already-regenerated `farben-zuordnen-001` bytes. The preserved private source and all non-media catalogue metadata remain unchanged, the old stable media files remain byte-identical, and only `thumb`, `preview`, and `print` URLs may switch to the new full-SHA-256 filenames. After the first persistent write, any error is a STOP with no automatic retry, rollback, cleanup, or alternate path.

The correction helper and its exact contract are embedded in the application image, but changes to those helper/contract paths do not independently trigger SIMPLE-DEPLOY. Releasing a reviewed helper revision therefore uses an existing approved application-image input such as a meaningful `Dockerfile` change; the SIMPLE-DEPLOY path allowlist is not broadened for one-off correction tooling.

## Multi-page activities

A catalogue item may contain one or more ordered A4-like PNG pages.

Single-page imports keep the existing paths unchanged:

```text
originals/<id>/source.png
public/media/<id>/thumb.webp
public/media/<id>/preview.webp
public/media/<id>/print.png
```

For an activity with multiple pages, the importer preserves page order and writes:

```text
originals/<id>/source-1.png
originals/<id>/source-2.png
...
public/media/<id>/thumb.webp
public/media/<id>/preview-1.webp
public/media/<id>/preview-2.webp
public/media/<id>/print-1.png
public/media/<id>/print-2.png
...
```

The thumbnail always comes from page 1. The catalogue keeps top-level `preview` and `print` pointing to page 1 for backward compatibility and adds an ordered `pages` array for multi-page-aware clients. The importer accepts at most 12 pages per activity and validates every page before publication.

The browser print document creates one A4 print sheet per `pages[]` item. CSS Paged Media fixes each sheet to A4 portrait and CSS Fragmentation uses `break-after: page` between sheets, so one `window.print()` action opens the normal browser/system print flow for the complete activity without introducing a PDF viewer.
