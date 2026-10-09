# Kita landing-page pilot — source and activation status

The original landing-page prototype was reviewed on 2026-10-07. Its verification notes below are historical source evidence, not a current production check. The campaign funnel follow-up later merged into GitHub source (PR #140); its Cloudflare D1 migration and Worker activation still require fresh LIVE verification and separately scoped owner authorization. A source merge alone is not proof of Cloudflare activation.

## Page and content

`/kita` serves `kita.html`; `/kita/` redirects to `/kita` preserving the query.
`/kita.html` also works on a plain static preview server. Both main CTAs open
`index.html#neu`, the existing catalog. Example cards open the existing
`detail.html?id=…` preview and its unchanged A4 print flow.

The page follows the existing static HTML shell from `detail.html`, reuses
`app.css`, the existing fonts, mobile menu and `createCatalogCard()` from
`app.js`. `kita.css` only adjusts the compact layout and focus outline. No new
card component, artwork, content store, dependency or backend is introduced.
The hero and catalog links work without JavaScript; examples use the site's
existing JavaScript catalog rendering. Failed/empty catalog loads show a short
fallback message; missing selected IDs are omitted, never replaced automatically.

`js/kita.js` holds six editorial ID references, not copies of metadata:

| Existing ID | Reviewed example |
| --- | --- |
| 3147286 | Dino Baby |
| 7078476 | Feuerwehrauto |
| cp-000008 | Deutsches Alphabet – A |
| 7884237 | Eule zum Ausschneiden und Zusammensetzen |
| 2612596 | Tulpe Einfach |
| 0821068 | Fröhliches Kätzchen |

These public thumbnails were visually reviewed on 2026-10-07 as generic,
unbranded subjects. Titles, thumbnails, age/difficulty and page-count badges
always come from the current `catalog.json`. Keep the selection explicit and
review replacement artwork before changing IDs. No branded figures or automatic
category selection. No safe dedicated number example was selected for this pilot.

## Initial prototype campaign limits (2026-10-07; superseded in source by PR #140)

The following text describes the initial landing-only prototype before the aggregate funnel source change. It must not be read as the current GitHub feature contract.

Proposed shared QR URL: `/kita?campaign=dortmund-01` (same for all letters).
Only this known campaign value is forwarded to same-origin catalog/detail links.
Unknown values are ignored; no recipient identifiers, cookies, session storage
or additional visitor IDs are added. The query is preserved for the immediate
handoff only, not persisted through subsequent browsing or later visits.

Kita loads call the existing `ColoringStats.trackVisit()` once. This contributes
to the existing host/day aggregate; it does **not** count Kita campaign visits
separately. Detail-view and print-intent hooks remain unchanged. Print intent
means pressing the print action, not proof of paper output.

Current Stats V1 has no campaign dimension, landing-to-catalog conversion event
or cross-day returning-user metric. Merely forwarding the query does not make
these measurable in the internal dashboards. Existing aggregate Cloudflare page
views/referrers may help if enabled; this prototype does not verify activation
or assume query-level reports are available.

Smallest future measurement change: extend the existing Stats Worker with
allowlisted campaign + event counters by day for landing and catalog entry,
and optionally existing detail/print events. Have the browser send those labels
only for the shared pilot campaign, with no free-text query values or recipient
IDs. This needs a separately reviewed source change and separately authorized
Cloudflare/schema activation. Do not infer repeat use from the current daily
unique-IP HMAC: it deliberately changes each day. Leave returning usage
unmeasured unless an existing approved privacy-safe aggregate supports it.

## Historical local prototype verification (2026-10-07)

Use an isolated checkout and an uncommitted public-catalog snapshot plus only
needed public media under `catalog.json` / `media/`, or route those requests in
the browser. Never commit those runtime copies. A plain Python static server can
preview `/kita.html`; exact `/kita` routing is owned by the nginx source.

Checks: `python3 -m unittest discover -s tests -v`, `node --check js/kita.js`,
`git diff --check`. `test_kita.py` checks packaged routing, linked asset hashes,
reviewed-ID selection against changing catalog metadata, graceful failures and
campaign allowlisting. Its JS checks use Node without npm dependencies; they skip
when Node is unavailable. Existing CI builds the application image.

Browser checks should cover 320/390/720/1280px widths, menu/Escape and keyboard
focus, CTA → catalog, example → detail → A4 print, catalog failure/empty/missing
IDs, and JavaScript disabled. Thumbnails alone should load on the landing page;
print assets load only after entering the existing print flow.

### Verified for this prototype (2026-10-07)

- 99 existing unit tests plus all 4 new Kita tests passed; Python compilation,
  JavaScript syntax and whitespace checks passed.
- Chromium at 320, 390, 720 and 1280px: no horizontal overflow, six decoded
  thumbnails, primary CTA at least 56px tall. At 390px the first cards start
  around 516px from the top, inside the initial 844px viewport.
- Mobile menu open/Escape/focus return and first-tab skip link passed.
- Primary CTA reached the existing catalog with the pilot label; category
  filtering worked. Dino example reached its detail preview and print action.
  The print iframe called `window.print()` (stubbed during verification) with
  the original 2480×3508 canvas; existing view/print hooks emitted the expected
  page ID to intercepted local stats requests. No actual printing or production
  analytics writes occurred.
- Empty, unrelated-only and HTTP-failed catalog responses retained working
  catalog CTAs. The primary CTA also worked with JavaScript disabled.
- Read-only, network-isolated local nginx smoke: config valid, `/kita` returned
  200 with `Cache-Control: no-cache`, `/kita/?campaign=dortmund-01` returned 308
  to `/kita?campaign=dortmund-01`, then identical HTML. This local route check used
  the available nginx 1.31.5 image; repository CI builds the actual Dockerfile.
- Local screenshots: `output/playwright/kita-390.png`, `kita-1280.png`, and
  `kita-detail.png`. Screenshots/media snapshots are verification artifacts only,
  excluded from the source PR.


## Current merged GitHub source: aggregate campaign measurement (PR #140)

This is a source contract, not proof that Cloudflare migration or Worker deployment has occurred. Fresh Cloudflare runtime evidence is required before declaring production campaign counters active.

The source-level follow-up uses only the shared allowlisted campaign `dortmund-01`.
The browser carries that campaign from `/kita` into the existing catalog and detail flow.
The Stats Worker stores only aggregate daily event counts for four funnel stages:

- `landing` — the campaign Kita page was loaded;
- `catalog` — the user followed the campaign into the main catalog;
- `detail` — a coloring-page detail view occurred while the campaign label was present;
- `print` — the existing A4 print action was pressed while the campaign label was present.

The internal `/stats.html` dashboard shows the four 30-day counters. These are event
counts, not unique Kitas or unique people. Repeated loads/actions can increment them.
The existing daily unique-IP HMAC remains separate and is not joined to the campaign,
so cross-day returning use is deliberately not inferred.

The new D1 table and Worker code require a separately owner-authorized Cloudflare
activation after source merge. The public application remains compatible with the
currently deployed Worker while that activation is pending: extra campaign fields are
ignored by the old write endpoints and the dashboard treats a missing campaign endpoint
as unavailable instead of failing the existing statistics.
