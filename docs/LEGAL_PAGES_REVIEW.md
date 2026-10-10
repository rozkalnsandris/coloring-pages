# Legal pages — source draft; **NOT RELEASE READY**

Scope: German `impressum.html`, `datenschutz.html`, legal footer links and static nginx image packaging; owner-approved source-only privacy minimization, local fonts, tests and legal draft wording. No merge or LIVE.
Source only; no GSC, Cloudflare, RPi5, deployed Worker or production data changes.

## Source-only privacy and font update — 2026-10-10

**Draft branch only; NOT LIVE; NOT RELEASE READY.**

- Seven HTML pages now reference first-party `css/fonts.css`, embedding Baloo 2/Nunito Latin variable WOFF2 with `font-display: optional`. Licensing is SIL OFL v1.1, with verbatim `assets/fonts/OFL-Baloo2.txt` and `assets/fonts/OFL-Nunito.txt`. Font binary provenance: `fontsource/font-files@c3f4e3e5a664d2c3002e800050ce809a790d7281`; original licenses: `google/fonts/ofl/{baloo2,nunito}/OFL.txt`. Browser visual/network verification is still required after authorized release.
- The frontend now posts existing Like IDs in the **body** of `POST /api/stats/page`, not the URL query. The Worker already supports POST and retains a legacy GET route for cached clients; legacy URLs may still expose a visitor ID. Creating/reading a persistent `localStorage` ID for Like is still subject to TDDDG §25 and GDPR Art. 6 review.
- Print intent does not create, read or transmit a permanent browser ID. The Worker uses a day-scoped HMAC derived from connection IP/host for rate limiting; no per-visitor print ID is stored in D1. The separate Rate Limiter receives a pseudonymous key, and its retention is not verified. Cloudflare warns that IP-derived keys can group users behind shared addresses; this is a tradeoff, not anonymity. Printing stays independent of tracking success.
- **Worker-first deployment gate:** the updated Worker must be explicitly authorized, deployed and verified *before* merging the application PR: the old Worker can reject the new frontend POST status request and ID-free print payload. This authorization permits source/tests/CI only. It does not permit Worker deployment, D1 mutation, merge or auto-LIVE.
- **Legal blockers remain:** Cloudflare account-specific DPA/transfers, processor and retention facts, purposes/legal bases for telemetry, TDDDG §25 Like storage, DDG §5 suitability of the provider's postal address, and actual LIVE/edge data flows. Historic review sections below describe previous source/edge behavior and must not be quoted as evidence that this new code is deployed.

## Source-only API contract and release-order review — 2026-10-10

**Baseline PR HEAD:** bbb41f38635f6a57dd47929ee7484fda92762e2e. This is a review baseline, not a perpetual head pin. The current source-only corrections and tests are still **NOT RELEASE READY**.

- Added dependency-free Node contract tests called by existing Python CI. They execute the actual Worker fetch() and the actual frontend JS against synthetic inputs, a fake D1 and a fake Rate Limiter. They are offline tests, not LIVE proof.
- Confirmed source order: updated Worker first, then after separate approvals and legal sign-off the new frontend. Existing frontend + updated Worker is backward-compatible, but new POST page-status / ID-free Print requests fail against the old Worker (404 / 400 respectively).
- Cloudflare distinguishes uploaded versions from active deployments; the active version and traffic split must be verified separately before frontend activation. No current account-specific Cloudflare version/binding, D1 rows, contracts, Rate Limiter retention, secrets, raw logs or LIVE browser traffic were accessed here.
- For a read-only public-edge contract check, use only legacy GET /page and new read-only POST /page with a synthetic page ID and no visitor ID, under appropriate owner authority. POST /print and /like mutate D1, so cannot be used in an unapproved read-only smoke test.
- Remaining legal blockers are DDG §5 provider/contact details and address suitability; GDPR Art. 13 purpose-specific lawful bases, controller/processor/transfer/retention details; TDDDG §25 for Like localStorage; Worker/D1/Rate Limiter processing and retention; actual active deployment and browser resource verification. No new privacy compliance conclusion follows from green CI.

References: https://developers.cloudflare.com/workers/testing/ ; https://developers.cloudflare.com/workers/versions-and-deployments/ ; https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/ ; https://www.gesetze-im-internet.de/ttdsg/__25.html

## Confirmed owner choices

