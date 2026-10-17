# PUBLISH file handoff: source-only capability spike (#258)

## Finding (2026-10-17)

The production publication pathway remains **Drive staging → trusted RPi5 import**.
`tools/coloring-pages-publish-preflight` can locally prepare independent v1
activities and freeze every PNG, manifest, SHA-256 and byte size. The missing
link is a supported exporter of those **exact local bytes** into file references
accepted by the active Google Drive connector.

The connected Google Drive `upload_file` capability takes `file_uri`:
a connector-owned file reference. It cannot be passed a local
`/mnt/data/...` path or a naked URL. Its `fetch(...,
download_raw_file=True, include_base64=False)` action can return a
`file_uri` for an **already stored Drive file**; that is NOT a supported
way to materialize a newly prepared local PNG/JSON into Drive. Existing
`source_file_ref` contract wording refers to the historical Files
uploader and is **not** evidence that the currently connected Google Drive
upload action accepts that field. The previous #141 docs-only fix did not
supply a compatible local-bytes snapshot/export tool.

| Surface | Observed input/output | Current implication |
| --- | --- | --- |
| Local A4 preflight | PNG/JSON paths + hashes + sizes | Files are locally prepared; not an upload reference |
| Historical Files staging | `source_file_ref` immutable snapshot | Contract vocabulary; not the active Google Drive input |
| Google Drive `upload_file` | `file_uri` connector-owned reference | Upload action exists; requires an upstream exporter |
| Google Drive raw `fetch` | May return `file_uri` for existing stored bytes | Read/download only; cannot turn an un-staged local file into a snapshot |
| RPi5 `rclone` | Drive → RPi5 trusted pull only | Never use as an alternate Chat-to-Drive uploader |

This is a **connector capability** gap, not a reason to weaken the
pre-mutation safety gates, upload to another provider or ask the owner to
repeat `PUBLISH`.

## Offline handoff probe

After the existing `tools/coloring-pages-publish-preflight` has produced
an independent-activities directory with `preflight-index.json`, run:

```bash
python3 tools/coloring-pages-publish-handoff-preflight \
  --prepared-dir /path/to/prepared \
  --capabilities /path/to/provider-capabilities.json \
  --bindings /path/to/provider-snapshot-bindings.json
```

The probe verifies each local PNG signature, exact SHA-256/size, filename,
manifest schema/identity and the complete declared pairing of PNG and JSON
to provider-exported snapshot references. It checks one upload surface,
`google-drive.upload_file`, with the same `file_uri` field for all files.

`--capabilities` is explicit observed connector inventory, not an
entitlement grant. Shape (example represents the **hypothetical** case where
a local-bytes exporter has been independently implemented and verified):

```json
{
  "schema": "rozkalns.coloring-pages.publish-handoff-capabilities.v1",
  "upload": {
    "surface": "google-drive.upload_file",
    "source_field": "file_uri",
    "accepts": ["image/png", "application/json"]
  },
  "snapshot_materializer": {
    "available": true,
    "source_field": "file_uri",
    "supports_local_png_and_json": true
  }
}
```

The current observed environment has **no verified local-bytes exporter**.
Record `snapshot_materializer.available=false` for it. Do not produce
fictitious snapshot bindings just to get a green probe.

The optional `--bindings` JSON has schema
`rozkalns.coloring-pages.publish-handoff-bindings.v1`, surface
`google-drive.upload_file`, source field `file_uri`, and `references`
containing **one entry for every PNG and JSON**. Each entry carries
`file`, `sha256`, `size_bytes`, `mime_type`, and a connector-exported
`file_uri` with `file_id`, `download_url`, `file_name` and
`mime_type`. These are *candidate declarations*: the probe cannot
authenticate that a reference is live, belongs to the right user/provider,
is unexpired, or contains the asserted bytes.

A missing capability or reference yields `HANDOFF_PREFLIGHT=BLOCKED`,
exit **2**, **no Drive write**. Even a complete synthetic reference inventory
returns `HANDOFF_PREFLIGHT=OFFLINE_CANDIDATE_ONLY` with exit **3** and
`REMOTE_SNAPSHOT_BYTES_VERIFIED=NO`, **not a production PASS**. Nonzero
exit status intentionally prevents a caller from interpreting the offline
candidate report as an upload authorization. If the reference has a signed
URL `se` expiry, malformed, duplicate and expired values are rejected;
a future timestamp still does **not** prove the reference is owned,
reachable or byte-identical. Its test
references are deliberately fake and may **never** be used for upload.
The tool deliberately contains no Drive SDK calls, credentials, external
HTTP, RPi5 commands or snapshot-generation side effects.

## Follow-up integration gate (not implemented by #258)

1. Provide a user-authorized connector capability that snapshots a local
   PNG/JSON byte stream into a stable, connector-owned `file_uri` and
   reports byte identity. Do not substitute local paths, arbitrary URLs,
   local file IDs or another provider.
2. Bind and independently verify all 2×N snapshots (including manifest
   JSON) *before the first Drive write*, ensure one upload surface and
   correct destination folder ID; use the frozen v1 manifests from the
   print preflight.
3. After fresh owner `PUBLISH` and current GitHub/LIVE/operator/importer
   alignment checks, upload PNG then its prebuilt manifest for each
   independent activity; run only the authorized trusted importer and
   respect terminal PASS or fail-closed STOP.
4. Integration tests should cover a real provider sandbox/canary with
   byte-exact SHA-256 and expiration behavior. Offline tests alone cannot
   prove that a provider snapshot can be created.

No change here authorizes Drive writes, RPi5 LIVE actions, secrets, permission
changes, `MERGE`, retries, rollback or cleanup. Do not update the canonical
staging contracts until a reviewed provider capability has actually been
demonstrated; the existing fail-closed semantics remain authoritative.
