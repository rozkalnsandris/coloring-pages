# SEO preflight v1 — reviewed source and staged SEO steps

## Boundary

This document records the current source-level search discoverability gaps and a safe next implementation plan. The initial preflight did **not** publish a sitemap, robots.txt, canonical tags, generated per-page HTML, Cloudflare settings or production content. This document is not a release. The separately reviewed home/Kita canonical implementation changes only two HTML heads and its matching tests; the RPi5 catalogue, not this GitHub repository, owns the LIVE IDs and print media.

## Verified home/Kita canonical scope (2026-10-09)

A minimum-sufficient read-only RPi5 origin and public HTTPS check confirmed HTTP 200 for `/`, `/index.html`, `/kita` and `/kita.html`. Public `/kita/?campaign=seo-probe` returns HTTP 308 with relative `Location: /kita?campaign=seo-probe`. None of these source HTML heads initially provided a canonical link. No Cloudflare or LIVE mutation was performed.

The chosen canonical URLs are `https://coloring.rozkalns.net/` for both home variants and `https://coloring.rozkalns.net/kita` for both Kita variants. These are fixed absolute URLs in the two HTML source files. The same canonical is served for campaign-tagged variants, deliberately omitting marketing query parameters. This expresses a preference for search engines; it does not itself create HTTP redirects or guarantee indexing.

Individual `detail.html?id=...` pages remain without a canonical pending a catalogue-backed per-ID strategy, and internal admin routes retain their existing `noindex`. If the public project moves to another domain, canonical URLs must be reviewed and updated together with the approved domain migration. No sitemap, robots.txt, Cloudflare or runtime content change was part of the initial canonical work. The separate static sitemap/robots follow-up, if merged, lists only the verified canonical home and Kita URLs; it does not pretend to enumerate LIVE coloring pages.

Google guidance: https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls and https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics.

## Findings to verify before a separate SEO implementation

1. Home (`/` and `/index.html`) and Kita (`/kita` and `/kita.html`) have verified HTTPS HTTP 200 responses. The reviewed source adds canonical links for these two pages only. Keep future redirect and sitemap signals consistent with these choices.
2. The index catalogue and detail content are populated from runtime `catalog.json` with JavaScript; `detail.html?id=<id>` initially has a generic `<title>` and description. Google can render JS, but a static app shell is not guaranteed to expose discoverable per-item content to all crawlers. Test actual rendered HTML and Search Console coverage before promising individual item indexing.
3. The HTML shell for `detail.html?id=` still returns HTTP 200. A focused client-side follow-up adds a `robots` `noindex` meta tag **only** after `catalog.json` loads successfully and the requested ID is confirmed absent. A catalogue network failure, HTTP failure or invalid response must **not** mark a potentially valid detail as `noindex`. This is a conservative soft-404 mitigation, **not** an HTTP 404 or an indexing guarantee. A later separately reviewed server-side 404/static-per-item HTML strategy is still required for comprehensive crawl semantics.
4. The focused static sitemap/robots follow-up adds only the two verified canonical HTML routes (`/` and `/kita`) and no dates, detail IDs, admin routes or invented catalogue data. Individual coloring pages still need a separately reviewed catalogue-backed sitemap strategy that includes only fresh LIVE IDs and respects content-publication authority; do not fabricate a fixed ID list.
5. Campaign query labels (`?campaign=dortmund-01`) and fragment routes must not become accidental duplicate canonical URLs. Choose query-safe canonical behavior only after verifying `/kita`, `/index.html`, and `/detail.html?id=` routes.
6. Internal `/stats.html` and `/traffic.html` already use `noindex,nofollow,noarchive`, but this does **not** provide access control. Cloudflare Access protection is a separate owner-gated LIVE task; do not expose confidential metrics through SEO work.
7. Verify consent/privacy/legal requirements and any externally hosted fonts before a wider Germany-focused campaign; this source-only SEO preflight grants no legal, tracking or Cloudflare mutation.

## Static sitemap/robots follow-up

The scoped source change ships a minimal UTF-8 sitemap at `/sitemap.xml` containing only `https://coloring.rozkalns.net/` and `https://coloring.rozkalns.net/kita`. The `/robots.txt` file permits crawling and advertises that sitemap URL; it deliberately does **not** block `/stats.html` or `/traffic.html` because their existing `noindex` directives must remain visible to crawlers. `robots.txt` is not an authentication or indexing-control substitute.

Both files are ordinary application-image inputs via the reviewed `Dockerfile`; GitHub source alone does not prove LIVE publication. This partial sitemap intentionally makes no claim about the runtime catalogue's IDs or update times. If the public domain changes, update both the sitemap and robots reference together with canonical URL migration.

