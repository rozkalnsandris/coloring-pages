# Coloring Pages SIMPLE-DEPLOY

This repository is a SIMPLE-DEPLOY v1 consumer for the static application image.

## Application image

- manifest: `.simple-deploy.json`
- image: `ghcr.io/rozkalnsandris/coloring-pages`
- target alias: `coloring-pages-public-rpi5`
- architecture: `linux/arm64`
- runtime class: `rpi5-compose`
- pull profile: `public-anonymous-pull`

The image contains only the application shell: HTML/CSS/JS/assets and nginx configuration. Production coloring-page binaries and the live catalogue are not baked into the image.

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

`.github/workflows/simple-deploy.yml` publishes application images only when application/deployment inputs change. Media importer/content changes do not need to mint a new application image.

The reusable workflow remains pinned to:

`rozkalnsandris/ops-workflows/.github/workflows/simple-deploy.yml@94187cc447fc80757db10ac25d49717d00dc8430`

## Authority boundary

Image publication, merge, RPi5 deployment, creation of the content store, importing artwork, Docker restart/redeploy and Cloudflare/DNS/tunnel work are separate operations. No repository source change grants LIVE authority.
