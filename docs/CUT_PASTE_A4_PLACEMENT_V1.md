# Cut & Paste A4 placement — MAKE worksheet profile (#221)

**Scope:** This is the source-only editorial/authoring rule for an explicitly requested two-page `MAKE Cut & Paste <subject>` activity. It does **not** alter ordinary single-page `MAKE`, waive the canonical output-size rule for AI drafts, change the runtime print UI, or authorize `PUBLISH`. It supplements [Cut & Paste assembly](CUT_PASTE_ASSEMBLY_V1.md), [Cut & Paste QA](CUT_PASTE_QA_V1.md), and [Chat image commands](CHAT_IMAGE_COMMANDS_V1.md).

## First A4 sheet: use all available height, not just canvas centering

1. Draw a simple attractive **fully assembled original** character. Derive the large **bare body/base**, the small finished reference and the detachable objects from the **same** canonical artwork/part IDs/transforms. One paper component must not appear both built into the base and as a cutout.
2. Place the small finished reference near the **top** of the first sheet and the large base as far **down** as possible **without overlapping** the small reference, the full-size virtual assembled artwork, or the future cutting area. Do **not** enlarge the reference as filler. The body remains the useful child-sized element.
3. Place by actual **ink bounds**, not by the PNG's white background, image frame or AI crop. Keep the two page-1 illustrations as separate transformable layers/groups, never shift the whole page as one.
4. **Do not resize either the body or the cutout parts independently** to satisfy margins. Change only their placement after the approved artwork geometry is frozen. A size change requires a fresh full-scale part-alignment and physical cutting check.
5. Page 2 contains the exact detachable shapes and outward dashed cut lines, with sufficient 4 mm cutting clearance per #221, within the same browser-safe ink rectangle.

## Physical bounds — Ausmalwiese browser printing

Source: current [js/print.js](../js/print.js) `visibleInkBounds` and `fitA4InkBounds`, with the A4 print layout in [Media standard](MEDIA_STANDARD_V1.md).

| Dimension | Portrait A4 ink bounds | Why |
| --- | --- | --- |
| Sheet | **210 × 297 mm**, **2480 × 3508 px** | 300 DPI print master |
| Exact-white paper margin | **15 mm** on all four sides | Canonical print-master gate |
| Browser no-downscale ink left/right | **17..193 mm** | 15 mm white + 2 mm guard |
| Browser no-downscale ink top | **17 mm** | **Not 15 mm:** a 2 mm guard applies |
| Browser no-downscale ink bottom | **256 mm** | 297 − 41 mm for brand footer and safety |
| Max ink-box height | **239 mm** | 256 − 17 |

The browser's `scale = min(1, 176/inkWidth, 239/inkHeight)`. Its ink-white test treats one RGB pixel as white only if **all three channels ≥250**; anything else counts as ink. The browser maps exact PNG width with `210/2480 mm per pixel` and height with `297/3508 mm per pixel`, which avoids accumulating nominal DPI rounding error.

Use `px = mm × 300 / 25.4` for nominal authoring estimates: **15 mm ≈177 px**, **17 mm ≈201 px**, **256 mm ≈3023 px**. These are **not** permission to place ink precisely on a rounding boundary and incur a 0.9999 print scale. Determine positions from full PNG raster ink bounds using the browser's actual A4 ratios, move the top reference **up** until its topmost visible pixels are at or slightly inside 17 mm, and move the body **down** until its bottommost cut/drawing pixels are at or just inside 256 mm. Recheck `scale=1`, x-guard, no overlap and body-to-parts geometry after every change. A 1–2 px internal buffer is preferable to accidental scaling. If either item cannot fit, fail closed.

Example of a correct vertical result: small ink starts at **~17.1 mm**, base ink ends at **~255.95 mm**, both remain the **same pixel sizes** and the print fit returns `scale=1`. Printing the same content with small ink at exactly 15 mm while base reaches 256 mm extends over 241 mm, *exceeding* the 239 mm area, and therefore triggers an unwanted full-page downscale.


**Exporter implementation (issue #220):** `tools/coloring-pages-cut-paste` deterministically translates the whole hypothetical full-scale assembly downward in the **page-1 layout only** when deriving the body printable position. The original per-part transforms and page-2 cutout positions stay unchanged, and glue/collision QA runs on a shifted copy of the same geometry. The small preview remains an exact clone of the original assembled scene and is aligned by its visible bounds to ~17.4 mm (allowing outline bleed). If either cannot fit, the exporter fails instead of resizing. Human art and physical glue approval remain pending.

## Workflow and acceptance

- `MAKE Cut & Paste Fledermaus` (example intent): generate character/master, base + small exact copy, and the separate components page as an **unpublished** two-page draft.
- At print-master preparation, deterministically place top preview and lower base using independent translations from their shared component master. Keep every part’s assembled scale/anchor and the cutout sheet invariant. The reviewed CPU `tools/coloring-pages-print-master` handles A4 size and 15 mm bands; it does **not** itself solve the two-component optimal placement—this must be explicitly done by the authoring/exporter, then revalidated.
- Run canonical `VALIDATE-PRINT` on both exact final A4 PNGs **and** the stricter #221 raster ink/geometry QA. Confirm the browser `scale=1`, no preview/full-size collision, intended glue targets, complete cuts and no branding/footer overlap.
- Physically print A4 at 100% and cut/glue a sample; obtain exact-version owner review before publication. A CI/geometry PASS alone never claims human art or assembly approval.
- Keep printed originals and production binaries **out of GitHub**. This authoring rule gives no merge, Drive staging, LIVE or publication authority.

References: [MDN `@page`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40page), [Chrome page margins](https://developer.chrome.com/blog/print-margins), [W3C CSS Paged Media](https://www.w3.org/TR/css-page-3/).
