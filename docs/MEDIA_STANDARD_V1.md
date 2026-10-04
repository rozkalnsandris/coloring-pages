# Coloring Pages Media Standard v1

## Purpose

Keep new coloring-page publication simple and repeatable while preserving the generated source artwork.

## Source PNG

Required:

- PNG format
- portrait orientation
- A4-like portrait ratio: native A4 (`210:297`) and standard generator `2:3` portrait output are accepted
- minimum safe source geometry: 800 px wide and 1100 px high
- white background
- black/high-contrast line art
- thick, clean contours
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

The normal generated source is an exact `1024×1536` PNG. The PNG remains the preserved source master, but the browser print action does not print it directly. `print.pdf` is the browser print source. A minimal hidden HTML print document loads the single-page PDF with pinned PDF.js, renders it with print intent, and calls `window.print()`; no PDF viewer UI is shown in the normal `A4 drucken` flow.

## Derivatives

One accepted source creates:

```text
source.png
├── thumb.webp      max width 400 px, lossless
├── preview.webp    max width 1000 px, lossless
├── source.png      exact public copy
└── print.pdf       A4 portrait derivative
```

The PDF keeps the source pixels at their original resolution. When the source ratio differs from A4, the importer adds only the minimum white padding needed for an A4-ratio canvas; it does not resize or upscale the artwork. The PDF is both the downloadable print file and the browser print input; it does not replace or redefine the preserved PNG source master.

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
/media/fire-pup-001/source.png
/media/fire-pup-001/print.pdf
```

## Runtime

The importer executes from the immutable Coloring Pages container image under the isolation contract in `docs/IMPORTER_RUNTIME_V1.md`. Host Python/Pillow is not a V1 requirement.

## Quality principle

V1 optimizes for a clean coloring experience and a one-command content workflow. If real printer tests later show that a higher native source resolution is required, that change belongs in this single importer/media contract rather than in per-image manual procedures.