- Display name: **Andris Rožkalns** (owner approval, 2026-10-09).
- Contact email: `andris@rozkalns.net`.
- Postal address: owner explicitly approved inclusion of their residential postal address in both public legal-page drafts on 2026-10-10, superseding the earlier do-not-publish choice. The full address is held in the legal HTML, not repeated in this checklist.
- Naming/domain and Kita marketing are intentionally deferred.

## Blocking checks before Ready / MERGE

1. **DDG § 5**: the owner-approved postal address is now present in `impressum.html` and `datenschutz.html`. Before release, confirm whether the provider-notice duty applies and that the address is actually suitable for legal service (`ladungsfähige Anschrift`); the HTML address alone is not legal sign-off.
2. **GDPR Art. 13**: validate Cloudflare DPA/third-country transfer information, recipients, log-storage periods and operator-contact details against active production agreements and settings (not merely GitHub).
3. **TDDDG § 25 / GDPR Art. 6**: assess terminal-storage necessity/consent and lawful bases for Like identity, unique visitors, page views and Print telemetry. Current PR source writes `localStorage["coloring-pages-visitor-v1"]` on first Like, not on Print. Like state still reads an existing ID. Neither consent exemption nor GDPR basis is assumed.
4. **Self-hosted font verification**: PR source embeds OFL-licensed Baloo 2 and Nunito locally. Check bundled licenses, browser requests and layout after separately authorized activation. Old LIVE observations of remote Google Fonts do not prove the new fonts are in production.
5. Confirm actual LIVE Cloudflare Analytics, Worker, D1 schema, origin logs, retention policy, contractual and configuration details. The legal draft truthfully marks some values as not confirmed, rather than inventing them.

## Data-flow evidence (source, not automatic LIVE proof)

- `js/stats.js` at this PR HEAD: writes a persistent visitor ID only when someone first Likes; sends that existing Like ID in a same-origin POST /api/stats/page JSON body; sends ID-free Print intent. It still emits aggregate page/visit events. Cached old clients can still use the legacy GET query endpoint; actual edge logs/retention are not proven.
- `cloudflare/stats-worker.js`: daily HMAC-SHA-256 over UTC day + hostname + Cloudflare connecting IP; only the HMAC is stored in `daily_visitors`. These IP-derived values should be described as **pseudonymized, not automatically anonymous**. Values older than yesterday are deleted **when a successful visit occurs**, not by guaranteed wall-clock retention.
- `cloudflare/stats-schema.sql`: D1 Likes keep hashed per-page visitor IDs without automatic expiry; view/print/campaign counts are aggregates. The Worker sends a Like visitor ID to the optional Like Rate Limiter, but sends an IP-derived UTC-day HMAC to the Print Rate Limiter; actual Rate Limiter state and retention remain unverified.
- `index.html`, `detail.html`, `kita.html` and internal dashboards at the PR HEAD: load same-origin OFL font CSS, not Google Fonts. Earlier read-only public-edge evidence showed Google Fonts and a Cloudflare Web Analytics beacon on then-deployed HTML; this is historical LIVE evidence, not evidence of the new PR being deployed.
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
| TDDDG § 25 — access to terminal information | Browser Web Storage access can fall under § 25 regardless of personal-data status. PR source writes the persistent Like ID on first user Like and reads it for Like state; Print no longer accesses this ID. Assess the Like-specific strictly necessary exception versus consent and a separate GDPR Art. 6 basis. | BLOCKED pending purpose-specific review. |
| Optional Print analytics | PR source no longer creates or transmits a persistent browser ID for Print. The Worker still handles connection IP in memory for a day-scoped HMAC rate key; the rate binding may process pseudonymous data. Source tests do not prove its retention or LIVE configuration. | BLOCKED pending rate-limiter/legal LIVE evidence, not the old browser-ID redesign. |
| Like identifier / request logs | The new frontend places any existing Like ID in a POST body, not the URL. Legacy cached browsers may still send it to the retained GET route; edge log processing and retention are unknown. | BLOCKED pending edge/log verification and legal basis. |
| Cloudflare Web Analytics versus first-party stats | Cloudflare documents its RUM beacon and measurement scope; **those statements do not cover the separate first-party Cloudflare Worker, D1 or Rate Limiter**. Any inference of cookie-free or anonymous processing for the whole site is invalid. | BLOCKED: independently confirm live beacon, Worker, D1, Cloudflare processing terms, recipient and transfer details. |
| Fonts | PR source self-hosts two OFL-licensed font families, replacing external Google Fonts references. Previous deployed HTML had remote font references. | BLOCKED only for authorized LIVE/browser verification and remaining global legal review, not a missing source-level font substitution. |

