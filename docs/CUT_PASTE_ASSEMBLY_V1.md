# Cut & Paste assembly source contract v1 — #219

Status: **source-only authoring contract proposal**. The renderer is #220, full geometric and print QA is #221. No new `MAKE` or `PUBLISH` authorization is implied. Follow `AGENTS.md`, `docs/CHAT_IMAGE_COMMANDS_V1.md`, `docs/MEDIA_STANDARD_V1.md` and the current `js/print.js`.

## One canonical scene graph
- A character is **one versioned SVG-derived JSON record** conforming to `metadata/cut-paste-character-v1.schema.json`. The record is the source for the printable base, parts and assembled preview. Never generate a second, independent AI example image.
- Every part has a unique stable `id`, `feature`, role (`base` or `cutout`), a closed local `art.outer_path_d` in SVG path notation, interior paths/colors, `art.size_mm`, an assembled translate/rotate/scale/z-index transform, and a cutting guide derived from **that same outer silhouette**.
- All SVG local and page coordinates are millimetres, origin top-left, y downward; a part's `size_mm` defines its local SVG viewBox. The assembled transform applies to artwork, derived cutting contour and glue anchor together; `page_layout.assembled_origin_mm` then positions it on sheet 1.
- There is **exactly one** base, and each cutout must have one declared front-facing glue anchor, target part, contact area floor and assembly order. The base has `glue=null` and `built_in_features` marking integrated anatomy.
- No feature may simultaneously be built into the base and provided as a separate cutout. Eyes, feet, ears, wings etc. must be intentionally assigned to exactly one location. Left/right counterparts get distinct IDs. Unused decorations and orphan/duplicate parts are forbidden.
- A finished small top-right example is a uniformly downscaled copy of the **same assembled parts and transforms**. Its geometry cannot be independently modified after rendering. The cutout sheet contains exactly one of every detachable ID.

## Assembly and cutting
- Glue targets must be accessible from the **front** at the declared assembly sequence; no hidden back-gluing behind a permanently attached pumpkin, branch or wing. Require sufficient overlapping contact area, scale compatibility and consistent layering.
- Each **physical cut target**, including the body silhouette, gets its own closed **dashed black guide** offset from its precise outer SVG contour. Artwork contours stay solid; dashes must never be applied to interior artwork or independently redrawn.
- Keep generous space between pieces and cutting guides. Prefer large rounded shapes and few pieces for ages 3–6; do not rely on tiny teeth, fine horns or tightly branched edges.
- A decorative feature exists only where the assembled result shows it. If the result cannot be assembled mechanically from those exact cutouts, QA must FAIL before an A4 render is approved.

## Two ordered A4 pages
1. **Körper/Grundform:** large base, deliberately lacking the cutout features, plus one small finished example at the upper right. The preview must not overlap the base cutting guide **or the complete hypothetical finished full-scale assembled silhouette** including ears, wings and hat.
2. **Ausschneideteile:** only the exact detachable parts, one per ID, spaced for scissors; separate dashed guide around every piece. No page frames, background filler, watermarks or baked-in QR/footer.

Physical output: exact opaque RGB **2480×3508** A4 portrait PNG with approximately 300 DPI and 15 mm precise-white outer bands. The current `js/print.js` footer-safe **ink region** is x=17..193 mm and y=17..256 mm (176×239 mm), leaving a 22 mm footer, gap, bottom margin and guard. The visible ink on *each sheet*, including the small preview and dashed lines, must fit without the browser's `fitA4InkBounds` shrinking the base (`scale=1`). The actual source PNG remains unbranded. These are authoring constraints; do not claim paper-print proof without a physical A4 test.

## Example fixtures and PASS/FAIL meanings
`tests/fixtures/cut_paste/`:
- `v1_bat_valid.json` — nine parts: plain bat body with built-in belly, two ears, two wings, two eyes, one mouth and one hat. Eight cutouts, no unattached leaf, pumpkin, star or separate feet. Structural plus **basic** semantic PASS only; not physically verified or publishable.
- `v1_bat_invalid_duplicate.json` — duplicate left-eye part ID and feature: **semantic FAIL**.
- `v1_bat_invalid_integrated_wing.json` — left wing is both integrated into base and a separate cutout: **semantic FAIL**.

JSON Schema enforces allowed types and value ranges, not array-property uniqueness, SVG path closure, visual overlaps, side-of-glue access, exact raster ink bounds or physical scissor usability. `tests/test_cut_paste_authoring_contract_v1.py` exercises only basic semantic examples. #220 must derive all sheets from the same source; #221 must implement independent geometry, image-output and hands-on gates. Do not treat passing current fixture tests as full art/print validation.

## Acceptance and trust boundary
Before promoting a character, record part inventory and glue order; derive base + parts + full assembled proof + small cloned preview; run geometric/print tests; physically cut and assemble one paper example; and obtain owner approval of the exact output. A later explicit owner `PUBLISH` plus fresh v2 publication preflight is required for each approved two-page set.

No merge, deploy, production upload, Drive staging, RPi5/LIVE or permissions/settings mutations are authorized by this document. No production PNG originals or unlicensed third-party art in GitHub.
