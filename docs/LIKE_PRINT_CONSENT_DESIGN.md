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

## Retention and erasure policy — owner product decision, legal gates open (2026-10-11)

**Owner correction, 2026-10-11:** "like ID nedzēšam nekad ārā" (do not delete the Like ID). Interpret this as a **product requirement not to automatically expire or delete the browser Like ID or active D1 Like records merely because they are 12 months old**. The owner rejects the previously suggested age-based purge and its unwanted drop in visible Like counts. Preserve recognition and reversible Like/unlike as long as valid permission and a justified purpose remain.

**Legal limit:** "Never delete, even after withdrawal or a valid erasure request" cannot be promised or implemented for pseudonymous personal data solely processed on consent. GDPR Art. 5(1)(e) requires storage limitation, Art. 7(3) permits withdrawal, and Art. 17 can require erasure; the European Commission explicitly confirms data processed only with consent must be erased after withdrawal absent another legal basis. There is no generally prescribed 12-month statutory period. No implementation, legal sign-off, or LIVE mutation is authorized by this design note.

### Revised policy choices

| Store | Proposed behavior under the owner's no-age-deletion preference | Remaining decision / evidence |
| --- | --- | --- |
| Browser `coloring-pages-visitor-v1` | **No 12-month TTL or scheduled purge** merely due to age. Reuse the same ID for the authorized Like and/or Print purpose(s) across visits while consent is valid. If permission is missing/expired/withdrawn, do not read/transmit it. If both purposes are withdrawn, current PR #183 removes it locally without sending it. | The ID cannot be promised eternal persistence in the browser: users can clear data, switch devices, revoke permission, and law may require deletion. Document actual retention criteria, consent renewal and the erasure flow. |
| D1 `likes(page_id, visitor_hash, created_at)` | **No 12-month purge; never remove an active Like only because it aged.** Keep Like count stable for continuing authorized Likes. Unlike deletes that row using the current Worker and decrements the count via `likes_after_delete`. | Retaining pseudonymous hashes indefinitely with no purpose/necessity assessment is not automatically lawful. Assess Art. 5(1)(e), 6, 7, 13 and 17 and an effective erasure solution after withdrawal, lost ID or verified request. Historical/legacy rows need a separate reviewed policy. |
| Browser `coloring-pages-consent-v1` | Store purpose-specific decisions, version and decision time, without a UID. A previously suggested **12-month renewal review** is about the **validity of consent**, not a reason to delete Likes automatically. On a material change, request fresh permission; fail closed until re-confirmed. | Select a defensible renewal interval based on actual purpose, expectations and legal guidance. Maintain immutable versioned banner/text source and test evidence; do not invent a legal default expiry. Existing PR #183 does not implement time validation. |
| D1 `daily_visitors` IP/day HMAC | Unchanged separate proposal: retain only current and previous UTC day, and consider daily bounded cleanup of older rows **without touching Likes**. | Current Worker cleanup runs only on successful visits; a Cloudflare Cron and its account configuration would require separate approval/implementation/LIVE gate. |
| Historic Print, daily aggregates, logging | Preserve counts and content; consented future Print intents only. Use the actual Cloudflare/Docker/Rate Limiter retention and logging evidence; do not claim size rotation or D1 Time Travel means row erasure. | Independently document Art. 6/13 lawful bases, transfers, retention criteria, and erasure obligations when data can be linked to a person. |

### Withdrawal and individual erasure are mandatory exceptions

1. **Unlike:** A user can reverse a Like while the original authorized identifier is available; the corresponding row is deleted, and the visible Like count drops for this explicit action. This is intentional, not an age-based purge.
2. **Withdraw only Like consent:** Stop using/transmitting the identifier for Like immediately. If Print remains allowed, the same browser ID can still be used **only for Print**; the Like-associated personal data require assessment and deletion where no other valid legal basis remains.
3. **Withdraw both permissions:** Immediately stop the optional purposes and discard the local visitor ID as in PR #183; **that action alone does not delete corresponding D1 Like hashes**. A separate, effective deletion process is a release blocker. Do not silently send the withdrawn ID in the background.
4. **GDPR Art. 17 erasure / lost ID:** Provide a properly authenticated, proportionate way to erase identifiable Like rows where required, without collecting new intrusive data or allowing arbitrary visitors to delete others' Likes. The current hash lookup `sha256(visitor_id)` cannot find a visitor's rows once their local ID is already lost. Review a separate user-triggered erasure operation **before** local ID removal or another safe alternative. Do not imply that requesting erasure requires an unwanted new tracking ID.
5. **Old Like rows:** No blanket migration, deletion, backend reset, schema change, or silent reduction in Like totals under this design decision. Assess their legal basis and lifecycle separately.

