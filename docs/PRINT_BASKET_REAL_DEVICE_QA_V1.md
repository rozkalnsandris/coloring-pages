# Meine Drucksammlung — real-media, browser and device QA gate (#206)

Status: **PLAN ONLY — NOT RUN / NOT APPROVED FOR RELEASE**. This is an evidence-gathering checklist, not a browser test result, an owner approval, or permission to deploy, enable `Alles drucken`, access RPi5, change catalogue media, or use a printer remotely. The current basket UI intentionally has a **disabled** `Alles drucken` button. The separately tested `stageCurrentBasketPrintSession()` returns **detached** A4 sheets and does not print. The final user-click integration is **not yet built**.

## Scope and evidence boundaries

- Track one issue: [#206](https://github.com/rozkalnsandris/coloring-pages/issues/206). Max **5 actual A4 sheets**, with complete ordered multi-page activities; use only public `/media/<id>/print*.png` paths from a fresh published `/catalog.json`. Do not read private `originals/` or substitute `preview.webp` / `thumb.webp`.
- GitHub is evidence for **source and exact-head CI**. RPi5 is canonical for **deployed content/runtime**; public HTTPS read-only results may establish the observed public response, not prove the installed RPi5 image or all LIVE services. Record both separately. Do not infer deployment from a merged PR.
- Observe public resources only through an authorized normal browser/session. Do not alter LIVE services, protected ADMIN, permissions, credentials, catalogue entries or binary originals. If host-local verification becomes necessary, stop for the exact RPi5 read authority. Avoid production instrumentation and personal data.
- CI `synthetic-a4-pdf`, `synthetic-firefox-layout` and PNG pipeline test validated generated images/DOM, not real printer output. A 375px desktop viewport does **not** prove physical phone memory capacity. No matrix row may be marked PASS based on CI alone.

## Gate 0 — freeze the tested inputs (read-only)

Record test date/time and timezone, exact `main` SHA/PR HEAD, browser + OS versions, physical device model/RAM when available, public origin, and **independently observed** deployment evidence if authorized. Record whether the product click is still disabled. A disabled click is **BLOCKED** for end-to-end visitor-print QA: do not enable it merely to finish a test.

Pick *actual published* activities that total **1, 3 and 5 physical sheets** and include a mix of portrait and landscape if the live catalogue contains those orientations. Keep `pages[]` atomic and ordered. If suitable public content is unavailable, mark the real-media case **BLOCKED**, never manufacture a production PASS from a synthetic fixture. For each selected public PNG, record catalogue ID, page position, public relative path, HTTP status/MIME/byte length, SHA-256 of downloaded bytes, intrinsic pixel dimensions and orientation. Expected print PNGs: RGB A4 **2480×3508 portrait** or **3508×2480 landscape**; no preview, private source or re-encoding.

If verifying ZIP alongside this gate, unzip locally and compare each extracted PNG SHA-256 and byte length with its recorded public print PNG, plus filename order. ZIP must preserve **exact source bytes**; printed canvas content and its footer are a separate browser-print presentation, not a modified download.

## Gate 1 — desktop browser / print-to-file

Once a **separately reviewed, still gated** visitor print flow exists, use current Chromium and Firefox on desktop, real public PNGs and the ordinary browser print dialog. Until then, a locally isolated staging harness can only be marked **STAGING PASS**, never **VISITOR PASS**.

For each available 1/3/5-sheet sample:

1. From the real basket, select activities in a defined cross-category order; confirm the displayed sheet count, no duplicates, no truncated multi-page activity and no unexpected selection/storage changes.
2. Initiate print **once from one explicit user click**. Before showing a print-ready result, all PNGs must have been successfully fetched, CRC/A4 checked and decoded; any failure means zero partial sheets and an understandable German error.
3. In the print dialog or print-to-file output check **exactly** 1/3/5 pages, each **A4 210×297 mm or 297×210 mm** in the expected order and orientation. For mixed P/L sheets, inspect every page individually; do not infer support from CSS alone.
4. Check that artwork is **fully contained** (not cropped, stretched or replaced by a preview) with 15 mm side/top paper spacing. Preserve the separate **22 mm footer region**, 15 mm paper-bottom clearance and at least 2 mm artwork/footer gap from [approved print branding](AUSMALWIESE_PRINT_BRANDING_LAYOUT_V1.md). The detached #206 text-only footer must visibly say **Noch mehr Ausmalbilder?** and **ausmalwiese.de**; do not assume QR is present. See [QR gate](PRINT_QR_V1.md) for any later QR-enabled variant.
5. Close/cancel the preview and repeat; verify dialog dismissal, cancellation, no duplicate print invocation, no stale pages, and canvases/bitmap resources released. `afterprint`/preview closure is **not** proof a sheet came out of a printer.

Capture local page-count + per-page orientation and visible margins (PDF inspection or redacted screenshots) without private browsing data. Browser header/footer and default scaling options can change the result: record the actual settings used; do not silently adjust output after an initial failure to manufacture PASS.

## Gate 2 — physical phones and constrained memory

Test real **Android Chrome** and **iOS Safari** where available, recording model/browser/OS and observed outcome; optionally Android Firefox. The phone must fetch public full-resolution PNGs, not just view scaled thumbnails. Test selection, ZIP and (when available) the explicit print workflow for 1, 3 and **5** sheets. Test orientation transitions, backgrounding, slow/failed network, abort, repeated use and navigation away. Record:

- Whether all 5 sheets load in order or the browser terminates/reloads, reports an out-of-memory condition or stalls.
- Peak browser memory **only if a trustworthy measurement is available**, otherwise `not measured` rather than a guess; 5 full native A4 RGBA canvases alone represent about **174 MB of raw pixel buffers**, excluding decoded images, JS, PDF generation and browser overhead.
- Time to prepare/print/ZIP with device and network conditions, successful downloadable ZIP byte equality and cleanup after cancellation/close.
- A phone's `Save as PDF` or print-share workflow only if that device/browser actually provides it; mark unavailable capabilities **BLOCKED**, not PASS.

Do **not** raise the five-sheet cap to ten from synthetic CI, desktop viewport simulation or a single fast phone.

## Gate 3 — actual non-borderless paper

With an explicitly available local printer, print at least one portrait, landscape and 3-/5-sheet mixed batch from the **visitor action** after Gate 1. Record paper setting **A4**, scale **100% / actual size**, margins, driver model/version and whether its printable area imposes extra insets. Inspect the **physical** page count, sequence, no clipped drawing or branding, 15 mm safe bands and legibility. A QR scan result applies only if the approved QR footer is actually present; otherwise verify the honest text-only fallback. Do not use page-count or PDF metadata as a substitute for physical evidence.

## Failure matrix — expected fail-closed behavior

| Scenario | Expected observed behavior |
|---|---|
| Selected activity withdrawn / changed between display and fresh catalogue | Reject whole staged print, explain recheck; no partial print |
| Missing, redirected, zero-length, malformed, CRC-invalid or wrong-size PNG | Reject whole job; do not silently replace with a preview or print subset |
| Abort, navigation, changed tab-scoped selection during await | Abort and release staged canvases; no hidden print |
| More than five sheets, including atomic two-page activities | Block addition without evicting current selection |
| Print preview cancelled or opened again | No auto-print, stale blobs/canvases or repeated analytics counts |
| Browser crashes / out of memory / unsupported named mixed page | FAIL or BLOCKED with device evidence; never mark PASS from synthetic test |

## Evidence receipt (one row per test case)

| Field | Required record |
|---|---|
| Gate + case | G0/G1/G2/G3; 1/3/5 sheets; P/L order |
| Status | `NOT RUN`, `PASS`, `FAIL` or `BLOCKED` — default NOT RUN |
| Environment | Date/time, test origin, source HEAD, browser/OS/device, printer if relevant |
| Public media | Catalogue IDs, relative PNG paths, bytes/SHA-256/dimensions (no private paths or credentials) |
| Observed outcome | Page count/orientation/margins, footer, ZIP equality, abort/cleanup, memory if measured |
| Evidence | Redacted PDF/screenshots or concise direct observations; no child photos or PII |
| Reviewer and decision | Human owner/reviewer and explicit next gate; never auto-approve LIVE or activation |

A genuinely clean release path still needs: reviewed UI wiring with the **visitor's single print click**, accessible German loading/error/cancel UX, exact-head CI/reviews, public-media and device QA evidence, separate owner MERGE authority, and the repository's bounded application LIVE gate if application inputs change. Documentation or source CI never grants permission to activate printing.

References: [#206 acceptance criteria](https://github.com/rozkalnsandris/coloring-pages/issues/206), [media standard](MEDIA_STANDARD_V1.md), [approved footer geometry](AUSMALWIESE_PRINT_BRANDING_LAYOUT_V1.md), [MDN `@page`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40page), [MDN printing](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Media_queries/Printing), [MDN `afterprint`](https://developer.mozilla.org/en-US/docs/Web/API/Window/afterprint_event).
