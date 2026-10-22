# Dein Name zum Ausmalen — no-backend A4 PNG research and design gate (#204)

Status: **source-only implementation planning**, not a generated worksheet, working download, feature release or artwork publication. Repository baseline: `rozkalnsandris/coloring-pages@30f4e17ab971fa54ac86a9f79ceb0e30b4cd971d` (2026-10-22). The page proposed here belongs to #204, **not** the personalized book cover in #199. No existing catalogue entry is presumed to represent a visitor's name.

## Product decision and boundaries

**Conditional GO for a single local-only name worksheet** in plain HTML/CSS/vanilla JS, after offline PNG and mobile/browser acceptance. A visitor enters a short name, sees large unfilled letter contours, and can print or download **one clean A4 PNG**. No third-party text-to-image service, HTTP API, account, session persistence, child's-name analytics event, query parameter, iframe to a third party, new publication activity, or RPi5 database. All generation happens **only after user interaction, in the current browser**. The UI must not claim export quality until the exact byte-level PNG tests pass.

**Do not implement this in the existing catalogue publication path.** A private, on-demand name worksheet does not get a catalogue ID, source-master upload, derivative creation, sitemap entry or global gallery card. Do not send the name to `PUBLISH` or protected ADMIN: the canonical content-ingest workflow has separate owner/PUBLISH/hash/gate rules. Standard `detail.html` and `print.html` continue serving approved published public `print.png` assets unchanged.

## Source and font choice

The repository already includes `assets/fonts/baloo2-latin-vf-26fb4610d4bc976d.woff2` and `nunito-latin-vf-ba344451eab25b21.woff2`, referenced by `css/fonts.css`. The corresponding committed `assets/fonts/OFL-Baloo2.txt` and `assets/fonts/OFL-Nunito.txt` both state **SIL Open Font License 1.1**; no proprietary font should be introduced. The existing CSS `unicode-range` covers German `Ä/Ö/Ü/ä/ö/ü/ß`, but *that declaration is not proof that every required glyph is present and clearly outlined*. **Baloo 2 is a candidate, not yet a validated contour alphabet.**

Prefer the existing Baloo 2 file for a **proof of concept** only, rendering a white-filled glyph with `CanvasRenderingContext2D.strokeText` (black outline) after `document.fonts.load()`. The live implementation must confirm the font really loaded and that the glyphs are present, including `Ä/Ö/Ü/ä/ö/ü/ß`. Test each character both individually and in mixed names. Reject a missing glyph or unexpected system fallback rather than silently outputting boxes. Review the font silhouette at physical paper size: rounded letter contours need **wide interiors** for coloring, black strokes without double outlines or closed counters too tiny to fill. If the available font fails legibility, STOP and identify a separately vetted OFL contour font with its unmodified license and verified glyph coverage; no binary-font commit is approved by this research doc.

## Input, copy and accessibility (German)

Proposed future public heading: **“Dein Name zum Ausmalen”**. Input label: **“Name oder kurzes Wort”**. Supporting text: **“Deine Eingabe bleibt in diesem Browser. Wir speichern oder versenden sie nicht.”** This text may be published only if an implementation/network audit actually verifies it. Buttons: **“Vorschau anzeigen”**, **“Als PNG speichern”**, **“A4 drucken”**, **“Eingabe löschen”**. If font, canvas or PNG validation fails: **“Das Ausmalbild kann auf diesem Gerät gerade nicht erstellt werden. Bitte versuche es mit einem kürzeren Wort.”** Do not show a false success message or offer a broken download.

