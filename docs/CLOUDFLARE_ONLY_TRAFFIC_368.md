# Traffic dashboard: Cloudflare-only data boundary (#368)

**Status (2026-10-25):** The Traffic frontend source has been merged and operator-supplied read-only SSH output supports its deployment on the public RPi5 app. This does **not** verify the live Cloudflare analytics provider, unique-person metric, or data accuracy. No Cloudflare Worker deployment, token, D1 migration, settings change or new LIVE action is authorized here.

## Source and LIVE evidence — bounded

- **GitHub source:** PR #373 was squash-merged as `5d0ca7593a9290d30d33e50fb264add8fa52a6a7`; the fail-closed hostname/status correction in PR #374 was squash-merged as `a80feb4391dad1be259142d7554e570c47106288`.
- **Exact-head CI/review for #374:** `d8b9fa9c4b250a45c02bff6870334841408796d5` passed CI and GitHub-first policy; no reviews or unresolved review threads were recorded at the merge gate.
- **Operator-reported RPi5 read-only checks (2026-10-25):** host `rpi5`; public app container reported `healthy`; `http://127.0.0.1:9191/health` and `/ready` returned HTTP 200; live `traffic.html` referenced `cloudflare-only-368-v4`. The running container's `org.opencontainers.image.revision` label exactly matched `a80feb4391dad1be259142d7554e570c47106288`, and the served `js/traffic-admin.js` included the new `Cloudflare analytics hostname not verified.` fail-closed message.
- **Boundary of proof:** these observations confirm the deployed application image revision and the served frontend marker, **not** the active Cloudflare Worker implementation, configured zone, upstream Analytics API responses, comparable Cloudflare dashboard totals, bot filtering quality or unique visitors. The frontend hostname field is Worker-declared, not independent provider verification.
- **Remaining #368 gate:** compare the same hostname/time window, bot policy and dataset in actual Cloudflare Analytics and the read-only Traffic endpoint; do not mark the issue done or publish additional metric claims until this succeeds.

## Dashboard separation

`/stats.html` is the engagement dashboard. It shows only:
- Total print actions
- Total Likes
- Print actions in the last 7 days
- Published pages, TOP lists and the per-page engagement table

QR and campaign acquisition panels are intentionally removed from Statistics. Existing aggregate D1 data and APIs are not deleted by this UI change.

`/traffic.html` is the acquisition and traffic dashboard. Numeric Traffic values may come only from Cloudflare analytics through the read-only `GET /api/stats/traffic?days=7|30` proxy. It must not read RPi5 logs/databases, persistent visitor identifiers, the D1 overview endpoint or D1 campaign counters.

## Current Cloudflare metrics

| Traffic UI | Provider source | Semantics / caveat |
| --- | --- | --- |
| Website visits | `httpRequestsAdaptiveGroups.sum.visits` with hourly grouping | Cloudflare HTTP Analytics visits, **not unique people**. Can be sampled. |
| HTTP requests | `httpRequestsAdaptiveGroups.count` with the same fixed-host filter | Request events, not people/page views; may include static resources and can be sampled. |
| Crawler requests and top paths | `httpRequestsAdaptiveGroups.count`, grouped by User-Agent and path | User-Agent heuristic, successful 2xx/3xx only; not verified bot identities. |
| Unique people | **N/A until separately verified** | Do not relabel Visits or a zone-wide unique rollup as visitors to `ausmalwiese.de`. |
| Views by coloring page | **Not yet available** | Current URLs use `detail.html?id=…`; path-only edge aggregates see the shared `/detail.html` path and cannot safely distinguish page IDs. |
| Instagram / QR / Kita acquisition | **Readiness only** | Existing D1 attribution is deliberately not mixed into Traffic. Show numeric channel data only after a Cloudflare-native path/referrer design is proven. |

