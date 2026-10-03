# Coloring Pages Media Standard v1

## Purpose

Keep new coloring-page publication simple and repeatable while preserving the generated source artwork.

## Source PNG

Required:

- PNG format
- portrait orientation
- approximately A4 ratio (`210:297`)
- minimum safe source geometry: 800 px wide and 1100 px high
- white background
- black/high-contrast line art
- thick, clean contours
- large coloring regions
- minimal tiny decorative details
- no watermark
- no JPEG input
- primary age target: 3–6

The importer validates file type, portrait geometry, A4-like ratio, minimum geometry and light page corners. It accepts production inputs only as direct children of the pre-created content-store `inbox/`. Visual/editorial properties such as clean outlines and lack of unwanted shading remain content-review requirements.

## No mandatory upscale

The source PNG is preserved byte-for-byte.

V1 does **not** require:

- vector tracing
- AI upscale
- a 2480×3508 source raster
- manual conversion before import

A4/300 PPI remains a useful high-quality generation target when a generator can natively provide it, but it is not a gate for V1 content import.

## Derivatives

One accepted source creates:

```text
source.png
├── thumb.webp      max width 400 px, lossless
├── preview.webp    max width 1000 px, lossless
├── source.png      exact public copy
└── print.pdf       A4 portrait derivative
```

The PDF fits the source into an A4 portrait canvas without changing aspect ratio. This is a print derivative; it does not replace or redefine the preserved source master.

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
