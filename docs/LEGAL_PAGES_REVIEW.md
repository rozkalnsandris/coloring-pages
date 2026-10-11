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

## Release blockers — owner/legal review required

1. **DDG § 5:** confirm provider classification, identification duties, and that the owner-approved address is a suitable `ladungsfähige Anschrift`.
2. **DSGVO Art. 13 and Art. 6:** confirm purposes, lawful bases, recipients/processors, Cloudflare agreements/transfers, retention periods or criteria, and data subject rights against actual production facts.
3. **TDDDG § 25:** consent is the starting rule for storing or reading a first-party Like/Print `localStorage` ID; the exception for an explicitly requested service requires strict necessity. Neither the exception nor a consent mechanism is verified for the current site. Assess separately the GDPR Art. 6 lawful basis; do not presume an exemption.
4. **Fonts and LIVE:** validate the self-hosted Google Fonts replacement and public page behavior after separately authorized release. Cloudflare Web Analytics' stated lack of cookies does not establish that separate Cloudflare security functions set no cookies. CI proves structure only, not legal compliance.

Official references (reviewed 2026-10-11): https://www.gesetze-im-internet.de/ddg/__5.html ; https://www.gesetze-im-internet.de/ttdsg/__25.html ; https://eur-lex.europa.eu/eli/reg/2016/679/ ; https://developers.cloudflare.com/web-analytics/about/ ; https://developers.cloudflare.com/fundamentals/reference/policies-compliances/cloudflare-cookies/

**NOT RELEASE READY**. No owner MERGE, Worker deploy, D1 mutation, or LIVE authorization is granted by this source document.
