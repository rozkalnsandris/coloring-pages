# Coloring Pages SIMPLE-DEPLOY

This repository is a SIMPLE-DEPLOY v1 consumer.

Canonical consumer contract:

- manifest: `.simple-deploy.json`
- image: `ghcr.io/rozkalnsandris/coloring-pages`
- target alias: `coloring-pages-public-rpi5`
- architecture: `linux/arm64`
- runtime class: `rpi5-compose`
- persistence: none
- pull profile: `public-anonymous-pull`

## Publication

`.github/workflows/simple-deploy.yml` runs on pushes to the default `main` branch only when a current site/build/consumer/deploy input changes, and delegates to the immutable reusable workflow:

`rozkalnsandris/ops-workflows/.github/workflows/simple-deploy.yml@94187cc447fc80757db10ac25d49717d00dc8430`

The caller passes exactly `${{ github.sha }}` as `source_sha`. The reusable workflow validates that the caller event is the default branch, checks out that exact source SHA, builds the declared Dockerfile for `linux/arm64`, publishes the exact source tag, records an immutable registry digest, and advances the mutable `:production` pointer to that digest.

The reusable workflow requires only:

- `contents: read`
- `packages: write`

No repository secret forwarding is declared by the consumer caller.

The caller intentionally skips documentation/test-only changes so a docs merge does not mint a new immutable image identity. Publication remains enabled for the workflow itself, the consumer manifest, Docker/build inputs, application HTML/CSS/JS/assets, canonical metadata/originals, build tooling, and deployment source under `deploy/**`.

## Immutable deployment evidence

RPi5_main must consume the immutable publication result, not the mutable `:production` tag.

The downstream source/runtime handoff requires:

- exact merged Coloring Pages source SHA;
- image repository;
- `sha256:...` image digest;
- immutable `image@sha256:...` reference;
- target alias;
- consumer manifest SHA-256;
- shared SIMPLE-DEPLOY workflow SHA;
- compose project/file/service identity;
- health/readiness contract;
- persistence declaration;
- registry pull profile.

The reusable workflow emits these facts through its public-safe SIMPLE-DEPLOY intent/output contract.

## Authority boundary

Publishing an image does not install or start it on RPi5 and does not authorize Cloudflare, DNS, tunnel, network, secrets, credentials, repository-settings or host-runtime mutations.

RPi5 target registration and LIVE cutover remain separate `RPi5_main` work items with their own authority and exact-SHA/digest gates.
