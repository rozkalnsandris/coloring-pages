# Ausmalwiese preview-only watermark — issue #169

Status: source implementation for **new imports only**, pending CI/review. Existing published media is unchanged.

## Design and media boundaries

- `preview.webp` (and `preview-N.webp` in a multi-page activity) gets a raster-baked, diagonal, centered `ausmalwiese.de` watermark. This is not a CSS overlay; it remains visible when the standalone image URL is opened or saved.
- Watermark: dark navy RGB(16,40,77), **13% maximum alpha** on the graphic, **46% of preview width** before rotation, **28° rotation**. Uses the Pillow built-in scalable default font; no new fonts/assets or network dependencies. Lossless WebP remains the output.
- `thumb.webp`, private `originals/<id>/source*.png`, public `print*.png`, direct PNG downloads and browser A4 printing remain unwatermarked.
- Preview aspect ratio/orientation, existing width limit (1000px), catalogue schema, single-/multi-page filenames, newest-first order remain unchanged.
- Accidental copying protection (drag/context menu) is not implemented: it is ineffective as security and can harm accessibility. This feature is attribution, not DRM.

## Publication and trust boundaries

- Normal **new imports** produce their own previously unused `/media/<new-id>/preview*.webp` assets via the existing importer. No published page ID or media URL is overwritten.
- Already-published media remain immutable, even if their previews are unbranded. Changing them requires a **separate exact-baseline, new-full-SHA-256 filename, owner-authorized LIVE/content migration** with catalogue URL switching. This PR does not include that migration.
- `tools/coloring-pages-import` is pinned by the trusted RPi5 publish operator contract. A source change will cause **fresh importer identity alignment to fail** on subsequent PUBLISH until a separately reviewed `RPi5_main` source pin/operator alignment is authorized. No assumption that a merged image can publish content automatically.
- No Drive, RPi5, DNS, Cloudflare, settings, release or LIVE operations are granted by this document.

## Verification

- Pillow CPU-only raster tests for portrait and landscape, single/multiple pages, source byte stability and clean thumbnail/print.
- Lossless `preview.webp` must differ from a clean white preview, with attributable color range around 13% alpha. Tests show the saved WebP contains actual changed pixels.
- CI includes an immutable-image smoke test; Docker build verifies the packaged Pillow supports `ImageFont.load_default(size=...)`.
- Before public rollout: inspect watermarks over actual representative line art and colorful worksheets at Galaxy A55 size, estimate WebP byte-size change, verify available font in built importer image. These visual/performance checks cannot be claimed from source unit tests alone.

References:
- [Pillow ImageFont](https://pillow.readthedocs.io/en/stable/reference/ImageFont.html)
- [Pillow ImageDraw](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html)
- [Pillow Image methods](https://pillow.readthedocs.io/en/stable/reference/Image.html)
- [MDN immutable URL caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching)
