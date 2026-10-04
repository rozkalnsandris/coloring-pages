# Multi-page activities v1

## Goal

Support printable activities that belong together as one catalogue item but require two or more physical A4 pages, for example:

- a pumpkin base plus a separate page of cut-out eyes, noses and mouths;
- matching or cutting exercises split across pages;
- multi-sheet craft templates.

The product remains simple:

```text
one gallery card
→ one detail page
→ switch between page previews
→ one A4 drucken action
→ browser/system print dialog with all activity pages
```

## Browser print basis

The implementation intentionally stays with HTML/CSS/PNG rather than introducing a generated PDF.

Current browser standards used:

- `window.print()` opens the browser print flow;
- CSS Paged Media `@page { size: A4 portrait; margin: 0; }` defines the print sheet;
- CSS Fragmentation `break-after: page` forces each activity sheet onto the next printed page.

References:

- https://developer.mozilla.org/en-US/docs/Web/API/Window/print
- https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Paged_media
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40page/size
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/break-after

## Catalogue compatibility

A legacy one-page entry keeps:

```json
{
  "thumb": "/media/example/thumb.webp",
  "preview": "/media/example/preview.webp",
  "print": "/media/example/print.png"
}
```

A multi-page entry additionally exposes ordered `pages`:

```json
{
  "thumb": "/media/example/thumb.webp",
  "preview": "/media/example/preview-1.webp",
  "print": "/media/example/print-1.png",
  "pages": [
    {
      "preview": "/media/example/preview-1.webp",
      "print": "/media/example/print-1.png"
    },
    {
      "preview": "/media/example/preview-2.webp",
      "print": "/media/example/print-2.png"
    }
  ]
}
```

Top-level `preview` and `print` intentionally remain page-1 fallbacks so older clients degrade to the first page rather than failing.

## Importer behavior

The importer accepts one or more ordered PNG source arguments.

- one page: legacy filenames stay unchanged;
- multiple pages: private masters become `source-1.png`, `source-2.png`, ...;
- multi-page public media becomes `preview-1.webp`, `print-1.png`, ...;
- `thumb.webp` always derives from page 1;
- every page must pass the existing PNG, portrait, geometry and light-corner validation;
- maximum activity size is 12 pages;
- the page ID stays one stable activity ID.

For multi-page CLI use, `--id` is mandatory so filenames such as `<id>-1.png` do not accidentally become the catalogue ID.

## Detail UX

For one-page items nothing changes.

For multi-page items:

- show a `N Seiten` badge;
- show page thumbnails under the main preview;
- selecting a thumbnail changes the large preview;
- PNG download applies to the selected page;
- the primary print button reads `A4 drucken (N Seiten)`.

## Print fail-closed rule

The print view waits until every declared page image is loaded successfully before it signals `coloring-pages-print-ready` to the parent frame. If one page is missing, it does not silently print a partial activity.

## Publication boundary

The catalogue, importer and browser UI are multi-page-aware. `deploy/chat-to-drive-ingestion-v2.json` now defines the source-side bundle contract: ordered `<id>-<index>.png` files, exact per-page SHA-256/size binding and manifest-last readiness. The existing Chat-to-Drive v1 path remains the only production-activated publication path until a separately reviewed trusted `RPi5_main` operator implements and activates v2. Do not infer multi-page LIVE ingest authority from this source contract alone.
