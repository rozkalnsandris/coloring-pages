# German legal pages — DRAFT / NOT RELEASE READY

## Scope

- Only `impressum.html`, `datenschutz.html`, the five site footers, existing styling, static Docker packaging, locally served Baloo 2/Nunito fonts (SIL OFL 1.1), and structural tests.
- The embedded WOFF2 fonts in `css/fonts.css` avoid remote Google Fonts requests on the seven updated HTML pages. Validate browser requests and layout after authorized release.
- **No changes to `js/stats.js`, `cloudflare/stats-worker.js`, `docs/CLOUDFLARE_STATS_V1.md`, D1 schema, Cloudflare routes, or LIVE.** This legal-only PR does not require a Worker-first deploy.
- The current `main` QR-gated A4 print, preview watermark, browse UI, and deletion of retired migration code remain unchanged.

## Existing statistics behavior (source evidence only)

- The existing browser `js/stats.js` creates and stores a persistent random visitor ID on the first Like **or Print** using `localStorage`.
- Existing Like status uses `GET /api/stats/page` and may transmit that ID as a URL query parameter. Like actions use POST; the Worker hashes the ID for D1 Like rows. These rows have no automatic expiration.
- Print actions submit the ID via POST. The Worker requires it and may supply it to the Rate Limiter; D1 Print counters remain aggregate. Clicks represent print intent, not verified prints.
- The separate visitor-counting Worker path produces daily IP-derived HMAC records (pseudonymous); deletion is triggered by successful future visits rather than scheduled expiry.
- LIVE verification, real Cloudflare DPA/transfers, origin/edge logs, exact retention periods, and Rate Limiter behavior are not proven by source. Previous edge checks showed legacy GET 200 and new POST page-status 404.

## Bounded runtime evidence — 2026-10-11 (read-only snapshot, not legal sign-off)

**Evidence boundaries:** GitHub files describe source only; below, public-edge HTTP observations and a read-only RPi5 container-inspection snapshot describe what was observed on 2026-10-11. Neither proves future deployed behavior, private Cloudflare settings, contract acceptance, or lawful bases. No raw logs, secrets, D1 rows or customer contracts were read.

- **RPi5/nginx/Docker:** Source `deploy/nginx.conf` uses `access_log /dev/stdout;`. The observed running container `coloring-pages-public-coloring-pages-1` used Docker logging driver `json-file`, with `max-size=10m` and `max-file=3`; the daemon default showed the same options. This provides size-triggered log rotation, **not a guaranteed retention period in days**, and does not establish the absence of other host/Cloudflare log stores. The inspection did not expose individual visitor log records.
- **Public-edge snapshot:** An HTTP GET to `/` returned 200. `/impressum.html`, `/datenschutz.html` and `/css/fonts.css` returned 404, so the draft legal pages and local font stylesheet were not observed LIVE. Served home HTML still referenced Google Fonts and the existing `js/stats.js?v=kita-campaign-v1`. A read-only `GET /api/stats/page?page_id=0000000` returned 200; a synthetic `POST /api/stats/page` returned 404, consistent with the old Worker API. That POST was a non-mutating page-status check, not a print/like event.
- **Cookie evidence boundary:** One home-page HTTP response had no `Set-Cookie` header. That does **not** demonstrate that the entire site, other routes, browser sessions or Cloudflare security challenges never set cookies. Cloudflare documents separate security cookies and their conditions.
- **Source-side retention distinctions:** `cloudflare/stats-schema.sql` defines `likes` rows without automatic expiry. Source `cloudflare/stats-worker.js` deletes older `daily_visitors` HMAC rows on *successful* visit processing, not on an independent wall-clock schedule. A D1 database-wide retention or deletion guarantee cannot be inferred from either. The Rate Limiter's retention/state was not verified.
- **Cloudflare Workers Logs product documentation:** published retention is 3 days (Workers Free) or 7 days (Workers Paid) for Workers Logs. Whether Workers Logs are enabled, which plan applies, and any sampling/export settings in this particular account are **unverified**. Those product limits must **not** be represented as the lifetime of origin logs, D1 rows, security data or all edge HTTP logs.
- **Contracts and transfers:** publicly available Cloudflare DPA / Trust Hub material does not verify this account's accepted agreements, product-specific subprocessors, processing location, transfer safeguards or actual retention configurations. Keep all these facts pending account-specific review.

**Still needed before legal sign-off:** verify actual Cloudflare account DPA/transfer settings, whether Workers Logs/Logpush are enabled, the origin and other Cloudflare log destinations and actual deletion practice, D1 Like retention/deletion policy, Rate Limiter retention, and the TDDDG § 25 consent or strict-necessity assessment. GDPR Art. 13 requires actual retention periods or the criteria used to determine them; size-based Docker rotation cannot be substituted for a fixed-day period.

