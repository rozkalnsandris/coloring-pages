# Advent website Topic Hero artwork — issue #619

The owner visually approved the colorful **Advent Hero** in this project conversation on **2026-11-21** (reply: **"der"**) after requesting it to follow the supplied Ausmalwiese Winter reference illustration. The owner-approved composition was generated as a PNG (ImageGen reference: `c1994cb4-e5c4-451f-9021-eed34a763f77`). The subsequent website WebP is an optimized derivative of this approved artwork, **not a byte-identical copy of the PNG**.

## Exact source and website artifact

- Source generation: original RGB PNG **1755 × 896 px**, **2,057,981 bytes**, SHA-256 `18f482b31f7954c38a70fa417866449c30dc3a4cfdfa321b7c26e53f94c1674a`. The original generation is conversation evidence; production coloring-page print originals are not involved.
- **Expected reviewed website source asset:** `assets/advent-topic-hero.webp`, RGB WebP **1755 × 896 px**, **191,818 bytes**, SHA-256 `ae442cd34ea9feead220a1bd17eb5bf84c1a38f4be126dd8371251f5b54c5960`, expected Git blob SHA-1 `688fcd153f2fa02fafde1f3706c2076411d27198` (compute and verify from actual GitHub-uploaded file before PR/CI). The file has already been decoded and verified locally; do not regenerate or recompress it while committing.
- Optimizing PNG into WebP changes encoded bytes and may change fine pixel details; the stated approval is for the visible composition, as delivered in the conversation, not a claim of mathematically identical PNG/WebP pixels.
- The artwork shows the recognizable friendly **brown-and-white Ausmalwiese dog** with a red paw-print backpack/harness beside a **green Advent wreath with four glowing red candles** in a bright snowy park; a lantern, two wrapped gifts, softly glowing lights, snow-covered trees and a warm winter sunrise support the Advent theme. The left edge is faded to provide a text-safe region, with small `Ausmalwiese.de` branding at lower right; there are no embedded headings, CTA or invented catalogue counts.
- German alt: `Ausmalwiese-Hund neben einem Adventskranz mit vier brennenden Kerzen im verschneiten Park`.
- German browse intro: `Advent-Ausmalbilder für Kinder: Entdecke festliche Malvorlagen und drucke sie kostenlos auf A4 aus.`.
- The source approval and work boundaries are recorded under [#619](https://github.com/rozkalnsandris/coloring-pages/issues/619) (parent [#565](https://github.com/rozkalnsandris/coloring-pages/issues/565)).

The owner-approved brand impression does **not** independently certify pixel-perfect identity with a logo master or official mascot artwork. Do not assert exact logo provenance from visual approval alone.

## Runtime, QA and owner gates

The source `advent` Topic remains `seasonal` with `active_from: "11-20"`, `active_to: "12-24"`. Protected runtime `/topics.json` remains the authority for actual managed Topic registration and labels, independent of this manifest. This approved artwork decorates browse-only `/?topic=advent`, not a new indexed `/advent` editorial page. No static `advent.html`, catalogue modification, fabricated print entry, sitemap/canonical change, protected runtime mutation or publication is in scope.

Source QA includes binary SHA-256/byte count and WebP geometry, manifest integrity, deterministic adapter projection and cache version, plus local-fixture Chromium tests at **320, 390, 412, 768 and 1440 CSS px**. It checks page Hero layout and native `Thema` selector, keyboard focus, Back/Forward, unknown/unregistered and label-only fallbacks. CI success cannot establish human appearance approval, native browser 200% zoom (#612), real-device printing, screen-reader testing or LIVE deployed-image identity.

**Source-only authorization:** branch, scoped docs/tests/assets, Draft PR and exact-HEAD CI through READY. Exact owner `MERGE` approval, then any authorized bounded LIVE process and runtime verification, are separate gates.
