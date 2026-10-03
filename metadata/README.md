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
  "category": "rettungshunde",
  "age": "3-6",
  "difficulty": "easy",
  "language": "de",
  "thumb": "/media/fire-pup-001/thumb.webp",
  "preview": "/media/fire-pup-001/preview.webp",
  "print": "/media/fire-pup-001/source.png",
  "pdf": "/media/fire-pup-001/print.pdf"
}
```

The repository-owned `tools/coloring-pages-import` creates and validates these records. Do not commit production page JSON or production artwork here.
