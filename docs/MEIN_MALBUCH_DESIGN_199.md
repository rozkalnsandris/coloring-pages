# Mein Malbuch erstellen — shared print/ZIP product design (#199)

Status: **GitHub-only product/implementation plan; no live book builder, child-name intake, new print page or ZIP is created here**. Source baseline: `coloring-pages@caba3d31c7662cfd0f40c9c8a6125748c9f6fb48` (2026-10-22). Research in #199 includes a 2026-10-12 TinyFish competitor observation; it is a design reference, **not** proof of exported competitor PDF contents or permission to copy its interface/artwork.

## Decision: phase behind the shared five-sheet basket

**GO for a future free, optional "Mein Malbuch" cover/preview extension to the common selection infrastructure from #206; NO-GO for a parallel basket, parallel archive builder, instant 10-activity download or a PDF generator.**

1. **Dependency stage: #206.** First deliver and manually validate the reusable **cross-category selection and printing model**, initially **five total physical A4 sheets**, including the entire ordered `pages[]` for each selected activity. In #206 there is **no cover**; its five-sheet limit stands. Each activity remains atomic. The source issue #206 is already detailed: do not duplicate it with an independent book basket.
2. **Book stage: #199.** Add **an optional one-sheet A4 cover** and a simple ordered book-preview experience to the *same* reviewed selector and export functions. For the initial book rollout, the cover consumes **one of the five sheet slots**; a selected two-sheet activity still consumes two slots. A coverless collection may use all five sheets; a book with cover has **at most four remaining print sheets**, possibly from fewer than four activities. Display the count as `X von 5 Druckseiten`, not `X Motive`.
3. **Growth stage, gated.** Increase to up to **ten total physical sheets including cover** only after evidence from constrained-memory Android, desktop Firefox/Chromium, realistic maximum PNG bytes, ZIP-store export integrity, preview memory use, orientation and real print testing. The competitor's ten-motif limit is not an Ausmalwiese performance result.
4. Fixed editorial 10-sheet sets in merged #197 are **different**: they may eventually use a **trusted offline, immutable publisher ZIP** of approved public print assets. They do not use the per-visitor browser export. Kita #203 describes a **six-sheet** editorial concept; it cannot fit unchanged into the first five-sheet visitor basket. A later Kita set needs its own bound and review, not silent dropping of a Cut & Paste cutout page.

The present site `js/print.js` renders **one catalogue activity** selected via `?id=` and expands that activity's `pages[].print` or top-level `print`. **It does not combine multiple IDs**. The existing `print.html` is not evidence that a book print job or multi-item ZIP already works.

## Minimal user journey (German, proposed copy)

```text
1. Motive wählen
   [Suche] [Kategorie] [Karte] [+ Hinzufügen]
   Meine Drucksammlung: 3 von 5 Druckseiten

2. Mein Malbuch gestalten             [optional after #206]
   [ ] Deckblatt hinzufügen           (counts as one Druckseite)
   Titel auf dem Deckblatt (optional): [Mein Ausmalbuch]
   Name auf dem Deckblatt (optional):  [              ]
   Deine Eingaben bleiben in diesem Browser.
   Ausgewählte Motive:
   [Vorschau] [Nach oben] [Nach unten] [Entfernen]
   4 von 5 Druckseiten (1 Deckblatt + 3 Ausmalseiten)

3. Vorschau und Ausgabe
   Seite 1 von 4 [Zurück] [Weiter]
   [Alles drucken] [Als ZIP speichern]
   Hinweis: Jede Druckseite ist ein A4-Blatt.
```

Actual navigation should be a small mobile-first, accessible page or panel using **semantic HTML, plain CSS and vanilla JS**. Keep the normal gallery→detail→`Drucken` path fully available for all visitors, including people who never use book creation. The cover and user-input fields must not be required merely to print selected pages. Do not automatically open a print dialog, save ZIP, or submit data as selection changes.

Recommended labels and states:
- Add/remove in cards: **“Zur Drucksammlung hinzufügen”**, **“Aus Drucksammlung entfernen”**, selected status **“In deiner Drucksammlung”**.
- Book entry point (after common selector works): **“Mein Malbuch gestalten”**.
- Zero items: **“Noch keine Druckseiten ausgewählt.”** and link **“Malvorlagen entdecken”**.
- Over limit: **“Maximal 5 A4-Druckseiten. Diese Malvorlage passt nicht mehr in deine Auswahl.”** Do not remove old choices when rejecting a new one.
- Removed/unavailable activity: **“Eine Malvorlage ist nicht mehr verfügbar und wurde aus deiner Auswahl entfernt.”** Update the visible count; user reviews changed list before export.
- Before download: **“Die A4-PNGs werden vorbereitet. Bitte schließe die Seite nicht.”** When the actual export is not verified, the corresponding button stays disabled; do not show deceptive "Fertig".
- Failure/cancel: **“Der Download konnte nicht fertiggestellt werden. Deine Auswahl bleibt erhalten.”** A new attempt starts only on a fresh visitor action.
- Clear selection: **“Auswahl leeren”** with a deliberate action; no surprise reset when another category is opened.

