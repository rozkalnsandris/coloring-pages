# SVG Cut & Paste exporter (issue #220)

One source JSON/SVG part tree (contract #219) produces **two ordered A4 SVG sheets**, one exactly cloned assembled preview, a separate assembled proof, **two 2480×3508 RGB ~300-DPI PNG draft exports**, and a SHA-256 authoring manifest.

Run from the repository root:

\`\`\`sh
python3 tools/coloring-pages-cut-paste tests/fixtures/cut_paste/v1_bat_valid.json /tmp/ausmalwiese-fledermaus
\`\`\`

Requires **Inkscape CLI** for PNG rendering plus pinned Pillow for opaque RGB/300-DPI serialization. If unavailable, the command stops before writing output. Output directory must be empty to prevent accidental overwrites.

The exporter rejects duplicate features, invalid front-glue references, bad page dimensions, previews intersecting the full assembled silhouette, and cutouts too large to pack in two A4 portrait columns. It assembles its preview by transforming **the identical SVG part graph**, never independent AI generation. All outputs are drafts; none is uploaded or published.

**Important limitation, reserved for #221:** a thick dashed stroke along the canonical outer SVG path is currently only an **approximation** of a true offset cutting contour; it is not accepted as a certified geometric offset. Precise collision, physical glue accessibility, scissor clearance, and full browser-print ink testing are also not proven by #220 tests. The #219 example is a structural fixture, not a child-ready design. Do not claim this activity is printable/publication-ready until separate geometric and manual QA are complete. Production binary originals stay outside GitHub; no LIVE operation here.