Sources: [Docker `json-file` rotation](https://docs.docker.com/engine/logging/drivers/json-file/); [Cloudflare Workers Logs limits](https://developers.cloudflare.com/workers/observability/logs/workers-logs/); [Cloudflare cookies](https://developers.cloudflare.com/fundamentals/reference/policies-compliances/cloudflare-cookies/); [GDPR Art. 13](https://eur-lex.europa.eu/eli/reg/2016/679/); [TDDDG § 25](https://www.gesetze-im-internet.de/ttdsg/__25.html).

---

## Free-tier operation — owner choice, 2026-10-11

- The owner reports that the Cloudflare Workers subscription was switched back to **Workers Free**. This is owner-reported configuration, not verified Billing/Subscriptions evidence. No new paid service or external vendor is required by the current stats source. Do not assume prior paid-plan entitlement remains in force.
- **Workers Free:** 100,000 requests/day **shared by the account**, CPU limit 10 ms/request. Cloudflare returns error 1027 at the daily request cap; dynamic engagement/analytics can temporarily fail, while the independently self-hosted PNG/site content does not depend on that Worker. Observe actual CPU and request usage in the Cloudflare dashboard; no future traffic/cost guarantee is implied.
- **D1 on Workers Free:** 5 million rows read/day, 100,000 rows written/day, 5 GB stored across the account, and a 500 MB single-database maximum. Once daily read/write limits are reached, D1 rejects queries until reset. The existing D1 likes, visits, rankings, daily counters and campaign tables are available on Free within those quotas; do not attempt automatic plan upgrades or charged overages.
- **Cloudflare Web Analytics** is free. Cloudflare's GraphQL Analytics `httpRequestsAdaptiveGroups` is documented as available on all plans, subject to account/zone query quotas and dataset settings. Thus the traffic dashboard needs **no paid Analytics upgrade**, but requires an eligible API token and current zone-level availability; these account settings remain unverified.
- **Workers Logs Free** currently documents 200,000 log events/day and 3-day retention **if enabled**. The Worker observability/sampling/export configuration was not independently checked, and Workers Logs limits do not establish D1, WAF, Logpush, or RPi5 data lifetimes. Docker origin logging is size-rotated (3 × 10 MB), not day-expiring.
- **Rate limiting:** source treats the Worker `RATE_LIMITER` binding as optional. Its absence is a weaker anti-abuse posture, not an equivalent substitute. Cloudflare documents Free-plan WAF Rate Limiting rules as an available no-extra-charge alternative, but adding/replacing security rules, bindings or Worker code is a separate authorized Cloudflare operation; none occurs here.
- **Free-first fallback:** if quotas become a problem, first reduce unnecessary Stats API requests and database row scans within a separately scoped source PR; keep the static RPi5 gallery/print independent of telemetry. Only if essential engagement cannot fit Free quotas, evaluate a small self-hosted RPi5 database/API under an explicit separate architecture/security/host owner gate; do not silently enable paid services or migrate existing D1 data.
- **No release clearance:** switching billing tier does **not** resolve GDPR Art. 6/13 lawful bases, TDDDG §25 storage consent/necessity, the Cloudflare contract/DPA, processor/transfer facts, D1 retention policy, or real account log settings. The legal pages remain a Draft and **NOT RELEASE READY**.

Official references: https://developers.cloudflare.com/workers/platform/limits/ ; https://developers.cloudflare.com/d1/platform/pricing/ ; https://developers.cloudflare.com/d1/platform/limits/ ; https://developers.cloudflare.com/workers/observability/logs/workers-logs/ ; https://developers.cloudflare.com/analytics/graphql-api/features/discovery/settings/ ; https://developers.cloudflare.com/web-analytics/about/ ; https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/

---

## Release blockers — owner/legal review required

1. **DDG § 5:** On 2026-10-11 the owner explicitly confirmed that official legal correspondence and registered letters can be received at the postal address already shown in `impressum.html`. This is an owner attestation, not an independent legal-service assessment. Verify the provider classification, any additional mandatory details, and final `ladungsfähige Anschrift` suitability before release.
2. **DSGVO Art. 13 and Art. 6:** confirm purposes, lawful bases, recipients/processors, Cloudflare agreements/transfers, retention periods or criteria, and data subject rights against actual production facts.
3. **TDDDG § 25:** consent is the starting rule for storing or reading a first-party Like/Print `localStorage` ID; the exception for an explicitly requested service requires strict necessity. Neither the exception nor a consent mechanism is verified for the current site. Assess separately the GDPR Art. 6 lawful basis; do not presume an exemption.
4. **Fonts and LIVE:** validate the self-hosted Google Fonts replacement and public page behavior after separately authorized release. Cloudflare Web Analytics' stated lack of cookies does not establish that separate Cloudflare security functions set no cookies. CI proves structure only, not legal compliance.

Official references (reviewed 2026-10-11): https://www.gesetze-im-internet.de/ddg/__5.html ; https://www.gesetze-im-internet.de/ttdsg/__25.html ; https://eur-lex.europa.eu/eli/reg/2016/679/ ; https://developers.cloudflare.com/web-analytics/about/ ; https://developers.cloudflare.com/fundamentals/reference/policies-compliances/cloudflare-cookies/

**NOT RELEASE READY**. No owner MERGE, Worker deploy, D1 mutation, or LIVE authorization is granted by this source document.
