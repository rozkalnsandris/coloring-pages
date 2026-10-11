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

## Decision: legacy ID rights handling and ordinary Like withdrawal — design only (2026-10-11)

**Authority:** owner authorized `RESOLVE=LEGACY-ID-ERASURE+ORDINARY-WITHDRAWAL-COMPLIANCE SOURCE-ONLY NO-MERGE NO-LIVE` for #182 at exact PR #183 HEAD `886e6441fcdea27c5b0258c9ca7f9f6419a10390`. This records a recommended solution and acceptance gates, **not approval to implement a new action or release the current code**. No existing D1 row, browser ID, Cloudflare setting or deployed Worker has been changed by this design. Do **not** age-purge any active Like or visitor ID merely after 12 months; the owner rejected that rule. Data subject withdrawal/erasure and a separately justified end of purpose remain exceptions to "keep active Likes".

### 1. Ordinary withdrawal: the deletion action must not be optional

**Policy conclusion:** With consent as the legal basis for personalized Likes, turning **Like** from ON to OFF normally also requires disposing of its associated D1 Like hashes unless a different genuinely applicable legal basis or GDPR Art. 17(3) exception is established. The existing separate `Meine gespeicherten Likes löschen` button is not enough: a user who unchecks Like, presses `Auswahl speichern`, or clicks `Alle ablehnen` currently stops tracking locally but can leave D1 Like rows. The frontend **must not claim that local removal equals server deletion**.

**Recommended minimal UX/source sequence for a later separately authorized implementation:**

1. Keep the slim three-button first-visit banner and two independent checkboxes. For **returning consented** Like users, settings must explain clearly *before the click* that `Alle ablehnen` or switching off Like also requests removal of their personalized stored Likes, so visible Like totals may decrease. Show the same explanation by the explicit `Meine gespeicherten Likes löschen` action. A single, comparably easy withdrawal gesture must work; **do not make withdrawal contingent on extra mandatory confirmation, a successful network request or a completed deletion**.
2. A click is explicit **user-initiated withdrawal/erasure** (selected erasure design A), not permission to transmit an ID on first-visit refusal, page load, Print-only withdrawal or passive navigation. If, and only if, Like was validly enabled and the browser currently possesses a **v2 high-entropy** proof, prepare a deletion-only proof under that existing permission as part of the clearly explained click. Immediately persist Like=false, end personalized Like requests and preserve independent Print choice. Send **one** purpose-limited `POST /api/stats/erase-likes` with the proof in JSON body, no GET URL/cookie/analytics/log, and no hidden retries. The proof is used only to perform deletion, not to restore Like tracking.
3. After confirmed D1 success, report Like deletion and retire the old shared optional ID; if Print still has consent, mint a *new* secure ID only on a later Print use (do not lose its consent). No other users' Likes, historical Print counts or printable content may be changed.
4. If offline, D1 fails, there is an ambiguous timeout or proof is unavailable, **withdrawal still takes effect immediately**, but communicate `Einwilligung widerrufen; Löschung nicht bestätigt` and a clearly accessible rights-request route. Do not show a success receipt, automatically re-enable Like, read the revoked ID for analytics or silently retry. Determine an explicit user-directed recovery path; avoid indefinite hidden retention of an erasure credential after withdrawal. The separate valid-rights-request process remains required if the browser key was already removed.
5. If both purposes are refused initially, or Like was never ON, do not access the visitor ID, do not send an erase request, and do not create a credential merely to erase nonexistent new-person Likes. Ordinary A4 printing and aggregate Like counters remain visible without consent.
6. **Race handling:** serialize the local erase transition in the current tab, handle `storage` revocation from other tabs and do not allow in-flight Like UI success to override revoked state. The existing one-day D1 `like_erasure_blocks` SQL barrier handles delayed Like writes *inside the barrier*, but **does not guarantee that a leaked old v2 token can never post a Like again after one day**. Before release either prove a durable replay/revocation mechanism with legally bounded storage, or explicitly redesign the credential protocol. A one-day guard must not be misrepresented as permanent erasure security.

