# PUBLISH staging bridge (#274 → #288)

**Goal:** keep the human workflow as `MAKE → PUBLISH`. Do not add a second
publication system.

## Canonical three-step flow

1. **PREPARE** — existing `tools/coloring-pages-publish-preflight` /
   `tools/coloring-pages-print-master` prepare and validate exact A4 PNG
   master(s), allocate fresh seven-digit IDs against fresh LIVE catalogue
   evidence, freeze SHA-256/bytes/category/metadata, and fully materialize the
   v1/v2 manifest before any Drive mutation.
2. **STAGE** — `tools/coloring-pages-drive-stage-envelope` validates those
   exact local PNG/manifest bytes and emits
   `rozkalns.rpi5-main.coloring-pages-drive-stage-envelope.v1`. The reviewed
   trusted RPi5 stage sender consumes that complete envelope and may write only
   through its fixed wrapper to production `pending/`, PNG page(s) first and
   the already-built manifest last.
3. **IMPORT** — the existing trusted RPi5 Drive ingest operator pulls from
   `pending/`, verifies exact hashes/metadata, invokes the immutable importer,
   and performs required public verification.

`COLORING_PAGES_DRIVE_STAGE=PASS` proves staging only.
`COLORING_PAGES_DRIVE_INGEST=PASS` remains terminal publication success.

## Why #274 is no longer the production blocker

Issue #274 added `tools/coloring-pages-drive-upload`, a source-only multipart
validator with an injected callback. Its CLI intentionally remains offline and
returns no production PASS. It was useful for validating exact v1 request bytes,
but the connected Files/Drive surfaces required provider-owned file references
that Chat-local prepared PNGs could not reliably materialize.

Issue #288 adopts the separately reviewed and canary-proven trusted RPi5 stage
sender instead. Production PUBLISH therefore no longer depends on
`source_file_ref` / `file_uri` handoff from Chat-local files.

The #274 helper remains a regression/diagnostic utility. It is not the canonical
production uploader and it must not be wired to a second HTTP/OAuth sender.

## Offline envelope adapter

Independent v1 activities prepared by the existing preflight helper:

```bash
python3 tools/coloring-pages-drive-stage-envelope \
  --v1-prepared-dir /path/to/prepared
```

One ordered v2 activity whose fully materialized manifest is next to its exact
page PNGs:

```bash
python3 tools/coloring-pages-drive-stage-envelope \
  --v2-manifest /path/to/7654321.json
```

The adapter:

- accepts only seven-digit new-publication IDs;
- validates exact filenames, PNG signature, SHA-256 and byte size;
- validates strict v1/v2 manifest fields, approved category/age/difficulty/
  language/source-kind/approval-class and page bindings;
- rejects duplicate JSON keys and duplicate v1 activity IDs;
- requires v2 indexes to be contiguous from 1 and filenames to follow that
  exact order;
- emits PNG page(s) before the manifest for every activity;
- bounds activities/pages/file sizes/aggregate raw bytes;
- performs no network, Drive, RPi5, credential, rclone, ingest or publish
  operation.

Full A4 geometry validation remains the job of the existing reviewed print
helper before envelope construction.

## Trusted stage sender boundary

Canonical machine contract:
`deploy/publish-trusted-rpi5-stage-sender-v1.json`.

Before the first Drive mutation, PUBLISH must freshly prove:

- current `RPi5_main/main`;
- installed `/usr/local/bin/coloring-pages-drive-stage-sender` matches current
  sender source;
- installed `/usr/local/libexec/coloring-pages-drive-stage-rcat` matches current
  wrapper source;
- reviewed sudoers/state-lock identities match the sender contract;
- production namespace remains exactly `pending`;
- canary namespace remains separate and is never used by PUBLISH;
- the existing ingest operator/importer alignment preflight also passes.

Arbitrary host `rclone` remains forbidden. The exception is narrow: the
reviewed stage sender may invoke only its fixed privileged wrapper, whose remote,
root folder and namespace are contract-bound. The Drive ingest operator remains
Drive→RPi5 pull-only.

The 2026-10-20 `canary/` result proves only that the sender→fixed-wrapper→Drive
transport can preserve the exact bounded activity without writing the same ID
to `pending/`. Historical canary evidence never replaces the fresh runtime
identity preflight.

## Failure rule

All PNG bytes and complete manifest bytes must be prepared, cross-bound and
wrapped into one validated envelope before the first Drive mutation.

After the first sender upload attempt, any error or ambiguity is a terminal
STOP for that authorized publication chain. No retry, rollback, overwrite,
cleanup, archive/delete, arbitrary rclone, direct connector fallback or second
staging surface is implied.

## Tests

```bash
python3 -m unittest tests.test_publish_trusted_rpi5_stage_sender_288 -v
python3 -m unittest tests.test_publish_stable_upload_source_refs -v
python3 -m unittest tests.test_chat_to_drive_ingestion tests.test_chat_to_drive_ingestion_v2 -v
```

The older `test_drive_simple_bridge_274.py` remains because the #274 helper is
still expected to be safe and offline.
