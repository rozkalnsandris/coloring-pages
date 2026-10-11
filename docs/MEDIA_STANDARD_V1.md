# Coloring Pages Media Standard v1

## Purpose

Keep new coloring-page publication simple and repeatable while preserving the generated source artwork.

## Source PNG

Required:

- PNG format
- portrait or landscape orientation
- A4-like ratio in either orientation: native A4 (`210:297` / `297:210`) and standard generator `2:3` / `3:2` outputs are accepted
- minimum safe source geometry: short side at least 800 px and long side at least 1100 px
- white/light page background
- preserve intentional source colors; ordinary coloring pages may use black/high-contrast line art, while learning worksheets may use color
- thick, clean contours where line art is used
- large coloring regions
- minimal tiny decorative details
- no watermark
- no JPEG input
- primary age target: 3–6

The importer validates file type, portrait/landscape geometry, A4-like ratio, minimum geometry and light page corners. Ratio validation is orientation-neutral: it compares the short side with the long side. The accepted short/long ratio starts at `2/3` (so both `1024×1536` and `1536×1024` are explicitly valid); the upper bound remains the A4-side tolerance of `210/297 + 0.04`. It accepts production inputs only as direct children of the pre-created content-store `inbox/`. Visual/editorial properties such as clean outlines and lack of unwanted shading remain content-review requirements.

## Chat publication print master

For new Chat-generated publication, the generation PNG is a draft. The normal owner flow is one publication command:

```text
MAKE / REMAKE / EDIT
→ PUBLISH
```

`PUBLISH` internally runs the mandatory print-master preparation and read-only validation before any Drive/content mutation. `UPSCALE-PRINT` and `VALIDATE-PRINT` remain optional manual inspection/debug commands only.

`UPSCALE-PRINT` uses the repository helper `tools/coloring-pages-print-master prepare`. It is deliberately CPU-only and depends only on the pinned Pillow build dependency already used by CI. It does not generate new artwork or use an AI/GPU upscaler.

The prepared publication master must be:

- PNG;
- exact `2480×3508` portrait or `3508×2480` landscape A4 raster, matching source orientation;
- RGB with no alpha;
- approximately 300×300 DPI metadata;
- exact `#FFFFFF` around the complete outer page border;
- a reserved 15 mm exact-white artwork-safe margin on every edge (`177 px` at 300 DPI): artwork is proportionally fitted inside that safe area before centering; the existing 1 px exact-white outer-border validation remains included inside this wider margin;
- aspect-ratio-preserving artwork centered on the A4 canvas;
- near-neutral white AI noise normalized to exact white;
- resized with Pillow `Resampling.LANCZOS`;
- sharpened only with the reviewed conservative `UnsharpMask` values in the helper.

The validator is read-only and fails closed if any required property is missing. During normal publication, `PUBLISH` runs it automatically after preparing the fresh print master and binds the reported exact SHA-256 and byte size before the first content mutation. `REMAKE` or `EDIT` invalidates any earlier manually prepared/validated master; the next `PUBLISH` prepares and validates again automatically.

This is resampling, not native-detail recovery. It improves the consistency of A4 raster delivery and background white while avoiding per-image API/GPU dependencies.

The importer remains backward-compatible with the broader geometry above and does not perform this authoring upscale itself.

## Original-resolution print

The source PNG is preserved byte-for-byte and is the canonical print artwork.

The importer itself does **not** require vector tracing, AI/GPU upscale or host-side enlargement. For the Chat publication path, `PUBLISH` derives and validates the owner-approved `2480×3508` portrait or `3508×2480` landscape PNG print master before any content mutation. The lower-resolution `1024×1536` / `1536×1024` generation draft is an authoring input, not the production source master.

The validated print-master PNG remains the preserved source master and the catalogue `print` PNG is the canonical browser print/download source. A minimal hidden HTML print document loads that PNG into a canvas, preserves canonical `2480×3508` / `3508×2480` raster dimensions exactly, uses the previous A4-padding calculation only for legacy/non-canonical rasters, preserves original pixel colors, infers portrait/landscape from dimensions, assigns the matching named CSS page, and prints it as A4 portrait or A4 landscape before calling `window.print()`. The detail page downloads the same `print.png` directly.

## Derivatives

One accepted source creates:

```text
originals/<id>/source.png    private canonical master
public/media/<id>/
├── thumb.webp               max width 400 px, lossless
├── preview.webp             max width 1000 px, lossless; diagonal Ausmalwiese watermark (new imports)
└── print.png                color-preserving original-size derivative
```

