# Cloudflare engagement stats v1

## Purpose
Keep Coloring Pages analytics off the Raspberry Pi while supporting:
- all-time print-click counts;
- one reversible like per browser/page;
- **Beliebte Malvorlagen** ranked by all-time `Drucken` clicks;
- **Trending** ranked by `Drucken` clicks from the current day plus the previous six UTC days.

A print count means **print intent** (the user pressed the print action), not proof that paper was physically printed.

## Runtime split
- Cloudflare Web Analytics remains the preferred aggregate source for page views/referrers/device data.
- One same-origin Cloudflare Worker owns `/api/stats/*`.
- One D1 database owns the small engagement state plus short-lived day-scoped visitor HMACs.
- The Raspberry Pi application remains static and does not host an analytics database or API.
- The browser creates a first-party random visitor ID only when the user first likes or prints. D1 stores only its SHA-256 hash for likes.
- Public page loads call the Stats Worker once; the Worker uses Cloudflare's request IP only transiently to derive an HMAC from UTC day + public hostname + IP. Raw IP addresses are never written to D1 or returned by the API.
- An optional Workers Rate Limiting binding uses the random engagement visitor ID rather than IP address.

## API
- `GET /api/stats/rankings?limit=6`
- `GET /api/stats/page?page_id=<id>&visitor_id=<optional>`
- `POST /api/stats/print` with `{"page_id":"...","visitor_id":"..."}`
- `POST /api/stats/like` with the same body; toggles the browser's like
- `POST /api/stats/visit` with an empty body; records one day-scoped host visitor HMAC

Write endpoints require same-origin browser traffic. D1 uniqueness on `(page_id, visitor_hash)` prevents a browser from storing multiple likes for one page.

## Ranking contract
- Popular: `page_stats.print_count DESC`.
- Trending: summed `daily_prints.print_count` over seven UTC calendar days.
- Likes are displayed as an independent signal and are not mixed into either ranking.
- The frontend maps returned page IDs against live `catalog.json`; unknown IDs are not rendered.

## Cloudflare owner gate
Repository source does **not** create or mutate Cloudflare resources. Activation requires separate explicit owner authorization:
1. create/bind one D1 database and apply `cloudflare/stats-schema.sql`;
2. deploy `cloudflare/stats-worker.js`;
3. bind the Worker to `/api/stats/*` on `coloring.rozkalns.net`;
4. set `PUBLIC_ORIGIN=https://coloring.rozkalns.net`;
5. set a separate random secret `VISITOR_HMAC_KEY` (at least 32 characters) for day-scoped visitor HMACs;
6. optionally bind a Worker Rate Limiter and use existing Cloudflare bot protections;
7. enable Cloudflare Web Analytics separately for aggregate views if it is not already enabled.

No RPi5 service, database, restart, package or host mutation is part of this design.

## Internal statistics dashboards

`/stats.html` is the read-only internal **engagement** dashboard. `/traffic.html` is the separate read-only **traffic and crawler analytics** dashboard linked from `/stats.html`. Both use the same design system as the public application and read only aggregate Stats V1 data.

- `GET /api/stats/overview` returns aggregate totals plus per-page print, like and anonymous page-view counters.
- `/stats.html` renders print actions, likes, Popular, Trending and the engagement catalog table.
- `/traffic.html` renders the Stats Worker’s latest available daily privacy-preserving unique-IP count, Cloudflare website visits (explicitly labelled as not unique people), total/seven-day page views, Most viewed, crawler activity and a page-view catalog table.
- Both dashboards read the public `catalog.json` to map page IDs to titles, thumbnails and categories.
- Neither dashboard returns visitor IDs, visitor hashes, raw `likes` rows, IP addresses or Cloudflare credentials.
- Both pages carry `noindex,nofollow,noarchive` and are intentionally absent from public navigation.
- `Drucken` remains print intent: a click on the A4 print action, not proof of a physical print.

