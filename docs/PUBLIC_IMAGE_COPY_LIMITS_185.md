# Public coloring-page copying: practical limits and recommendation (#185)

Status: **research-only source proposal**, no new technical protection or LIVE operation. Source baseline `219fd6a281d9c0c118016149cea0158ecf3f939f` (2026-10-22). The existing implementation in `docs/PREVIEW_WATERMARK_V1.md` belongs to #169 and already embeds attribution into **new** `preview.webp` derivatives. This document does not authorize another watermark or migration.

## Boundary and threat model

Public `thumb.webp` and `preview.webp` are intentionally fetchable. The public full-quality `print.png` is intentionally downloadable and printable without registration. Private `originals/<id>/source*.png` remain outside the public web root. A legitimate visitor can always save the deliberately public printable PNG; stopping them would contradict Ausmalwiese's free-print goal. Neither a UI gesture block nor an image watermark establishes copyright ownership or prevents screenshots, file copying, offline sharing, or access through browser developer tools.

Potential adversaries range from accidental uncredited sharing to deliberate scraping/rehosting. Separate these in product messaging: discourage attribution loss and commercial rehosting rather than claiming "downloads are impossible." Never claim a security control prevents extraction of public bytes.

## Options and trade-offs

| Candidate | Discouragement | Easy bypass | User/accessibility/SEO cost | Decision |
|---|---|---|---|---|
| Existing raster-baked watermark on preview-only WebP (#169) | Visible attribution on saved previews | Clean public print PNG still accessible | Low if contrast and legibility are tested; can obscure previews | **Retain** existing design for new imports; no overwrite |
| Disable `contextmenu`, `dragstart`, CSS `user-select`, pointer events or long-press | Discourages only casual actions | Direct URL, browser share/save, screenshot, devtools, network | Breaks Android long-press, screen-reader workflows, accessible drag/copy; frustrates legitimate users | **Reject** |
| CSS overlay or watermark displayed only over an `img` | Marks the browser view | Save underlying image or remove CSS | Overlay can obstruct visual/keyboard access | **Reject**; baked watermark is more honest |
| Draw preview to canvas or split image into tiles | Modestly complicates casual download | Screenshot, inspect network and canvas | More JS, memory, decoding work, accessibility loss; may hide images from crawlers | **Reject** |
| Signed URLs, gated `Referer`, session tokens or anti-hotlink rules for media | Can constrain some external embedding/bandwidth misuse | Genuine browser request reveals public data; copied printable files persist | Cache breakage, print/CDN failure, privacy state, image indexing, sharing and false positives | **Reject for free public print**; separately evaluate rate/bandwidth abuse only if supported by real evidence |
| `Content-Disposition: attachment` for images | Can influence download behavior | Direct download still works | Damages inline preview/print semantics and does not stop saving | **Reject as protection** |
| Replace preview with lower-res thumbnail | Reduces preview copying quality | Full-resolution print remains public | Makes gallery decision harder and harms accessibility/print perception | **Reject** |
| Watermark or downscale `print.png` | More visible mark in redistributed files | Screenshot or crop possible | Violates clean 300 DPI A4 print/master contract and project promise | **Forbidden** |

## Decision

1. **No new browser blocker and no media access gate.** Keep the existing browse → detail → `Drucken` and direct full-resolution PNG download. Do not obstruct right-click, touch gestures, keyboard access or assistive technologies.
2. **Keep #169 preview-only baked attribution**, on *new imports only*, without modifying `thumb.webp`, `print.png`, or private originals. The existing #169 contract describes approximately 13% alpha, broad diagonal brand text, and required representative visual checks. No global overwrite of existing media or same-URL changes is allowed.
3. Use a brief, accurate German site notice only after ordinary editorial/legal review, for example: **“Die Ausmalbilder sind zum Ausdrucken gedacht. Bitte respektiere die jeweiligen Nutzungsrechte; eine Weiterveröffentlichung ist nicht automatisch erlaubt.”** Do not assert an unverified specific license, restrict ordinary home/classroom uses unexpectedly, or imply that download equals redistribution permission.
4. Resolve provenance/rights separately: source ownership or applicable third-party licenses, permission for family/Kita use, redistribution conditions, a contact/takedown route, and a documented decision process. A watermark or no-right-click handler is not evidence of ownership.
5. No new implementation issue is necessary for the default decision. Open a small scoped follow-up only if data shows concrete hotlink/bandwidth abuse or if an authorized legal/UX review requests a notice change. No Cloudflare exception, bot rule or crawler block follows from this issue.

## Read-only browser and media regression checklist

**Android Chrome and Firefox desktop/Chromium desktop, portrait and landscape:**
- [ ] Tap and keyboard-navigate gallery, detail, print and PNG download normally; screen-reader descriptions and focus remain available.
- [ ] Save and drag a preview; attribution is actually baked into the downloaded `preview.webp` pixels for **newly imported** images, not merely layered in CSS. Existing previews may be unbranded and must not be overwritten.
- [ ] Directly open each `thumb.webp`, `preview.webp`, and `print.png` URL. No 403 or login requirement is added; correct MIME and cache headers and normal Google Images eligibility need checking.
- [ ] Check saved preview, screenshot, direct URL and network-panel behavior to confirm the technical limit: a determined user can still obtain the **public** file.
- [ ] Open single-page and ordered `pages[]` multi-page activities. Both `print.png` and `print-N.png` must be clean, not watermarked; correct ordering and portrait/landscape A4 output must survive.
- [ ] Check the prepared master remains RGB/no alpha, exact A4 (2480×3508 or 3508×2480), around 300 DPI, full 15 mm white artwork safety margin, without recompression, crop or blur from the preview attribution pipeline.
- [ ] Compare preview readability of fine letter-tracing/number worksheets and high-density drawings at mobile sizes. Check brand text isn't confused with educational worksheet instructions.
- [ ] Test with scripting disabled, slow mobile network, assistive navigation and normal image sharing where applicable; do not break direct image links or alter SEO/robots directives.
- [ ] Confirm that public `print.png` and screenshots remain practically copyable. This is expected, **not** a failed security test.

The checks above are a **future manual/read-only QA plan**, not claims of device/browser or RPi5 test execution. Actual production media and deployed image are evidenced only by authorized RPi5/public checks, not GitHub source or its CI.

## Release boundary

This work changes only this research Markdown file. It does **not** mutate importer, CSS, JS, metadata, media, Drive, DNS, Cloudflare, RPi5, existing previews, catalog IDs or live rights notices. Issue #169 remains canonical for preview attribution; do not create a second implementation or republish existing files under mutable URLs. Any new code, media migration, settings, permissions, legal text or LIVE operation requires its own exact scope and owner approval. Do not close #185 as if copy prevention had been delivered.
