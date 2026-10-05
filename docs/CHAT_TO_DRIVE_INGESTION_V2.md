# Chat-to-Drive ingestion v2 — multi-page activity source contract

## Status

This is a **production-activated** extension for activities with 2–12 ordered PNG pages. The reviewed host operator repin for canonical newest-first catalogue order was installed and verified on 2026-10-05.

The existing single-page production path remains unchanged and continues to use:

- `deploy/chat-to-drive-ingestion.json`;
- manifest schema `rozkalns.coloring-pages.drive-staging-manifest.v1`;
- one staged `<id>.png` plus `<id>.json`.

The trusted host implementation now runs `RPi5_main@7e3e6b6d6574c1dc5199618dbb974b1fae83eaf5`. The verified installed `/usr/local/bin/coloring-pages-drive-ingest` blob is `399df72159479c405166d011f140a967bdb749a5` (`root:root:755`) and pins importer image `ghcr.io/rozkalnsandris/coloring-pages@sha256:53801684e0ce5a30d195d3436220a71b350112fc6e6fdc6fe107779d13c857ba`. This restores normal v1/v2 `PUBLISH` eligibility while preserving the existing rule that every activity requires fresh owner approval of the exact latest draft or ordered draft set.

## Simple model

One activity stays one catalogue item:

```text
<id>-1.png
<id>-2.png
...
<id>.json
```

The manifest is uploaded last and is the readiness signal. Before the first Drive mutation, `PUBLISH` has prepared and validated every page locally, frozen every per-page SHA-256/byte size, and validated the complete manifest.

The manifest carries the ordered page identities:

```json
{
  "schema": "rozkalns.coloring-pages.drive-staging-manifest.v2",
  "id": "8152047",
  "pages": [
    {
      "index": 1,
      "file": "8152047-1.png",
      "sha256": "<64 lowercase hex>",
      "size_bytes": 123456
    },
    {
      "index": 2,
      "file": "8152047-2.png",
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

For new Chat publications, the authoring layer follows `metadata/id-policy.json` and allocates an opaque random seven-digit decimal ID independently for each activity. The candidate must be absent from fresh LIVE catalogue state before the first mutation and distinct from any other candidate in the same local publish batch. The v2 ingestion schema continues to accept historical descriptive and sequential IDs for backward compatibility; published IDs are immutable.

## Trusted host flow

The activated `RPi5_main` operator stays small:

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

After the importer and every contract-required post-import verification item PASS, publication is complete: immediately report `PASS` and stop. Do not continue with discretionary diagnostics, repeated verification, Drive archive/delete, cleanup or unrelated runtime work.

## Repin activation

The catalogue-order fix changed the importer contract to canonical newest-first order. The reviewed host repin was installed on 2026-10-05 with exact operator blob `399df72159479c405166d011f140a967bdb749a5`; the installer reported no state/lock creation, no rclone configuration change, no sudoers change, no rclone execution, no content import and no systemd change.

## Activation record

Production activation was completed on 2026-10-04 after:

- reviewed `RPi5_main` implementation merged at `dc6b784bba471731ff060ece207e06d67cda16d3`;
- exact installed operator identity matched source blob `5d6821ad42c8c9d887a03606279e6c70745a993f`;
- installed metadata matched `root:root:755`;
- an installed-operator non-production v2 canary passed for two ordered page identities and rejected a deliberately mismatched page SHA-256;
- the canary executed no `rclone`, Docker/import or production-content mutation.

Single-page v1 remains active and backward compatible. Multi-page v2 publication is active through the same owner-gated `PUBLISH` trust boundary, now using the repinned newest-first importer image.