## Data semantics — activity IDs, actual sheets and cover

Define a shared **selection model** owned by #206; #199 *uses* it and adds only transient cover settings:

```js
// Illustrative shape, NOT a running production API:
{
  activityIds: ["<existing-published-id-A>", "<existing-published-id-B>"],
  cover: {
    enabled: false,
    title: "Mein Ausmalbuch",
    name: ""
  }
}
```

The IDs above are placeholders, not real published items. `activityIds` must contain **distinct, ordered, currently published catalogue IDs**, not arbitrary URL strings. They may be held tab-locally in `sessionStorage` per #206, subject to privacy review, with revalidation against the current public catalogue on each page visit and immediately before each export. **Never persist the cover title or name**, not even in sessionStorage, URL fragments, query parameters, localStorage, analytics, exception logs, service-worker caches, filenames or a backend request. Keep cover fields in in-memory UI state and clear on reload or “Entwurf löschen”. Any UX promising that the name survives tab navigation must be explicitly dropped or designed without retaining a name.

`expandActivity(entry)` must reject invalid/unpublished records. For `pages[]`, expand **all** ordered pages only when *every* required public `print` path exists. For legacy records without `pages[]`, accept the canonical top-level `print`. Zero, missing or partial pages mean the whole activity cannot be selected/exported; never truncate a two-page Cut & Paste to one sheet. All file URLs come from validated catalogue entries, not from user-supplied names or arbitrary paths. The sum of those **physical sheet counts** plus `cover.enabled ? 1 : 0` is the **only count** compared to the configured limit.

Operations `add`, `remove`, `reorder`, `clear`, `toggleCover` are **idempotent or explicit**. Reordering affects activity blocks only; never detaches page 2 from page 1 of a multi-page activity. If enabling the optional cover would cross the five-sheet limit, reject the cover operation with a clear message and retain the original selection, rather than silently removing a drawing. Distinguish *number of motifs (activities)* from *A4-Druckseiten* in all counters, print messages and ZIP contents.

## Cover, lettering and privacy

The cover is optional: default title **“Mein Ausmalbuch”**, optional short first-name text. No title/name goes to a service or becomes a public catalogue entry. A simple large typographic cover on exact-white A4 can use existing locally served licensed fonts if their German characters and embedding/rendering are verified; no stock clipart or external font CDN. Never add children's real names to metadata, a public feed, log, QR destination, filename or metrics.

Reuse any separately verified high-resolution local lettering/rendering work from #204, but **do not infer it is implemented** because `docs/NAME_COLORING_PAGE_RESEARCH_204.md` was merged. A browser `Canvas.toBlob("image/png")` usually encodes **96 DPI metadata** and sometimes RGBA; it is **not** automatically the publication-quality RGB ≈300 DPI cover PNG. To place a cover in the downloadable ZIP, separately validate its exact A4 raster **2480×3508 portrait**, **15 mm (177 px) white margin**, **RGB no alpha**, and a valid PNG **`pHYs` ≈300 DPI**, plus legible glyphs. Use the same cover PNG bytes in ZIP and print if practical. If the cover is not yet conformant, **disable the covered-book ZIP export**; a print-only cover may be offered only after its own physical print testing with clear status, and must not be misrepresented as a conformant exported A4 master.

For normal catalogue artworks, ZIP/print must use **existing full-quality public `print.png` or ordered `pages[].print`** byte-for-byte. Watermarked `preview.webp` and low-resolution `thumb.webp` are only for selection thumbnails. Never copy private `originals/<id>/source.png`, resample print PNGs for ZIP, serialize names into ZIP filenames, auto-upload user text or create a new public `PUBLISH` activity.

The sentence **“Deine Eingaben bleiben in diesem Browser.”** can appear publicly only once a real DevTools/network/log audit confirms it for the implemented feature. Browser extensions and screenshots remain outside the site's complete control; do not promise absolute secrecy.

## Shared printing and ZIP — no duplicate exporter

A future common export layer belongs to #206:

- **Print:** validate that every selected public full-resolution print PNG loads before activating the final explicit `window.print()`; expand each activity atomically; compose in visitor-specified activity order and internal page order. Apply one A4 page per source sheet and one cover sheet if enabled, with correct mixed portrait/landscape handling. Verify branding/QR footer conventions and do not silently increment existing Print/Trending rankings per sheet. One visitor click is one basket-print intent, subject to existing approved privacy and statistics semantics.
- **ZIP:** use one audited and pinned **client-side ZIP STORE** implementation (if measurements allow) and byte-for-byte unchanged public print PNG members. Names must be deterministic, numbered, path-safe, based on verified catalogue IDs and page ordinal, e.g. `01-1234567-01.png`. The optional cover may use a generic `00-deckblatt.png`; its content can hold locally rendered title/name but **its filename never does**. Reject ZIP slip, extra members, duplicate names, missing/mixed files, partial Blob creation, invalid PNG and wrong order.
- **Memory:** downloading multiple ≈8.7-megapixel PNGs can incur simultaneous byte buffers, decoded bitmaps, canvas surfaces and ZIP Blob copies. Use a small bounded concurrency and test 5-sheet worst-case on Android; don't decode every PNG solely to package bytes. Abort/cancel must release Blob URLs, arrays, image bitmaps and pending requests; refuse an export that exceeds measured safe memory rather than crashing.
- **One failure = honest failure:** if one selected public page is unavailable, its bytes fail validation, or the mobile browser refuses the download, do not publish/claim a complete ZIP or trigger a partial multi-sheet print. Keep selection and show actionable retry-on-click message. The user must actively re-trigger a retry. No server fallback, external converter, or hidden copy of children's input.

**No PDF in the initial book feature.** A competitor displaying PDF downloads does not override Ausmalwiese's PNG-only original/print export policy, and a PDF generator would require separate quality, legal, performance, release and scope approval.

## Acceptance matrix before real implementation

| Test | Expected evidence |
| --- | --- |
| Count math | Single-page activity = 1 sheet, two-page activity = 2; multi-page atomic; optional cover = +1; 5-sheet ceiling, explicit reject on 6; later 10-sheet limit blocked without benchmarks |
| Navigation | Gallery search and category selection retained between pages using only ID state; preview route, keyboard buttons and existing one-activity printing unchanged |
| Ordering | Reordering swaps activity **blocks**, never reorders their inner `pages[]`; ZIP filenames and print pages reflect the same visible order |
| Catalogue freshness | Revalidate IDs before action; missing/unpublished/malformed/duplicate IDs handled without silent substitution; avoid arbitrary media URL strings |
| Cover language | Empty title/name, long title, German **Ä Ö Ü ä ö ü ß**, two-part names, overflow, baseline, no clipping, no tiny text at actual A4 paper size |
| Cover export | Independently parse/download PNG, assert 2480×3508, RGB, no alpha, pHYs ≈300 DPI, 177 px exact-white safe frame and no pixel degradation |
| Print | One explicitly triggered print job with exactly one A4 sheet per item, optional cover, landscape/portrait and QR/footer handling in Chrome Android, Firefox/Chromium desktop and paper/PDF print-to-file QA |
| ZIP | Verify member order and safe names, ZIP STORE source-byte SHA-256 equality, all expected members and no extra files, extraction, corruption/truncated-file rejection |
| Mobile & abort | Budget Android 360–412 px, slow/offline PNG, 0-byte responses, missing font, disabled storage, cancel/reload, excessive size, memory/Blob cleanup; never claim success on failure |
| Privacy & safety | No name/title in network requests, URLs, console, filenames, analytics, cookies or storage, no user upload or public content indexing; accessible descriptions/focus/live status |
| UI regression | Existing semantic search, category filters, detail view, standalone clean A4 `Drucken`, multi-page cut-and-paste, local fonts and SEO unaffected |

Checks in this section are **proposed**, not executed by this documentation work. No user-visible "Alles drucken" or "Als ZIP speichern" button may be enabled merely because this source research is merged.

## Authorization and next gates

1. **#206 first**: a separately frozen implementation PR for shared catalogue-ID selection, five-sheet validations, cross-activity print/ZIP and real device QA. Await review, exact-head CI and explicit owner merge; application JS/HTML/CSS merges can enter the repo's *bounded reviewed app deploy* path, which must be verified independently. No merge is authorized by this research.
2. **#199 second**: separate targeted source PR for optional cover/preview and integration with #206's tested exporter. No parallel packer or second cart; optionally reuse #204's validated local name font/PNG encoder. Review before enabling cover ZIP.
3. **#197 editorial and #203 Kita**: reuse the same catalogue semantics but respect their own static ZIP publishing and six-sheet educational constraints. Nothing here approves Drive staging, RPi5 content import, media overwrites or actual public ZIP hosting.
4. Any secrets, permissions, settings, analytics identity, external posting, PDF, LIVE outside the bounded app workflow, Cloudflare or private data collection requires separately scoped explicit owner authorization and verified access.

**Outcome of this document:** selection/count/export/privacy decisions and test gates are prepared for review, not deployed. Leave #199 open until an actual functional and verified feature exists.
