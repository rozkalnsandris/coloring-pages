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
3. **TDDDG § 25 / GDPR Art. 6**: assess both terminal-storage legality and a separate lawful basis for each of day-scoped visitor counts, page views, Like identity and Print telemetry. Storing/reading `localStorage["coloring-pages-visitor-v1"]` is tied to Like and Print actions, but print counting is not required for printing itself. Do not claim an essential-service exemption or legitimate interest without a documented necessity / balancing assessment; if required, add valid consent or minimize/disable the optional telemetry in a separately scoped feature change.
4. Review whether remote **Google Fonts** should be replaced with self-hosted, properly licensed font files and check external requests. The HTML source currently requests `fonts.googleapis.com` and `fonts.gstatic.com`.
5. Confirm actual LIVE Cloudflare Analytics, Worker, D1 schema, origin logs, retention policy, contractual and configuration details. The legal draft truthfully marks some values as not confirmed, rather than inventing them.

## Data-flow evidence (source, not automatic LIVE proof)

- `js/stats.js`: first-party random visitor ID is created on first Like or Print and stored in browser localStorage; `POST /api/stats/visit` on home/detail, `/view` on detail, `/print` and `/like` on interactions. `GET /api/stats/page` sends a pre-existing **raw visitor ID as the `visitor_id` URL query parameter**, before the Worker hashes it; Like/Print actions send the raw ID in JSON bodies over the HTTPS same-origin API. Request-URL exposure to proxy/edge/access logs needs a separate assessment and possibly an API redesign. No such redesign is authorized by this legal-docs PR.
- `cloudflare/stats-worker.js`: daily HMAC-SHA-256 over UTC day + hostname + Cloudflare connecting IP; only the HMAC is stored in `daily_visitors`. These IP-derived values should be described as **pseudonymized, not automatically anonymous**. Values older than yesterday are deleted **when a successful visit occurs**, not by guaranteed wall-clock retention.
- `cloudflare/stats-schema.sql`: Likes contain per-page visitor hashes and have no automatic deletion period; daily views, prints, campaign counts are aggregates and likewise lack a demonstrated universal expiry. `cloudflare/stats-worker.js` passes the raw ID to the optional Rate Limiter binding; its active configuration, logging, storage and retention are not proven by repository source.
- `index.html`, `detail.html`, `kita.html`, admin pages: remote Google Fonts; read-only LIVE HTML showed Cloudflare Web Analytics beacon injection.
- nginx config logs public requests to stdout; whether other processing/storage happens must be checked against RPi5 and Cloudflare runtime.
- No new cookies/consent flows introduced by this PR; lack of a `Set-Cookie` response is not proof that all tracking is exempt.
- This draft's GDPR Art. 13 review must still bind **purposes, Art. 6 lawful basis per processing activity, legitimate interests, recipients, non-EEA transfers and safeguards, storage/deletion durations, user rights and any mandatory-contact fields** to confirmed actual operations; source evidence alone is not sufficient.
- Do not treat a hash, Cloudflare's cookie-free Web Analytics product, or a page's lack of scripts as proof that the whole site is anonymous or consent-exempt; the site's own Worker handles visitor-linked data.
- The relevant NRW complaint authority is LDI NRW (https://www.ldi.nrw.de/).

## Official-law review: 2026-10-10 (read-only public sources)

This is an evidence and decision checklist, **not** an approval that the deployed service complies with law. The statutory sources below are current public texts; source-level facts refer to the PR head noted in the review, not to independently attested LIVE settings.

| Requirement | Evidence / unresolved decision | Release disposition |
| --- | --- | --- |
| DDG § 5 — provider identification | The draft displays owner name, email and owner-approved postal address. § 5 concerns businesslike digital services *generally offered for remuneration*; free page access **alone does not settle applicability**, especially if commercial promotion, donations or later paid offerings are involved. Validate classification, all applicable mandatory fields and real legal-service suitability of the postal address; do not invent register, VAT, telephone or supervisory details. | BLOCKED pending owner/factual and legal review. |
| GDPR Art. 13(1)–(2) — at collection | For each processing purpose, identify its Art. 6 basis and (where applicable) specific legitimate interest, recipients/processors, third-country transfer safeguards, retention **period or criteria**, rights, provision consequences and applicable contact details. Current draft still refers to future confirmation of hosting/Cloudflare log retention and of visitor hashes. | BLOCKED: no invented periods, transfer basis or blanket legitimate-interest conclusion. |
| TDDDG § 25 — access to terminal information | DSK OH Digitale Dienste v1.2, paras 18, 21 and 26, confirms the rule covers Web Storage and is not dependent on personal-data status. `js/stats.js` reads a persistent `localStorage` visitor ID when displaying Like state and writes one on the first Like/**Print** action. No automatic exemption follows from avoiding cookies. The separate GDPR basis for subsequent personal-data processing still needs assessment. | BLOCKED: decide valid consent **or** demonstrably necessary/minimized design with purpose-specific legal assessment. |
| Optional Print analytics | `trackPrint()` creates/reads a durable ID purely to report a print action. Printing is user-requested; durable identifier-based **counting** is not demonstrated to be necessary for printing. An exemption for this analytics operation must not be assumed. | BLOCKED: consider removing durable ID from Print telemetry in a separately scoped, tested source change; preserve printing without optional statistics where feasible. |
| Existing raw visitor ID / request logs | `getPage()` puts a pre-existing raw `visitor_id` in a GET query. The worker hashes it only later. Potential edge/proxy/access-logging exposure cannot be dismissed because D1 stores a hash. | BLOCKED: identify actual retention/access and decide whether an independently reviewed API minimization change is necessary. |
| Cloudflare Web Analytics versus first-party stats | Cloudflare documents its RUM beacon and measurement scope; **those statements do not cover the separate first-party Cloudflare Worker, D1 or Rate Limiter**. Any inference of cookie-free or anonymous processing for the whole site is invalid. | BLOCKED: independently confirm live beacon, Worker, D1, Cloudflare processing terms, recipient and transfer details. |
| Google Fonts | Existing public HTML contains requests to Google-hosted font CSS; Google's Fonts API documentation confirms the stylesheet varies by user agent and fonts are fetched separately. | BLOCKED: favor properly licensed self-hosting in a separately verified source change or document an actual suitable legal basis; verify the browser's external requests after release. |

**Smallest next decisions (no mutation implied):** (1) confirm provider/business classification and whether this address receives legally served mail; (2) choose a privacy-preserving approach to optional Print/Like telemetry, without disabling printing; (3) obtain minimum-sufficient read-only *actual* hosting, Cloudflare agreement/settings and retention evidence through the appropriate authorized runtime/provider boundary; (4) verify Google Fonts handling. Once these are resolved, update the public wording with established facts, rerun source tests/CI, and request legal/content sign-off before Ready/MERGE. No automatic LIVE, Worker, D1, network, consent or font-source change is authorized by this review.

## Reference sources

- DDG § 5: https://www.gesetze-im-internet.de/ddg/__5.html
- DSGVO Art. 13: https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32016R0679
- TDDDG § 25: https://www.gesetze-im-internet.de/ttdsg/__25.html
- DSK guidance for digital services: https://www.ldi.nrw.de/orientierungshilfe-der-aufsichtsbehoerden-fuer-anbieter-von-digitalen-diensten
- GDPR Art. 13: https://eur-lex.europa.eu/legal-content/EN-DE/TXT/?uri=CELEX:32016R0679
- LDI NRW complaint authority: https://www.ldi.nrw.de/
- Datenschutzkonferenz OH Digitale Dienste: https://www.datenschutzkonferenz-online.de/media/oh/OH_Digitale_Dienste.pdf
- Cloudflare Web Analytics: https://developers.cloudflare.com/web-analytics/data-metrics/data-origin-and-collection/
- Google Fonts API: https://developers.google.com/fonts/docs/technical_considerations

**Policy:** Draft only; no merge or automatic application LIVE before the blockers are resolved and owner expressly authorizes the exact merge. Do not conflate CI success with legal compliance.
