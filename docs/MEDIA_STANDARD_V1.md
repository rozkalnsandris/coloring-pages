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

Already-published derivatives are never silently rewritten by a normal import. If a historical derivative was produced under an older media transform, correction requires a separately reviewed exact-baseline regeneration contract.

Issue #71 binds one correction only for `farben-zuordnen-001`: the preserved private source size/SHA-256, exact current derivative hashes, exact catalogue entry, shared Drive-ingest lock, and only the three derivative paths are frozen before any write. The tool regenerates `thumb.webp`, `preview.webp`, and `print.png` with the current color-preserving importer functions. It must not modify `originals/farben-zuordnen-001/source.png` or `public/catalog.json`. All derivative bytes are generated and validated before the first persistent write; after the first persistent write, any error is a STOP with no automatic retry, rollback, cleanup, or alternate path.