Google documentation:
- https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- https://developers.google.com/search/docs/crawling-indexing/robots/intro
- https://developers.google.com/search/docs/crawling-indexing/block-indexing

## Detail missing-ID noindex follow-up

The reviewed JavaScript branch handles one narrow case: when an ID is not present in a successfully fetched and parsed production catalogue, dynamically append `<meta name="robots" content="noindex">` to the detail head. Do not treat a temporary catalogue outage as proof of deletion. No generic canonical URL is added to the detail shell. The `js/detail.js` version parameter is updated to the exact content hash to prevent stale browser-side execution. Initial HTTP 200 remains unchanged; indexing outcomes must be validated separately.

Official Google guidance: https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics and https://developers.google.com/search/docs/crawling-indexing/javascript/fix-search-javascript

## Verified-entry meta description follow-up

For a successfully loaded existing catalogue activity with at least one page, the detail JavaScript updates the existing HTML meta description with the catalogue title and the actual A4 page count. The original generic description is retained if the catalogue request fails, the ID does not exist, the catalog is invalid, or the detail cannot be rendered. The script's HTML cache-busting version is pinned to its SHA-256 prefix, and regression tests cover one- and multi-page items as well as missing/failure paths.

This is client-side metadata, not per-item static HTML, a catalogue-derived sitemap, a new per-ID canonical, or an HTTP status-code change. Google's displayed snippet may differ from the supplied description. Indexing is not guaranteed.

Official documentation:
- https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics
- https://developers.google.com/search/docs/appearance/snippet

## Per-activity canonical follow-up

The shared `detail.html` source intentionally has no static canonical because it represents many distinct catalogue IDs. After a successfully loaded and renderable catalogue entry, `js/detail.js` appends **one** canonical link to `https://coloring.rozkalns.net/detail.html?id=<url-encoded-catalogue-id>`. Marketing query parameters are not copied to canonical URLs. Repeated page hydration must not duplicate the canonical link. No canonical is added when the ID is absent, the catalogue cannot be fetched/parsed, or the activity is not renderable. The separately reviewed missing-ID `noindex` behavior remains intact.

Google recommends providing canonicals in original HTML where possible; it supports a JavaScript-inserted canonical if the source cannot contain the correct per-item URL, but indexing and Google-selected canonicals are not guaranteed. This change does **not** create per-ID static HTML, server-side HTTP 404, catalogue-derived sitemap or Search Console submission. The site domain is frozen only for this existing production hostname and must be revisited with any authorized domain migration.

Google documentation:
- https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics
- https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls

## Next owner-gated SEO work

- Read-only: inspect LIVE status codes, redirect chains, rendered HTML, indexability and catalog cardinality; establish sample mobile/desktop crawl results without mutating production.
- Design: choose the canonical home/Kita/item URL strategy and whether to serve static per-item HTML; do not add a generic detail canonical that collapses every item to one URL.
- Implement in a separately reviewed source PR: metadata, meaningful HTTP statuses, catalogue-derived sitemap and appropriate automated tests. Respect the approved image-trigger and LIVE authorization boundaries.
- Verify deployment and indexing only with fresh evidence; GitHub CI passing does not establish Search Console indexing.

## References

- https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics
- https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- https://developers.google.com/search/docs/crawling-indexing/javascript/dynamic-rendering

## Catalogue-derived sitemap generator (source-only)

The current root sitemap contains only the two verified canonical URLs for home
and Kita; the authoritative published activity IDs belong to the RPi5 LIVE
public/catalog.json, not to GitHub. The standalone read-only helper
tools/coloring-pages-sitemap --catalog PATH now generates a candidate UTF-8 XML
sitemap on stdout from that catalogue, retaining those two static URLs and
adding one canonical detail.html?id=ID URL per verified renderable record.
IDs are validated using the importer ID contract, duplicates and malformed
records fail closed, output order is stable, and no invented lastmod dates or
marketing query parameters are emitted. A multi-page activity is one URL.
The single-file 50,000-URL/50 MB limits fail closed rather than truncating.

Not activated: This helper does not modify the importer, its pinned RPi5
operator identity, the public content store, Dockerfile, nginx, existing static
/sitemap.xml, Cloudflare or Google Search Console. It has no production write
side effect and does not assert that entries are currently reachable or indexed.
Passing tests is source evidence only.

A later separately reviewed runtime lane must (1) check the helper against the
current LIVE catalogue and representative detail pages, (2) stage and validate
the exact output and its equivalence to the published catalogue, (3) publish it
atomically through a trusted content/host operator without breaking the
current importer boundary, (4) route public /sitemap.xml to the generated
artifact with a fail-safe fallback, and (5) verify public XML and Search
Console status. Production writes, host/operator changes and Search Console
submission require their own exact owner authorization.

Reference: https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap

