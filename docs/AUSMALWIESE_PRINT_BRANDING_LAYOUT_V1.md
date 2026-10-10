# Ausmalwiese A4 print branding — layout decision for #168

Status: **DESIGN PROPOSAL ONLY — not approved for implementation**  
Scope: **#168 print-only footer and shared QR**; #169 preview watermark is independent.

## Decision and invariants

The user-facing idea from 2026-10-10 is a discreet colored paw, **Ausmalwiese** wordmark, German tagline `Ausmalwiese – Malspaß zum Ausdrucken`, visible `ausmalwiese.de`, and the *same* optional QR on each browser-printed A4 page. There is **no diagonal watermark on the printed drawing**.

This proposal changes **no** application files, runtime media, catalogue, DNS/Cloudflare, redirect, QR artifact or print behavior. Before any code change that resizes/reflows artwork, the owner must approve an exact layout.

Non-negotiable:

- Private `source.png` and public downloadable `print.png` remain byte-identical. Do not re-encode or stamp either; PNG-only, original canonical `2480×3508` / `3508×2480` orientation and metadata remain unchanged.
- Existing 15 mm exact-white artwork-safe bands in A4 master PNGs remain unchanged.
- `preview.webp` and `thumb.webp` remain unaffected by print branding; `preview.webp` watermark is a separate #169 lane.
- Only the browser print *presentation* may contain branding; each sheet of a multi-page activity would receive the same presentation.
- No `®` unless registration is separately verified; no ad, analytics pixel or per-page tracking in print.

## Evidence: current implementation and web standards

At the inspected `main` revision `139d9d5c7faac78288d113d3013e23378e862e0b`:

1. `tools/coloring-pages-print-master` / `docs/MEDIA_STANDARD_V1.md`: art may reach exactly 15 mm from any A4 edge; that 15 mm band is inside the PNG.
2. `js/print.js`: canonical A4 canvas is rendered at exact PNG raster dimensions and appended to each `.print-sheet`; no independent footer zone exists.
3. `css/app.css`: named `@page a4-portrait` and `a4-landscape` use `margin: 0`; each sheet and canvas occupy the full `210×297` or `297×210` mm page.
4. `detail.html` / the detail UX offers a direct clean `print.png` download, distinct from browser printing.

Standards checked (read-only public docs):

- MDN, print styles / `@media print`: https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Media_queries/Printing
- MDN, named `@page` / dimensions and margins: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40page
- DENSO WAVE QR quiet zone: **four modules on every side**: https://www.qrcode.com/en/howto/code.html

**Incompatibility:** a nominal **20×20 mm QR including its quiet zone cannot be fully contained in a 15 mm bottom band**. Rendering that QR as an absolute overlay on the unaltered full-page image would potentially cover legitimate artwork and/or enter a non-borderless printer's unprintable region. This is not acceptable as a default implementation.

## Option A — text-only footer in existing safe band (no QR)

No A4 artwork reflow. Print presentation would overlay only the existing *known-white* bottom 15 mm band, using small brand lettering and URL (not the QR). A provisional layout reserves:

- 5 mm minimum from physical sheet bottom; text baseline and lettering contained within the remaining roughly 10 mm;
- x positions starting at least 15 mm from either paper edge;
- no background tint or gray strip; all branding is below the original art start;
- no changes to the canvas image, its scale, or the download.

Advantage: smallest implementation and zero artwork resizing. Trade-off: does **not** meet the 20 mm QR idea; a QR must be omitted, not silently reduced below a demonstrably scannable size. Non-borderless printer behavior still requires physical validation.

## Option B — full 20 mm QR footer with browser-only artwork reflow

This option **requires separate, explicit owner approval** before any source implementation. Keep the underlying original raster and `print.png` untouched; lay out each printed page in two *presentation* regions: a uniformly contain-scaled artwork viewport and a bottom footer. No clipping or image re-encoding is permitted.

Proposed geometries (mm, measured from page top-left):

