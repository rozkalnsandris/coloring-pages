# Preview-only immutable migration plan — `8774852` (#169)

**Status: source-only PLAN. Not a runtime authorization or an executable migration.**

## Decision and official guidance

The owner authorized planning only: `AUTHORIZE PLAN coloring-pages #169 PREVIEW-ONLY ID=8774852 NO-LIVE`. No new preview bytes, catalogue changes, Drive writes, Docker runs, host installs, deployments, or media deletion are authorized. This file and its JSON contract document the **single-page dog** only. Do not generalize authorization to any other activity.

Nginx serves `/media/**` with `Cache-Control: public, max-age=31536000, immutable`. [MDN's HTTP caching guidance](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching#cache_busting) requires a **new URL** when an immutable resource changes; never edit `/media/8774852/preview.webp` in place. The matching application already uses the current watermark algorithm in `tools/coloring-pages-import`.

## Frozen, read-only LIVE evidence (2026-10-11)

Canonical record in `public/catalog.json`: activity `8774852`, `Hund zum Ausmalen`, `tiere`, one page; top-level `thumb`, `preview`, and `print`, no `pages[]`. Its complete original catalogue entry and immutable file identities are recorded in `deploy/preview-8774852-migration-plan-v1.json`.

| Item | Bytes | SHA-256 |
|---|---:|---|
| `public/catalog.json` (201 entries) | not pinned | `1eff2cd32be795ce92f1785731d60b11055b1ed662cdfea2463158a5531b9b49` |
| `originals/8774852/source.png` (2480×3508) | 1032144 | `be2eea2e56760a21eb35c425b100cea1ce69efe3a9820550078d7660b3bec7b1` |
| `public/media/8774852/preview.webp` | 144450 | `9455e016fee1382214050b48678202c62dcb17c5ea86b3122b8086a41e7aece4` |
| `public/media/8774852/thumb.webp` | 30158 | `3a2d6977281bdb477237575b02200f6008bb5e3ef6edc95a7ce4dea5dc3181af` |
| `public/media/8774852/print.png` | 1032144 | `be2eea2e56760a21eb35c425b100cea1ce69efe3a9820550078d7660b3bec7b1` |

The RPi5 host Python does **not** have Pillow. Do not install packages or use host Pillow as an alternate renderer. The candidate must be made **in memory, read-only** with the reviewed immutable Coloring Pages importer runtime, whose image for `coloring-pages/main@337f78988064536250a6094a01563233d81891ff` is `ghcr.io/rozkalnsandris/coloring-pages@sha256:2a80b56c20c37f4a530059c3e438c6627fd962786e6590dd914e59e86a837ba8` and importer blob is `6d95f40112dc0ffae51e29af8508c305cf680f3e`.

## Stage 1: candidate proof — separate read-only decision

Before requesting any LIVE content mutation, prepare the candidate **without writing to production or staging**:

1. Confirm the current GitHub main/importer/image identity and catalogue SHA-256, full matching entry, all source/stable derivative SHA-256 and byte sizes, symlink safety, and shared `state/drive-ingest/.lock` exclusion. If any differ, **STOP** and refresh the GitHub plan first. An ordinary new publication changes the catalogue hash, so this historical baseline is intentionally strict.
2. Via the exact immutable importer image with read-only source bind, no network, no added privileges and no writable content mount, load private `originals/8774852/source.png`, *not* existing `preview.webp` (avoids double watermark). Use the reviewed Pillow code: `resized_copy(source, PREVIEW_MAX_WIDTH)` → `watermark_preview` → lossless `WEBP` save with `quality=100, method=6` into an **in-memory `BytesIO`**. Preserve 90%-width, 13% alpha, 28° and `ausmalwiese.de`. No re-import, no new PNG.
3. Record candidate byte size, 64-character SHA-256, portrait preview dimensions, screenshot/visual acceptance at mobile width, and WebP loading/performance. The only allowed filename is `preview-<full-sha256>.webp` at `public/media/8774852/` and URL `/media/8774852/preview-<full-sha256>.webp`. Check exclusive destination absence. Do **not** invent these values in advance.
4. Independently recheck that `thumb.webp`, `print.png` and private source bytes are unchanged. Lock the exact resulting candidate identity and updated catalogue entry in a separate reviewed, exact-baseline LIVE implementation plan. Only then can the owner authorize production mutation. A source-only plan merge is **not** that authorization.

## Stage 2: possible LIVE apply — NOT APPROVED

A future separately reviewed executor must hold the shared content-writer lock, revalidate **all** frozen identities and candidate bytes **before** first persistent write, and then write **only** the new full-SHA filename with exclusive creation (`O_EXCL`, `O_NOFOLLOW`), fsync it, and atomically switch **only** activity `8774852`'s `preview` URL in `public/catalog.json`. Its `thumb`, `print`, metadata, order, original and other 200 entries must be identical. The old `preview.webp` must remain present and byte-identical.

Afterward, verify catalogue SHA and exact entry, new candidate HTTP 200 with matching bytes, old URL HTTP 200 with unchanged bytes, original/print/thumb digests unchanged, and no unexpected paths written. Do not call the historical issue #74 regenerator: it is **hard-coded to a different activity** and migrates all three derivatives.

Any drift, unexpected destination, lock conflict, read-only proof failure or unexpected error: **STOP**, never retry, rollback, clean up, restart services or use another mutation path under the original authorization.

## Gates and follow-up

The immediate output of this PR is only the versioned contract, documentation, and automated **contract assertions**, with **no** runtime/app image rebuild or new image binary. GitHub PR CI must pass, and the owner must explicitly authorize merging the exact HEAD. A further **read-only candidate proof** and **separate exact-bound content/LIVE authorization** are necessary before any existing-media migration.

Related: `docs/PREVIEW_WATERMARK_V1.md`, `tools/coloring-pages-import`, `tools/coloring-pages-regenerate-derivatives`, and [Pillow Image documentation](https://pillow.readthedocs.io/en/stable/reference/Image.html).