**Suggested MVP validation** (to be confirmed with German-language and accessibility review):
- Normalize user text to **Unicode NFC**, trim and collapse internal spaces. Accept only German Latin letters `A–Z a–z ÄÖÜäöüß`, a **single internal space** or hyphen between parts; reject digits, line breaks, URLs, emoji, control/bidi characters, HTML, punctuation and leading/trailing separators. This is an editorial MVP subset, not proof that other names are invalid.
- Permit **1–18 letters** in total and at most one inter-word separator. Long strings need explicit helpful error copy rather than tiny, illegible glyphs. Do not uppercase silently: verify requested mixed-case, including `ß` rather than replacing it with `B` or `SS`.
- Empty input keeps both export actions disabled and shows an accessible hint; `Eingabe löschen` removes the visible field value and in-memory rendered page. Use `autocomplete="off"`, `spellcheck="false"` and no form `action`, but note that browsers, screenshots or extensions are outside the site's complete control.
- Every input state has a real `<label>`, `aria-describedby` hint, visible keyboard focus and a polite `role="status"` region for rendering/print errors; no title-based accessibility or inaccessible canvas-only copy. Provide text equivalent `aria-label` or accompanying noncanvas preview description, without transmitting names.
- Keep the existing **gallery → detail → Drucken** navigation intact and avoid automatic printing, route/query changes or hidden telemetry. Rendering and downloading occur only on deliberate local button actions.

## A4 geometry and typography algorithm

Start with **portrait 2480×3508 pixels** and a fully opaque, exact-white `#FFFFFF` background. For a name that requires a very different layout, permit landscape **3508×2480** only after separately approved visual/browser tests; no arbitrary non-A4 dimensions. Target about **300 DPI metadata** and the existing **177 px (15 mm) exact-white safety margin** on **all four edges**. Put every antialiased glyph contour entirely *inside* this safe region, including at letter extrema and stroke width. Do not crop umlaut dots or descending glyphs. Do not use watermarks, decorative textures, faces, borders or compulsory QR inside the PNG.

Use canvas measurements from **the loaded, verified font** (`TextMetrics` widths and appropriate actual bounding boxes where available) to fit the complete name. Prefer one centered line for short text; for a validated two-part name, at most two centered lines only if each line remains large, readable and has generous vertical separation. Account for `strokeText` width and half-stroke extents, not merely `measureText().width`. Require a reviewed **minimum printed glyph height** and a fixed upper/lower bound on stroke thickness; if the longest name cannot fit, show a length/fit error rather than silently shrinking to unreadable letters. No hard split through an umlaut/combining grapheme or hyphen. The preview may be CSS-scaled **only for display**; its source for download must remain the full-resolution raster.

Actual raster pixels alone are insufficient to guarantee the downloadable print-master contract. Validation must check byte-level PNG encoding as well as visual readability. One A4 canvas is about 8.70 million pixels, and an RGBA buffer can require roughly 34.8 million bytes (**33.2 MiB**) before encoder and Blob copies. Test peak memory on budget Android devices; never rely on many simultaneous canvases. The app should render one page at a time, remove superseded Blob object URLs and handle `toBlob` returning null.

## PNG 300 DPI and RGB/no-alpha gate — REQUIRED

**Critical trap:** `canvas.toBlob(callback, "image/png")` generally encodes resolution metadata of **96 DPI**, as specified by MDN, even when the bitmap is 2480×3508. A raw Canvas PNG is therefore **not yet** Ausmalwiese's ~300-DPI master. Furthermore some encoders choose PNG color type **6 (RGBA)** even if all pixels are opaque, while the canonical print-master standard requires **RGB, no alpha** (PNG color type 2). Neither a white canvas nor `{alpha:false}` alone proves its emitted PNG color type.

A separately reviewed future client-side encoder/export helper must:

