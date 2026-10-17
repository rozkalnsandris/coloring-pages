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
1. **Hold application MERGE** until the owner approves one coordinated rollout.
   A `MERGE coloring-pages` with HTML/JS may automatically publish an immutable
   image and activate RPi5 SIMPLE-DEPLOY. Neither that merge nor GitHub CI
   authorizes Cloudflare Worker changes, the host sitemap, or the old-host 301.
2. **Prepare the RPi5 operator upgrade first, without content publication.**
   `RPi5_main` has reviewed the `ausmalwiese.de` generator pin and coordinated
   three-component upgrade in PR #1029 (source only). The installed ingester,
   publisher and generator remain independent LIVE evidence. Obtain verified
   exclusion of all Drive/external automation, importer, post-ingest and direct
   catalogue writers for a bounded maintenance window; do not infer this from
   a free advisory lock, cron keyword scan or Docker read-only web mount alone.
   Separately authorize the root-owned quiescence attestation and then the exact
   coordinated LIVE upgrade. Preserve the enabled Post-PUBLISH marker; if any
   step fails or drifts, STOP without retry, rollback, cleanup or reactivation.
   **Keep PUBLISH/ingestion suspended until the new app origin works.**
3. **Deploy and verify the application via separately authorized owner MERGE.**
   Once RPi5 has the matching new operators and the maintenance boundary holds,
   an owner-authorized merge may trigger the normal GHCR → `:production` →
   RPi5 SIMPLE-DEPLOY application rollout. Verify the exact deployed image,
   `/health` and `/ready`, both new-domain hosts and self-canonical home,
   Kita and verified detail pages, plus the existing A4 detail/print flow.
   Stop on release uncertainty; do not automatically proceed to Worker or sitemap.
4. **Stats Worker separately deploys from the reviewed source.** The PR changes
   the hard-coded `/q` redirect in `cloudflare/stats-worker.js`, not its
   running Worker. After the matching source merge, require a separate exact
   Cloudflare Worker LIVE authorization and trusted deploy procedure; verify
   `GET /q` and `HEAD /q` yield 302 with
   `Location: https://ausmalwiese.de/`, no-store, no arbitrary query-controlled
   redirect, and expected counting/prefetch exclusions. Never infer that an
   application deployment updated the Worker.
5. **Publish and verify the dynamic sitemap, still excluding catalogue writers.**
   The deployed nginx `/sitemap.xml` route prefers the existing host-owned
   catalogue-adjacent `/var/lib/coloring-pages/public/sitemap.xml` over the
   image-bundled static fallback. The reviewed pinned generator
   `49c8ba34cf0a4c4ab100463df9adacc4c6e90c2c` is *not* itself a
   published sitemap. Separately owner-authorize one exact LIVE publication
   through the installed trusted publisher, using the same-inode ingest lock,
   catalogue SHA-256 freeze, staged XML verification, atomic replacement and
   read-only HTTP proof. Confirm every published activity ID is present and
   no `coloring.rozkalns.net` URL remains. Do not publish from this source PR.
6. **End the maintenance window only by a separate owner decision.**
   Resume any suspended writer or PUBLISH flow only after the app, Worker and
   sitemap have each passed their LIVE checks. A quiescence attestation file
   never substitutes for continuing writer exclusion; any attestation removal
   or service reactivation needs its own explicit LIVE authority.
7. **Redirect the legacy host last.** Only after destination checks pass,
   `RPi5_main#996` may install one exact-hostname Cloudflare 301 under a
   separate owner LIVE gate. Preserve path/query, verify one hop for root,
   Kita, detail, print and media, and rule out loops or unrelated-host changes.
8. **Search Console remains separate.** Submit the verified sitemap and perform
   the Change of Address only after relevant properties and LIVE conditions
   are independently confirmed; DNS TXT alone does not prove GSC ownership.

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
