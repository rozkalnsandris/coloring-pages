# Chat-to-Drive ingestion v2 — multi-page activity source contract

## Status

This is a **source-ready, host-not-activated** extension for activities with 2–12 ordered PNG pages.

The existing single-page production path remains unchanged and continues to use:

- `deploy/chat-to-drive-ingestion.json`;
- manifest schema `rozkalns.coloring-pages.drive-staging-manifest.v1`;
- one staged `<id>.png` plus `<id>.json`.

This v2 contract does not authorize Google Drive writes, RPi5 execution or production import. The trusted host implementation belongs to `rozkalnsandris/RPi5_main` and must be reviewed/activated separately.

## Simple model

One activity stays one catalogue item:

```text
<id>-1.png
<id>-2.png
...
<id>.json
```

The manifest is uploaded last and is the readiness signal. Before the first Drive mutation, every page already exists locally and the complete manifest is validated.

The manifest carries the ordered page identities:

```json
{
  "schema": "rozkalns.coloring-pages.drive-staging-manifest.v2",
  "id": "kuerbis-gesicht-001",
  "pages": [
    {
      "index": 1,
      "file": "kuerbis-gesicht-001-1.png",
      "sha256": "<64 lowercase hex>",
      "size_bytes": 123456
    },
    {
      "index": 2,
      "file": "kuerbis-gesicht-001-2.png",
      "sha256": "<64 lowercase hex>",
      "size_bytes": 123789
    }
  ],
  "title": "Kürbis-Gesicht",
  "character": "",
  "category": "lernen",
  "age": "3-6",
  "difficulty": "easy",
  "language": "de",
  "source_kind": "chatgpt-generated-png-set",
  "approval_class": "explicit-owner-chat-approval"
}
```

Page indexes start at 1 and must be contiguous. Filename order is print order.

## Intended trusted host flow

The future `RPi5_main` operator should stay small:

1. read one v2 manifest from the exact bound Drive pending folder;
2. validate the complete manifest and page count;
3. download every declared PNG to `state/drive-ingest/<id>-<index>.png.partial`;
4. verify every page filename, byte size and SHA-256;
5. only after all pages pass, publish the verified files to direct-child inbox paths `<id>-<index>.png`;
6. invoke the existing immutable importer once with the ordered page paths and explicit `--id <id>`;
7. verify one catalogue entry, ordered `pages[]`, all derivatives and all public URLs;
8. write one success receipt binding the exact page set.

The importer already accepts multiple ordered source arguments. No PDF generator, ZIP layer, database, application restart or separate per-page catalogue item is required.

## Failure rule

Before the first mutation, any mismatch is a normal fail-closed rejection.

After the first authorized mutation, any error is STOP. There is no automatic retry, rollback, cleanup, overwrite or alternate path.

## Activation gate

v2 may become a production content path only after a separate reviewed `RPi5_main` change implements the operator and proves exact-page verification with a non-production canary. Until then, normal single-page `PUBLISH` remains the only active Chat-to-Drive publication path.
