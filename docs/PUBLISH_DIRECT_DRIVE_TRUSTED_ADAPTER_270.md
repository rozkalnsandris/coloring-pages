# Direct Drive trusted upload adapter — source-only design (#270)

**Status: BLOCKED_FOR_REAL_UPLOAD.** This PR introduces a narrow, dependency-free **offline state-machine model**, not an HTTP or OAuth implementation. It has no network calls, token access, provider writes, RPi5 execution or LIVE authority. A synthetic two-file success is `SIMULATED_ONLY_NOT_PUBLISH`. It is not a replacement for the canonical Chat→Drive→trusted-RPi5 `PUBLISH` workflow.

Earlier independent work: issue #266 / Draft PR #267 (offline `multipart/related` byte composer) and issue #258 / Draft PR #259 (Google Drive plugin `file_uri` handoff gap). This PR is based on current main, does not import their unmerged source, and does not modify the canonical production content or importer contracts.

## Trust-boundary and auth preflight (design, not performed)

For a future real uploader, a dedicated, owner-authorized executor would need to verify **all** of the following *freshly and independently before the first mutation*:

1. **Owner intent:** exact latest owner `PUBLISH` approval for approved A4 print masters; no `START`, generic `OK` or source merge implicitly authorizes this.
2. **Single upload surface:** preselect `direct-drive.files.create.multipart` for the entire activity; no mid-flight switch to plugin `file_uri` or RPi5 `rclone` uploads. Production contracts currently require a stable immutable snapshot handoff; adopting a different direct API surface needs separate review and contract update, not a quiet override.
3. **OAuth:** a separately granted least-privilege session with independently established client identity, account, scope, expiry and access to the *specific* destination. Google's `drive.file` may be an option but does not imply arbitrary existing-folder access. Never accept self-asserted token claims or log, expose or store secrets. No OAuth availability is claimed here.
4. **Exact destination:** read and pin the actual `pending/` Drive folder ID from a trusted binding; verify it is an actual folder, belongs to the expected account/parent/drive, is not trashed and permits additions by the effective identity. Do **not** trust folder display name or a syntactically valid ID alone. The source model checks strict consistency of intended and observed IDs, but **only for synthetic fixtures**.
5. **Pre-mutation state:** fresh LIVE catalogue collision test for every 7-digit ID, operator/importer exact source alignment, category and manifest validation, fully validated A4 300-DPI print masters, all PNG/manifest SHA-256/byte sizes, and confirmation that the exact `pending/` folder has no conflicting names or in-flight unacknowledged upload. A list result may be partial or stale; pagination, permissions and race semantics must be reviewed separately.
6. **Time/evidence binding:** bound expiry plus observed-at timestamp, provider identity/folder response provenance and exact artifact hashes; an arbitrary caller-supplied `ready=true` is not proof. The current `SyntheticGate` accepts **only** `synthetic-offline-only` proof class, fixture owner command `PUBLISH-fixture-only` and synthetic states. It explicitly refuses real `PUBLISH`, real auth claims and unknown conditions.
7. **Single immutable pair:** for this **v1-only simulation**, prebuild one `<id>.png` then `<id>.json` request with exact SHA-256/bytes, manifest bindings and MIME `image/png`/`application/json`; manifest is prepared before both requests. The in-memory pair is checked before any simulated request. There is **no v2 activity support** in #270.

## Source adapter model

`tools/coloring-pages-drive-trusted-upload-adapter` offers:

- `plan_v1(id, png, manifest, folder_id, synthetic_gate)`: verifies exact seven-digit ID, category, PNG signature, v1 manifest fields, full SHA-256/byte size and order, and builds both canonical `multipart/related` request byte bodies in memory. Request framing must fit 5,000,000 bytes; JSON manifest is capped at 64 KiB. This is not the canonical print validator: the PNG signature cannot prove A4 dimensions, 300 DPI or printable safety.
- `simulate_v1(plan, tuple(mock_png_receipt, mock_manifest_receipt))`: exercises one-way success/failure response classification **without creating a transport**. It checks mock file IDs, names, MIME, bound folder and byte sizes. Any missing, ambiguous or incorrect response yields STOP. A timeout-like exception on the first or second scripted reply is terminal; there is **no automatic retry, rollback, cleanup, overwrite or alternate uploader**.
- `StopBeforeWrite` and `StopAfterWrite` distinguish pre-mutation validation failures from potentially committed remote requests. Mock `attempted/accepted` numbers describe **only a simulation**. No method exists to send requests, and no actual owner or OAuth authorization is accepted.

The Google Drive API supports `files.create` upload with `uploadType=multipart`, metadata first and binary media second. The future execution component would need a separately reviewed fail-closed transport and independently verify server-side byte integrity and RPi5 importer outcome. A `files.create` response or matching file name alone cannot prove exact uploaded bytes or live publication. Google Drive permits duplicate filenames. The 5 MB bound is conservative: larger files require a separately reviewed resumable design **before any upload**.

Google official documentation:
- https://developers.google.com/workspace/drive/api/guides/manage-uploads
- https://developers.google.com/workspace/drive/api/reference/rest/v3/files/create
- https://developers.google.com/workspace/drive/api/guides/folder
- https://developers.google.com/workspace/drive/api/guides/api-specific-auth

## Offline validation

```bash
python3 -m unittest discover -s tests -p 'test_drive_trusted_upload_adapter_270.py' -v
```

Tests construct only synthetic Bytes + Gate + Receipt fixtures; no Drive read/write, OAuth, file permission access or LIVE request. They verify that missing owner-like evidence, a stale or mismatched folder, client/scope assertions, unverified catalog/operator, ambiguous duplicate filenames, MIME/order mismatches, altered hashes, oversized media/manifest, and simulated partial or ambiguous responses fail closed.

## Remaining owner gate / implementation blockers

1. No supported real OAuth access or low-level `files.create` connector is exposed through the current ChatGPT Drive app. The available `upload_file` accepts connector-owned `file_uri` references; this source change does not create them.
2. No production execution environment, effective folder ID binding or provider permission/evidence mechanism has been independently established for a direct uploader.
3. No reviewed replacement for the canonical stable snapshot source-ref contract has been approved. Any direct API execution requires separate source/security review, exact owner authorization, a production runtime gate, and tested post-mutation STOP semantics.
4. No LIVE canary was attempted, no secrets/settings/permissions were read or changed, and no Drive write occurred. This PR must **remain Draft/unmerged** for the feasibility gate. Merging it alone would **not** repair `PUBLISH`.

**Outcome:** `OFFLINE_ADAPTER_MODEL_ONLY`; `PUBLISH=BLOCKED` until a separately authorized and tested provider execution path exists.
