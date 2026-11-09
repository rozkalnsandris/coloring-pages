# SVG Cut & Paste exporter (issue #220)

One source JSON/SVG part tree (contract #219) produces:

- **01-base.svg / 01-base.png** — page 1 with only the base/body;
- **02-cutouts.svg / 02-cutouts.png** — page 2 with only detachable cut pieces;
- **03-assembly-proof.svg** — QA-only assembled proof built from the exact same part graph;
- **04-manifest.json** — SHA-256 authoring/provenance manifest.

There is **no assembled preview printed on either A4 sheet**. The assembly proof is diagnostic only and must never be treated as printable page content.

Run from the repository root:

```sh
python3 tools/coloring-pages-cut-paste tests/fixtures/cut_paste/v1_bat_valid.json /tmp/ausmalwiese-fledermaus
```

Requires **Inkscape CLI** for PNG rendering plus pinned Pillow for opaque RGB/300-DPI serialization. If unavailable, the command stops before writing output. Output directory must be empty to prevent accidental overwrites.

The exporter:
- consumes one canonical per-character part graph;
- renders the exact same part IDs, colors, geometry and transforms in the A4 sheets and assembly proof;
- rejects duplicate/integrated features, invalid front-glue references, bad page dimensions and oversize layouts;
- creates outward vector cut contours from the original SVG silhouette;
- keeps printed page 1 free of the assembled preview;
- exports two A4 portrait pages as opaque RGB PNG **2480×3508** at approximately **300 DPI**;
- keeps all output as drafts until the separate QA and owner publication gates pass.

The exporter is deterministic for the same source and refuses a non-empty output directory rather than overwriting prior output.

**Cutting geometry, assembly-fit and raster QA:** see [Cut & Paste QA v1](CUT_PASTE_QA_V1.md) and [Cut & Paste playbook v1](CUT_PASTE_PLAYBOOK_V1.md).

Automated source/raster checks do **not** certify physical child usability. Final readiness still requires the current mandatory assembly-fit checks, exact A4 validation, human visual review, physical cut-and-glue QA and a fresh exact-version owner `PUBLISH` authorization.