The exact approved source PNG bytes are not copied into the public media directory. The public `print.png` keeps the source dimensions and visual colors without grayscale or black-line conversion. The importer composites transparency onto white paper, writes the public print derivative as opaque RGB, and preserves valid source DPI metadata when present; therefore a canonical Chat print master keeps its approximately 300 DPI metadata in the public print PNG. The browser uses that same PNG for A4 printing and direct download without recoloring it.

New imports bake a discreet diagonal attribution watermark **only** into preview derivative pixels, never into `thumb.webp`, `print.png` or the private source. Preview-only source behavior and the immutable historical migration gate are described in [Preview watermark v1](PREVIEW_WATERMARK_V1.md). Existing published previews are not rewritten by this source change.

## Stable IDs

The importer remains backward-compatible with historical IDs matching:

```text
^[a-z0-9]+(?:-[a-z0-9]+)*$
```

New Chat publications use the opaque random seven-digit policy in `metadata/id-policy.json`:

```text
NNNNNNN
```

Examples: `0427183`, `9676349`.

Each activity ID is allocated independently as exactly seven decimal digits (`0000000`–`9999999`). Allocation is random with a fresh LIVE-catalog collision check; there is no shared sequence and no highest-ID scan. Type, topic, title and category never determine the ID.

Before the first content mutation, the candidate must be absent from the fresh LIVE catalogue and distinct from any other candidate in the same local publish batch. A pre-mutation collision is handled by generating another random candidate. Exhaustion is a STOP.

Existing legacy IDs stay accepted and immutable. They are never renamed and do not participate in new-ID allocation.

Once published, every ID is immutable in V1. Duplicate IDs fail closed. Replacing existing artwork is outside this workflow and requires a separate reviewed contract.

## Public paths

For `0427183`:

```text
/media/0427183/thumb.webp
/media/0427183/preview.webp
/media/0427183/print.png
```

## Runtime

The importer executes from the immutable Coloring Pages container image under the isolation contract in `docs/IMPORTER_RUNTIME_V1.md`. Host Python/Pillow is not a V1 requirement.

## Quality principle

V1 optimizes for a clean coloring experience and a deterministic publication workflow. The tested CPU/Pillow print-master step standardizes Chat-generated pages before publication without changing the importer/runtime trust boundary. If printer tests later show that interpolation is insufficient and a higher native generation resolution is required, that change belongs in this media/authoring contract rather than in per-image ad-hoc procedures.

## Existing derivative correction

Already-published media URLs are immutable and must never be overwritten as the normal correction mechanism. If a historical derivative needs correction, the corrected bytes are validated against a separately reviewed exact baseline, then published under a new content-addressed filename containing the full SHA-256. Only after all new media files exist does the workflow atomically switch that catalogue entry's media URL fields. `catalog.json` is `no-cache`, so clients discover the new immutable media URLs without a CDN purge.

Normal new imports keep their existing stable filenames because those bytes are never rewritten. The content-addressed naming rule applies when an already-published immutable media identity needs replacement.

Issue #74 applies this rule to the already-regenerated `farben-zuordnen-001` bytes. The preserved private source and all non-media catalogue metadata remain unchanged, the old stable media files remain byte-identical, and only `thumb`, `preview`, and `print` URLs may switch to the new full-SHA-256 filenames. After the first persistent write, any error is a STOP with no automatic retry, rollback, cleanup, or alternate path.

The correction helper and its exact contract are embedded in the application image, but changes to those helper/contract paths do not independently trigger SIMPLE-DEPLOY. Releasing a reviewed helper revision therefore uses an existing approved application-image input such as a meaningful `Dockerfile` change; the SIMPLE-DEPLOY path allowlist is not broadened for one-off correction tooling.

## Retired one-time A4 print migrations

The frozen historical print-scale and 15 mm safe-margin migration programs have been retired from the current application image. Their exact-baseline source contracts and tests remain available in Git history for audit, but must not be treated as tools for ordinary publication or reusable LIVE authority.

All new pages use the current deterministic `coloring-pages-print-master` and `coloring-pages-import` path. Any future correction to already-published media needs a separately reviewed exact baseline and immutable full-SHA-256 content-addressed URLs; private originals and existing public media bytes must never be overwritten in place. See **Existing derivative correction** above.

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

The browser print document creates one A4 print sheet per `pages[]` item. Each sheet infers orientation from its print PNG and selects a named `@page` rule for A4 portrait or A4 landscape; CSS Fragmentation uses `break-after: page` between sheets. Mixed-orientation multi-page activities therefore remain printable through one normal browser/system `window.print()` flow without introducing a PDF viewer.
