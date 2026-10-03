# Coloring Pages SIMPLE-DEPLOY

This repository is a SIMPLE-DEPLOY v1 consumer for the static application image.

## Application image

- manifest: `.simple-deploy.json`
- image: `ghcr.io/rozkalnsandris/coloring-pages`
- target alias: `coloring-pages-public-rpi5`
- architecture: `linux/arm64`
- runtime class: `rpi5-compose`
- pull profile: `public-anonymous-pull`

The image contains the application shell plus the isolated importer runtime (`python3`, Pillow and `/usr/local/bin/coloring-pages-import`). Production coloring-page binaries and the live catalogue are not baked into the image. The long-running nginx service still receives only the public content surface, read-only.

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

`.github/workflows/simple-deploy.yml` publishes the immutable application image only when an actual image input changes:

- `Dockerfile`;
- `tools/coloring-pages-import`;
- `deploy/nginx.conf`;
- the three HTML entry points;
- `css/**`, `js/**` or `assets/**`.

The content lane is deliberately separate. Changes to the Chat-to-Drive contract, metadata, documentation, tests, Compose source, SIMPLE-DEPLOY manifest or the workflow definition itself do not mint a new application image on their own. Production coloring-page media is imported through Drive/RPi5 and does not require application rebuild or redeploy.

The reusable workflow remains pinned to:

`rozkalnsandris/ops-workflows/.github/workflows/simple-deploy.yml@94187cc447fc80757db10ac25d49717d00dc8430`

## Authority boundary

Image publication, merge, RPi5 deployment, creation of the content store, importing artwork, Docker restart/redeploy and Cloudflare/DNS/tunnel work are separate operations. No repository source change grants LIVE authority.