**Important owner boundary:** previous design A permits **explicit user-initiated erasure POST**, not silent ID transfer on every denial. A properly labelled normal Like withdrawal by a previously consented user can be designed as such an explicit action; this documentation is **not** authorization to change the existing `Alle ablehnen` or `Auswahl speichern` handlers. Reconfirm the reviewed German wording and the legal/security assumptions before any source implementation.

### 2. Legacy and orphaned Like IDs: no unsafe bulk-delete shortcut

Existing older browser identifiers can include a secure `crypto.randomUUID()` UUID **or** the weak date/`Math.random()` fallback from the earlier client. Older IDs were also submitted through `GET /api/stats/page?visitor_id=...`, which could expose them in logs. Therefore the mere shape of a UUID **cannot retroactively establish exclusive ownership**; the current `erase-likes` endpoint must keep rejecting all non-v2 IDs. Neither reusing an old ID as a powerful bearer deletion token nor blindly upgrading it to v2 is a secure fix.

**Legacy policy for now:**

- **Known, validly consented legacy ID still present in the browser:** preserve ordinary Likes until withdrawal, but do not create an irreversible automated all-Likes erase route using only the weak/leakable token. A user must be given an accessible individual rights-request/contact flow with a proportionate review of what evidence actually connects the requester to the pseudonymous record. A prior single-page Unlike is not a substitute for full erasure where required. No raw legacy ID should be requested through email, URL, screenshots, public issue or generic support logs.
- **Old ID discarded at first new consent decision, browser reset, or lost device:** current source discards the pre-opt-in ID without reading it, so an orphaned `sha256(visitor_id)` D1 row cannot later be associated with a particular visitor from ordinary client state. Never silently read an unconsented ID, reconstruct it from logs, guess hashes or delete other users' rows. Document the limits of matching and maintain an effective DSAR route where a requester can provide genuinely sufficient additional information; use GDPR **Art. 11** correctly, rather than claiming that all orphaned hashes were anonymized or erased.
- **Controller/legal retention review:** inherited, unlinked but still pseudonymous Like rows require a documented purpose, lawful basis and proportionate deletion or de-identification strategy. The owner's ban on **automatic age-based purges of *active, authorized* Likes** does not automatically justify keeping orphaned or invalidly consented rows forever. No legacy bulk D1 mutation is allowed under this design.
- **No forced paid infrastructure:** do not install an authentication service or collect IDs/passports solely to support Likes. If the legacy population cannot safely support one-click erasure, keep the source Draft and disclose the limitation rather than lowering deletion authorization checks.
- **Do not silently switch lawful bases:** a withdrawal of consent is not an invitation to invent a new legitimate-interest basis afterwards. Validate the intended deletion processing, provider logs, D1 Time Travel and user notice separately.

### 3. Tests and exact release gates

| Scenario | Later source/CI acceptance |
| --- | --- |
| New visitor clicks `Alle ablehnen` | Zero Like ID reads or transmission; browsing, PNG and A4 print remain available |
| Returning v2 Like user turns Like OFF and saves | One clearly disclosed user-directed erase POST; Like stops **before** network completion; Print consent independently preserved |
| Returning v2 Like user clicks `Alle ablehnen` | Equivalent withdrawal and erase attempt, no second modal needed to withdraw, no automatic retry |
| Existing user requests `Meine gespeicherten Likes löschen` | Same single erasure pipeline; remove only the user's D1 hashes; counts updated once |
| Print-only consent withdrawal | No Like ID read/erasure without a previously approved Like purpose |
| Weak/non-v2 legacy ID, even UUIDv4, requests bulk erasure | No automatic destructive operation; accessible rights-request review; no false success |
| Browser ID missing or previously discarded | No reconstruction, no new pseudo-ID for erasure, explain verification limits under Art. 11 |
| Erase response timeout/D1 or rate-limit failure | Consent OFF immediately; erasure reported unconfirmed, with workable rights/recovery route |
| Two tabs and Like write racing erasure | No resurrected Like within reviewed server-side protocol; ensure protection **beyond one day** if old token remains replayable |
| Other visitor Likes, aggregate Prints, historical data | Not deleted by this individual erasure; no Like age purge |
| Migration and public release | Source/offline tests alone insufficient; distinct preflight/migration/Worker release authorization and coordinated PR #158 privacy review required |

