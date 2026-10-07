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
- One D1 database owns the small engagement state.
- The Raspberry Pi application remains static and does not host an analytics database or API.
- The browser currently creates a first-party random visitor ID only when the user first likes or prints. D1 stores only its SHA-256 hash for likes. The backend also supports a separate hash-only daily visitor counter; frontend activation of that counter is a later source step.
- An optional Workers Rate Limiting binding uses the random visitor ID rather than IP address.

## API
- `GET /api/stats/rankings?limit=6`
- `GET /api/stats/page?page_id=<id>&visitor_id=<optional>`
- `POST /api/stats/print` with `{"page_id":"...","visitor_id":"..."}`
- `POST /api/stats/like` with the same body; toggles the browser's like
- `POST /api/stats/visit` with `{"visitor_id":"..."}`; reserved for one anonymous browser-profile registration per UTC day

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
5. optionally bind a Worker Rate Limiter and use existing Cloudflare bot protections;
6. enable Cloudflare Web Analytics separately for aggregate views if it is not already enabled.

No RPi5 service, database, restart, package or host mutation is part of this design.

## Internal statistics dashboards

`/stats.html` is the read-only internal **engagement** dashboard. `/traffic.html` is the separate read-only **traffic and crawler analytics** dashboard linked from `/stats.html`. Both use the same design system as the public application and read only aggregate Stats V1 data.

- `GET /api/stats/overview` returns aggregate totals plus per-page print, like and anonymous page-view counters.
- The overview also returns `unique_browsers_7d`, calculated as `COUNT(DISTINCT visitor_hash)` across the current UTC day plus the previous six days.
- `/stats.html` renders print actions, likes, Popular, Trending and the engagement catalog table.
- `/traffic.html` renders website visits (explicitly labelled as not unique people), total/seven-day page views, Most viewed, crawler activity and a page-view catalog table.
- Both dashboards read the public `catalog.json` to map page IDs to titles, thumbnails and categories.
- Neither dashboard returns visitor IDs, visitor hashes, raw `likes` rows, IP addresses or Cloudflare credentials.
- Both pages carry `noindex,nofollow,noarchive` and are intentionally absent from public navigation.
- `Drucken` remains print intent: a click on the A4 print action, not proof of a physical print.

The source pages contain no authentication secret. Before production exposure, protect both exact internal paths (`/stats.html` and `/traffic.html`) or an equivalently bounded pattern with Cloudflare Access. That Access setting is a separate owner-gated Cloudflare mutation; it is not created by repository source or SIMPLE-DEPLOY.

The aggregate read-only API responses intentionally contain no visitor-level data.

## Anonymous browser-profile visitor counter

The backend contains an additive, privacy-bounded counter intended to provide a closer approximation to unique visitors than Cloudflare `sum.visits`:

- `daily_visitors` stores only UTC `day` plus SHA-256 `visitor_hash` of the existing first-party random browser ID.
- It stores no IP address, User-Agent, fingerprint, page history or raw visitor ID.
- The primary key `(day, visitor_hash)` makes repeated registrations from the same browser on the same UTC day idempotent.
- `POST /api/stats/visit` is same-origin-only, validates the random visitor ID, hashes it inside the Worker, and inserts with `INSERT OR IGNORE`.
- Visitor rows older than 30 days are deleted during successful visitor registration.
- `GET /api/stats/overview` exposes only the aggregate `unique_browsers_7d`; hashes are never returned to the browser.
- This metric represents **browser profiles, not people**. One person using multiple browsers/devices can count more than once, while multiple people sharing one browser profile count once.
- This commit does not activate frontend visitor registration. Activation requires a later reviewed application source change after the additive D1 schema and Worker version are LIVE.

Deployment order is fail-closed: apply the additive D1 schema first, then deploy the matching Worker, verify the new aggregate field, and only then enable frontend registration/UI in a separate application change.

## Admin traffic and crawler analytics

The separate `/traffic.html` dashboard uses a bounded traffic extension:

- `POST /api/stats/view` records one anonymous coloring-page detail view for a validated `page_id`.
- `daily_views` stores only `page_id`, UTC day and aggregate `view_count`. It stores no IP address, User-Agent, fingerprint or visitor ID.
- `GET /api/stats/traffic?days=7` (or `30`) is a fixed read-only proxy to Cloudflare GraphQL `httpRequestsAdaptiveGroups`.
- Visits and crawler rows use separate GraphQL queries. The visits query follows Cloudflare's hostname analytics pattern with a `$filter: filter` variable, hourly `dimensions { datetimeHour }`, and client-side summation of `sum.visits`; crawler path/User-Agent aggregation uses its own fixed filter/query shape.
- Cloudflare `sum.visits` is shown as **Website visits (not unique people)**. A visit is not an identified or unique person; one person can create multiple visits. `crawler_requests` is a separate request-count metric and must not be subtracted from visits to estimate humans.
- Crawler rows aggregate User-Agent, request count and top requested paths. URL query strings are intentionally not returned.
- Crawler names are labelled **User-Agent heuristic** because User-Agent strings can be spoofed. This is not equivalent to Cloudflare Bot Management verification.
- Adaptive Analytics data can be sampled; the dashboard marks sampled results.

Required Worker runtime configuration for the traffic endpoint:

- secret `CF_ANALYTICS_API_TOKEN`;
- variable `CF_ZONE_TAG`;
- optional `CF_ANALYTICS_HOST` (defaults to the `PUBLIC_ORIGIN` hostname).

Use a least-privilege Cloudflare API token with Analytics read access scoped to the relevant zone. The token is a runtime secret and must never be committed to GitHub or returned to the browser.

Activation is a separate Cloudflare owner gate. Applying additive D1 schema changes (including `daily_views` or `daily_visitors`), adding Worker secret/variables, deploying the updated Worker, and changing Cloudflare Access or analytics settings are **not** authorized by repository source work or by an application merge.