The Worker fixes `clientRequestHTTPHost:"ausmalwiese.de"` and `requestSource:"eyeball"`, with rolling 7/30-day UTC windows. It returns `sampled` based on `avg.sampleInterval`. Tokens/account identifiers remain server-side.

## Why Unique Visitors disappeared

The former project-specific persistent/IP-derived visitor mechanism was retired by the privacy simplification. The current source deliberately returns:
- `unique_visitors: null`
- `unique_visitors_status: "removed"`
- `unique_visitors_basis: "removed-no-persistent-visitor-metric"`

Current Cloudflare `httpRequestsAdaptiveGroups` documentation supports Visits but does not provide the already-proven hostname-scoped unique-person metric required by this dashboard. Until a supported provider field is verified against the exact `ausmalwiese.de` host and matching dashboard semantics, the honest UI value is `N/A`.

## Page-level and acquisition roadmap

Cloudflare Web Analytics/RUM can expose browser-side dimensions such as host, path and referrer and page-view style datasets. That is a separate measurement model from edge HTTP Analytics. It must not be enabled or queried automatically just to fill dashboard cards.

Before adding it:
1. Verify the exact API dataset/schema and plan availability read-only.
2. Verify hostname/site-tag scoping, bot policy, sampling, retention and data-location implications.
3. Confirm whether the dataset can distinguish the current `detail.html?id=…` page IDs. If not, prefer stable dedicated paths (for example a page-specific route) rather than guessing from query strings.
4. For Instagram, verify referrer/landing-path attribution before showing numbers.
5. For printed QR and Kita campaigns, prefer dedicated first-party landing paths so Cloudflare edge analytics can measure them without a custom visitor identity.
6. Keep all provider credentials out of browser code.

Cloudflare documents Web Analytics as privacy-first and says it does not collect or use visitors' personal data, but browser-side RUM is still a distinct processing path from the current edge-only implementation and needs a separate legal/technical review before activation.

## Cookie / consent UI

Do **not** add an Accept/Reject cookie banner merely for the current Cloudflare edge-only Traffic dashboard. German TDDDG §25 concerns storing or accessing information on the user's terminal device, and German DSK guidance says consent banners should be used only when consent is actually required; otherwise the UI can misleadingly imply that choosing Accept/Reject changes processing.

If a later design introduces consent-requiring client storage or non-essential browser tracking, add a real consent mechanism before that processing starts and reconcile the public Datenschutz text. A banner must control actual processing; it must not be decorative.

## Open LIVE/provider gates

1. Read-only verify that the active Stats Worker uses the correct Cloudflare zone and exact `ausmalwiese.de` host; compare the same interval/filter with the Cloudflare dashboard.
2. Probe supported Cloudflare schemas for a genuinely hostname-scoped unique-visitor metric. Keep `N/A` if it cannot be proved.
3. Separately evaluate Web Analytics/RUM for page views/referrers and data-location/privacy constraints.
4. Design dedicated first-party landing paths for QR/Kita and, if useful, Instagram attribution.
5. Reconcile legal copy in the existing legal workstream before any new client-side measurement activation.

None of these gates authorizes Worker upload/deploy, D1/schema changes, Cloudflare settings/tokens/permissions, RPi5 mutation, merge or LIVE work.

## Official references

- https://developers.cloudflare.com/analytics/graphql-api/features/filtering/
- https://developers.cloudflare.com/analytics/graphql-api/features/data-sets/
- https://developers.cloudflare.com/analytics/graphql-api/limits/
- https://developers.cloudflare.com/analytics/account-and-zone-analytics/zone-analytics/
- https://developers.cloudflare.com/web-analytics/
- https://developers.cloudflare.com/web-analytics/get-started/
- https://developers.cloudflare.com/privacy/data-localization/customer-metadata-boundary/
- https://www.gesetze-im-internet.de/ttdsg/__25.html
- https://www.datenschutzkonferenz-online.de/media/oh/20211220_oh_telemedien.pdf
