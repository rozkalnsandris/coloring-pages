# Coloring Pages SIMPLE-DEPLOY

This repository is a SIMPLE-DEPLOY v1 consumer for the static application image.

## Application image

- manifest: `.simple-deploy.json`
- image: `ghcr.io/rozkalnsandris/coloring-pages`
- target alias: `coloring-pages-public-rpi5`
- architecture: `linux/arm64`
- runtime class: `rpi5-compose`
- pull profile: `public-anonymous-pull`

The image contains the application shell plus the isolated importer runtime (`python3`, Pillow and `/usr/local/bin/coloring-pages-import`). It also embeds the reviewed existing-media correction helper and its exact contract. The `Dockerfile` validates both helper runtime inputs during image build. Production coloring-page binaries and the live catalogue are not baked into the image. The long-running nginx service still receives only the public content surface, read-only.

## Required content persistence identity

The consumer declares one stable SIMPLE-DEPLOY persistence identity:

```text
coloring_pages_content
```

The consumer Compose mounts that identity read-only at:

```text
/var/lib/coloring-pages/public
```

The consumer manifest does not embed `/srv` host paths. The trusted `RPi5_main` adapter must separately map `coloring_pages_content` to the approved host path `/srv/coloring-pages-content/public`.

Only the public content surface is exposed to the container. `inbox/`, `originals/` and `state/` remain outside the container.

That RPi5-side mapping and any filesystem/runtime mutation remain separate owner-gated work.

## Publication

`.github/workflows/simple-deploy.yml` publishes the immutable application image only when an approved application-image input changes:

- `Dockerfile`;
- `tools/coloring-pages-import`;
- `deploy/nginx.conf`;
- the three HTML entry points;
- `css/**`, `js/**` or `assets/**`.

The approved auto-LIVE path allowlist remains intentionally narrow. The existing-media correction helper and its exact correction contract are embedded Docker image inputs, but those paths are not independent auto-LIVE triggers. A reviewed revision of those helper inputs is released only together with an approved image-input change such as the corresponding `Dockerfile` wiring or validation change.

The content lane is deliberately separate. Changes to the Chat-to-Drive contract, metadata, documentation, tests, Compose source, SIMPLE-DEPLOY manifest or the workflow definition itself do not mint a new application image on their own. Production coloring-page media is imported through Drive/RPi5 and does not require application rebuild or redeploy.

After an owner-authorized eligible `main` merge, this application lane is allowed to continue automatically through the reviewed release chain:

`merge → immutable GHCR image → :production pointer → RPi5 SIMPLE-DEPLOY reconcile → container deploy/redeploy/restart → /health + /ready verification`.

That authority is limited to the exact merged `main` SHA, its immutable image digest, target `coloring-pages-public-rpi5`, the reviewed Compose/runtime/mount contract and the existing SIMPLE-DEPLOY verifier.

The reusable workflow remains pinned to:

`rozkalnsandris/ops-workflows/.github/workflows/simple-deploy.yml@94187cc447fc80757db10ac25d49717d00dc8430`

## Authority boundary

The application auto-LIVE exception does not authorize Cloudflare/DNS/tunnel work, secrets/credentials, permissions/ownership, repository settings, host package installation, production content mutation, Drive mutation, cleanup, rollback or an alternate deployment path.

Content publication is a separate lane and does not rebuild/redeploy the application. Manual deploy/restart or any runtime mutation outside the reviewed auto-LIVE flow still requires separate explicit owner authorization.