**Remaining decisions, not facts:** prove whether v2 credentials can still be replayed after the temporary D1 block expires, choose a proportionate legacy/orphaned-row lifecycle, and approve the one-click withdrawal/erase wording and endpoint behavior under GDPR/§25 TDDDG. These remain **release blockers**. Do not change `js/consent.js`, `js/stats.js`, `cloudflare/stats-worker.js`, D1 schema or PR #158 under this design-only authority. The next owner gate is an **exact-head, source-only implementation + tests approval** if the reviewed design is accepted; afterward obtain exact-head CI/review and independent legal/release/LIVE approvals.

Official guidance verified 2026-10-11: [GDPR Arts. 5, 7, 11, 13, 17 (EUR-Lex)](https://eur-lex.europa.eu/eli/reg/2016/679/oj); [European Commission consent and withdrawal](https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/legal-grounds-processing-data_en); [EDPB data subject rights](https://www.edpb.europa.eu/topics/key-gdpr-concepts/data-subject-rights_en); [Cloudflare D1 transactional batch](https://developers.cloudflare.com/d1/worker-api/d1-database/).

---

## Source design convergence — normal withdrawal and replay protection (2026-10-11)

This section supersedes earlier one-day barrier/optional erasure discussion. Source work was explicitly authorized for #182; **no merge, Cloudflare Worker deploy, D1 migration, production deletion or RPi5 action**.

- When **previously consented Like** is switched off through the ordinary **Alle ablehnen** or **Auswahl speichern** action, the client treats that explicit user gesture as the deletion request. It captures an eligible v2 proof while permission is still valid, **saves withdrawal immediately**, discards the old optional local ID (Print stays separately consented), and sends **one** purpose-scoped POST request. First-visit refusal, Print-only withdrawal or missing consent do not read/submit the ID. The separate explicit erase button still works, but is no longer a prerequisite for withdrawal.
- A failed/ambiguous POST or legacy/non-v2/missing proof **does not claim erasure**. The UI offers a privacy contact with instruction **not to email the browser identifier**. Old potentially weak/leaked UUID and timestamp IDs are never accepted as sufficient irreversible delete proof; a rights review must assess individual requests and Art. 11 verification limits without demanding intrusive identification by default. Orphaned historic Like hashes still need a justified legal lifecycle.
- Replay: replacing the former temporary one-day SQL guard with an **indefinite revocation record** (hash plus sentinel `blocked_until='9999-12-31 23:59:59'`), created in the **same D1 transaction as erasure**, prevents the already-erased visitor credential from adding new Likes later. The *unexpired* guard check is inside each SQL insertion, not a separate read. The browser uses a new cryptographically random ID for a later newly consented Like/Print.
- **Privacy tradeoff / mandatory owner and legal review**: this retains a minimal pseudonymous revocation hash rather than guaranteeing deletion of every identifier-derived value. It can itself be personal data, so Article 5(1)(e), Article 6, Article 13 and Article 17 require an explicit proportionality/legal basis assessment and actual retention/deletion criteria; do **not** claim GDPR compliance or permanent lawful retention from CI. If indefinite tombstones are not justified, a different revocation/credential protocol is a release blocker. This does **not** age-purge any active Like.
- Offline tests cover SQL guard, other-user Likes and Print aggregates, invalid/weak IDs, error acknowledgments, and source consent wiring. In-flight network, storage failures, cross-tab and real D1 schema/deploy ordering require further review. `cloudflare/migrations/like-erasure-blocks.sql` remains **unapplied**.
- PR #158 German privacy wording must accurately describe the eventually implemented flow, D1, provider/log retention and data subject rights before any coordinated release. **PR #183 remains Draft/NOT READY** pending legal sign-off, security acceptance and separate LIVE authorization.

Official sources: [Cloudflare D1 `batch()`](https://developers.cloudflare.com/d1/worker-api/d1-database/), [OWASP CSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html), [GDPR Arts. 5, 7, 11, 13, 17](https://eur-lex.europa.eu/eli/reg/2016/679/oj).

---

## Bounded resolution proposal for revocation, legacy DSAR, erasure authorization and PR #158 — 2026-10-11

**Owner scope:** \`AUTHORIZE DESIGN coloring-pages #182 PR=183 HEAD=e26bd72525cb91a65a419a62620572c4e2cc0933 RESOLVE=REVOCATION-RETENTION+LEGACY-DSAR+ERASURE-AUTH+PR158-LEGAL-ALIGNMENT SOURCE-ONLY NO-MERGE NO-LIVE\`. This is a **reviewed design proposal and release-gate inventory**, not an owner-approved data-retention legal basis or a permission to edit executable source, the independent legal PR #158, D1 or LIVE. It supersedes earlier claims that the issue is already fully security/legal resolved.

### 1. Revocation: necessary suppression is a distinct processing purpose

**Keep the owner's product rule:** no automatic age purge of *active* Likes, no arbitrary 12-month Like-ID deletion, and no suppression of ordinary A4 printing or aggregate Like counts. Separately, if a Like is withdrawn and the browser's v2 credential is retired, the server must not let the *same credential* recreate Likes by replay.

The current Worker places the same \`SHA-256(visitor_id)\` in \`like_erasure_blocks\` with \`blocked_until='9999-12-31 23:59:59'\`. Its atomic D1 \`batch()\` writes this hash and deletes all the matching \`likes\`; conditional Like INSERT checks the block. **This is indefinite pseudonymous storage, not a proven GDPR-compliant retention period.** Source CI tests only SQL behavior. The earlier one-day guard did not provide security after expiry. The permanent-looking sentinel is **not** a justified retention decision.

**Proposed smallest implementation path, legal approval required before Ready:**

- Treat the hash-only entry as an **erased-credential suppression record** with the sole purpose of preventing recreation following a verified user's erasure. Store no page ID, raw ID, IP, request path, visitor behavior log or additional tracking attributes in that table. Do not reuse the suppression record for analytics, profiling or counting.
- Write a short **documented necessity/balancing assessment** for a possible GDPR Art. 6(1)(f) legitimate-interest legal basis for preventing replay; assess reasonable alternatives, legitimate expectations, risks and user rights. This is a *candidate*, not legal approval or an automatic fallback legal basis for keeping Like rows after withdrawal. Record Art. 13 retention **criteria** (e.g. suppression only while the old credential could be accepted) and review/erasure strategy, not an invented "forever under GDPR" assertion.
- **Safety tradeoff to resolve:** an ID accepted forever and a promise to block it forever imply a persistently queryable revocation mechanism. A fixed tombstone TTL alone permits replay after that TTL. If unbounded hashed suppression is not legally defensible, select a separate, **bounded-lifetime credential protocol** with a server-enforced expiry/renewal and matching bounded revocation lifetime. Such a protocol must preserve user-approved cross-visit Likes without re-enabling old credentials, and requires separate design, code, schema and legal authority. Never quietly reduce security by purging suppression hashes without expiring the credentials too.
- Replace the misleading \`blocked_until=9999\` label with an explicit schema meaning (\`revoked_at\` plus reviewed retention criteria) **only in a separately authorized code/migration change**; do not treat the present schema as a production policy. Specify eventual erasure of the suppression hash if no further replay prevention/legal retention is needed, including related D1 Time Travel/provider backups.
- **Open owner/legal gate:** choose explicitly between (A) minimal hash-only revocation list **with a defensible documented basis/criteria** or (B) bounded-lifetime server-verifiable credential design. Neither choice is automatically authorized by this design review. No destructive cleanup and no expiry of active Like rows.

### 2. Legacy and DSAR — proportional, genuine verification

- A legacy value may be a random UUID *or* a weaker \`Date.now()/Math.random()\` token. It may also have appeared in historical GET \`visitor_id\` query strings. The ability to supply its raw value or know the pages liked **alone does not reliably prove control**. Never accept legacy IDs in the bulk \`erase-likes\` endpoint merely after a format conversion; that could let a copied or guessed token delete someone else's Likes.
- Provide a **plain German privacy request path** already linked from the consent footer: \`Datenschutzanfrage (ohne Browserkennung)\`. Explain what the user wishes to erase, ask for no credentials, IDs, identification-document photographs, screenshots, or sensitive logs by ordinary email. A support reply should offer **only the minimum necessary verification** after assessing the case and the evidence available; keep the message and retention/process scoped to the DSAR, not reuse it for visitor tracking.
- If there is **sufficient reliable evidence** to link a person to a row, decide the lawful, narrowly targeted D1 deletion with owner-gated operator authority and verify it; do not assert that a support email itself automatically deletes rows. If a formerly held ID is irretrievably lost and reliable identification is impossible, document the controller's assessment under **GDPR Art. 11(1)–(2), 12(2), 12(6)**, inform the requester as far as possible, and do not collect extra identity data solely to meet a requirement that genuinely does not need identification. Art. 11 is **not a blanket exception** to storage limitation or Art. 13 transparency.
- Unlinked pre-consent or abandoned Like hashes require an independent necessity/lawful-basis/lifecycle review; owner instruction **"no age purge of active, authorized Likes" does not authorize perpetual orphaned or improperly consented records**. No indiscriminate database purge or stealth hash matching from logs.
- If the real rights mechanism cannot identify older records even when the browser still holds a legacy ID, mark **NOT READY** and disclose the limitation precisely. Do not call the email contact alone a demonstrated complete erasure mechanism.

### 3. Erasure security/authorization boundary

- Selected **ERASURE-A** sends one explicit, purpose-limited \`POST /api/stats/erase-likes\` with **v2 256-bit browser proof** in the JSON body after an informed Like withdrawal or dedicated erasure action. The client stops processing immediately, even on network failure; it does **not** send a new ID on initial denial. Other user's Likes and Print history stay unchanged.
- This is **bearer-like capability possession, not proof of a human's real-world identity**. The high-entropy ID and same-origin/fetch-metadata checks mitigate guessing and browser cross-site requests but **cannot protect an ID already copied through device compromise/XSS/extension misuse**. Explicitly document this residual risk and require TLS, no ID in URL/referrer/logs, CSP/XSS review, no caching of sensitive responses, request-size validation and rate limits. Prevent adding legacy IDs or arbitrary caller-supplied \`visitor_hash\` to the endpoint.
- No silent retry after an uncertain request: avoid a false "erased" receipt or recreating a Like with a stale ID. Cross-tab storage and in-flight request behavior need integration coverage. Database \`batch\` is atomic for the tombstone + targeted delete, **but offline CI does not prove the effective LIVE Worker route, D1 schema migration, account limits or bound Rate Limiter**.
- Because the user previously chose *no automatic age-based deletion*, **do not conflate the need to erase withdrawn Likes with a time-based purge of remaining, actively authorized Likes**. Local withdrawal must remain easier than opt-in, and no additional required modal blocks withdrawal.

### 4. Exact PR #158 legal alignment (proposal, NOT applied in that PR)

The current legal Draft HEAD \`06a3d9ce90ebc82cc68fbfb5f64d2601afb897ae\` is textually **out of date** relative to PR #183. A separate exact-head authorization is required to modify the legal branch, and the final German page must reflect **verified deployed behavior**. Minimum controlled changes to \`datenschutz.html\`:

1. **Section 4 Like status:** replace the statement that \`visitor_id\` may be transmitted as an HTTPS **GET URL parameter** with an explicit **HTTPS POST JSON body** description when a personalized Like state is requested. Anonymous public totals still use GET without the ID. Do not assert that historical logs are cleaned by the change.
2. **Section 4 Like withdrawal:** replace \`nicht automatisch bereits in D1 vorhandene Hashwerte\` blanket language with accurate conditional language: *for previously consented, valid v2 Like IDs*, ordinary Like withdrawal sends an explicit erasure request; a confirmed server response means matching Like rows were deleted and per-page Like totals adjusted. On missing/legacy ID, rate-limit/network/D1 error, deletion is **not confirmed** and a proportionate rights-request route is available. Withdrawal stops further Like use immediately regardless of erase success.
3. **Describe separate suppression hashes truthfully:** D1 \`like_erasure_blocks\` persists a hash after confirmed erasure to block replay, under a separately disclosed purpose/lawful basis/retention criterion *only after legal choice*. Do **not** call it "fully deleted all personal data" or claim that the hash is anonymous. Disclose how related D1 recovery history, Cloudflare/security logs, and existing consent records are handled with verified facts.
4. **Legacy/Art. 11:** describe the limited, safely verified manual rights route for old/lost IDs without inviting IDs/passwords or identification photos in ordinary email. Avoid falsely promising deletion of records the controller cannot identify.
5. **Source & LIVE coordination:** PR #183 consent footer currently points to \`datenschutz.html\`, which only PR #158 provides. Both Drafts have CI PASS, **not legal sign-off**. Do not merge them separately, and do not deploy a Worker requiring \`like_erasure_blocks\` before a separately approved exact D1 migration. The current main has moved, so refresh/reconcile both PR bases before any merge gate. \`impressum.html\` and unrelated legal sections are outside this design scope.

**Suggested controlled German explanation (draft text; not a published declaration):**

> Wenn Sie Ihre Einwilligung für „Gefällt mir“ widerrufen, verwenden wir Ihre Browserkennung für diesen Zweck nicht weiter. Bei einer ausreichend gesicherten, aktuellen Kennung versuchen wir zugleich, die zugehörigen gespeicherten Likes per HTTPS-POST zu löschen. Die Löschung ist erst nach erfolgreicher Bestätigung durch den Server abgeschlossen. Bei älteren oder nicht mehr verfügbaren Kennungen sowie technischen Fehlern ist die Löschung nicht bestätigt; hierfür steht Ihnen unser Datenschutzkontakt zur Verfügung. Zur Verhinderung einer erneuten Speicherung mit einer bereits gelöschten Kennung kann ein gesonderter pseudonymer Sperrvermerk erforderlich sein; dessen Rechtsgrundlage und Speicherkriterien werden vor Veröffentlichung festgelegt.

This text intentionally **does not** state that actual LIVE currently performs the erasure or that the necessary lawful retention choice has already been signed off. It must be reviewed and adjusted to the behavior actually released.

### Acceptance before Ready

- [x] Review identified contradictions and preserves active Likes/no automatic age purge.
- [x] Define legacy/DSAR security constraints and a conditional legal alignment text for PR #158.
- [ ] Obtain explicit legal/policy determination for **suppression-list basis, proportionality and lifecycle** versus a bounded-lifetime credential alternative; no silent indefinite hash retention.
- [ ] Verify a workable verified erasure route for legacy/lost IDs (including candid Art. 11 limits), or keep the feature Draft and describe limitations.
- [ ] Complete security review of bearer proof, XSS/Origin, replay, stale-tabs, logs, ambiguous network outcomes; distinguish source-level tests from LIVE evidence.
- [ ] Separately authorize and implement PR #158's exact-head legal text after final reviewed source decisions; neither Draft may ship alone.
- [ ] Before any release, coordinate exact-head CI/reviews, current \`main\`, legal sign-off, separately authorized D1 migration **before** Worker activation, and LIVE verification. **This source-design authorization grants none of these LIVE actions.**

Sources checked 2026-10-11:
- [GDPR Arts. 5, 6, 7, 11, 12, 13, 17](https://eur-lex.europa.eu/eli/reg/2016/679/oj)
- [EDPB — Data subject rights](https://www.edpb.europa.eu/sme/be-compliant/respect-individuals-rights_en)
- [EDPB — Consent Guidelines 05/2020](https://www.edpb.europa.eu/documents/guideline/guidelines-052020-on-consent-under-regulation-2016679_en)
- [DSK — Orientierungshilfe Digitale Dienste](https://www.datenschutzkonferenz-online.de/media/oh/OH_Digitale_Dienste.pdf)
- [Cloudflare D1 \`batch()\` SQL transaction semantics](https://developers.cloudflare.com/d1/worker-api/d1-database/)
- [Cloudflare D1 Time Travel and backups](https://developers.cloudflare.com/d1/reference/time-travel/)

---

## Source hardening follow-up: user-directed erasure retry and transitional API — 2026-10-11

**Source only; neither PR #183 nor PR #158 nor Worker/D1 is LIVE.** This follow-up is narrowly bounded to #182 and the current main reconciliation.

1. **One user-directed withdrawal, a bounded recovery window:** After a previously authorized v2 Like is withdrawn, a 256-bit erasure-purpose proof is written to a separate `localStorage["coloring-pages-erasure-pending-v1"]` record for **at most 24 hours** before the shared Like/Print ID is removed. The record contains only the original v2 proof and an expiry timestamp. It is **not a Like/Print consent** and must never be supplied to personalized status, Like or Print endpoints. A confirmed erasure removes it immediately. A failure or ambiguous response shows "Löschung nicht bestätigt" and a visible **manual** "Löschung erneut versuchen" control; it never automatically retries or reactivates Like consent. Expiry is enforced lazily when the page reads the record; if storage is cleared, disabled, the page closes without reopening, or expiry occurs, the rights-request route remains and server-side erasure is **not** promised. No background polling or unbounded retention. This still requires GDPR/TDDDG review before release.
2. **Legacy URL compatibility (temporary):** New `js/stats.js` sends visitor-bound page status via `POST /api/stats/page`, but old cached clients issue `GET /api/stats/page?page_id=…&visitor_id=…`. Worker temporarily accepts that **read-only GET** form, validates the ID, checks obviously cross-site browser requests, and uses `Cache-Control: no-store`. This does **not** make query-string credentials safe; historical/ongoing legacy URLs can still appear in access logs. Owner review must schedule a separate GET sunset after real old-client usage/cache evidence. No GET endpoint may delete Likes or recreate erased credentials.
3. **Legacy/DSAR operating contract:** An old, weak, absent or irretrievable ID never gains access to `POST /erase-likes` based solely on knowing a Like count, identifying a drawing, a timestamp or submitting an email. On a privacy inquiry: acknowledge the request, collect only the minimum supporting information needed for the specific right, assess whether a particular D1 row can lawfully and reliably be identified, and document the case and statutory response deadline. Do **not** ask users to email raw browser identifiers, credentials, IDs from logs or identification photographs. If identity and linkage can actually be shown by permitted evidence, any targeted operator D1 deletion must have its own exact owner authorization and verification; an email is not authority for D1 writes. Where matching is genuinely impossible, assess GDPR Arts. 11–12 and explain the limitation without saying the old row was erased. Establish a controller-side DSAR record/retention procedure separately, with no covert browser identification or broad cleanup.
4. **Release order and unresolved gates:** Keep both PRs Draft. Source tests exercise one denied withdrawal, explicit retry, and new POST plus old GET client behavior. CI does not prove browser/XSS resistance, deployed Worker/cache rollout, migration existence, D1 erasure, or user rights handling. PR #158 German privacy draft needs a separately authorized legal-copy update describing the 24-hour proof and temporary legacy GET; do not falsely claim that all ID-bearing GET requests have ceased. Proportionality and lawful basis for permanent pseudonymous `like_erasure_blocks` retention remain explicitly **NOT READY**. Approval of this source correction does not authorize a D1 migration, merge, any host change, or LIVE rollout.

Official references: [Cloudflare D1 batch atomicity](https://developers.cloudflare.com/d1/worker-api/d1-database/); [MDN storage event](https://developer.mozilla.org/en-US/docs/Web/API/Window/storage_event); [EDPB Consent Guidelines 05/2020](https://www.edpb.europa.eu/documents/guideline/guidelines-052020-on-consent-under-regulation-2016679_en).

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
