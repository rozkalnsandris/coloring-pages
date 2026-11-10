# Dein Name zum Ausmalen — browser-only design and acceptance gates (#204)

**Status:** reviewed-design candidate only. This document does **not** implement a public name generator, establish browser/physical QA PASS, or authorize production release. Issue #204 remains open until the visitor feature and real-device evidence exist.

## Scope and current source anchors

- One **independent single-page** personalization feature, distinct from the optional cover title in #199. Keep the rest of Ausmalwiese's `find → preview → print` path unchanged. Do not add a catalogue activity, backend service, account or production media record.
- Proposed UI: a separate semantic HTML5 `name.html` page reachable from the existing `Lernen & Basteln` discovery group. **No route or link is implemented by this design PR.**
- Existing self-hosted `Baloo 2` and `Nunito` WOFF2 are referenced in `css/fonts.css`; SIL OFL 1.1 notices exist at `assets/fonts/OFL-Baloo2.txt` and `assets/fonts/OFL-Nunito.txt`. Reuse a licensed local font, not a new remote font service or unlicensed asset. The published Latin `unicode-range` includes U+00C0–00FF, covering `Ä Ö Ü ä ö ü ß`; actual glyph drawing and chosen weight still need browser validation.
- `js/print.js` currently prints **catalogue IDs** sourced from `catalog.json`, including its own page/footer layout. Do not send a private name through `id`, a catalogue lookup, a URL parameter or an analytics event to reuse that path. Build a contained in-browser print surface for the generated page; add no public content to GitHub.

## German interface contract (draft copy)

| Element | Accessible German copy | Behavior |
| --- | --- | --- |
| Heading | `Dein Name zum Ausmalen` | Real `<h1>` and one concise explanation for parents. |
| Field | `Name eingeben` | Associated `<label>`, `autocomplete="off"`, `spellcheck="false"`, no query-bound form action. |
| Generate | `Vorschau anzeigen` | Explicit click; do not pre-generate or automatically store every keystroke. |
| Download | `Als A4-PNG speichern` | Disabled until valid preview and successful high-resolution export. |
| Print | `A4 drucken` | One user action; print the current validated artwork only, without tracking the name. |
| Clear | `Eingabe löschen` | Clear input, error, preview, object URLs and generated canvases. |
| Empty state | `Gib zuerst einen Namen ein.` | Announced in an `aria-live` / `role="status"` region. |
| Validation | `Bitte verwende nur Buchstaben, Leerzeichen oder Bindestriche.` | Visible, associated field error; do not silently strip input. |
| Oversize | `Der Name ist für eine A4-Seite zu lang.` | No truncated text, clipping or unexpected small print. |
| Technical error | `Das PNG konnte auf diesem Gerät nicht erstellt werden. Drucken bleibt möglich.` | Do not silently offer a low-quality or wrong-DPI PNG. |

One initial alphabetic profile: support Latin letters needed for German names (`A–Z a–z Ä Ö Ü ä ö ü ß`; additionally supported Latin-1 accented letters after visual checks), up to 24 code points including an optional internal single space or hyphen. Normalize NFC and trim leading/trailing whitespace; reject controls, emoji, markup, tabs/newlines, repeated separators and unsupported combining sequences. Use code-point-aware validation instead of untrusted regex interpolation into HTML. A longer input that cannot be rendered legibly must fail with a clear error, not downscale indefinitely. Review reasonable real-world names containing an apostrophe before widening validation: no claim of universal name coverage.

Only insert the name into an `input`, `textContent` and a local Canvas drawing API; **never `innerHTML`**. Keep download filenames generic (`name-a4.png`) to avoid writing a child's name into filesystem metadata.

## Rendering and PNG export contract

