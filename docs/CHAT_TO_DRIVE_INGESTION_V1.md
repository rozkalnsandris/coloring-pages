# Chat-to-Drive ingestion v1

## Goal

Make the normal content workflow close to:

```text
generate PNG in ChatGPT
→ owner approves the page
→ upload the exact PNG blob plus a small SHA-256 manifest to Google Drive
→ trusted RPi5 operator pulls and verifies it
→ immutable coloring-pages importer publishes it
→ verify catalog, derivatives and public URLs
```

Google Drive is transport only. It is not the production source of truth and it does not replace the RPi5 content store.

Machine contract: `deploy/chat-to-drive-ingestion.json`.

## Trust boundary

Canonical ownership remains unchanged:

- GitHub owns application source, importer source, schemas, tests and this transport contract.
- `/srv/coloring-pages-content/originals/` owns production source PNG masters.
- `/srv/coloring-pages-content/public/catalog.json` and `public/media/` own the published catalogue and derivatives.
- Google Drive is a temporary transport/staging surface.
- `rozkalnsandris/RPi5_main` owns host-side rclone binding, credentials, trusted execution and runtime coordination.

Merging this source does not authorize a Drive upload, Drive download, RPi5 command, content import, archive/delete action, credential read, settings change or application deployment.

## Why raw Drive blob files are acceptable

The staged PNG must be uploaded as a normal Google Drive blob file. Google Workspace conversion is forbidden.

Google documents raw file upload separately from Workspace-native documents, and raw blob content is downloaded with the Drive file content endpoint rather than exported. The operator still verifies the exact SHA-256 itself; provider behavior alone is never treated as integrity proof.

References:

- https://developers.google.com/workspace/drive/api/guides/manage-uploads
- https://developers.google.com/workspace/drive/api/guides/manage-downloads
- https://rclone.org/drive/

The rclone Drive backend supports file hashes including SHA-256 for normal Drive files. Fresh pending discovery must not rely on `--fast-list`, because new Drive listings can be delayed/cached.

## Staging layout

The logical Drive layout is:

```text
Coloring_pages/
├── pending/
│   ├── <id>.png
│   └── <id>.json
└── processed/
```

The visible folder name is convenience only. A future LIVE operator must bind an exact Drive folder ID in trusted `RPi5_main` configuration. Runtime selection by folder title alone is forbidden.

The PNG is uploaded first. The matching JSON manifest is uploaded last and acts as the readiness signal, so a half-uploaded PNG is never eligible for import.

## Manifest

A staging manifest uses schema:

```text
rozkalns.coloring-pages.drive-staging-manifest.v1
```

Example:

```json
{
  "schema": "rozkalns.coloring-pages.drive-staging-manifest.v1",
  "id": "aviator-pup-001",
  "sha256": "<64 lowercase hex characters>",
  "size_bytes": 1162127,
  "title": "Aviator Pup",
  "character": "",
  "category": "rettungshunde",
  "age": "3-6",
  "difficulty": "easy",
  "language": "de",
  "source_kind": "chatgpt-generated-png",
  "approval_class": "explicit-owner-chat-approval"
}
```

Unknown manifest fields fail closed. Metadata values must stay inside the importer-supported age, difficulty and language sets.

## Integrity canary before activation

Before this path is activated for production, run one separately authorized non-production canary:

1. take one generated PNG and calculate its SHA-256 before upload;
2. upload that exact file as a normal Drive blob;
3. download it through the intended RPi5 rclone path;
4. calculate SHA-256 again;
5. PASS only when the two SHA-256 values are identical.

A mismatch, conversion or re-encode blocks activation.

## Production activation evidence

The path is now production-activated.

The first owner-authorized production import completed successfully on 2026-10-03 with:

- ID: `bauarbeiter-hund-001`;
- source size: `1258789` bytes;
- SHA-256: `d3162381a26ba47d847d28f6dc6349efa003f69807f4e902f8d116634130e8df`;
- trusted runtime owner: `rozkalnsandris/RPi5_main`;
- runtime revision used for the successful import: `d663073e4a0b7e33bba3b73b84643b4035839640`;
- success receipt present;
- original and public source bytes matching the approved size and SHA-256;
- exactly one matching catalogue entry;
- all five required public verification URLs returning HTTP 200.

This is historical activation evidence, not current LIVE authorization. Every future production import still requires fresh owner authorization for the exact page ID, SHA-256 and byte size. Drive archive/delete remains a separate owner-gated mutation.

## RPi5 pull and publish sequence

The host implementation belongs in `RPi5_main`, not this repository.

For one manifest it must:

1. resolve only the pre-bound exact Drive staging folder;
2. download the PNG to `/srv/coloring-pages-content/state/drive-ingest/<id>.png.partial`;
3. validate manifest shape, ID, byte size and SHA-256;
4. atomically rename the verified file to `/srv/coloring-pages-content/inbox/<id>.png`;
5. invoke the exact immutable importer runtime defined by `deploy/importer-runtime.json`;
6. write a success receipt under `state/drive-ingest/`;
7. verify production originals, catalogue, derivatives and public URLs.

The importer itself remains networkless and does not gain Drive credentials. rclone performs transport before importer execution.

## Idempotency

A matching success receipt plus the same SHA-256 classifies the item as already processed.

An existing page ID without a matching success receipt is a STOP. The pipeline must never silently overwrite an existing original, media directory or catalogue entry.

No automatic retry, rollback, cleanup or alternate mutation path is allowed after the first authorized mutation fails.

## Post-import proof

A successful content publication proves at minimum:

- `originals/<id>/source.png` SHA-256 equals the manifest;
- `public/media/<id>/source.png` SHA-256 equals the manifest;
- exactly one catalogue entry exists for the ID and metadata matches;
- `thumb.webp`, `preview.webp` and `print.pdf` exist;
- public catalogue, thumbnail, preview, source PNG and PDF URLs return HTTP 200.

No application rebuild, redeploy or restart is required merely to publish one new page.

## Drive post-success handling

Moving the PNG+manifest pair from `pending/` to `processed/` is useful for queue hygiene, but it is a separate Drive mutation and requires whatever fresh authority the future runtime operation defines.

A Drive archive failure must not rewrite or roll back a production import that has already passed. Production remains canonical on RPi5.

## Intended user experience

After the transport canary and trusted host operator are activated, the human workflow should be:

```text
User: "Liekam iekšā."
ChatGPT: freeze exact approved image + manifest
→ Drive staging
→ RPi5 pull + SHA verification
→ immutable import
→ public verification
ChatGPT: report PASS or STOP
```

The owner approval is content authority for that exact image only when the future LIVE command explicitly binds the file/hash/ID and the runtime operation.
