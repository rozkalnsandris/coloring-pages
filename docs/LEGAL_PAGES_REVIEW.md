# Legal pages — source draft; **NOT RELEASE READY**

Scope: German `impressum.html`, `datenschutz.html`, legal footer links and static nginx image packaging.
Source only; no GSC, Cloudflare, RPi5, deployed Worker or production data changes.

## Confirmed owner choices

- Display name: **Andris Rožkalns** (owner approval, 2026-10-09).
- Contact email: `andris@rozkalns.net`.
- Postal address: owner explicitly approved inclusion of their residential postal address in both public legal-page drafts on 2026-10-10, superseding the earlier do-not-publish choice. The full address is held in the legal HTML, not repeated in this checklist.
- Naming/domain and Kita marketing are intentionally deferred.

## Blocking checks before Ready / MERGE

1. **DDG § 5**: the owner-approved postal address is now present in `impressum.html` and `datenschutz.html`. Before release, confirm whether the provider-notice duty applies and that the address is actually suitable for legal service (`ladungsfähige Anschrift`); the HTML address alone is not legal sign-off.
2. **GDPR Art. 13**: validate Cloudflare DPA/third-country transfer information, recipients, log-storage periods and operator-contact details against active production agreements and settings (not merely GitHub).
3. **TDDDG § 25**: determine whether writing/reading `localStorage["coloring-pages-visitor-v1"]` for Likes / print tracking requires prior consent. Avoid asserting an exemption without evidence; if required, implement consent or minimize the feature before release.
4. Review whether remote **Google Fonts** should be replaced with self-hosted, properly licensed font files and check external requests. The HTML source currently requests `fonts.googleapis.com` and `fonts.gstatic.com`.
5. Confirm actual LIVE Cloudflare Analytics, Worker, D1 schema, origin logs, retention policy, contractual and configuration details. The legal draft truthfully marks some values as not confirmed, rather than inventing them.

## Data-flow evidence (source, not automatic LIVE proof)

- `js/stats.js`: first-party random visitor ID is created on first Like or Print, stored in browser localStorage; `POST /api/stats/visit` on home/detail, `/view` on detail, `/print` and `/like` on interactions.
- `cloudflare/stats-worker.js`: daily HMAC-SHA-256 over UTC day + hostname + Cloudflare connecting IP; only the HMAC is stored in `daily_visitors`. Values older than yesterday are deleted **when a successful visit occurs**, not by guaranteed wall-clock retention.
- `cloudflare/stats-schema.sql`: Likes contain per-page visitor hashes and have no automatic deletion period; daily views, prints, campaign counts are aggregates and likewise lack a demonstrated universal expiry.
- `index.html`, `detail.html`, `kita.html`, admin pages: remote Google Fonts; read-only LIVE HTML showed Cloudflare Web Analytics beacon injection.
- nginx config logs public requests to stdout; whether other processing/storage happens must be checked against RPi5 and Cloudflare runtime.
- No new cookies/consent flows introduced by this PR; lack of a `Set-Cookie` response is not proof that all tracking is exempt.

## Reference sources

- DDG § 5: https://www.gesetze-im-internet.de/ddg/__5.html
- DSGVO Art. 13: https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32016R0679
- TDDDG § 25: https://www.gesetze-im-internet.de/ttdsg/__25.html
- Datenschutzkonferenz OH Digitale Dienste: https://www.datenschutzkonferenz-online.de/media/oh/OH_Digitale_Dienste.pdf
- Cloudflare Web Analytics: https://developers.cloudflare.com/web-analytics/data-metrics/data-origin-and-collection/
- Google Fonts API: https://developers.google.com/fonts/docs/technical_considerations

**Policy:** Draft only; no merge or automatic application LIVE before the blockers are resolved and owner expressly authorizes the exact merge. Do not conflate CI success with legal compliance.
