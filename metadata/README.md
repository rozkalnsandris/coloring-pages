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
