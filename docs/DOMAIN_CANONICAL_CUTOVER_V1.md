# Ausmalwiese domain cutover — source preparation (#213)

## Target
`https://ausmalwiese.de` is the one preferred indexable hostname. The separate
`RPi5_main#996` edge change will permanently redirect
`https://coloring.rozkalns.net/<path>?<query>` to
`https://ausmalwiese.de/<path>?<query>`, preserving each path and query.
**This source change does not configure or authorize that redirect.**

## Scope in the coloring-pages source
- Homepage (`/`, `/index.html`) is self-canonical to `https://ausmalwiese.de/`.
- Kita (`/kita`, `/kita.html`) is self-canonical to `https://ausmalwiese.de/kita`.
- `js/detail.js` adds an `ausmalwiese.de/detail.html?id=<encoded-ID>`
  canonical only after successfully verifying the requested activity is renderable
  in `catalog.json`. The generic shell is not falsely canonicalized. The existing
  missing-ID `noindex` policy still applies only after a successful catalogue load.
- Both static sitemap fallback URLs, the `robots.txt` sitemap declaration,
  and the read-only catalogue-backed sitemap generator use the new origin.
  The generator emits only real published IDs, no print/admin or invented pages.
- The *existing* printed QR still targets `https://ausmalwiese.de/q`. Its
  host-locked Worker 302 is updated to send visitors **directly** to
  `https://ausmalwiese.de/`; counting, HEAD/prefetch and no-open-redirect
  logic and the old Stats origin allowlist/default remain unchanged.

## Mandatory owner gates / deployment sequence
1. **Hold application MERGE** until an owner-reviewed coordinated rollout.
   An owner-authorized `MERGE coloring-pages` touching HTML/JS can automatically
   trigger immutable-image publication and RPi5 SIMPLE-DEPLOY. GitHub source/CI
   alone is not production or Search Console verification.
2. **RPi5 runtime sitemap supersedes static fallback.** The deployed nginx
   `/sitemap.xml` route serves the host-owned catalogue-adjacent
   `/var/lib/coloring-pages/public/sitemap.xml` first if it exists.
   Simply shipping the new static `sitemap.xml` does **not** update that file.
   `RPi5_main` must separately review and pin the changed
   `tools/coloring-pages-sitemap` Git blob in
   `deploy/sitemap-publication-handoff-v1.json`, coordinate every catalogue writer
   using the approved shared advisory lock, and obtain owner LIVE approval for
   deterministic publication against an exact live-catalogue snapshot, with
   safe stage/hash/durability rules and read-only public verification.
   Do not run the host publisher from this source issue.
3. **Stats Worker separately deploys.** The changed `/q` destination is just
   Worker source; it does not deploy the Worker, modify Cloudflare routes,
   counters or secrets. Separately owner-authorize the exact Worker deploy
   through the approved path and validate `GET /q` and `HEAD /q`: status 302,
   `Location: https://ausmalwiese.de/`, no-store, no query-controlled destination,
   single GET counter increment, no prefetch/bot increments.
4. Deploy the application through its separately owner-authorized merge/release,
   confirm `https://ausmalwiese.de` serves correct self-canonicals and A4
   `detail.html?id=`/print flows; confirm updated dynamic sitemap is published.
   Ensure the new sitemap lists every currently published activity ID and no
   `coloring.rozkalns.net` URL. Submit it to Google Search Console only
   after the new property is verified by Google.
5. Only then let `RPi5_main#996` install a **single hostname-scoped 301**
   using independently checked Cloudflare Rules/zone credentials and an
   explicit owner LIVE decision. Test normal, unforced browser/public HTTPS
   for old root, Kita, detail, print, media and query URLs, no loops/chains,
   valid TLS, and unrelated `rozkalns.net` hostname behavior.
6. Google Search Console Change of Address remains a separate owner/browser
   step after both old/new properties are verified. It is not implied by DNS TXT.

## Known constraints
- `coloring-pages` source and repository tests do not prove LIVE sitemap,
  installed operator repins, Cloudflare Rules, Search Console ownership, or
  a future redirect. Do not mark the migration complete based on source checks.
- Historical SEO and sitemap activation reports retain old hostname references
  as dated evidence; do not rewrite those observations retroactively.
- No secrets, private media, worker credentials, destructive cleanup, retries,
  Cloudflare changes or host mutations are in this source-only scope.

## References
- https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes
- https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- https://developers.cloudflare.com/rules/url-forwarding/single-redirects/
- `RPi5_main#996`, `coloring-pages#213`
