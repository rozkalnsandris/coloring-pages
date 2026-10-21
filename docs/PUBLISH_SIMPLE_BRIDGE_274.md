# PUBLISH staging bridge (#274 → #288 → #290)

**Goal:** keep the human workflow as `MAKE → PUBLISH` and keep staging simple.

## Canonical three-step flow

1. **PREPARE** — existing `tools/coloring-pages-publish-preflight` /
   `tools/coloring-pages-print-master` prepare and validate exact A4 PNG
   master(s), allocate fresh seven-digit IDs against fresh LIVE catalogue
   evidence, freeze SHA-256/bytes/category/metadata, and fully materialize the
   v1/v2 manifest before any Drive mutation.
2. **STAGE** — the connected Google Drive `upload_file` surface receives the
   exact prepared PNG page(s) through runtime-materialized top-level `file_uri`
   references, then the already-built manifest last, all to the exact bound
   production `pending/` folder ID.
3. **IMPORT** — the existing trusted RPi5 Drive ingest operator pulls from
   `pending/`, verifies exact hashes/metadata, invokes the immutable importer,
   and performs required public verification.

Drive staging success is not publication success.
`COLORING_PAGES_DRIVE_INGEST=PASS` remains terminal publication success.

For v1, invoke the trusted operator exactly as `/usr/local/bin/coloring-pages-drive-ingest --id <id> --expected-sha256 <sha256> --expected-size <bytes>`. For v2, use `--id <id>` plus one repeated `--expected-page <index>:<sha256>:<bytes>` per ordered page. Do not derive a shorter CLI from memory.

## Why this is the normal path

The older #274 helper proved the direct multipart model offline but did not own
OAuth/HTTP. Issue #288 introduced a reviewed RPi5 stage sender to work around
missing Chat-local file-reference handoff. That workaround is functionally
correct but sending large image bytes through interactive RDC/Base64 is
needlessly slow.

The current connector surface accepts top-level runtime-materialized file
references. Normal PUBLISH therefore uses the connected Google Drive action
directly and keeps RPi5 responsible only for Drive→RPi5 verification/import.

## File-reference boundary

Before the first Drive mutation:

- every PNG and the complete manifest already exist locally;
- SHA-256, byte size, category and filenames are frozen;
- the manifest is parsed and validated;
- each local artifact is materialized by the runtime for the connector's
  top-level `file_uri` parameter;
- bare file IDs, inline Base64, arbitrary URLs and raw local paths at the
  connector boundary are forbidden;
- the exact `pending/` folder ID is bound;
- the ingest operator/importer runtime alignment passes.

Use one staging surface for the entire publication. Dispatch one explicit
`Google_Drive.upload_file` mutation per artifact; do not place multiple mutating
uploads inside one code-mode loop/batch. Upload page PNGs in the required order
and the manifest last. Verify `accepted_input=file_uri`, filename and MIME type,
then require the exact pending folder from upload `parent_id` or metadata readback
`parent_ids` before dispatching the next artifact.

## Legacy stage sender

`deploy/publish-trusted-rpi5-stage-sender-v1.json` remains reviewed historical
fallback source, including its canary evidence. It is not the normal production
PUBLISH staging surface and must not be selected as an alternate path after a
connector mutation attempt.

Arbitrary host `rclone` remains forbidden.

## Failure rule

Before the first mutation, any validation/materialization/runtime mismatch is a
normal fail-closed STOP.

After the first Google Drive upload attempt, any error or ambiguity is a
terminal STOP for that authorized publication chain. No retry, rollback,
overwrite, cleanup, archive/delete, Base64/RDC fallback, host-sender fallback or
second staging surface is implied.

## Tests

```bash
python3 -m unittest tests.test_publish_stable_upload_source_refs -v
python3 -m unittest tests.test_chat_to_drive_ingestion tests.test_chat_to_drive_ingestion_v2 -v
python3 -m unittest tests.test_drive_simple_bridge_274 -v
```

The #274 offline helper and #288 envelope/sender tests remain regression coverage
for their bounded source contracts; they are not normal production uploaders.
