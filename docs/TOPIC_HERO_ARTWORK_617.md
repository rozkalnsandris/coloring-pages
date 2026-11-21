# Winter website Topic Hero artwork — issue #617

The owner approved the **exact colorful Winter Hero** for Ausmalwiese on 2026-11-21 (reply: **"der"**), after supplying the previously approved **Einhörner** website Hero as the visual style reference. Selected ImageGen reference: `e815d6f3-4ace-453d-90cd-dafd234734cd`.

## Exact owner-approved artwork

- Canonical source asset: `assets/winter-topic-hero.webp`, **RGB WebP**, **1755 × 896 px**, **180,328 bytes**, SHA-256 `402ac180590351e93c8729769344e745f8185752c97aba21985a543130d9e9e3`, Git blob SHA-1 `f722f6a6ad6d217abcab1bba820e00b7f41392b1`.
- The local owner-approved WebP was decoded and checked against the repository upload using the file size and exact Git blob digest. The artifact was **not** re-created, cropped, resized or recompressed in the source branch.
- Composition: consistent friendly **brown-and-white Ausmalwiese dog** with a red paw-print backpack/harness beside a smiling white **snowman** wearing a red winter hat, red mittens and a striped red/yellow scarf. Snowy firs, bright blue sky, snow-covered trees and a park bench form the scene. The left edge is softly faded to create a text-safe area; small `Ausmalwiese.de` brand lettering appears at lower right. It contains **no embedded H1, HTML CTA or unverified item counts**.
- German alt text: `Ausmalwiese-Hund mit einem fröhlichen Schneemann in einem verschneiten Winterpark`.
- German browse intro: `Winter-Ausmalbilder für Kinder: Entdecke winterliche Malvorlagen und drucke sie kostenlos auf A4 aus.`.
- Exact owner decision and review scope: [#617](https://github.com/rozkalnsandris/coloring-pages/issues/617) under [shared Hero standard #565](https://github.com/rozkalnsandris/coloring-pages/issues/565).

The approved illustration includes a recognizable dog and brand logo, but owner visual approval alone **does not establish pixel-identical logo-master certification**. Visually inspect the actual rendered Hero across supported mobile and desktop sizes before claiming strict branding equivalence.

## Runtime and verification boundaries

The existing `winter` seed in `metadata/topics.json` is `seasonal`, `active_from: "12-01"`, `active_to: "02-29"` (cross-year season). This source definition is preserved. The protected runtime `/topics.json`, **not this manifest or seed file**, determines which managed Topic labels are actually registered at runtime. The Hero decorates only the browse state `/?topic=winter`. No indexed `winter.html`, separate `/winter` SEO route, sitemap/canonical, fictional print items, live content publication or protected Topic registration is created.

The website Hero WebP is **not** an A4 printable coloring-page original or a `PUBLISH` asset. Source QA covers strict image-byte and manifest integrity, deterministic adapter projection and cache hash, and local-fixture Chromium responsive assertions at **320, 390, 412, 768, 1440 CSS px**. It covers a keyboard-focusable native `Thema` select, browser Back/Forward, overflow and unknown/label-only/unregistered Topic fallbacks. The QA does **not** establish native browser 200% zoom (#612), manual logo aesthetics, real-device physical printing, screen-reader behavior or LIVE deployment.

No new CSS, protected production content, runtime changes, secrets or permissions are authorized by the source-only PR. Merge and LIVE gates are separate owner decisions.
