# Meine Drucksammlung — real-media, browser and device QA gate (#206)

Status: **PLAN / HARNESS AVAILABLE — QA NOT RUN / NOT APPROVED FOR RELEASE**. This is an evidence-gathering checklist plus a local staging harness, not a browser test result, owner approval, LIVE proof, or permission to enable output. Source now contains the reviewed visitor-click combined-print wiring and isolated print host from #425, but the canonical production gates remain fail-closed (`combinedPrint=false`, `coveredZip=false`). `Alles drucken` therefore remains visitor-disabled until the evidence below is actually collected and reviewed.

## Scope and evidence boundaries

- Track one issue: [#206](https://github.com/rozkalnsandris/coloring-pages/issues/206). Max **5 actual A4 sheets**, with complete ordered multi-page activities; use only public `/media/<id>/print*.png` paths from a fresh published `/catalog.json`. Do not read private `originals/` or substitute `preview.webp` / `thumb.webp`.
- GitHub is evidence for **source and exact-head CI**. RPi5 is canonical for **deployed content/runtime**; public HTTPS read-only results may establish the observed public response, not prove the installed RPi5 image or all LIVE services. Record both separately. Do not infer deployment from a merged PR.
- Observe public resources only through an authorized normal browser/session. Do not alter LIVE services, protected ADMIN, permissions, credentials, catalogue entries or binary originals. If host-local verification becomes necessary, stop for the exact RPi5 read authority. Avoid production instrumentation and personal data.
- CI `synthetic-a4-pdf`, `synthetic-firefox-layout` and PNG pipeline test validated generated images/DOM, not real printer output. A 375px desktop viewport does **not** prove physical phone memory capacity. No matrix row may be marked PASS based on CI alone.

## Gate 0 — freeze the tested inputs (read-only)

Record test date/time and timezone, exact `main` SHA/PR HEAD, browser + OS versions, physical device model/RAM when available, public origin, and **independently observed** deployment evidence if authorized. Record whether the product click is still disabled. A disabled click is **BLOCKED** for end-to-end visitor-print QA: do not enable it merely to finish a test.

Pick *actual published* activities that total **1, 3 and 5 physical sheets** and include a mix of portrait and landscape if the live catalogue contains those orientations. Keep `pages[]` atomic and ordered. If suitable public content is unavailable, mark the real-media case **BLOCKED**, never manufacture a production PASS from a synthetic fixture. For each selected public PNG, record catalogue ID, page position, public relative path, HTTP status/MIME/byte length, SHA-256 of downloaded bytes, intrinsic pixel dimensions and orientation. Expected print PNGs: RGB A4 **2480×3508 portrait** or **3508×2480 landscape**; no preview, private source or re-encoding.

If verifying ZIP alongside this gate, unzip locally and compare each extracted PNG SHA-256 and byte length with its recorded public print PNG, plus filename order. ZIP must preserve **exact source bytes**; printed canvas content and its footer are a separate browser-print presentation, not a modified download.

### Local real-media staging harness (source-only; never a release PASS)

For desktop staging before visitor activation, run from a trusted local checkout:

\`\`\`bash
python3 tools/print-basket-real-media-qa-server.py --origin https://ausmalwiese.de
\`\`\`

Then open the printed loopback URL (default \`http://127.0.0.1:8765/qa/\`) in the browser under test. The helper binds **only** to \`127.0.0.1\`, fetches a fresh public \`/catalog.json\` once at startup, proxies only catalogue-authorized public \`/media/.../print*.png\` paths, follows no redirects, writes no media cache to disk, and is not copied into the production Nginx image. The browser harness imports the repository's real #199/#206 session, cover renderer and print-host modules; it does not alter \`BOOK_OUTPUT_RELEASE\`.

Use **Auswahl prüfen** before a case to record public-only receipt fields for the selected artwork pages: exact checkout source SHA, browser/test environment, activity/page order, public path, HTTP/MIME, byte count, SHA-256, intrinsic A4 dimensions and orientation. This validation fetch is deliberately separate from **Druck staging** so it does not inflate the memory profile of the actual print-staging run. The generated JSON receipt uses a generic filename and deliberately excludes cover title/name.

\`ZIP staging\` and \`Druck staging\` may establish **STAGING PASS** only. They do not establish \`VISITOR PASS\`, LIVE deployment, constrained-phone memory, print-dialog pagination on another browser, or physical-paper quality. Do not change \`combinedPrint\` or \`coveredZip\` merely to complete the harness.

**Datenschutz-Canary prüfen** uses generated, non-personal cover text only in browser memory, runs the reviewed covered ZIP preparation path without exposing a download, and immediately disposes the result. Its audited fetch wrapper permits only same-origin `GET` requests with no body and records only request paths/statuses. The resulting privacy receipt checks the canary against the current page URL, cookies, `sessionStorage`, `localStorage` and newly observed `PerformanceResourceTiming` resource URLs. Before the operation, the harness requires `Performance.setResourceTimingBufferSize()` and expands the resource buffer so a full default buffer cannot silently drop the canary request; MDN documents an initial resource-timing buffer of 250 entries and explicit buffer-size management. If that preparation or any storage/performance surface is unavailable, the canary result is **BLOCKED**, not PASS. This automated check is useful evidence but **does not replace** the manual DevTools Network/Console inspection required before public privacy copy is approved.


### Loopback visitor-mode QA — production flag remains closed

The same loopback server also exposes `/qa/visitor/`. This page sets a QA-only
release override **before** importing the real production
`js/print-basket-ui.mjs`, so the normal `Hinzufügen` → `Meine Drucksammlung`
→ `Alles drucken` / covered-ZIP click wiring can be exercised with fresh public
media without changing `BOOK_OUTPUT_RELEASE`.

The override is accepted only for plain-HTTP `127.0.0.1` or `localhost`.
On `https://ausmalwiese.de` and every other host it is ignored and the canonical
production flags remain `coveredZip=false` and `combinedPrint=false`. Record
this as **VISITOR-STAGING** evidence only. It is not LIVE deployment evidence,
physical-paper proof, constrained-phone evidence or release approval.


## Gate 1 — desktop browser / print-to-file

A **separately reviewed, still gated** visitor print flow now exists in source, but production activation remains closed. Use current Chromium and Firefox on desktop, real public PNGs and the ordinary browser print dialog. While `combinedPrint=false`, the local harness above can only be marked **STAGING PASS**, never **VISITOR PASS**; do not flip the release flag as a shortcut to finish QA.

For each available 1/3/5-sheet sample:

1. From the real basket, select activities in a defined cross-category order; confirm the displayed sheet count, no duplicates, no truncated multi-page activity and no unexpected selection/storage changes.
2. Initiate print **once from one explicit user click**. Before showing a print-ready result, all PNGs must have been successfully fetched, CRC/A4 checked and decoded; any failure means zero partial sheets and an understandable German error.
3. In the print dialog or print-to-file output check **exactly** 1/3/5 pages, each **A4 210×297 mm or 297×210 mm** in the expected order and orientation. For mixed P/L sheets, inspect every page individually; do not infer support from CSS alone.
4. Check that artwork is **fully contained** (not cropped, stretched or replaced by a preview) with 15 mm side/top paper spacing. Preserve the separate **22 mm footer region**, 15 mm paper-bottom clearance and at least 2 mm artwork/footer gap from [approved print branding](AUSMALWIESE_PRINT_BRANDING_LAYOUT_V1.md). The detached #206 text-only footer must visibly say **Noch mehr Ausmalbilder?** and **ausmalwiese.de**; do not assume QR is present. See [QR gate](PRINT_QR_V1.md) for any later QR-enabled variant.
5. Close/cancel the preview and repeat; verify dialog dismissal, cancellation, no duplicate print invocation, no stale pages, and canvases/bitmap resources released. `afterprint`/preview closure is **not** proof a sheet came out of a printer.

### Browser standards and reproducibility limits (documentation rechecked 2026-10-29)

- **Named A4 pages:** MDN [`@page`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40page) describes the `page` property and named page rules, including per-page size and orientation. Support varies with browser versions and features. Capture an actual **P/L/P** or **P/L/P/L/P** print preview or print-to-file per browser; a matching CSS DOM box or `@page` declaration is not evidence that the browser generated correctly oriented paper pages.
- **Print-media emulation is CSS evidence only:** Chrome DevTools documents **Rendering → Emulate CSS media type → print**, and Firefox DevTools documents enabling \`@media print\` emulation in the Rules view. Use these to inspect hidden/visible print DOM and CSS before opening a real dialog, but record them only as layout diagnostics. They do not prove generated page count, mixed-page paper orientation, printer settings or physical output.
- **Do not substitute rotation:** MDN marks the [`page-orientation` descriptor](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40page/page-orientation) as having limited availability. Do not silently switch to `page-orientation: rotate-*` to pass mixed-A4 testing; record a failure if a target browser does not honor the selected named page `size`.
- **Chromium PDF vs Firefox:** Playwright [`page.pdf()` reference](https://playwright.dev/python/docs/api/class-page#page-pdf) describes PDF generation as Chromium-only, with CSS `@page` precedence controlled by `prefer_css_page_size`. For Chromium, record `prefer_css_page_size=True`, any scale/margins, and inspect the actual PDF `MediaBox` of *every page*. For Firefox, use its **real browser print dialog / Save to PDF or an actual printer**, not Playwright Chromium's PDF output labeled as a Firefox result. When that cannot be performed, Firefox pagination remains **BLOCKED** regardless of synthetic layout CI.
- **Print event is not print success:** MDN [`afterprint`](https://developer.mozilla.org/en-US/docs/Web/API/Window/afterprint_event) is dispatched after printing **starts** or preview **closes**. It cannot confirm printer delivery, output page count, or that the user accepted rather than cancelled. `afterprint` may be a cleanup signal, but physical printing requires separate direct observations. A repeated click must not re-use disposed canvases or double-count analytics.
- **System print settings:** Record browser print headers/footers, scale, paper and margins used for the first observation. If the system adds headers or scaling, capture **FAIL** with the observed settings; an adjusted second print is a separate case, not a retroactive PASS.

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

References: [#206 acceptance criteria](https://github.com/rozkalnsandris/coloring-pages/issues/206), [media standard](MEDIA_STANDARD_V1.md), [approved footer geometry](AUSMALWIESE_PRINT_BRANDING_LAYOUT_V1.md), [MDN `@page`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40page), [MDN printing](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Media_queries/Printing), [MDN `afterprint`](https://developer.mozilla.org/en-US/docs/Web/API/Window/afterprint_event), [Chrome DevTools print-media emulation](https://developer.chrome.com/docs/devtools/rendering/emulate-css/), [Firefox DevTools media-condition emulation](https://firefox-source-docs.mozilla.org/devtools-user/page_inspector/how_to/examine_and_edit_css/), [MDN Resource Timing](https://developer.mozilla.org/en-US/docs/Web/API/Performance_API/Resource_timing), [MDN Web Storage](https://developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API/Using_the_Web_Storage_API).