1. Receive exactly the one rendered A4 page, opaque white background and authorized validated text. Encode or convert losslessly to an **RGB 8-bit PNG, color type 2**, preserving exact pixel colors and complete `177 px` white edges. Do not merely strip a PNG's alpha channel header without correctly rewriting the entire deflated image payload. Do not pass through JPEG, WebP or a 96-DPI canvas file as the approved download.
2. Write precisely **one `pHYs` chunk** with X and Y = **11,811 pixels/metre**, unit = **1 (metre)**, yielding approximately 300 DPI; ensure valid PNG chunk ordering and recompute its **CRC-32**. A chunk may be inserted before the first `IDAT`, after `IHDR`, with full bounds/signature checking. Remove or replace any existing `pHYs` chunk; **never** allow conflicting duplicates or corrupt the `IDAT` compressed raster data.
3. Reparse the resulting bytes independently and assert PNG signature, IHDR width/height, bit depth 8, RGB color type 2, exactly one `pHYs` = 11811/11811/metre, chunk ordering/length/CRC, valid image decompression, absence of transparency, and white exact `177 px` safe bands. Roundtrip pixel checksum or compare decoded pixels to the source. STOP/disable download if a browser cannot produce a conforming file.
4. Only then permit a download using a generic sanitized filename such as `mein-name-a4.png` (**never** a child's name in filename/URL/telemetry). Release transient `Blob` URLs/arrays carefully.

A tiny pinned, audited, locally hosted library could be considered *only* if measured mobile performance proves that no smaller standards-compliant RGB encoder works. Do not add a large PNG/WebAssembly dependency or claim `CompressionStream` is universally adequate without benchmark evidence. Encoding 2480×3508 RGBA may be prohibitively expensive on some phones; the exact fallback must be a **disabled unsafe PNG download**, not silent quality degradation. It is acceptable to phase browser print before downloadable PNG **only if** the UI labels what is actually available and paper output is separately verified.

**Standards references:** [MDN `HTMLCanvasElement.toBlob()`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/toBlob) (96 DPI behavior); [PNG Specification, Second Edition](https://www.libpng.org/pub/png/spec/iso/index-object.html) (`pHYs`, `IHDR`, chunk order and CRC). These describe browser/spec contracts, **not completed Ausmalwiese tests**.

## Printing is a separate quality check

For a source-only MVP, a dedicated browser `@page { size: A4 portrait; margin: 0; }` view may print the **same locally generated image**; ensure exactly one sheet, proper sizing, no clipped contours, exact paper white/safe area and no surprise browser header/footer. Do not claim printers or drivers are identical; test Android Chrome, Firefox/Chromium desktop, mixed names and portrait/landscape in print preview and print-to-file/real paper. An A4 print preview succeeding does **not** prove the downloaded PNG's pHYs, RGB color type or actual printer resolution.

Do not add this generated private page to the existing single-activity `print.html?id=...` route: that route resolves a published catalogue ID and already has QR/footer behavior. No private name data should be put into a URL, postMessage analytics counter or catalogue lookup.

## Concrete acceptance matrix

| Test class | Minimum required cases and evidence |
| --- | --- |
| German glyphs | A/a, `Ä/ä`, `Ö/ö`, `Ü/ü`, `ß`, mixed case, `HANS`, `Mia`, one space, one hyphen; font loaded, no fallback/tofu, dots and descenders intact |
| Invalid data | Empty, 19+ letters, repeated separators, emoji, digits, HTML-like text, bidi controls, URL, line breaks and overlong Unicode; clear failure without exporting |
| Raster | Portrait **2480×3508** (optional tested landscape **3508×2480**), exactly white RGB corner and **177 px** safe band, no added marks, large legible letter interiors |
| PNG chunks | Independent parser verifies `IHDR` RGB 8-bit no alpha, `pHYs` at 11811 pixels/m on each axis, all CRC/chunk bounds, valid decoding and pixel equality |
| Client privacy | DevTools network audit: input never sent in POST/query, analytics, console, image URL, filename or retained storage; no account, cookie or server state created for name generation |
| UI/mobile | 360–412 px viewport, slow font loading, font missing, canvas allocation failure, null Blob, interrupted export, screen reader, tab order, touch sizing, refresh/clear and file URL cleanup |
| Print | Correct single A4 physical page, orientations as approved, no clipping or browser text overlays, paper margin/shape tests in Android and desktop browsers |
| Regression | Existing gallery, category/search, `detail.html`, public single/multi-page `Drucken`, direct full-resolution PNG download, fonts and SEO unaffected |

**State after this document:** implementation method and acceptance gates are specified, but **no actual font/glyph visual QA, browser-generated RGB/300-DPI PNG, live page, child-privacy audit or device print testing has been performed**.

## Follow-up gates and owner authority

Only a later, explicitly scoped source work item may add an accessible standalone page, local JS, local styles and offline PNG byte-validation tests to a branch/PR. The source-only PR can run CI and review, but must not merge without a fresh exact-head owner command. Any publication, external data handling, third-party font/image binary, new legal declaration, LIVE deploy, permission, settings or Cloudflare change needs its own gate. The standard owner `PUBLISH` contract is separate and does not apply to a visitor's locally rendered name. **This research file changes no existing application input and never triggers LIVE deploy.**
