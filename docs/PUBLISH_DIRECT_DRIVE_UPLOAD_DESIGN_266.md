# Direct Google Drive API upload — source-only feasibility (#266)

**Status:** OFFLINE DESIGN ONLY. No Drive credentials, API call, upload, publish or LIVE authority. Existing canonical `PUBLISH` lane remains unchanged and blocked on the local-files-to-`file_uri` handoff described in #258 / Draft PR #259. This proposal does **not** implement or authorize a replacement.

## Verified official Google API behavior

- Google Drive API v3 `files.create` supports `POST https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart`.
- `multipart/related` contains exactly two parts: first JSON metadata (`application/json; charset=UTF-8`), then original media (`image/png` or `application/json`), with correct byte-accurate boundaries and `Content-Length`. Metadata includes `name`, `mimeType` and `parents: [pinned_pending_folder_id]`, so no Workspace-native conversion is requested.
- Multipart is documented for files of **5 MB or less**; the offline prototype applies a conservative **5,000,000-byte bound on the entire request**. For an eventual larger activity file a separately reviewed resumable protocol would be required, not an automatic switch after any mutation.
- A client would need an *independently authorized* Google OAuth session, appropriate access to the exact `pending/` folder ID, and user/provider permission for writing there. Google's narrower `drive.file` scope is a candidate only if the app has the required folder/file access; it does not automatically grant access to an arbitrary existing folder. **Do not request, read, log, generate or transmit tokens as part of #266.**
- `files.create` creates a new file; identical names are not an overwrite barrier because Google Drive can store duplicate file names. A real uploader therefore needs fresh exact-folder duplicate discovery, stable file-ID tracking, and safe fail-closed staging that does not retry after first write.
- Google Drive returning file metadata is not evidence that exact SHA-256 bytes reached RPi5 or that a page is public. Require independent verified-byte integrity + the trusted RPi5 operator's terminal PASS in any separately authorized publication implementation.

Official references:
- https://developers.google.com/workspace/drive/api/guides/manage-uploads
- https://developers.google.com/workspace/drive/api/reference/rest/v3/files/create
- https://developers.google.com/workspace/drive/api/guides/api-specific-auth

## Purely local prototype

`tools/coloring-pages-drive-multipart-design` uses the offline output directory from `tools/coloring-pages-publish-preflight`. It performs no network or Drive operations. It validates every independent v1 PNG+manifest pair, category, frozen 7-digit ID, SHA-256 and byte size. It validates filenames, opens the prepared directory once with `O_DIRECTORY|O_NOFOLLOW`, then opens each regular file relative to that directory descriptor with `O_NOFOLLOW|O_NONBLOCK`. It rejects oversized files by `fstat` **before reading**, then reads at most the bound plus one byte and checks the file identity, size and timestamps again after reading. The limits are 64 KiB for the index, 64 KiB for a manifest and 5,000,000 bytes for individual PNG media; multipart framing must also fit the overall 5,000,000-byte limit. Symlink substitution at file-open time and detected concurrent in-place mutations fail closed. The prototype builds all requests **in memory** and emits only request metadata/hashes to stdout.

**Proof boundary:** this is a bounded, defensive *offline source read*, not a formally immutable snapshot. Concurrent filesystem writes can escape timestamp comparisons; any future runtime uploader requires an independently verified immutable byte handoff. Only the first eight PNG signature bytes are checked here: the CLI explicitly reports `PNG_PROOF=SIGNATURE_ONLY` and `PRINT_VALIDATION=NOT_PERFORMED`. Signature agreement does **not** establish decodability, true A4 dimensions, 300 DPI, safe margins, meaningful art content, or publication acceptance. Full canonical print validation remains a separate mandatory gate before real `PUBLISH`. No owner authorization, fresh LIVE catalogue or folder ownership is inferred.

Example (locally supplied symbolic folder ID is not permission evidence):

```bash
python3 tools/coloring-pages-drive-multipart-design \
  --prepared-dir /tmp/publish-preflight-prepared \
  --folder-id <exact-folder-id>
```

A valid offline design returns `DIRECT_DRIVE_DESIGN=OFFLINE_ONLY`, `DRIVE_WRITE=NO`, and **exit code 3** rather than 0. An invalid prepared batch or oversized multipart body returns `DIRECT_DRIVE_DESIGN=BLOCKED` and **exit code 2**. Both deliberately prevent any downstream script from treating this prototype as PUBLISH success. No HTTP body is sent or written as a persistent artifact.

Each plan has a frozen ordered pair `<id>.png`, `<id>.json`; manifest JSON is fully ready before the first hypothetical mutation. All local artifacts across the batch must validate before any request would be eligible. Python API `multipart_request(...)` is test-only byte composition, not a sender.

The test suite `tests/test_drive_multipart_design_266.py` asserts exact RFC-style framing, original binary media identity, JSON metadata ordering, exact pending folder binding, 5 independent activities, failure on tampering, fake category/ID/path, 5 MB limits, boundary collision and non-publication exit semantics.

## Gap analysis / next gate

1. **Execution location:** A source-only Python design in GitHub cannot call the owner's Google Drive by itself. Current ChatGPT Google Drive plugin only uploads provider-owned `file_uri` references; it does not expose a general token-bearing raw `files.create` API or a local-PNG snapshot materializer. This prototype does not make the missing connector capability appear.
2. **Trust and auth design:** Any future direct uploader would need a separately reviewed bounded execution environment, an owner-authorized OAuth credential surface and folder-scoped semantics. The narrower `drive.file` permission must be tested with the actual destination folder before assuming it is sufficient. No secrets/settings/permissions changes are approved by this issue.
3. **Prewrite reconciliation:** Before any live upload: fresh owner `PUBLISH`, exact approved A4 print masters and independent v1 manifests, fresh LIVE catalog IDs, pinned importer/operator source alignment, *all* bytes frozen, no duplicate folder names, and a single reviewed upload surface. Decide the alternate direct-API surface **before** the first mutation; never switch surfaces mid-flight.
4. **Failure boundary:** For any failure after the first upload: STOP, preserve state, no retry, rollback, cleanup, overwrite or alternate uploader. On success, the existing trusted RPi5 Drive pull/verify/import and public verification would still be required.
5. **Release gate:** A separate exact owner authorization + security review and new source/runtime contract would be required before enabling a direct API uploader. Do not modify `AGENTS.md`, `deploy/chat-to-drive-ingestion*.json`, `RPi5_main` or LIVE on the strength of this feasibility PR.

## Explicitly not implemented

No real Drive API client; no OAuth token ingestion, testing or storage; no network calls or Drive writes; no direct-API deployment; no importer invocation; no owner permission inference; no external staging canary; no `PUBLISH` automation. #258 and its Draft PR #259 remain independent and unresolved. This work is a feasibility result, not a production fix.
