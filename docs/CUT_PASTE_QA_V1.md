# Cut & Paste QA — issue #221

This stage upgrades the #220 authoring exporter to construct a **separate outward vector cut path**, instead of a thick dashed stroke placed on the art itself.

## Dependencies and use
Shapely is pinned for the offline authoring/CI geometry checks only. It is **not** installed by the production importer Dockerfile.

    python3 -m pip install -r requirements-build.txt -r requirements-cut-paste.txt
    python3 -m unittest discover -s tests -p 'test_cut_paste*' -v
    python3 tools/coloring-pages-cut-paste tests/fixtures/cut_paste/v1_bat_valid.json /tmp/ausmalwiese-bat

The output directory must be empty, and Inkscape CLI must be present for two opaque RGB 2480×3508 A4 PNG outputs. Every generated activity remains a DRAFT and requires a later exact owner PUBLISH before any content ingest.

## Machine gates
- Only one absolute, closed and non-self-intersecting SVG silhouette is supported per part (M/L/C/Q/Z). Curves are sampled at up to 0.12 mm *control polygon* steps, then a round-join outward Shapely buffer creates the dashed cutting contour. Unsupported constructs fail closed. This is an authoring vector approximation, not a proof of mathematical exactness for all SVG syntax.
- Each cutout has exactly one ID, an accessible front glue target, a geometry-aligned anchor and at least the declared glue contact area (actual polygon intersection). Original art dimensions must contain their vector silhouette.
- Separate cut guides must fit inside x=17..193 mm and y=17..256 mm and have at least 4 mm between stroke envelopes (scissor allowance). The finished example must not collide with any full-scale assembled component, including a hat or wings.
- Actual exported PNG dimensions, mode, ~300 DPI, and visible nonwhite pixel bounds are checked using the same RGB >=250 white threshold as the current browser print.js. Raster ink must fit in the browser/footer-safe area without shrinking. The 15 mm all-white margin follows automatically from that stricter ink box.
- The generated local authoring manifest records geometry results, actual raster ink bounds, source SHA-256, and file hashes. A recorded machine PASS alone never authorizes publication.

## Art-first illustration quality gate (human, not CI)
Before treating any machine-validated A4 draft as a candidate for printing/publishing, apply [Cut & Paste art-first visual review](CUT_PASTE_ART_DIRECTION_V1.md). The 2026-10-15 primitive bat/pumpkin prototypes are **VISUAL_FAIL** despite correct A4 geometry. Realistic, appealing editable Bézier contours and a human visual acceptance of the **exact final assembled reference** are required before progressing to paper assembly. Geometry-only sample fixtures must not be promoted on test success. Output `art_review.status=PENDING` means **not approved**; it is not a substitute for the human decision.

## Human/owner gate still required
Print at 100% on real A4 (including branding/QR from Ausmalwiese print UI), cut out and glue the parts using a real physical prototype. Check where paper overlaps, the finished result against the small top-right picture, any very small/tight cuts, uncut glue tabs, and any printer-induced scaling. Record observed pass/fail for the bat **and a non-bat** example. No such physical observation can be inferred from GitHub CI or a manifest.

If any geometry check rejects the original #219 bat demo fixture, repair the canonical SVG source before declaring that pilot accepted; **never** weaken QA to fake a pass. Until both physical examples and owner visual approval are available, issue #221's complete DoD stays open even when its CI is green.

No binary originals in GitHub. No source merge, runtime, Drive, RPi5 or production publishing permissions are granted by this QA work.
