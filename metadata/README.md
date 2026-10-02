# Catalogue metadata

This directory is the canonical source for coloring-page catalogue records.

Store one JSON object per coloring page. Generated `dist/catalog.json` is derived from these files and must not be edited by hand.

## Required fields

```json
{
  "id": "ben-001",
  "title": "Ben hilft bei der Feuerwehr",
  "character": "Ben",
  "category": "rettungshunde",
  "age": "3-6",
  "difficulty": "easy",
  "language": "de",
  "original": "originals/rettungshunde/ben-001.png"
}
```

Rules:

- `id` must be unique and use lowercase letters, digits and hyphens.
- `age` must be one of `3-6`, `4-8`.
- `difficulty` must be one of `easy`, `normal`, `detailed`.
- `language` is currently `de`.
- `original` must be a repository-relative path below `originals/`.
- The referenced original must exist before the catalogue build succeeds.
- Web/print derivative URLs are generated deterministically from `id`; do not duplicate them in metadata.

Current pipeline scope is catalogue validation + `dist/catalog.json` generation only. Image normalization/WebP/PDF generation remains a later slice once real master artwork exists.
