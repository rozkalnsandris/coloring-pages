# SEO preflight v1 — source review, not a release

## Boundary

This document records the current source-level search discoverability gaps and a safe next implementation plan. It does **not** publish a sitemap, robots.txt, canonical tags, generated per-page HTML, Cloudflare settings or production content. The RPi5 catalogue, not this GitHub repository, owns the LIVE IDs and print media.

## Findings to verify before a separate SEO implementation

1. Home (`/` and `/index.html`) and `/kita` have initial HTML titles and German descriptions. Choose one canonical address for each route, verify nginx redirects and actual LIVE responses, and avoid contradicting canonical/redirect/sitemap signals.
2. The index catalogue and detail content are populated from runtime `catalog.json` with JavaScript; `detail.html?id=<id>` initially has a generic `<title>` and description. Google can render JS, but a static app shell is not guaranteed to expose discoverable per-item content to all crawlers. Test actual rendered HTML and Search Console coverage before promising individual item indexing.
3. An unknown `detail.html?id=` currently uses HTTP 200 for the HTML shell, then shows a client-side unavailable state. Investigate a server-side missing-item/404 or static per-item HTML strategy before indexing these query URLs; do not claim the browser message is a real HTTP 404.
4. This source tree does not ship `robots.txt` or `sitemap.xml`. Do not manufacture a fixed ID list from editorial samples or GitHub tests. If approved, generate a crawlable sitemap from a freshly verified production catalogue, include only public canonical URLs and define a safe publish/update owner boundary.
5. Campaign query labels (`?campaign=dortmund-01`) and fragment routes must not become accidental duplicate canonical URLs. Choose query-safe canonical behavior only after verifying `/kita`, `/index.html`, and `/detail.html?id=` routes.
6. Internal `/stats.html` and `/traffic.html` already use `noindex,nofollow,noarchive`, but this does **not** provide access control. Cloudflare Access protection is a separate owner-gated LIVE task; do not expose confidential metrics through SEO work.
7. Verify consent/privacy/legal requirements and any externally hosted fonts before a wider Germany-focused campaign; this source-only SEO preflight grants no legal, tracking or Cloudflare mutation.

## Next owner-gated SEO work

- Read-only: inspect LIVE status codes, redirect chains, rendered HTML, indexability and catalog cardinality; establish sample mobile/desktop crawl results without mutating production.
- Design: choose the canonical home/Kita/item URL strategy and whether to serve static per-item HTML; do not add a generic detail canonical that collapses every item to one URL.
- Implement in a separately reviewed source PR: metadata, meaningful HTTP statuses, catalogue-derived sitemap and appropriate automated tests. Respect the approved image-trigger and LIVE authorization boundaries.
- Verify deployment and indexing only with fresh evidence; GitHub CI passing does not establish Search Console indexing.

## References

- https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics
- https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- https://developers.google.com/search/docs/crawling-indexing/javascript/dynamic-rendering
