# Ausmalwiese browser-print footer — issue #168

Status: **owner-approved B-DOTS print layout, source PR pending review**. Activation of the shared `/q` route is **separately owner-gated**. Related preview watermark: #169, out of scope.

## Approved appearance and exact physical coordinates

This spec supersedes the earlier Option A/B exploratory measurements. It reflects the owner's reviewed 2026-10-11 layout: use the existing colored CSS paw, **Ausmalwiese** wordmark, visible **ausmalwiese.de**, German call-to-action **Noch mehr Ausmalbilder? Einfach scannen!**, and **20 × 20 mm Dots QR without an outside frame**.

All coordinates are measured in mm from the *physical A4 top-left*, not from a mockup's blue rulers:

| Feature | A4 portrait 210 × 297 | A4 landscape 297 × 210 |
|---|---|---|
| Content horizontal extent | x=15..195 | x=15..282 |
| Printed QR bounds, **including four-module quiet zone** | x=175..195; y=262..282 | x=262..282; y=175..195 |
| Bottom and right QR clearances | 15 and 15 | 15 and 15 |
| Footer bounds | x=15..195, y=260..282 (22 mm high) | x=15..282, y=173..195 (22 mm high) |
| Gap footer top → QR top | 2 | 2 |
| Artwork viewport (contain-scaled entire clean PNG; no clipping) | x=15..195; y=15..258 | x=15..282; y=15..171 |
| Artwork viewport → footer vertical gap | 2 | 2 |

**Important:** the footer content begins no closer than 15 mm to the left edge; the first colored paw dot is aligned with the 15 mm guide. The QR code is bounded by the right/bottom 15 mm guides, not offset another 15 mm inward. The QR's blank quiet zone is **inside** the 20 mm rectangle. The footer's *content* occupies 22 mm; the sheet must reserve the 15 mm bottom clearance outside it, making the top of footer 37 mm from the physical bottom.

The print rendering may make the drawing physically smaller (especially on landscape) to fit the approved footer. It must **contain**, never crop, the entire input PNG. Do not alter the `2480×3508` / `3508×2480` source or downloadable image raster, SHA, visual colors, or DPI metadata.

## Media and code boundaries

- The source and public `print.png` remain unwatermarked, byte-identical. A clean PNG download remains clean, and original artwork is never re-encoded as a branded image.
- Branding exists only in `js/print.js` / print-specific CSS; it is not added to `preview.webp` or `thumb.webp`.
- `@page` keeps named portrait/landscape A4 pages with `margin: 0`; actual printers may impose their own scaling/nonborderless insets despite this. Do not claim physical size proof from unit tests alone.
- Footer uses the same HTML/CSS wordmark and paw palette as `index.html`, no new logo or external QR-generation service. The embedded SVG contains a single shared `https://ausmalwiese.de/q`, QR version 3 with Q error correction and a four-module quiet zone on all sides, standard square finder patterns, round body modules.
- **Fail-closed activation:** `PRINT_QR_ROUTE_VERIFIED = false` until independent authorized setup and LIVE verification of the stable `/q` redirect; only the unobtrusive text-only logo footer is enabled. This also avoids shrinking art before the QR can be used. A QR image load error falls back to text-only without blocking print.
- QR route, domain/DNS, redirect, scan analytics, and RPi5/Drive/content changes are explicitly out of this source PR's authority.

## Verification checklist and unproven conditions

Source tests must check portrait+landscape physical coordinates; multi-page wrappers and no artwork raster mutation; disabled-QR fallback; SVG source structure/quiet zone. The vector QR was independently decoded locally from a 20 mm / 300 DPI raster test, but **paper scanning remains unverified**.

Before any QR activation or eventual merge/release of QR-enabled code: verify `https://ausmalwiese.de/q` resolves over HTTPS, scan a physically printed 100% A4 Dots QR using a phone, and inspect at least one real non-borderless inkjet print including portrait/landscape and multi-page cases. Browser-generated scaling, page clipping, extra sheets, external fonts and printer-specific printable margins must be observed, not assumed.

Web standards and design references:
- MDN printing: https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Media_queries/Printing
- MDN `@page` (named pages): https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40page
- MDN `print-color-adjust` (not a printer guarantee): https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/print-color-adjust
- DENSO WAVE QR quiet zone: https://www.qrcode.com/en/howto/code.html

No PDF, existing-media overwrite, catalogue migration or LIVE action occurs in this issue.
