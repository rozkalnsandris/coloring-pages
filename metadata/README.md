# Runtime catalogue schema reference

Production catalogue records are no longer canonical GitHub content.

The live `catalog.json` belongs to the RPi5 content store:

```text
/srv/coloring-pages-content/public/catalog.json
```

This directory documents the record shape only.

Example:

```json
{
  "id": "fire-pup-001",
  "title": "Fire Pup 001",
  "character": "",
  "category": "tiere",
  "age": "3-6",
  "difficulty": "easy",
  "language": "de",
  "thumb": "/media/fire-pup-001/thumb.webp",
  "preview": "/media/fire-pup-001/preview.webp",
  "print": "/media/fire-pup-001/print.png"
}
```

The repository-owned `tools/coloring-pages-import` creates and validates these records. Do not commit production page JSON or production artwork here.

## Categories

`metadata/categories.json` is the canonical source-level category registry.

The current V1 category IDs are:

- `tiere`
- `fahrzeuge`
- `alphabet`
- `lernen`
- `figuren`
- `jahreszeiten`

A production record must use exactly one registered category. The importer rejects unknown category IDs, and category selection must be bound before Drive staging. Future categories are added through a reviewed source change that keeps the registry and public category UI aligned.

## Published file mode

The live `public/catalog.json` must remain readable by the unprivileged nginx container. Every atomic catalogue replacement performed by repository-owned tooling must publish the replacement with mode `0644` before the final `os.replace()`.

A temporary file mode such as `0600` must never become the final published catalogue, because nginx runs as a different unprivileged UID and would return HTTP 403 for `/catalog.json`.


## Multi-page activity record

Existing one-page records remain valid. A multi-page activity adds an ordered `pages` array while keeping top-level `preview` and `print` as page-1 compatibility fields:

```json
{
  "id": "kuerbis-gesicht-001",
  "title": "Kürbis-Gesicht",
  "character": "",
  "category": "lernen",
  "age": "3-6",
  "difficulty": "easy",
  "language": "de",
  "thumb": "/media/kuerbis-gesicht-001/thumb.webp",
  "preview": "/media/kuerbis-gesicht-001/preview-1.webp",
  "print": "/media/kuerbis-gesicht-001/print-1.png",
  "pages": [
    {
      "preview": "/media/kuerbis-gesicht-001/preview-1.webp",
      "print": "/media/kuerbis-gesicht-001/print-1.png"
    },
    {
      "preview": "/media/kuerbis-gesicht-001/preview-2.webp",
      "print": "/media/kuerbis-gesicht-001/print-2.png"
    }
  ]
}
```

The order of `pages` is the print order. The detail UI lets the user switch previews and download the selected PNG; `A4 drucken` prints every page in one browser print session.
