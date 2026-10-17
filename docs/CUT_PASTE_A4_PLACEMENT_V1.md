# Cut & Paste A4 placement — MAKE worksheet profile (#221)

**Scope:** This is the source-only editorial/authoring rule for an explicitly requested two-page `MAKE Cut & Paste <subject>` activity. It does **not** alter ordinary single-page `MAKE`, waive the canonical output-size rule for AI drafts, change the runtime print UI, or authorize `PUBLISH`. It supplements [Cut & Paste assembly](CUT_PASTE_ASSEMBLY_V1.md), [Cut & Paste QA](CUT_PASTE_QA_V1.md), and [Chat image commands](CHAT_IMAGE_COMMANDS_V1.md).

## Strict pre-export gate: finished assembled character must physically fit

For every `CUT`, require **art concept → canonical SVG/JSON parts and glue transforms → 100% full-size assembled silhouette → measured fit gate → two A4 sheets**. **Do not** reverse this sequence by independently generating finished A4 images and assuming the assembled figure will fit. The two 2026-10-17 pumpkin-with-wings visual attempts are `ASSEMBLED_FIT=FAIL` examples, not measured-mm evidence.

Form the **full union of actually attached base+cutout artwork** (all wing tips, ears, stems, hats, outline strokes and other projecting elements) at their correct page-1 physical placement and record `assembled_bbox_mm=[left,top,right,bottom]` and assembled width/height. After applying **the same `js/print.js` XY offset and scale used for printing the base page**, the full assembled silhouette must fit x=17..193 mm (**width ≤176 mm**) and y=17..256 mm (**height ≤239 mm**) with 1–2 raster px clearance inside the browser-safe page bounds. The **original page-1 print scale must equal 1.0**; do not count browser downscaling as a fix.

If an ImageGen-only flat raster lacks separate geometry, label `ART_CONCEPT_ONLY / ASSEMBLED_FIT=UNVERIFIED` and STOP rather than claiming a finished CUT. If any attached part would fall off page, mark `ASSEMBLED_FIT=FAIL` and reshape the **shared** source parts/anchors, then regenerate both A4 sheets from the same SVG source; preserve child-usable cut sizes. Never shrink only one image, use `Fit to page`, or regenerate the same incorrect proportions with a verbal promise. This is a documented required gate, **not proof that the currently installed exporter already enforces it**. Full contract: [Cut & Paste playbook](CUT_PASTE_PLAYBOOK_V1.md).

## First A4 sheet: body only

The current owner-approved authoring flow intentionally removes the small assembled reference from the printed worksheet.

1. ImageGen is used only for the initial character concept. After the owner returns vectorized SVG file(s), the accepted version becomes **SVG-only authoring**; do not redraw it with ImageGen.
2. **Page 1 contains only the base/body. Page 2 contains only the detachable cut parts.** A diagnostic assembled proof may be created separately for QA, but it is never printed on page 1.
3. Preserve the supplied SVG shapes, colors and relative proportions. Prefer translation only. If the complete intended assembly cannot fit the physical A4 limits, apply at most one **uniform shared scale** consistently to the base and every detachable part, then recompute all intended glue anchors.
4. Page 2 keeps each detachable shape at the same shared physical scale as the assembly and uses independent outward dashed cut guides with sufficient cutting clearance.
5. Never repair an accepted SVG handoff by regenerating one page or one part with ImageGen. A geometry/fit change must be derived again from the same SVG source.

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


**Current SVG-handoff placement rule:** the accepted SVG geometry is the source after vectorization. Derive page 1 from the base/body only and page 2 from the detachable vectors only. QA may construct a separate virtual full assembly from the same vectors and anchors to measure `ASSEMBLED_FIT`, but no preview is added to the printed first page. If fit requires a size change, use one consistent uniform scale across the complete character rather than independent page/part resizing. Human art and physical glue approval remain pending.

## Workflow and acceptance

- `MAKE Cut & Paste Fledermaus` (example intent): generate the character concept, receive owner-vectorized SVG file(s), then derive the base page and cut-parts page as an **unpublished** two-page draft.
- At print-master preparation, preserve the SVG geometry and common scale. Position page 1 body and page 2 parts independently within their safe areas, without adding an assembled preview. The reviewed CPU `tools/coloring-pages-print-master` handles A4 size and 15 mm bands; assembly fit still needs explicit SVG-derived geometry QA.
- Run canonical `VALIDATE-PRINT` on both exact final A4 PNGs **and** the stricter #221 raster ink/geometry QA. Confirm the browser `scale=1`, intended glue targets, complete cuts and no branding/footer overlap.
- Physically print A4 at 100% and cut/glue a sample; obtain exact-version owner review before publication. A CI/geometry PASS alone never claims human art or assembly approval.
- Keep printed originals and production binaries **out of GitHub**. This authoring rule gives no merge, Drive staging, LIVE or publication authority.

References: [MDN `@page`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40page), [Chrome page margins](https://developer.chrome.com/blog/print-margins), [W3C CSS Paged Media](https://www.w3.org/TR/css-page-3/).
