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
