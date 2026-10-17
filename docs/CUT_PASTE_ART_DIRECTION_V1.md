# Cut & Paste — art-first visual quality review (issue #221)

**Status:** editorial acceptance criteria for original draft art; not an autonomous art critic and not an approval to publish. This supplements the canonical part/assembly contract (#219), exporter (#220), and geometric/print QA (#221). Use **one seasonal tracker** (#222 Halloween / #223 Weihnachten); do not make separate issues for each character.

## Why the two 2026-10-15 experiments failed visual review
The previous bat's body was a uniform oval with angular wings and triangle ears; the pumpkin was a near-circle with a rectangular stem, oval eyes, and basic triangular nose. Their A4 dimensions and cut-outline checks do **not** establish appealing preschool illustration quality. Treat these particular prototypes as **VISUAL_FAIL / do not publish**, even if a source geometry fixture passes CI.

## Correct authoring order
1. **Art first:** draw an original friendly character illustration as an editable vector master. Use deliberately placed cubic `C` / quadratic `Q` Bézier paths and smooth nodes; focus on the whole silhouette and proportions before splitting the character into glue pieces. The generator's supported cut-silhouette path commands are **absolute `M/L/C/Q/Z`**, not the full SVG path standard.
2. **First owner visual review:** show a comfortably readable complete character image **before** generating A4 cutouts. Review as a piece of illustration: anatomy, balance, visual personality, legibility, no accidental floating pieces and no copyright-derived character copying. A machine PASS does not grant this review.
3. **Split from the same art:** assign what stays on the base and what is detached. Preserve one canonical SVG path tree / component IDs; the small final example and detachable shapes are derived from exactly those objects/transforms, with no independent AI regeneration or geometric approximations by eye.
4. **Deterministic physical geometry:** derive the outward dashed cut lines from each finished original path; ensure easy scissors, reasonable size, front-facing glue surfaces, part clearances, full assembled silhouette / preview clearance, and footer-safe native A4.
5. **Print, cut, glue, then approve:** inspect a real A4 print at 100%, physically place each part and compare the result with the example. Record exact source/preview and owner decision. Only then can a separate explicit owner `PUBLISH` gate be considered; do not pretend a local review file itself conveys publication permission.

## Visual art standards (human PASS / FAIL)
- **Expressive silhouettes rather than primitive approximations.** Pumpkin: asymmetric rounded lobes and gently curved, coherent stem (not a circle and block). Bat: substantial rounded head/body, softened ear edges, natural flowing scalloped wing membranes (not a basic oval with wedges).
- **Simplification without losing identity.** A 3–6-year-old should recognize the character without accessory labels. Keep a few large, intentional shapes and a consistent dark outline; no tiny teeth/claws or random detail used to mask poor proportions.
- **Clear integrated vs detachable features.** One feature exists either on the base or on the cutout sheet. All detached pieces are present and correctly oriented in the assembled preview; no arbitrary leaves, stars or redundant ornaments.
- **Front assembly physically plausible.** Layer order must not imply sliding a wing/leaf underneath a fully attached body. If a part is drawn behind, either redesign it for visible front gluing or explicitly revise the assembly procedure and review geometry.
- **Quality of the reference example:** sufficiently large and readable at printed A4 scale, clear separation from the entire full-size assembled figure, same colors and outlines as physical parts. Do not mistake an oversized source screenshot for readability at physical print size.
- **Age-appropriate cutting:** no excessive part inventory, sliver-thin bridges, sharp forks, excessively tight concave curves, poorly differentiated guide strokes, or tiny islands.
- **No generic decoration:** use only artwork essential for the character / task. White background, no baked-in page border, QR or watermark, no unlicensed stock/reference tracing.
- **Art approval is subjective and explicit:** automated geometry/PNG validators may only report machine checks, never claim this rubric passed. Record a manual pass/fail with the exact source SHA and visually inspected preview. *PENDING* or *FAIL* blocks editorial promotion.

## Source/review separation and evidence
The current `tests/fixtures/cut_paste/v1_bat_valid.json` is a **structural + geometric test example**, not visually accepted artwork. Its filename `valid` does **not** mean print-ready or art-approved. The bat/pumpkin October prototypes reviewed by the owner are **visual FAIL** regardless of their PNG dimensions.

A concept review can be kept as a design preview outside production originals; if a human-approved concept is converted into SVG paths, re-review the **actual** source-derived finished result. Never treat auto-tracing as a faithful geometry conversion without manual verification. Do not commit production PNG originals, approvals, personal details, or external rights assumptions into GitHub.

## Recommended review record (manual, separate from exporter)
```text
Character / season:
Canonical input source SHA-256:
Preview / artwork version:
Artwork silhouette and friendly proportions: PASS / FAIL
Reference and cutout consistency: PASS / FAIL
Scissors / age 3–6 suitability: PASS / FAIL
Physical print + assembly observed: PASS / FAIL / NOT_DONE
Owner acceptance of exact version: APPROVED / REJECTED / PENDING
Notes / next design correction:
```

**Documentation:** Inkscape's official [Pen Tool guide](https://inkscape-manuals.readthedocs.io/en/latest/pen-tool.html) explains hand-shaped Bézier nodes; the [Tracing an Image guide](https://inkscape-manuals.readthedocs.io/en/1.1/tracing-an-image.html) warns bitmap tracing is not perfectly faithful and color results may be hard to edit. The [SVG 2 Paths specification](https://www.w3.org/TR/SVG/paths.html) defines path commands and Bézier curves.

**Boundaries:** This art-first review process remains source/editorial work for #221. No new per-character issue, merge, Drive, PUBLISH, LIVE, settings or permission authority is created.
