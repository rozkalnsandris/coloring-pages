# Ausmalwiese: Like/Print consent design (#182)

Status: SOURCE IMPLEMENTATION DRAFT — not legally signed off, merged or LIVE.
Scope: [issue #182](https://github.com/rozkalnsandris/coloring-pages/issues/182). Independent legal-page Draft: [PR #158](https://github.com/rozkalnsandris/coloring-pages/pull/158).

## Decision required before implementation

Keep both Like/unlike and Print-intent counters, and keep a persistent browser visitor ID **only with valid purpose-specific permission**. Browsing, downloading and actual A4 printing must remain available without permission.

The current Cloudflare Worker **requires** a visitor_id on POST /api/stats/print. Therefore counting every Print action without consent is **not** supported by the existing API:

- **A — recommended minimal source design:** Count only Print intents from visitors who explicitly opted in to persistent Print statistics. Preserve all historical totals and Like/Print UI. Do not submit a Print event without consent. Admin must label the metric as "consented print intents" (not all prints). No Worker/D1 mutation required. **Owner acceptance of undercount is not yet recorded.**
- **B — separate backend proposal:** Count nonconsenting Print intents through a reviewed ID-free endpoint and bounded anti-abuse controls. Requires separate privacy/security assessment, source/API/tests scope, and owner authorization for any Worker/D1/LIVE changes. Do not treat an "anonymous" HTTP request as automatically free of IP/logging/privacy implications.

**Owner instruction on 2026-10-11:** implement the very slim fixed bottom-of-screen first-visit banner, 12–13px text, three comparable actions (Alle ablehnen, Einstellungen, Alle akzeptieren), and independent Like/Print opt-ins. The owner accepted the immediately preceding description that refused Print telemetry is not counted. Thus implementation selects option A: consented-only future Print intents, with historical totals preserved. The limitation remains explicit. No API/Worker/D1 changes.

## Verified source wiring, not LIVE proof

- js/stats.js: getVisitorId(false) reads localStorage["coloring-pages-visitor-v1"] on getPage; toggleLike and trackPrint call getVisitorId(true). getPage sends the ID in a GET query; Like and Print send it in POST bodies.
- js/detail.js: on "A4 drucken" click, invokes trackPrint before startHtmlPrint; print.html/js/print.js actually renders printable pages. print must never wait for/require telemetry permission.
- cloudflare/stats-worker.js: page status optionally accepts a visitor_id; Like and Print writes require it. The raw ID may be used for rate-limiting; Like rows retain a SHA-256 visitor hash, with no built-in expiry in cloudflare/stats-schema.sql. Print counts are aggregates. This is source behavior; actual Cloudflare retention/settings and deployed versions need separate evidence.
- Existing GET /api/stats/page?visitor_id=... risks ID exposure in URL logs; do not silently change the API in this design lane.

## Proposed minimal consent UX

Use a compact **full-width fixed bottom banner** (12–13px desktop text, narrow height, small buttons) shown on first visit. The settings view offers independent, initially unchecked Like and Print choices. The banner exposes equal-prominence deny, settings and accept controls. Footer "Datenschutzeinstellungen" reopens these choices. **"A4 drucken" always works without telemetry consent**. Do not interpret clicking Like or Print as consent.

Illustrative short labels (final German text and legal scope require review):
- Like: "Gefällt-mir-Funktion mit Wiedererkennung" — allow the page to remember your Like on later visits.
- Print: "Druckstatistik mit Wiedererkennung" — allow counting repeated print intentions using a stored ID; no claim that a sheet was printed.
- Buttons: "Zustimmen" / "Ablehnen" (comparable size/prominence); settings: "Datenschutzeinstellungen", "Einwilligung widerrufen".

Both permissions start unset/off; no prechecked box. Consent is given through explicit affirmative action for that one purpose. Refusal does not block gallery, A4 print, print preview or PNG download. Display aggregate Like counts without personalization; a new Like attempt may offer opt-in, but declining leaves Like personalization unavailable rather than inventing a visitor ID. Keep keyboard, focus, screen-reader and small-screen behavior accessible.

## Minimal implementation state proposal (for later, not written here)

A purpose-specific consent record can contain only a policy version, two separate decisions (like, print: granted/denied/unset) and a decision timestamp. No raw visitor ID belongs in the consent record. Evaluate the strict-necessity basis for reading/storing **the consent preferences themselves** separately under TDDDG §25; do not claim they are automatically exempt. Record acceptance evidence proportionately under GDPR Article 7(1) and define validity/re-prompt criteria after material purpose or policy changes.

Treat previously stored visitor IDs as **unconsented** until a fresh explicit affirmative decision. Check the relevant permission before *any* access to the visitor ID key, before adding visitor_id to GET URLs or any POST payload, and after a reload. If a relevant permission is missing/denied, do not read, create, send or reuse the visitor ID for that purpose. Consent can be stored without immediately generating an identifier; generate it only when first needed for an authorized operation.

If only Like permission is revoked, immediately cease personalized Like GETs and Like POSTs; leave a still-authorized Print ID usable solely for Print. Vice versa for Print. If **both** are revoked, stop further accesses and remove the browser identifier through an explicit withdrawal path without transmitting it; do not claim that this deletes Cloudflare logs or historical D1 rows. Design deletion/retention handling of existing server-side Like hashes and consent evidence before release. Revocation must be as easy and as visible as granting permission.

No third-party consent management service, Cloudflare upgrade, new API token, D1 schema change or host mutation is proposed by default.

## Required acceptance matrix for a separate, authorized source PR

| Scenario | Visitor ID read/write/transmit | Like function | A4 print | Print event |
| --- | --- | --- | --- | --- |
| First visit or unknown consent | None | Aggregate count only, offer Like opt-in | Works immediately | None under A |
| Explicit refusal of both | None | Aggregate count only | Works immediately | None under A |
| Like-only permission | For Like only | Like/unlike and returning status | Works immediately | None under A |
| Print-only permission | For Print only | Aggregate count only | Works immediately | Count consenting intentions |
| Both permissions | For their respective purposes | Like/unlike and returning status | Works immediately | Count consenting intentions |
| Withdraw Like, keep Print | Never for Like | Aggregate count only; server record retention to review | Works immediately | Only while Print consent remains |
| Withdraw Print, keep Like | Never for Print | Like continues | Works immediately | None under A |
| Withdraw both | No future reads/sends; remove ID locally | Aggregate count only | Works immediately | None |
| Existing legacy ID, no fresh decision | Must not read/send legacy ID | Aggregate count only | Works immediately | None |
| Storage unavailable, malformed or outdated permission record | Fail closed; no ID accesses | Aggregate count only | Works immediately | None |

Tests must cover event-order races (including print dialog), reload, browser storage errors, repeated click, purpose separation, network failures, consent revocation, inaccessible controls, no unauthorized visitor_id in GET/POST, existing aggregate Like counts, and unchanged historical Print totals. Test as an opt-in flow on mobile and desktop. Do not silently change the current print orchestration or degrade the downloadable A4 PNGs.

## Retention and erasure policy proposal (owner decision pending)

**Design authority only (2026-10-11):** owner explicitly authorized a retention/erasure policy design for issue #182; **no term below is an owner-approved retention rule, legal sign-off, implemented expiry, running cleanup, or LIVE fact**. The proposal is deliberately small, Cloudflare Workers Free-compatible and separate from PR #158's legal Draft. A maximum lifespan is a product/policy choice to justify, **not a statutory German/European fixed 12-month period**.

### Proposed decisions, not current code

| Data | Recommended policy choice for owner/legal approval | Enforcement gap |
| --- | --- | --- |
| Browser consent preference \`coloring-pages-consent-v1\` | Store *only* policy version, independent Like/Print decisions and \`decided_at\`. Suggest **12 months from each explicit decision**, then re-prompt for positive consent; never silently extend it through browsing. Denial is remembered without a UID. Immediately honor withdrawal; a material purpose/text change invalidates affected previous consent. | PR #183 checks types/version but does **not** currently expire decisions, validate timestamps strictly, or archive each actual banner text/configuration release. Future frontend source/test change needed. |
| Browser \`coloring-pages-visitor-v1\` | Only for explicitly permitted Like and/or Print; propose **at most until consent expiry / 12 months after explicit opt-in**, whichever is sooner. Do not read, send, or rotate an unconsented ID; remove it locally after both permissions cease. Never use it for the separate visitor-HMAC analytics. | The current source has no expiry or purpose-specific ID rotation at the proposed deadline. Any renewal/new ID must be considered alongside D1 Like-row lifecycle. |
| D1 \`likes(page_id, visitor_hash, created_at)\` | To retain cross-visit Likes without indefinite personal identifiers, suggest **maximum 12 months after each original Like** as a bounded starting point, then delete that row and let the existing \`likes_after_delete\` trigger decrement \`page_stats.like_count\`. An explicit Unlike deletes the row sooner. Re-consenting after 12 months does **not** silently renew an old Like record. | No TTL/cleanup exists. A daily bounded cleanup would need a separate Worker source change, correctly verified schema queries and a separate owner-authorized LIVE/Worker release. **This reduces visible Like totals as old Likes age out**; explicit owner product approval is required, and legacy rows must not be silently bulk-deleted. |
| D1 \`daily_visitors(day, visitor_hash)\` HMAC | Keep **current UTC day and previous UTC day** only; delete all older days during one regular daily cleanup (for example at 00:20 UTC). Define this as a *day-based* window, not a guarantee of exactly 48 hours. Keep the existing deletion on successful visitor requests as a bounded fallback. | Current Worker only deletes old rows on *successful subsequent* visits. During quiet periods data can remain indefinitely. Propose one daily Cloudflare Worker **Cron Trigger**, if a free slot exists (Workers Free currently permits five Cron Triggers **per account**); implementation, schedule, observation and deployment are separately gated. |
| Print-intent/daily aggregate counters | Preserve historical counts and continue counting only consented new Print intents as decided for PR #183. No visitor ID stored in \`daily_prints\` or the aggregate \`page_stats\` counts. Do not equate these with physical printed sheets. | Their retention remains a separate proportionality/true-anonymity review; do not assume any aggregation is automatically anonymous under every context. Do not reset existing counters. |
| Rate Limiter, Workers Logs, D1 Time Travel, origin logs | Use provider-verified actual configuration and lawful storage criteria in the published notice; **do not choose a fake expiry**. A 10/60-second rate-limiting counter window is not a proven erasure guarantee. Workers Free Logs are up to 3 days **if enabled** under the present pre-Dec-2026 plan. D1 Time Travel's Free recovery window is 7 days, **not live-row TTL**. Existing nginx/Docker volume rotation is size-based, not time-based. | The account's actual observability setting, other edge/security logs, Rate Limiter state, transfers, third-party retention, and any backups remain unverified. These need bounded read-only evidence, not an unapproved Cloudflare settings write. |

### Consent proof without tracking for proof

The **German DSK OH Digitale Dienste v1.2 (Nov 2024), paragraphs 84–85** explicitly says proof of browser consent does *not* require long-lived unique-ID cookies. Usually the controller can document the consent-gathering process, a decision record *without UID*, and the actual banner text/configuration and technical flow shown at the time. Keep a **versioned, immutable-in-history source archive** of each real banner and privacy-text revision in GitHub with date, release SHA, text/purposes, and controls/tests. An on-device \`version/like/print/decided_at\` record is a working preference, not independently verified evidence of a particular individual's assent; document its limits. **No new server-side per-person consent ID/database is recommended by default.** Verify whether storing the non-identifying preference qualifies for §25(2) strict necessity separately from browser visitor-ID consent. Under EDPB Guidelines 05/2020, consent has **no automatic fixed statutory validity period**; renew at context-appropriate intervals and immediately when purposes materially change.

### Erasure versus withdrawal — unresolved critical release gate

1. **Withdraw one purpose:** Immediately stop access/transmission for that purpose; other approved purpose may remain active. Anonymous Like counts and A4 print continue. No hidden or background tracking request on withdrawal.
2. **Withdraw both purposes:** UI must complete withdrawal immediately and remove the local visitor ID without first sending it, preserving the explicit #182 scope. **This is not server erasure.** D1 may still contain that visitor's pseudonymous \`likes\` records, including orphaned pre-consent legacy entries. Consent withdrawal and any valid GDPR Article 17 erasure request must be evaluated distinctly; an expiry in 12 months **does not by itself prove that an earlier erasure obligation has been satisfied**.
3. **Technical incompatibility to resolve before release:** With the current D1 schema, the Worker locates the visitor's Like rows using \`sha256(visitor_id)\`. If the browser destroys its ID without any earlier verified deletion request, the Worker cannot identify those rows to delete for that user. Do not claim that old Like rows vanish on withdrawal. A secure erasure endpoint and **separate, consciously initiated "Meine Likes löschen"** action *while the user still holds the ID*, with confirmation before removal, is one candidate; this would transmit a scoped deletion credential in a user-invoked erasure flow rather than silently in a withdrawal event. Another lawful erasure design could be reviewed, but must not weaken easy immediate withdrawal. No implementation or production deletion is authorized yet.
4. **Backend implementation gate:** Before allowing a persistent Like-ID release, settle whether the explicit erasure flow is necessary, its lawful-basis/authenticity/abuse and race handling, how the client can initiate deletion after declining, and the retention/delete status of related Worker logs/Time Travel. Avoid raw IDs in GET query strings for any new erasure endpoint. Keep unrelated historical print counters, media and catalog untouched.
5. **Legacy records:** Pre-consent Like hashes may be inaccessible once PR #183 discards a legacy ID; owner must expressly approve any reviewed, exact-scope migration/cleanup that changes old counts. No bulk D1 purge, overwrite or manual production mutation under this design authority.

### Source acceptance and owner gates (not actions taken)

- [ ] Owner picks or revises **12-month proposal** for affirmative consent, browser identifier and D1 Like rows; owner expressly accepts expiry reducing visible Like counts, or selects a different bounded policy after legal review.
- [ ] Owner decides the **erasure design** compatible with immediate no-ID-on-withdrawal, including whether a separate pre-withdrawal deletion flow and Worker endpoint are authorized. No implied privilege to delete D1 rows.
- [ ] Confirm the Worker Free **Cron Trigger slot** using a separately authorized minimum-sufficient account read, then independently approve source design of one daily \`scheduled()\` handler/SQL cleanup and separately gate its LIVE deployment. Do not presume the cron is configured.
- [ ] Document timestamp/date parsing, exact UTC cutoffs, denied vs granted preference expiry, clock-skew handling, 12-month renewal, no ID reads on expired/legacy consent, last-consent expiry and storage-unavailable behavior in unit/browser tests.
- [ ] Test that deleting aged Likes updates counts via the existing trigger and does not reset historical Print counters; confirm D1 SQL semantics in isolated tests only. Ensure retry/rate-limit failures do not silently drop erasure requests while the client claims erasure.
- [ ] Keep archived versions of consent text and GitHub CI/release evidence **without per-visitor IDs**, actual data retention and Article 13 disclosure, processing basis for separate visit-HMAC analytics, DSFA/Article 8 applicability if needed, and justified actual Cloudflare logs/transfers; legal sign-off before coordinated PR #158/#183 release.
- [ ] **Source/docs design only today:** no \`js/consent.js\`, Worker, schema, D1 data, account settings, Cron, RPi5, merge or LIVE mutation.

Authoritative references, checked 2026-10-11:
- [DSK *Orientierungshilfe für Anbieter:innen von digitalen Diensten* v1.2 (paras. 78–85, 128–136)](https://www.datenschutz-berlin.de/fileadmin/user_upload/pdf/publikationen/DSK/orientierungshilfen/2024_DSK-OH_Digitale-Dienste.pdf).
- [TDDDG §25](https://www.gesetze-im-internet.de/ttdsg/__25.html); [GDPR Arts. 5(1)(e), 7, 13, 17](https://eur-lex.europa.eu/eli/reg/2016/679/oj).
- [EDPB Guidelines 05/2020 consent](https://www.edpb.europa.eu/sites/default/files/files/file1/edpb_guidelines_202005_consent_en.pdf).
- [Cloudflare Workers Free Cron Trigger quota](https://developers.cloudflare.com/workers/platform/limits/); [Cron Trigger lifecycle](https://developers.cloudflare.com/workers/configuration/cron-triggers/); [Rate Limiting](https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/).
- [D1 Time Travel](https://developers.cloudflare.com/d1/reference/time-travel/); [Workers Logs as of 2026-10-11](https://developers.cloudflare.com/workers/observability/logs/workers-logs/).

---

## Release gates and sources

- Legal review: TDDDG §25 strict necessity vs specific informed consent; GDPR Articles 6, 7 and 13, plus Article 8 if actually offering information society services directly to children; minimize retention and verify data subjects' rights. Review the Cloudflare logs, D1 Like-row retention and cross-border processing against operating facts. Existing Self-Serve DPA incorporation is documented in PR #158 but is **not** legal sign-off.
- Privacy page updates must be reviewed alongside PR #158, which remains Draft/NOT RELEASE READY; no dependency-based merge without separate approval.
- Owner must choose Print counting A/B before implementation; if B, authorize separate API/Worker/source design and later the appropriate LIVE gate. An implementation PR still requires its own scoped approval and exact-head CI/reviews.

Official references, reviewed 2026-10-11:
- [TDDDG §25 — law](https://www.gesetze-im-internet.de/ttdsg/__25.html).
- [DSK *Orientierungshilfe für Anbieter:innen von digitalen Diensten*, v1.2 (2024), paras. 36–39, 59–63, 78–81, 128–136](https://www.datenschutzkonferenz-online.de/media/oh/OH_Digitale_Dienste.pdf).
- [GDPR Articles 6–8, 13 — EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj).
- [EDPB Guidelines 05/2020 on consent](https://www.edpb.europa.eu/documents/guideline/guidelines-052020-on-consent-under-regulation-2016679_en).

## Source implementation evidence (2026-10-11)

- `js/consent.js` and `css/consent.css`: first-visit slim fixed footer strip, two independently persisted opt-ins, equal-weight denial/acceptance, accessible settings and withdrawal, legacy-ID discard on first explicit choice without reading the old value.
- `js/stats.js`: only accesses/creates/sends `visitor_id` for the specific purpose with explicit consent; otherwise `getPage` requests aggregate public numbers without visitor_id, `toggleLike` cannot post, and `trackPrint` returns without telemetry.
- `js/detail.js`: Like asks for explicit settings when disabled; consent change refreshes Like status. Print continues into A4 print regardless of telemetry permission.
- `stats.html` labels cumulative metrics as historical, with future counts consent-limited. The actual retention, consent evidence adequacy and deletion policies remain unresolved legal gates.
- Only index/detail/kita pages currently load the banner. The legal pages in Draft PR #158 must be updated to describe the actual consent behavior and must be present before releasing this feature: until then the banner Datenschutz link would point to a page not yet published. This keeps PR #183 in Draft until legal coordination.
