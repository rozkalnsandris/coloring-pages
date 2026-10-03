# Coloring Pages Importer Runtime v1

## Goal

Publish new coloring pages with one isolated command on RPi5 without installing Python or Pillow on the host.

The importer runtime is embedded in the same immutable Coloring Pages image that is already published by SIMPLE-DEPLOY. The long-running nginx container does not receive access to the private content-store surfaces.

## Runtime boundary

A future trusted RPi5 wrapper must execute the reviewed immutable image by exact digest and apply all of these controls:

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

After the trusted RPi5 wrapper is installed, the intended daily importer command remains:

```bash
coloring-pages-import /srv/coloring-pages-content/inbox/fire-pup-001.png --category rettungshunde
```

The wrapper is host-control policy and therefore belongs to the trusted `RPi5_main` runtime boundary. It must supply the exact immutable image digest and the isolation flags from `deploy/importer-runtime.json`.

The repository does not authorize installing that wrapper, running Docker, downloading Drive content or importing production media.

## Publication

Because the importer is embedded in the application image, changes to either:

- `Dockerfile`
- `tools/coloring-pages-import`

trigger the normal SIMPLE-DEPLOY image publication on merged `main`.

Publishing a new image does not itself import media. Once an approved importer image is installed for the wrapper, individual coloring-page imports do not require an application rebuild or redeploy.

## Host dependencies

The importer runtime itself requires Docker only.

A future Chat-to-Drive transport operator additionally uses host-managed rclone under the trusted `RPi5_main` boundary. Its Drive credentials are not part of this repository and must never be committed or emitted.

Do not install host Python/Pillow merely to run the importer.