**Smallest next decisions (no mutation implied):** (1) confirm provider/business classification and the address's suitability for service; (2) review remaining Like localStorage, IP-derived rate limiting, visitor and page analytics without disabling printing; (3) obtain bounded read-only actual Cloudflare DPA, deployed Worker version and retention evidence under appropriate authority; (4) verify locally hosted fonts after separately authorized application activation. Once these are resolved, update the public wording with established facts, rerun source tests/CI, and request legal/content sign-off before Ready/MERGE. No automatic LIVE, Worker, D1, network, consent or font-source change is authorized by this review.

## Follow-up: provider documents and bounded public evidence (2026-10-10)

This section concerns **public external documents and minimally scoped public-edge evidence**, not authenticated proof of the Cloudflare account's contract or protected host configuration. No Worker/D1/provider configuration, private logs, personal data or secret material was accessed for this follow-up.

- **Public edge response:** A read-only `HEAD https://coloring.rozkalns.net/` returned `HTTP/2 200` with `server: cloudflare` and `cf-cache-status: DYNAMIC`. This supports Cloudflare involvement at the public edge **only**. It does not establish the deployed Worker revision, whether the Web Analytics beacon runs on each page, server/container-log retention or actual D1 contents.
- **Public Cloudflare DPA:** Cloudflare's published **Data Processing Addendum v6.4 (effective 2026-04-03)** describes the controller/processor relationship and possible EEA-to-third-country transfers, and includes contractual provisions for EU Standard Contractual Clauses. The *existence* of this public document is not evidence that this owner/account has agreed to that version, which services and sub-processors apply, or which safeguards govern a particular LIVE data flow. Do not copy generic contract terms into the notice as account-proven facts.
- **Cloudflare analytics retention is product/dataset-specific:** The public *Web Analytics* FAQ says the Web Analytics interface currently offers the previous **six months**. Cloudflare's 2026-10-02 Analytics changelog separately announces 30 days of queryable history for certain general analytics datasets (at least 31 days retained for Free/Pro). Neither statement proves retention of origin logs, the project's own D1 `likes`/daily counters, Rate Limiter input or the owner's account-specific dataset settings. **Do not substitute any of these values as a blanket visitor-data deletion period.**
- **TDDDG § 25(1)–(2):** the official statute requires informed consent for accessing/storing terminal information unless the expressly defined necessity exemptions apply. The project's persistent `localStorage` visitor ID and optional print counts remain an open purpose-by-purpose consent/necessity decision; a cookie-free Cloudflare Web Analytics beacon does not settle this.
- **GDPR Art. 13 and DDG § 5:** the current public legal draft must still disclose supported processing bases, recipients, transfer information, retention periods/criteria and any actually required provider-contact information. Confirm whether an email-only operator contact is sufficient for the legally required immediate communication; do not fabricate phone, register details, contractual acceptance or address serviceability.
- **Protected runtime boundary:** `RPi5_main/AGENTS.md` excludes protected configuration, process/container environment, `docker inspect`, logs and other restricted host data unless there is separately explicit, appropriately scoped authority. Public edge/source observations cannot replace this proof. Further protected-runtime checks are **not** authorized by the current review command.

**Decision:** keep this PR Draft and **NOT RELEASE READY**. A production-accurate privacy notice cannot be signed off from public provider material or static source alone. Any redesign of the statistics/Fonts subsystem, consent feature, Cloudflare/D1 change, host inspection of protected data or release needs its own appropriately scoped owner decision; this follow-up does not authorize any such mutation.

## Sanitized LIVE origin logging metadata — 2026-10-10

**Authorization and evidence scope:** the owner explicitly authorized one minimum-sufficient **read-only** metadata inspection of the existing RPi5 container `coloring-pages-public-coloring-pages-1`: `LOG-DRIVER, ROTATION, RETENTION, ACCESS-LOG-FIELDS`, with **sanitized output only**. The observation queried target container logging configuration and the *effective NGINX configuration's access-log directives and format names*, rather than raw log events. This authorization did not grant source/runtime changes, credential or environment access, raw-log access, database access or merge.

