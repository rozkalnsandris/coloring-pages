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
- The browser creates a first-party random visitor ID only when the user first likes or prints. D1 stores only its SHA-256 hash for likes.
- An optional Workers Rate Limiting binding uses the random visitor ID rather than IP address.

## API
- `GET /api/stats/rankings?limit=6`
- `GET /api/stats/page?page_id=<id>&visitor_id=<optional>`
- `POST /api/stats/print` with `{"page_id":"...","visitor_id":"..."}`
- `POST /api/stats/like` with the same body; toggles the browser's like

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
