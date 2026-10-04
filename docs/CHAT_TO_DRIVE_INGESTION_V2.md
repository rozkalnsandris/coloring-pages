# Chat-to-Drive ingestion v2 — multi-page activity source contract

## Status

This contract is in **production repin pending LIVE install** state for activities with 2–12 ordered PNG pages. The transport design remains activated, but new `PUBLISH` execution is paused until the reviewed host operator repin is installed and verified.

The existing single-page production path remains unchanged and continues to use:

- `deploy/chat-to-drive-ingestion.json`;
- manifest schema `rozkalns.coloring-pages.drive-staging-manifest.v1`;
- one staged `<id>.png` plus `<id>.json`.

The currently verified installed host operator remains the earlier blob `5d6821ad42c8c9d887a03606279e6c70745a993f` (`root:root:755`) from `RPi5_main@dc6b784bba471731ff060ece207e06d67cda16d3`, which pins the older importer image `sha256:09822c1ceed359e0365c0e647763c6f1d8b31fb4f4ab564d7959c383709034b2`. Reviewed source for the required repin is merged at `RPi5_main@7e3e6b6d6574c1dc5199618dbb974b1fae83eaf5`; its target operator blob is `399df72159479c405166d011f140a967bdb749a5` and it pins importer image `sha256:53801684e0ce5a30d195d3436220a71b350112fc6e6fdc6fe107779d13c857ba`. Until that exact operator is installed and verified on the trusted host, `PUBLISH` must stop before any Drive/content mutation. After activation, every activity still requires fresh owner `PUBLISH` approval of the exact latest ordered draft set.

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

## Repin transition

The original v2 activation evidence below remains historical. A later catalogue-order fix changed the importer contract to canonical newest-first order, so the host publish operator now requires a separate owner-authorized LIVE install of the reviewed repin before publication resumes.

## Activation record

Production activation was completed on 2026-10-04 after:

- reviewed `RPi5_main` implementation merged at `dc6b784bba471731ff060ece207e06d67cda16d3`;
- exact installed operator identity matched source blob `5d6821ad42c8c9d887a03606279e6c70745a993f`;
- installed metadata matched `root:root:755`;
- an installed-operator non-production v2 canary passed for two ordered page identities and rejected a deliberately mismatched page SHA-256;
- the canary executed no `rclone`, Docker/import or production-content mutation.

Single-page v1 remains backward compatible at the schema level, but the shared installed publish operator is temporarily gated by the same repin requirement. No v1 or v2 `PUBLISH` should proceed until the target operator blob is installed and verified.