The source pages contain no authentication secret. Before production exposure, protect both exact internal paths (`/stats.html` and `/traffic.html`) or an equivalently bounded pattern with Cloudflare Access. That Access setting is a separate owner-gated Cloudflare mutation; it is not created by repository source or SIMPLE-DEPLOY.

The aggregate read-only API responses intentionally contain no visitor-level data.

## Host-scoped unique visitors

The production site is `coloring.rozkalns.net` inside the shared `rozkalns.net` Cloudflare zone. Cloudflare's GraphQL rollups expose `uniq { uniques }` for unique IP counts, while hostname filtering is documented on `httpRequestsAdaptiveGroups`; AdaptiveGroups does not expose the same unique-IP aggregate. A zone-level rollup therefore cannot safely be presented as a host-scoped Coloring Pages metric.

Coloring Pages keeps the metric host-scoped without storing raw IP addresses:

- Public `index.html` and `detail.html` loads call `POST /api/stats/visit`. Internal admin pages do not call this endpoint.
- The Worker reads `CF-Connecting-IP` only in memory and derives `HMAC-SHA-256(VISITOR_HMAC_KEY, UTC-day + hostname + IP)`.
- D1 stores only `day` and the HMAC in `daily_visitors`, unique on `(day, visitor_hash)`.
- Each successful visit also removes rows older than yesterday; the read path ignores anything older than yesterday.
- `GET /api/stats/traffic` returns the latest available daily count plus its UTC date. It never returns visitor hashes or raw IP addresses.
- The metric is approximate rather than a count of people: shared NAT can merge several people, changing IPs can split one person, clients that never execute the public JavaScript are not counted, and automated clients that execute JavaScript can be counted.

The HMAC key is a dedicated Worker runtime secret and must never be committed to GitHub.

## Admin traffic and crawler analytics

The separate `/traffic.html` dashboard uses a bounded traffic extension:

- `POST /api/stats/visit` records one host-scoped daily unique-IP HMAC without persisting the raw IP address.
- `POST /api/stats/view` records one anonymous coloring-page detail view for a validated `page_id`.
- `daily_views` stores only `page_id`, UTC day and aggregate `view_count`. It stores no IP address, User-Agent, fingerprint or visitor ID.
- `GET /api/stats/traffic?days=7` (or `30`) combines the latest D1 daily unique-visitor count with fixed read-only Cloudflare analytics queries for visits and crawlers.
- Visits and crawler rows use separate `httpRequestsAdaptiveGroups` GraphQL queries. The visits query follows Cloudflare's hostname analytics pattern with a `$filter: filter` variable, hourly `dimensions { datetimeHour }`, and client-side summation of `sum.visits`; crawler path/User-Agent aggregation uses its own fixed filter/query shape.
- Cloudflare `sum.visits` is shown as **Website visits (not unique people)**. A visit is not an identified or unique person; one person can create multiple visits. `crawler_requests` is a separate request-count metric and must not be subtracted from visits to estimate humans.
- Crawler rows aggregate User-Agent, request count and top requested paths. URL query strings are intentionally not returned.
- Crawler names are labelled **User-Agent heuristic** because User-Agent strings can be spoofed. This is not equivalent to Cloudflare Bot Management verification.
- Adaptive Analytics data can be sampled; the dashboard marks sampled results.

Required Worker runtime configuration for the traffic endpoint:

- secret `CF_ANALYTICS_API_TOKEN` for Cloudflare visits/crawler analytics;
- secret `VISITOR_HMAC_KEY` (at least 32 characters) for the day-scoped visitor HMAC;
- variable `CF_ZONE_TAG`;
- optional `CF_ANALYTICS_HOST` (defaults to the `PUBLIC_ORIGIN` hostname).

Use a least-privilege Cloudflare API token with Analytics read access scoped to the relevant zone. The token is a runtime secret and must never be committed to GitHub or returned to the browser.

Activation is a separate Cloudflare owner gate. Applying the `daily_visitors` D1 schema, adding `VISITOR_HMAC_KEY` or other Worker secret/variables, deploying the updated Worker, and changing Cloudflare Access or analytics settings are **not** authorized by repository source work or by an application merge.