1. **Preview:** render a small responsive preview (for example about 620×877 pixels) with white paper and thick, closed black letter outlines. Do not allocate a full A4 bitmap on each keystroke. Use `document.fonts.load()` with the existing self-hosted font and verify the intended glyphs are available before enabling export; a silent system-font substitute is not a lettering QA PASS. Render glyph outlines with `CanvasRenderingContext2D.strokeText` plus white fill, and check holes/counters in `A`, `B`, `P`, `R`, `a`, `e`, `ß`. This is a *candidate* method, not a proven printable alphabet.
2. **Layout:** use explicit line measurements (`measureText` / ink bounds) and deterministic centered placement. Prefer one line; permit at most two clearly separated lines at a reviewed minimum physical glyph height. Do not split grapheme clusters or cut diacritics. Account for actual text ink (ascenders, descenders and umlaut dots), not just baseline width. Keep every non-white pixel inside an exact-white 15 mm / 177 px A4 edge band, and verify additional print contour/footer clearance if sharing the site's print treatment.
3. **Export:** allocate exactly `2480×3508` canvas pixels **only on the explicit PNG action**, with opaque white background and no shadows. Export via asynchronous `toBlob("image/png")`, not `toDataURL()`; immediately dispose of temporary buffers and object URLs when no longer needed. A bitmap dimension alone is **not** evidence of DPI metadata or color type. Handle allocation failure, canvas context loss and null blob without a bogus download.
4. **Validate PNG before enabling download:** inspect actual PNG bytes (signature, chunk boundaries, valid `IHDR` = 2480×3508, 8-bit RGB color type **2** with no alpha, `IDAT` and `IEND`, and valid chunk CRCs). If native `toBlob` produces RGBA color type **6**, **do not** relabel it as RGB by editing `IHDR`; implement and separately test a real color conversion/re-encode before release, or show a clear export-unavailable state. `alpha:false` is an optimization hint, not proof of an RGB PNG.
5. **DPI metadata:** MDN documents native `HTMLCanvasElement.toBlob()` output at **96 DPI** where resolution metadata is encoded. To meet the local ~300 DPI standard, build a well-formed PNG `pHYs` chunk with **11811 pixels/metre** on both axes and unit **1** (about 300 DPI); replace an existing `pHYs` only after parsing and checking original chunk ordering; calculate a new CRC32 over `pHYs` type and payload, then re-parse and independently validate the full result. Never edit a file header or byte offsets blindly. `pHYs` metadata must not disguise a wrong pixel count, RGBA raster, gray edges or clipped glyphs.
6. **Image QA:** verify every edge of the output PNG is pure `#FFFFFF`, including all 177-px safe bands; ensure strokes and optional attribution (if separately approved) fit without browser downscaling. Preserve one printable A4 page; browser headers, printer scaling and save-to-file settings can change physical output. A printed-PDF or test Canvas screenshot is not a physical-paper PASS.

The W3C PNG specification requires valid chunk ordering, per-chunk CRC and distinguishes `pHYs` physical dimensions from RGB/RGBA pixel types. References: https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/toBlob and https://www.w3.org/TR/png/ (sections 5 and 11.3.4.3).

## Privacy and failure isolation

The name and its rendered pixels remain **in process memory** only while the page is open. Do not send user input, rendered URLs, hashes or generated images to the application origin, Google Fonts, GoatCounter, Cloudflare analytics, Google Drive or other endpoints; do not include input in `location.search`, `location.hash`, `history`, error reports, logs, telemetry, browser storage, cookies or page titles. Static app fonts/scripts may be fetched by ordinary page navigation, but their request URLs contain no name. Do not call `fetch` with name data or send network beacons.

A network/privacy test must enter a distinctive **synthetic** canary name, record only sanitized request destinations (never real children's names), and assert zero canary copies in URLs, request bodies, storage and newly created resource-timing entries. Do not assert that any HTTP server *never* processes IP addresses just because the form is client-only. Ensure print can still work if PNG export is unsupported; export cannot be marked PASS on that device.

## Acceptance evidence required **before** a release PR can be READY

| Gate | Exact acceptance evidence |
| --- | --- |
| Input + accessibility | Field label/help/error association, keyboard-only use, focused errors and clear state; `aria-live` does not repeatedly announce keystrokes; empty, control characters, leading/trailing separators, long names all tested. |
| Font and language | View/export `Ä Ö Ü ä ö ü ß`, `Mia`, `Max-Paul`, `Anna Maria`, `Groß`, one 24-character edge case; record verified font family, glyph counters and diacritic placement. |
| PNG metadata/pixels | Independent decoder check for PNG + RGB 8-bit no alpha, `2480×3508`, `pHYs=11811×11811 unit=1`, valid CRCs, all-white 177px outer bands and closed dark contours; compare two decoded exports. |
| Print | Chromium and Firefox desktop print-to-PDF with inspected per-page A4 MediaBox and actual scale; iOS Safari and Android Chrome device/manual print. Confirm no crop, incorrect orientation or unexpected extra page; physical A4 print quality separately observed. |
| Mobile memory | 375px viewport *and* real constrained-phone evidence: preview, export, repeat, cancel, navigation away, OOM/context-loss recovery and resource cleanup. A desktop narrow viewport is not mobile-RAM proof. |
| Privacy | Synthetic canary with network/storage/performance observations; no name leaves process; no name-based counters, browser persistence or name in a URL. |
| Gates | Exact-head CI and reviews; explicit owner `MERGE` for any app-input change. No `PUBLISH`, RPi5/Cloudflare/permissions or production-media modification. |

**Remaining unresolved implementation gates:** actual browser code, proof that the existing self-hosted font renders all accepted glyphs, cross-browser RGB PNG encode + `pHYs` support, real-device memory/print tests, UI integration and owner review. Document/CI success cannot close #204 or imply a working public feature.

References: `AGENTS.md`, `README.md`, `css/fonts.css`, `assets/fonts/OFL-Baloo2.txt`, `assets/fonts/OFL-Nunito.txt`, `js/print.js`, `docs/MEDIA_STANDARD_V1.md`, `docs/PRINT_BASKET_REAL_DEVICE_QA_V1.md`.
