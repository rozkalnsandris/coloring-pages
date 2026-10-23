# Traffic dashboard: Cloudflare-only data boundary (#368)

**SOURCE CANDIDATE ONLY — no Cloudflare Worker deployment, RPi5 LIVE action, token, D1 migration or production verification.**

## Data source separation

`/traffic.html` uses only read-only `GET /api/stats/traffic?days=7|30`.
That endpoint obtains the **Website visits** and **crawler requests** from the Cloudflare GraphQL `httpRequestsAdaptiveGroups` dataset through the existing Stats Worker. The browser does not contact the GraphQL endpoint or receive Cloudflare tokens. It does not read the Cloudflare D1 `/overview` or `/campaigns` endpoints, the catalogue or RPi5 traffic logs. The separate `/stats.html` dashboard continues to show engagement counters from Cloudflare D1 (prints, Likes, QR and pilot attribution). No existing D1 data is deleted.

| Traffic UI | Provider source | Semantics / caveat |
| --- | --- | --- |
| Website visits | `httpRequestsAdaptiveGroups.sum.visits` with hourly grouping | Cloudflare HTTP Analytics visits, **not unique people**. Can be sampled. |
| HTTP requests | `httpRequestsAdaptiveGroups.count` in the same exact-host hourly series | Cloudflare request events (not visitors and not page views); may include bots and static resources, and may be sampled. Available only after separate owner-gated Worker activation. |
| Crawler requests and top paths | `httpRequestsAdaptiveGroups.count`, grouped by User-Agent and path | User-Agent heuristic, non-verified bots, successful 2xx/3xx requests only, sampled; counts cannot be subtracted from visits. |
| Unique visitors | **N/A**, explicitly not displayed as zero | `httpRequests1dGroups.uniq.uniques` is a zone rollup and is **not proved hostname-scoped**; never substitute it for unique visitors to `ausmalwiese.de`. |
| Image-specific/detail-page views | **Not displayed** | Former data came from custom D1 counters rather than Cloudflare-native page views; zone HTTP path reporting without query strings cannot reliably separate `detail.html?id=...` activities. |
| Instagram profile/story/reel arrival counts | **Not displayed** | Existing D1 campaign attribution is not Cloudflare HTTP/Web Analytics attribution. Campaign data remains in the Worker for separate uses. |

## Filters and security

The new Worker source fixes `clientRequestHTTPHost:"ausmalwiese.de"` and applies `requestSource:"eyeball"` with a rolling last 7 or 30 x 24 hours `datetime_geq` / `datetime_lt` filter and UTC ISO timestamps; it queries `httpRequestsAdaptiveGroups` and returns a `sampled` flag from `avg.sampleInterval`. The crawler query also applies successful status bounds and an allowlist of User-Agent substrings. The script renders all provider strings with `textContent`.

**Open verification gate:** the previous Worker source could fall back to `CF_ANALYTICS_HOST` / `PUBLIC_ORIGIN` for its query hostname. The new Worker pins the Cloudflare Traffic analytics hostname to `ausmalwiese.de` and rejects missing zone results. This source change does **not** prove that the existing LIVE `CF_ZONE_TAG` corresponds to the correct zone or that the new Worker version is deployed. The UI labels that LIVE proof as pending. A real read-only Cloudflare verification must bind the correct zone and host before declaring exact comparability with Cloudflare dashboard figures. Do not infer host from an HTTP request count alone.

The documented Cloudflare Web Analytics sensor measures browser-side visits/page views under a different model from the zone HTTP Analytics rollups. Compare only **same source, interval, hostname, bot policy, sampling**; 24-hour Web Analytics `Visits` cannot be compared directly to seven-day HTTP Analytics `Visits`.

## Next phase before FULL acceptance

1. Prove from read-only Cloudflare/provider evidence that the active Stats Worker analytics query targets the exact `ausmalwiese.de` hostname and correct zone; confirm metrics against same provider dashboard window and bot policy.
2. If Cloudflare provides a hostname-scoped unique visitor count through a supported, authenticated, read-only API, add it with correct name and tests. Otherwise keep N/A and show the exact limitation; never revive IP-HMAC identity storage.
3. The new source now provides site-wide **HTTP request totals** from Cloudflare only, after a separate owner-gated Worker deployment. True browser page views and referrers need a separate provider-dataset review (such as Cloudflare RUM `rumPageloadEventsAdaptiveGroups` scoped to the exact site tag), access/retention checks, sampling and absence handling, and an independently authorized Worker/runtime change. Never label raw HTTP requests as browser page views or expose provider credentials in the frontend.
4. Preserve RPi5 as a static app server without traffic storage. Keep `stats.html` and engagement data as a separate system. Owner authorization for the source PR does not authorize Cloudflare Worker upload/deploy, D1/secret/settings/Access changes, merge or any manual LIVE action.

## References

- https://developers.cloudflare.com/analytics/graphql-api/features/filtering/
- https://developers.cloudflare.com/analytics/graphql-api/features/data-sets/
- https://developers.cloudflare.com/analytics/graphql-api/tutorials/end-customer-analytics/
- https://developers.cloudflare.com/web-analytics/