### Acceptance/gates

- [x] Owner rejected automatic 12-month deletion of Like ID / active Like rows as a product design.
- [ ] Establish and document a GDPR-compliant **purpose-based** retention justification for as-long-as-needed Like recognition, instead of claiming a literal "forever" right.
- [ ] Design and test withdrawal/erasure handling without invisible use of a revoked identifier; resolve server-side Like hash deletion and user authentication.
- [ ] Evaluate consent validity and re-prompt separately, without automatically deleting a Like due only to an age threshold.
- [ ] If needed, separately authorize a source/API/Worker or D1 change; apply no deletions, Cron changes, account settings, or LIVE changes here.
- [ ] Coordinate any final retention/withdrawal wording with legal Draft PR #158 and obtain legal sign-off before owner-authorized coordinated release.

Official references (reviewed 2026-10-11):
- [European Commission — Legal grounds for processing data](https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/legal-grounds-processing-data_en)
- [EDPB — Respect individuals' rights](https://www.edpb.europa.eu/sme/be-compliant/respect-individuals-rights_en)
- [EDPB — Consent Guidelines 05/2020](https://www.edpb.europa.eu/documents/guideline/guidelines-052020-on-consent-under-regulation-2016679_en)
- [GDPR Arts. 5, 7, 13 and 17](https://eur-lex.europa.eu/eli/reg/2016/679/oj)
- [TDDDG §25](https://www.gesetze-im-internet.de/ttdsg/__25.html)

---

## Like erasure and withdrawal flow — A approved in design, implementation gated (2026-10-11)

**Authority and product constraint:** The owner first authorized design for issue #182 with `ERASURE-FLOW KEEP-LIKES-NO-AGE-PURGE SOURCE-ONLY NO-MERGE NO-LIVE`, then explicitly selected **`ERASURE=A EXPLICIT-USER-ERASURE-POST`** with **`NO-IMPLEMENTATION NO-MERGE NO-LIVE`** on 2026-10-11. The decision approves only the *design*: a narrowly scoped, clearly requested erasure POST may carry a deletion proof for that one request. It does **not** authorize implementation, any API/Worker/D1/Cloudflare change, sending a real ID, deleting production data, merge or LIVE. Active Likes and the browser ID remain free of automatic age-based deletion; withdrawal and valid erasure requests still require lawful handling.

### Verified implementation gap

- The existing Worker accepts `POST /api/stats/like` with both `page_id` and `visitor_id`, and deletes **one matching Like for one page** when a user toggles it off. It has **no all-Likes erasure API**.
- D1 `likes` rows have `(page_id,visitor_hash)` keys, and the existing `likes_after_delete` trigger decrements corresponding public `page_stats.like_count`. `DELETE FROM likes WHERE visitor_hash = ?` is the natural candidate for a verified, targeted all-pages deletion; assess in isolated SQLite tests, including multiple rows, idempotence, triggers, and untouched Print counters.
- Worker `allowedWriteOrigin()` already filters some cross-origin requests, and `rateLimit()` exists, but neither alone establishes ownership of a visitor ID. `getPage()` currently sends raw `visitor_id` as a GET query parameter when the Like purpose is consented, increasing its possible visibility in request logs. `js/stats.js` currently has a **non-cryptographic `Math.random()` fallback** when `crypto.randomUUID()` is missing; that fallback is not suitable as the proof for an irreversible deletion endpoint.
- `js/consent.js` currently removes the local ID immediately after both purposes are rejected or withdrawn, without contacting D1. The issue's **existing no-ID-transmission-on-withdrawal** constraint is preserved until the owner explicitly decides whether a scoped *user-directed erasure request* is an authorized exception. No backend deletion can be inferred from a local ID removal.
- The legacy pre-opt-in ID is discarded on a first choice without being read; any older D1 Like rows associated with it can be orphaned. No silent attempt to read those IDs, reconstruct identity or bulk-delete them is permitted.

### Minimal proposed UX

The small full-width consent strip stays unchanged. Inside its existing `Datenschutzeinstellungen` panel, add a clearly separate, optional action labelled **"Meine gespeicherten Likes löschen"** with a precise confirmation step. It should explain that this removes **only the user's own existing Likes**, changes the corresponding visible Like counts, cannot be undone automatically, and does **not** delete anyone else's Likes, historical Print counts, page content or media.

The purpose-specific Like/Print toggles remain independent. An ordinary `Gefällt mir` click still toggles a single page. With Like permission active, users never have their Likes automatically removed just because 12 months passed. Download, public aggregate counts, and A4 printing remain available without Like or Print permission.

**Legal constraint:** GDPR Article 7(3) makes withdrawal easy; Article 17(1)(b) and EDPB Guidelines 05/2020 paragraph 119 generally require erasure of data held only on the withdrawn consent unless a valid independent retention basis applies. Therefore **"withdraw Like consent but indefinitely leave identifiable Like hashes in D1" is not a release-ready final workflow**. A separate optional delete button cannot replace any erasure actually required on withdrawal. A new legal basis must never be silently substituted after withdrawal.

### Candidate flow and unresolved authority boundary

**Selected A (owner-approved design; security review and implementation authority still pending): one visibly user-initiated operation combining withdrawal and erasure.** If Like was consented and a visitor ID exists, take a single deletion-only proof *at the user's explicit request*, stop further Like operations immediately, and issue **one** HTTPS `POST /api/stats/erase-likes` with the proof in a JSON body (never a URL/query/cookie). On confirmed server success, keep any separately consented Print permission; remove the local ID only if neither purpose remains. Unrelated historical Print counters and active Likes of other visitors stay unchanged. Explain to the user *before* the click that the ID is sent solely to fulfill their erasure request, not for tracking.

**Approved design exception, not code authority:** The owner accepts a visitor deletion proof being sent *only within the user-explicit, purpose-limited erasure POST*, rather than as Like/Print telemetry. Ordinary withdrawal, refusal, browsing or printing must not silently send the ID. This approval supersedes the earlier **no-ID-transmission** design prohibition **only for the requested erasure operation**, and only at the design level. The actual proof, authorization of the sender, lawful basis, data minimization, browser-ID leakage and fail-closed behavior must pass a security/legal review before any source implementation.

**Failure semantics:** Withdrawal must take effect immediately even if the network or D1 is unavailable; the website must never falsely report server-side erasure, nor re-enable Like telemetry without a new affirmative choice. On timeout or ambiguous Worker outcome, show **"Einwilligung widerrufen; Löschung nicht bestätigt"** and a clear next user-controlled recovery/DSAR path; do not claim that deleting the browser ID is enough. The exact minimum erasure-proof lifetime, preservation after failed requests, handling browser reload/offline, and permitted manual user-triggered resubmission must be designed before implementation. No indefinite or covert identifier retention merely for a hypothetical future request.

**Alternative B (not selected for the intended product, preserved as a safety fallback):** Allow immediate local withdrawal with no network request, but **do not call it completed server erasure**. The controller would need an effective separate deletion/verification mechanism for identifiable D1 rows, including the case where the browser no longer has the ID. Until that mechanism and Art. 17 handling are justified, **do not release** the consent-enabled Like feature. Do not solve this by quietly purging all users' Likes.

### Selected A: bounded security handoff and no-LIVE proof

1. **UI intent:** Keep the compact first-visit strip unchanged. Expose a distinguishable `Meine gespeicherten Likes löschen` / withdrawal-and-erasure choice in `Datenschutzeinstellungen`. Before irreversible deletion, explain the affected Like counts and require a direct confirmation. The action is **not** triggered by an unrelated Like, Print, page navigation or rejection of cookies. Normal withdrawal must always immediately disable Like processing, even if deletion cannot complete.
2. **Minimal scoped request:** Only after explicit confirmation, propose exactly one `POST /api/stats/erase-likes` over HTTPS with the required validated deletion proof in the **request body**, not URL, fragment, referrer, log or analytics. No `page_id` is needed for all-pages erasure; no batch caller list, chosen `visitor_hash`, wildcard or admin operation. An explicit "erase" action cannot be used to renew Like consent.
3. **Caller binding/security gate:** Current Like IDs are bearer-like identifiers and can be exposed in `GET /api/stats/page?visitor_id=...`; historical fallback `Math.random()` is not cryptographically strong. **Do not deploy an erasure endpoint relying only on arbitrary current/legacy ID possession without resolving that risk.** Evaluate a securely generated, scope-limited deletion credential and authenticated caller-binding model, origin/CSRF checks, replay/rate limits and safe migration of old IDs. No new persistent tracking or per-person database merely to make an erasure credential.
4. **D1 effect (design only):** A correctly authenticated, bound SQL deletion restricted to the caller's `visitor_hash` may remove only their Like rows; existing SQLite delete triggers maintain each public Like count. Verify D1 result metadata and errors before acknowledging success. Never delete another visitor's rows or adjust the Print, visit, catalog or content datasets. **No automatic time-based Like purge.**
5. **Consent sequencing:** The Like-purpose permission must stop immediately upon withdrawal. If Print remains separately allowed, it may continue. Any necessary deletion-only proof must be isolated from Like/Print telemetry, ephemeral and explicitly user-invoked; **do not assume the existing frontend can both erase the browser key immediately and later recover the necessary proof**. If deletion fails, do not claim completion or restore Like consent; offer a clear explicit user-driven recovery or rights-request path. No silent automatic retries or hidden ID access after withdrawal.
6. **Tests before code Ready:** first visit, denied consent, both consented, Like-only, Print-only, explicit one-page Unlike, multi-page own erasure, other-user rows untouched, concurrent/in-flight Like, idempotent repeat, no ID/legacy weak ID, CSRF/hostile Origin, replay, quota limit, offline, response timeout, D1 error, withdrawal while Print stays on, and successful result/trigger consistency. Run schema SQL tests offline; never point test erasure at production D1.

**Release dependency:** Selected A is not implemented. Draft PR #183 code still lacks the erasure UI/client flow, and the current Worker has no endpoint. Draft PR #158's legal text likewise cannot be claimed to describe a deployed erasure feature. Do not merge either draft as a complete privacy solution or assert GDPR compliance based on this design sign-off.

### Candidate Worker contract (not implemented)

- `POST /api/stats/erase-likes`, explicit deletion intent, same public origin, limited JSON body with visitor proof; no required `page_id` because erasure spans all the requesting browser ID's pages. Use a **separate validated parser**, not the existing `parseBody()` (which requires `page_id`). Never allow a caller-supplied SQL hash, page selection wildcard, arbitrary visitor list or mass-delete flag.
- Confirm truly **unpredictable** browser IDs (secure Web Crypto; no `Math.random` fallback), and mitigate leakage caused by the existing personalized GET query. Until this is resolved, possession of a raw ID should not be treated as a strong authenticated authorization to erase another user's rows. Assess scoped signed deletion proof or other minimal trustworthy design without paid Cloudflare services.
- Check real Origin/site policy and request abuse controls, `no-store` responses, no sensitive IDs in GET URLs, analytics, request logs or error text. Apply the same hashed visitor lookup used for Like matching; only delete matches for the proven caller, not the full `likes` table. Account for replay and concurrent Like requests.
- Database candidate: one bound parameterized `DELETE FROM likes WHERE visitor_hash = ?` after server-side hashing, letting existing delete triggers maintain page counts. Do not independently subtract counts a second time. Verify D1/SQLite transaction semantics, trigger behavior, error handling and response/receipt correctness with isolated tests. Never modify `daily_prints`, `page_stats.print_count`, `daily_visitors` or other accounts' Likes.
- A successful erasure receipt must be returned **only after the D1 write is confirmed**. A second same-visitor deletion with zero matched rows may be idempotently successful. Errors or interrupted operations must not generate success assertions. Record no unnecessary visitor-level deletion audit trail.
- `GDPR Art. 11`: When the controller genuinely cannot identify the person from the existing data, it is not obliged to collect additional identification solely for rights requests; it should communicate this where possible and act when the requester supplies sufficient information. A lost local ID is **not** grounds to pretend the D1 hash was deleted.
- Existing D1 Time Travel recovery, Worker/security logs and any retained extracts/backups must be addressed separately; `DELETE` success is not a statement that all physical copies have already expired.

### Required acceptance matrix for a later implementation

| Scenario | Expected privacy-safe behavior |
| --- | --- |
| Like consented, active Likes, no withdrawal | Keep ID/rows across visits; **no automatic age purge**, counts unchanged. |
| User unlikes one page | Only its own row deleted; corresponding count decreases once. |
| User explicitly requests all-Likes erasure | Only verified own rows deleted, with clear confirmation; other users and Print statistics intact. |
| Like withdrawn; Print still granted | No future Like identifier use; Print may continue under its separate permission, and only own Like rows are within erasure scope. |
| Like+Print both withdrawn | Neither purpose continues; local ID handling and D1 erasure must follow an owner-approved, legally sound sequencing plan. |
| Anonymous first visit / denied Like consent | No ID lookup or deletion endpoint call, no blocked A4 printing. |
| Network timeout / D1 failure / rate limit | Immediate withdrawal possible; show deletion *not confirmed*, user recovery path, no false receipt or silent retries. |
| GET URL containing legacy ID / weak legacy ID / hostile request | No arbitrary account deletion; reject or require an independently secure verification design. |
| Two concurrent deletes / earlier in-flight Like | No double decrement or Like recreation after confirmed final erasure; deterministic checks. |
| Lost legacy ID / user asks for deletion | Explain verifiable Art. 11 limits and available lawful rights process; do not claim deletion happened. |

**Exact next gate:** Perform a **source-only security and erasure-protocol review** of selected A (caller proof, secure new IDs, legacy/leaked IDs, withdrawal/error sequence, in-flight races, request Origin/CSRF protection, ID minimization and D1 deletion/count triggers). Any executable client/Worker changes require a separate **explicit `AUTHORIZE SOURCE`** specifying the exact head/scope. A Worker release, D1 mutation, Cloudflare setting or LIVE action requires its own authorization. Legal Draft PR #158 remains separately gated; its privacy notice must describe the **implemented and verified** flow before a coordinated release. **No merge or LIVE under this design approval.**

Official sources reviewed 2026-10-11:
- [GDPR Articles 7, 11, 17 — EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj).
- [European Commission — Consent and withdrawal](https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/legal-grounds-processing-data_en).
- [EDPB Guidelines 05/2020, especially section 5.3 and paragraph 119](https://www.edpb.europa.eu/documents/guideline/guidelines-052020-on-consent-under-regulation-2016679_en).
- [Cloudflare D1 Worker binding, parameterized statements and batch transaction semantics](https://developers.cloudflare.com/d1/worker-api/d1-database/).
- [Cloudflare D1 SQL and SQLite compatibility](https://developers.cloudflare.com/d1/sql-api/sql-statements/).

---

## Source security implementation — guarded Draft, 2026-10-11

Owner-authorized source-only erasure flow is now implemented as a **Draft**, not a released GDPR-compliant service:
- Browser IDs freshly created with Web Crypto 256-bit randomness use `v2-` + 64 lowercase hex characters. There is **no `Math.random` fallback**. Existing consented legacy IDs remain usable for ordinary Like/Print to avoid destroying active Like records; they are **not** accepted by the irreversible erasure endpoint, and an explicit individual rights process is still required for them.
- Personalized Like status uses **POST /api/stats/page** with `visitor_id` in a JSON body instead of GET query; GET with `visitor_id` is rejected. The unchanged anonymous GET still reports aggregate counts. Historic GET logs/backups may retain older IDs; source changes cannot erase them.
- The dedicated user-confirmed `Meine gespeicherten Likes löschen` control captures only an eligible v2 proof while Like consent is valid, disables Like processing locally **before the request**, and sends one `POST /api/stats/erase-likes` with explicit JSON content. The Worker requires exact Origin and `sec-fetch-site=same-origin`, strict v2 credential shape and bounded request size, plus an available rate limiter. One bound SQL deletion deletes only rows for the hashed v2 ID; existing triggers maintain public Like counts. No automatic age-based purge or Print-counter change.
- Failure, no proof, old ID or unconfirmed D1 response are **not represented as successful erasure**. Withdrawal must remain immediate, and the UI displays the privacy contact for a separate request. There is no automatic network retry or any silent deletion request triggered by ordinary consent withdrawal.
- **Remaining release blockers:** old/leaked IDs and pre-banner Like hashes lack an automated erasure proof; existing user consent withdrawal by toggling off Like does not itself initiate server deletion; cross-tab/in-flight Like writes may race an erasure request without a durable server-side tombstone. Adding such a tombstone would require separately scoped D1 schema/migration and coordinated Worker deployment, not supplied by this command. Review whether this feature may be released under GDPR Articles 7 and 17, add secure handling of those cases, verify real worker runtime/settings, and update PR #158 legal copy before authorizing any merge/LIVE.
- The production Worker, D1, RPi5 and Cloudflare were **not changed**. Source CI cannot prove deployment or legal compliance.

References: [Cloudflare D1 prepared statements](https://developers.cloudflare.com/d1/worker-api/prepared-statements/), [D1 result metadata](https://developers.cloudflare.com/d1/worker-api/return-object/), [MDN Crypto.getRandomValues](https://developer.mozilla.org/en-US/docs/Web/API/Crypto/getRandomValues), [GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj).

---

## Security hardening: cross-tab withdrawal and D1 race barrier (2026-10-11)

- Under owner-authorized **source-only** scope, the client checks the current consent decision on each Like/Print operation and follows cross-tab `storage` changes. An old open tab cannot simply rely on a stale in-memory permission.
- Erasure D1 `batch` atomically creates a **one-day temporary write barrier**, deletes Likes for only the requesting v2 hash and opportunistically cleans expired barriers. Like creation is a single conditional SQL insert that checks that barrier in the **same statement**, preventing a delayed in-flight Like write from restoring erased rows. Existing Like triggers maintain counts; Print totals and other Likes remain intact, with no age-based Like deletion.
- `cloudflare/migrations/like-erasure-blocks.sql` is an **unapplied migration** for existing D1; schema source also includes it for fresh databases. Worker requires it **before activation**. LIVE migration, Worker deploy and runtime verification are **not authorized**.
- Guard expiry is only a logical one-day write-block window. Cleanup is opportunistic: there is no demonstrated guaranteed physical purge or configured scheduled cleanup. Appropriate actual retention and GDPR Art. 7/17 processing remain legal/release gates.
- After confirmed user-requested erasure, the browser removes its old shared ID without reading it under withdrawn Like consent. Separately consented Print can generate a fresh ID. If the Worker returns an error, no erasure is claimed.
- Weak/legacy IDs remain **ineligible for irreversible automated deletion**: possession cannot be treated as cryptographically strong proof. The site offers the privacy contact for manual rights review; inherited D1 hashes and lost-ID recovery need separate legal assessment. No blanket deletion, database reset or automatic age-based Like purge.
- Outstanding before Ready: normal Like-checkbox withdrawal currently does not request backend erasure, and older credentials/manual erasure still require a legally adequate rights path. The exact LIVE D1 schema/Worker sequencing, cookie/Cloudflare processing facts, and legal Draft PR #158 review also remain mandatory. Tests are source/offline only.

Official guidance: [Cloudflare D1 batch](https://developers.cloudflare.com/d1/worker-api/d1-database/); [OWASP CSRF](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html); [Web Crypto](https://developer.mozilla.org/en-US/docs/Web/API/Crypto); [GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj).

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