| Observed target metadata (not raw records) | Confirmed result | Interpretation / limitation |
| --- | --- | --- |
| Container Docker log driver | `json-file` | Docker stores container `stdout`/`stderr` log messages in JSON files; this is not an analytics-platform retention policy. |
| Rotation options | `max-size=10m`; `max-file=3` | File-size/count-based rotation; does **not** imply deletion after 7/30 days or any fixed time interval. Options apply to this inspected container, not every service or Cloudflare. |
| Time-based retention option | Not configured among the inspected Docker log-driver options | No complete end-to-end retention period can be derived; other copies/collectors/backups were not inspected. |
| Effective NGINX access-log directives | Three directives classified as `stdout` and `off` | Some NGINX locations suppress access logging; normal logged requests go to `stdout`, which Docker can capture. This is not proof every request is logged. |
| NGINX access-log format | Default `combined`, with no custom `log_format` declaration found | The standard fields include client address, remote user, local time, request line, HTTP status, response-body byte count, referer and user agent. The request line can include a query string. |
| Worker/D1/edge log processing | **Not inspected** | Do not infer Worker/D1 log persistence, Cloudflare retention, Cloudflare IP-address treatment, or whether `/api/stats/*` requests traverse this NGINX instance. |

**Privacy consequence:** for requests that actually reach an NGINX location using `combined`, a query string **may** appear in an origin access log. The project's `js/stats.js` sends an existing raw `visitor_id` in a request URL to `/api/stats/page`, but routing through the Cloudflare Worker is a separate data-flow boundary. The metadata inspection does **not** show that this particular endpoint reaches NGINX or that such a raw ID appears in any real NGINX entry. Assess the Worker/edge handling separately before a statement about endpoint-level log exposure.

**Evidence hygiene and release gate:** no raw log records, personal information, secrets, process/container environment, database content or protected configuration dumps were copied into GitHub. This new, separately granted read-only review supersedes the **inspection authorization status** reported in the earlier public-evidence section, not its legal conclusions. The present evidence improves the origin logging inventory only. `Datenschutzerklärung` remains a **draft / NOT RELEASE READY** until the real purposes, legal bases, processor/transfer arrangements and valid retention **periods or criteria** are documented for each service and processing activity. Do not replace the outstanding retention text with an invented number of days or conflate Docker's file rotation with GDPR-compliant data deletion.

## Reference sources

- DDG § 5: https://www.gesetze-im-internet.de/ddg/__5.html
- DSGVO Art. 13: https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32016R0679
- TDDDG § 25: https://www.gesetze-im-internet.de/ttdsg/__25.html
- DSK guidance for digital services: https://www.ldi.nrw.de/orientierungshilfe-der-aufsichtsbehoerden-fuer-anbieter-von-digitalen-diensten
- GDPR Art. 13: https://eur-lex.europa.eu/legal-content/EN-DE/TXT/?uri=CELEX:32016R0679
- LDI NRW complaint authority: https://www.ldi.nrw.de/
- Datenschutzkonferenz OH Digitale Dienste: https://www.datenschutzkonferenz-online.de/media/oh/OH_Digitale_Dienste.pdf
- Cloudflare Web Analytics: https://developers.cloudflare.com/web-analytics/data-metrics/data-origin-and-collection/
- Cloudflare Web Analytics FAQ (interface data window): https://developers.cloudflare.com/web-analytics/faq/
- Cloudflare Analytics retention update (2026-10-02): https://developers.cloudflare.com/changelog/post/2026-10-02-30-days-analytics-on-every-plan/
- Cloudflare DPA v6.4: https://www.cloudflare.com/cloudflare-customer-dpa/
- Cloudflare Worker version and deployment: https://developers.cloudflare.com/workers/versions-and-deployments/
- Cloudflare offline Worker testing: https://developers.cloudflare.com/workers/testing/
- Cloudflare Rate Limiting: https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/
- Google Fonts API: https://developers.google.com/fonts/docs/technical_considerations
- Docker JSON File logging driver (rotation behavior): https://docs.docker.com/engine/logging/drivers/json-file/
- NGINX ngx_http_log_module (default combined format, access_log directives): https://nginx.org/en/docs/http/ngx_http_log_module.html

**Policy:** Draft only; no merge or automatic application LIVE before the blockers are resolved and owner expressly authorizes the exact merge. Do not conflate CI success with legal compliance.
