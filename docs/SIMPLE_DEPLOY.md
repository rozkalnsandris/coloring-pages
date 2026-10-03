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

`.github/workflows/simple-deploy.yml` publishes the immutable application image when application/deployment inputs or `tools/coloring-pages-import` change. Production media content changes do not mint a new image and do not require application redeploy.

The reusable workflow remains pinned to:

`rozkalnsandris/ops-workflows/.github/workflows/simple-deploy.yml@94187cc447fc80757db10ac25d49717d00dc8430`

## Authority boundary

Image publication, merge, RPi5 deployment, creation of the content store, importing artwork, Docker restart/redeploy and Cloudflare/DNS/tunnel work are separate operations. No repository source change grants LIVE authority.
