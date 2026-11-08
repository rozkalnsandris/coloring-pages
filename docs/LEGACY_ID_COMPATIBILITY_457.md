# Legacy ID compatibility — issue #457

The canonical alias source is `metadata/legacy-id-aliases.json`, bound to production catalogue SHA `efa6a736839657f849606f665b09bd51dff1165a1c9c2038e9d5b7e720cc7ba9`, 477 entries / 30 legacy IDs, #455 plan manifest `80538dd2bda9755212c599d1b75a106673e1eb5c774cebc47f4192e0478fad9c`, and alias-list SHA `24cf6ec46ba2ad2b1791c8aff8975937bb9b0e629076d0d34b828ee30d6308b5`. Do not maintain a second hand-edited map.

The image build validates that JSON and generates nginx maps from it. Browser basket reconciliation reads the same JSON only after cutover activation.

Compatibility is deliberately latent before data movement. The exact activation marker is:

`/var/lib/coloring-pages/public/.legacy-id-aliases-80538dd2bda9755212c599d1b75a106673e1eb5c774cebc47f4192e0478fad9c.active`

Before that marker exists, existing legacy detail/print/media behavior is unchanged and the alias JSON returns 404. After a separately authorized one-shot migration has verified the new catalogue/media/state and creates the marker, known old detail/print IDs return direct 308 redirects, missing old media paths redirect to the same filename under the new ID, and saved basket IDs translate only when the exact new catalogue target exists. Old+new selections deduplicate before the five-sheet reconciliation. Unknown IDs retain normal 404/noindex behavior.

The marker must be created only after the later data migration succeeds for this exact manifest. Sitemap publication, aggregate Like/Print migration, reports/GoatCounter treatment, ADMIN archive/jobs and RPi5 data movement remain separate gates.

SEO continuity follows the Google Search Central contract recorded in #455/#457: exact one-to-one permanent redirects, no chains, new canonical/internal URLs, and long-lived old redirects.
