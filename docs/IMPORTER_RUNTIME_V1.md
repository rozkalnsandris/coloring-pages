# Coloring Pages Importer Runtime v1

## Goal

Publish new coloring pages with one isolated command on RPi5 without installing Python or Pillow on the host.

The importer runtime is embedded in the same immutable Coloring Pages image that is already published by SIMPLE-DEPLOY. The long-running nginx container does not receive access to the private content-store surfaces.

## Runtime boundary

The trusted RPi5 publish operator executes the reviewed immutable image by exact digest and applies all of these controls:

```text
image              ghcr.io/rozkalnsandris/coloring-pages@sha256:<reviewed-digest>
entrypoint         /usr/local/bin/coloring-pages-import
network            none
root filesystem    read-only
tmpfs              /tmp
capabilities       drop ALL
no-new-privileges  true
user               current host operator UID:GID
content mount      /srv/coloring-pages-content -> /srv/coloring-pages-content (read-write)
```

The only read-write mount exists because the importer must preserve originals, create derivatives and atomically replace the public catalogue.

The normal web container remains different: it receives only the public content identity at `/var/lib/coloring-pages/public`, read-only.

## Source restriction

The importer accepts a source only when it resolves to a direct child of:

```text
/srv/coloring-pages-content/inbox/
```

It rejects a source outside the inbox, a nested inbox source, a missing content root, missing required directories or a missing published `catalog.json`. It also requires an explicit `--category` whose ID exists in `metadata/categories.json`; there is no implicit default category.

The importer does not bootstrap host directories. Content-store creation is a separate trusted RPi5 operation.

## Chat-to-Drive staging boundary

Google Drive staging does not change the importer trust model.

The transport contract in `deploy/chat-to-drive-ingestion.json` requires a trusted RPi5 operator to pull the staged PNG outside the inbox, verify its manifest, size and SHA-256, then atomically rename the verified file into the inbox. The importer never receives Drive credentials and remains networkless.

The host-side rclone binding and execution belong to `rozkalnsandris/RPi5_main`. This repository only defines the consumer contract.

See [Chat-to-Drive ingestion v1](CHAT_TO_DRIVE_INGESTION_V1.md).

## One-command operator model

The host has one publish operator owned by the trusted `RPi5_main` runtime boundary. It verifies the staged manifest and PNG, publishes the exact source into `inbox/`, then directly runs this immutable importer image with the isolation flags from `deploy/importer-runtime.json`.

There is no separate host `coloring-pages-import` wrapper. The importer command exists inside the immutable application image as `/usr/local/bin/coloring-pages-import`.

This repository does not authorize installing/replacing the publish operator, running Docker, downloading Drive content or importing production media.

## Publication

Because the importer is embedded in the application image, changes to either:

- `Dockerfile`
- `tools/coloring-pages-import`

trigger the normal SIMPLE-DEPLOY image publication on merged `main`.

Publishing a new image does not itself import media. Once the publish operator is aligned to an approved immutable importer image, individual coloring-page imports do not require an application rebuild or redeploy.

## Host dependencies

The importer runtime itself requires Docker only.

A future Chat-to-Drive transport operator additionally uses host-managed rclone under the trusted `RPi5_main` boundary. Its Drive credentials are not part of this repository and must never be committed or emitted.

Do not install host Python/Pillow merely to run the importer.

## Canonical ADMIN taxonomy integration (issue #427)

The immutable image now includes `metadata/categories.json` and
`metadata/topics.json` under `/usr/local/share/coloring-pages/` for the
networkless importer. It also serves the *same* source registries as
`https://ausmalwiese.de/categories.json` and
`https://ausmalwiese.de/topics.json`, revalidating via
`Cache-Control: no-cache`. No separate taxonomy backend is deployed.

The existing `--category` is mandatory. Optional
`--topic <id>` selects exactly one registered public topic; its ID must
match the pinned image-local registry and its kind must agree with the
category (seasonal → `jahreszeiten`; evergreen → another category).
Unknown, duplicate or malformed topic registry entries, invalid IDs or
mismatched topic/category combinations fail before publication writes.
When selected, one activity catalogue record gets
`"topics": ["<exact-id>"]`, including multi-page activities.
No topic is inferred from title, filenames, legacy keywords or characters.
Without `--topic`, the old importer behavior remains unchanged, and
existing catalogue records are preserved as-is.

**Owner gates:** this is application source only; a reviewed
`MERGE coloring-pages #<PR> HEAD=<sha>` is required before an approved
app-image-input change may trigger the narrowly scoped SIMPLE-DEPLOY
flow. The ready source-only `RPi5_main#1277` ADMIN change requires a
**separate** RPi5 reviewed importer-image repin and ADMIN backend
installation authorization after the public application's exact deployed
registry and pinned importer have been verified. Until compatible
preconditions are proven, ADMIN must fail closed. No source-only PR,
merge, Docker build or documentation implies content publication or
other host/network/settings/permission authority.

## Managed runtime categories (#436)

The original immutable categories v1 registry has been superseded for import validation by the **mandatory** mounted v2 runtime registry. Refer to [RUNTIME_CATEGORIES_V2_436.md](RUNTIME_CATEGORIES_V2_436.md) for exact canonical host path, version/SHA256 lock checks, rollout and safety. The image-local v1 JSON remains an immutable seed only; without a valid v2 live registry all imports fail before mutation. This source change grants no host seed/mount/restart, importer repin, publication or ADMIN write authority.

## Managed runtime Topics v2 (#438)

The immutable `metadata/topics.json` stays a v1 seed only. Public and networkless importer read managed `/srv/coloring-pages-content/public/topics.json`, requiring exact canonical v2 JSON for every import, even those without topic metadata. Optional `--topics-sha256` guards an ADMIN snapshot and the importer rechecks the topic digest before the first permanent media/catalog change. See [RUNTIME_TOPICS_V2_438.md](RUNTIME_TOPICS_V2_438.md). Missing v2 file yields HTTP 503 and importer fails closed. Neither source merge nor CI authorizes host seed/mount, importer repin, ADMIN backend upgrade/restart, content or LIVE operations.
