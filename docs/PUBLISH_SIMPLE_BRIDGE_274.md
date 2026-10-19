# PUBLISH simple bridge (#274): one missing upload helper

**Goal:** user workflow stays MAKE → PUBLISH. Do not build another publication system.

## Keep only three existing steps

1. PREPARE (existing): tools/coloring-pages-publish-preflight invokes tools/coloring-pages-print-master to prepare/validate A4 PNG, allocate a fresh random 7-digit ID against LIVE catalogue evidence, freeze SHA-256/bytes/category, and construct the full v1 manifest **before** staging.
2. UPLOAD (one new source helper): tools/coloring-pages-drive-upload checks prebuilt preflight-index.json, corresponding PNG and manifest files, freezes all request bodies and exposes a single sender callback for a *future separately authorized* API integration.
3. IMPORT (existing): trusted RPi5_main Drive importer checks exact hashes and publishes + verifies the public result.

**Current result: SOURCE-ONLY, no provider connected.** The ChatGPT Google Drive upload action requires a provider-owned file_uri, not a local PNG path. The helper neither generates file_uri nor accesses Google OAuth, Drive, network, LIVE or RPi5. Source merge alone cannot activate PUBLISH.

## Offline command: check only

    python3 tools/coloring-pages-drive-upload --prepared-dir /path/to/preflight-output --folder-id EXACT_PINNED_PENDING_ID

This does not upload. Folder ID syntax does not prove access or ownership. Valid input returns exit **3**, BRIDGE=OFFLINE_ONLY / UPLOAD_PERFORMED=NO / PUBLISH=NOT_PERFORMED. Invalid input returns exit **2**, BRIDGE=BLOCKED. No PASS can be returned by the CLI.

The helper accepts 1–20 independent v1 activity pairs only, checks unique seven-digit IDs, exact SHA-256/bytes, canonical metadata/category, the complete prebuilt manifest and symlink/path hazards, and refuses oversized files before unbounded reads. All PNG+JSON request bytes are frozen before the first hypothetical write. Per activity, PNG is sent first and its **already prepared** JSON manifest last. Full A4 print validation remains the job of the existing print helper; testing the PNG magic bytes is not enough.

## Only one future sender callback, no OAuth framework

The source integration interface is send_once(frozen_requests, sender_callback), where the injected sender receives (fixed Drive files.create upload URL, multipart content-type, exact body bytes). It is not connected to HTTP here. A future owner-authorized runner must independently prove live PUBLISH intent, OAuth identity/permission, actual exact pending folder binding, fresh LIVE ID absence, operator/importer alignment, no duplicate Drive names, and immutable prepared source bytes. No such runner has been built, trusted or authorized in this issue. Adopting a direct API sender requires separate review of the current stable upload source-ref contract.

Before any sender call, the bridge now re-extracts the actual media bytes from each frozen multipart body, reconstructs the canonical request, and checks exact equality against all stored metadata, SHA-256, MD5 and byte counts. Recalculating a caller-supplied fingerprint is insufficient: the actual body must match. It also rejects a batch containing mixed pending-folder IDs or repeated seven-digit activity IDs, and checks all these conditions across the entire batch before its first hypothetical mutation. The existing PNG-before-prebuilt-JSON order is unchanged.

Before calling the sender, the same strict v1 manifest validator used by the offline `freeze()` gate checks each JSON payload extracted from its immutable multipart request against its paired PNG: ID, SHA-256, exact byte size, schema and approved metadata. Duplicate JSON keys, missing fields, unrecognized categories and malformed manifests block the **entire** batch before the first callback. A valid multipart envelope or a matching request fingerprint does not bypass the cross-file binding. This is source-only: it does not replace full A4 print validation or prove actual Drive permissions.

The intended Google v3 call is files.create with uploadType=multipart. Returned metadata must match the file name, MIME, actual parent, decimal-string size and binary md5Checksum, and return distinct file IDs. This is an additional transport identity check, not proof of RPi5 import or published content. On any first or later sender ambiguity/response mismatch, STOP without retry, rollback, overwrite, cleanup or switching to another uploader. Host-side rclone push remains forbidden.

References: https://developers.google.com/workspace/drive/api/guides/manage-uploads ;
https://developers.google.com/workspace/drive/api/reference/rest/v3/files/create ;
https://developers.google.com/workspace/drive/api/guides/api-specific-auth

## Tests and decisions

    python3 -m unittest discover -s tests -p 'test_drive_simple_bridge_274.py' -v

Tests exercise independent v1 pairs, ordering, SHA/size/manifest mismatches, forged media SHA-256/MD5/size with recalculated fingerprints, **forged valid multipart manifests with incorrect PNG SHA-256, byte size, ID or category**, duplicate/missing JSON keys including the later activity in a batch, body-embedded folder tampering, mixed destination folder IDs, repeated activity IDs, unreadable/symlink/oversized files, mock provider responses, failures after any write attempt and no retry. No real OAuth, Drive or LIVE access is performed.

Other Draft experiments (#259, #267, #273) are unchanged; this implementation does not depend on them. The next blocker is one authorized provider bytes upload connection, not additional mock frameworks.