| Measurement | A4 portrait (210×297) | A4 landscape (297×210) |
| --- | ---: | ---: |
| Side safe margins | 15 | 15 |
| Top safe margin | 15 | 15 |
| Reserved bottom region | 35 | 35 |
| Artwork viewport x range | 15–195 | 15–282 |
| Artwork viewport y range | 15–262 | 15–175 |
| Artwork viewport size | 180×247 | 267×160 |
| Footer QR x range | 175–195 | 262–282 |
| Footer QR y range | 270–290 | 183–203 |
| Bottom QR clearance | 7 | 7 |
| Vertical space from artwork viewport to QR | 8 | 8 |

The QR rectangle **includes** the four-module quiet zone, which must stay all white. Use black QR modules on white. The left-side footer lettering (colored paw + accessible dark wordmark + tagline + visible URL) fits in the horizontal span x=15 mm to x=(QR left − 6 mm); ensure at least 6 mm horizontal separation from the QR's total quiet-zone rectangle. Footer text vertically fits y=(page height − 27 mm) to y=(page height − 7 mm), with no gray band. In the preview, prevent text collisions and clipped letters.

Worst-case art extending to all four original 15 mm boundaries:

- Portrait original artwork box: 180×267 mm; proposed maximum: 180×247 mm → a uniform presentation scale as low as **247/267 ≈ 92.5%** (approximately 7.5% smaller physically).
- Landscape original artwork box: 267×180 mm; proposed maximum: 267×160 mm → **160/180 ≈ 88.9%** (approximately 11.1% smaller physically).

These are *physical print presentation* size changes even though original PNG bytes/pixel dimensions are preserved. The actual art fit should be measured per page without upscaling and must not be cropped. Do not describe this alternative as equivalent to unchanged physical artwork scale.

A5/Letter, browser scale-to-fit, print headers/footers, physical printer margins and mobile browser printing may produce further changes. They are *not* proved by a CSS mockup or unit test.

### QR routing and fallback

The agreed shared QR would encode the stable **`https://ausmalwiese.de/q`** target for all pages; this document does **not** claim that route is live or grant authority to create it. Do not deploy a QR that resolves to a missing endpoint. DNS/Cloudflare/Worker/redirect/analytics activation is a separate owner-gated task.

A future source PR must generate/ship the QR **same-origin and locally** (no third-party QR image service or user-identifying URL). No per-page/user QR tokens. If the QR asset is unavailable or the stable target is not verified, fail closed to **text-only footer** and preserve the clean PNG; never block safe print due to a branding asset failure. The existing JavaScript-required print view's ordinary error state must remain explicit; this proposal does not promise a new no-script print capability.

## Accessibility and verification requirements (future implementation, not claimed PASS)

- Keep the visible URL legible and high contrast; the colored paw is decorative, not the only means of identifying the brand. The descriptive text remains selectable/available to assistive tech in on-screen print preview.
- Use the current one-page and ordered multi-page print path; preserve page order, correct named A4 orientation and one printed sheet per `pages[]` entry.
- Test **portrait and landscape**, art touching the existing 15 mm boundary, single/multi-page (including mixed orientation), and clean direct download. Assert that source and `print.png` SHA-256/byte size and raster dimensions do not change.
- Test browser print layout with native A4 and **a realistic 5 mm non-borderless printable inset**. Inspect for browser-created extra page, automatic scaling, cut-off footer, collisions, QR quiet-zone integrity, and any crop/overlay of artwork.
- Scan the **physical** QR printed at 100% from at least one representative inkjet printer and phone camera; verify stable HTTPS redirect, readability and reasonable contrast. This test cannot be satisfied by visual inspection alone.
- Test error paths: absent/unavailable QR asset, absent/unverified `/q` target, JavaScript print failure; avoid remote QR service dependencies.
- Inspect browser support for `@page` and print margins across target browsers; do not assume all UAs honor borderless margin zero.

## Proposed gate

**Default recommendation: Option A first** (text + web address, no QR) because it does not alter drawing size or raster. The requested QR can be added only after the owner explicitly accepts **Option B's** 35 mm reserved lower band and approximately 7.5% / 11.1% worst-case physical artwork-size reduction—or chooses a third separately documented design supported by printer evidence.

Review and merge of this **design-only** document is not consent to implement Option B, activate `/q`, modify source media, publish content or deploy LIVE. Issue #168 remains incomplete until a separately reviewed implementation and required printer/scan evidence are provided.
