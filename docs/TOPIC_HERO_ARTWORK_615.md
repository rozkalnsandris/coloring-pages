# Einhörner website Topic Hero artwork — issue #615

The owner approved the **exact colorful Einhörner Hero** in the project chat on 2026-11-21 (reply: **"der"**), using the previously owner-approved Sport website Hero as the style reference. Selected image-generation reference: `0f8e21f1-1fa8-448e-ba93-6f1487043752`.

## Approved asset

- Path: `assets/einhoerner-topic-hero.webp`. Final approved **RGB WebP**, **1755 × 896 px**, **224,144 bytes**; SHA-256 `c2a995c219d126c14cfa6b35454f5cf0192820a89b3cb36446566cb7d68ee294`; Git blob SHA-1 `74cb3cc2f65894303a6399cfe1089bb253ae302a`.
- The exact approved WebP was checked against the branch upload identity, not regenerated/recompressed/cropped. This is **colored website Hero art**, not a printable A4 coloring-page original or `PUBLISH` input.
- Composition: original brown-and-white Ausmalwiese puppy with red paw harness/backpack beside a white unicorn with pastel rainbow mane and golden horn; vivid meadow, flowers, trees, rainbow, bright sky, softly blended text-safe left edge and small lower-right `Ausmalwiese.de` mark. The source artwork contains no embedded H1, body copy, item counts or CTA.
- German image alt: `Ausmalwiese-Hund neben einem weißen Einhorn mit Regenbogenmähne auf einer bunten Wiese`.
- German intro: `Einhörner-Ausmalbilder für Kinder: Wähle eine Malvorlage aus und drucke sie kostenlos auf A4 aus.`.
- Approval evidence: [issue #615](https://github.com/rozkalnsandris/coloring-pages/issues/615), under [shared standard #565](https://github.com/rozkalnsandris/coloring-pages/issues/565). This owner image approval does **not** independently certify pixel-exact trademark/brand-master identity. Visually check logo, dog and artwork against approved Sport/Herbst reference at responsive widths before claiming aesthetic QA PASS.

## Source-only implementation and limits

The existing `einhoerner` seed in `metadata/topics.json` is not proof of a deployed runtime Topic. Actual `/topics.json` is authoritative. Reviewed `topics.einhoerner` manifest entry and its generated JS adapter decorate only the **browse-only** `/?topic=einhoerner` state; unavailable/invalid/unregistered runtime Topics must not fabricate the Hero. No new `einhoerner.html`, indexed `/einhoerner`, canonical, sitemap, protected Topic-registration, production catalogue/media or fake items.

QA includes deterministic asset/manifest integrity and JS projection plus source-local Chromium checks at **320/390/412/768/1440 CSS px**, native `Thema` select/keyboard focus, URL/history transitions, unknown/label-only/unregistered fallbacks and no stale art. This CI is **not** native browser 200% zoom (#612), physical-device/print/screen-reader verification or LIVE proof.

Any merge is a separate owner gate; source implementation alone confers no LIVE, ADMIN, Drive, publication, permissions, secrets or settings authority.
