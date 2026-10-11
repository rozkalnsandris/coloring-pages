# Ausmalwiese: Like/Print consent design (#182)

Status: DESIGN PROPOSAL — no implementation, legal sign-off, MERGE or LIVE.
Scope: [issue #182](https://github.com/rozkalnsandris/coloring-pages/issues/182). Independent legal-page Draft: [PR #158](https://github.com/rozkalnsandris/coloring-pages/pull/158).

## Decision required before implementation

Keep both Like/unlike and Print-intent counters, and keep a persistent browser visitor ID **only with valid purpose-specific permission**. Browsing, downloading and actual A4 printing must remain available without permission.

The current Cloudflare Worker **requires** a visitor_id on POST /api/stats/print. Therefore counting every Print action without consent is **not** supported by the existing API:

- **A — recommended minimal source design:** Count only Print intents from visitors who explicitly opted in to persistent Print statistics. Preserve all historical totals and Like/Print UI. Do not submit a Print event without consent. Admin must label the metric as "consented print intents" (not all prints). No Worker/D1 mutation required. **Owner acceptance of undercount is not yet recorded.**
- **B — separate backend proposal:** Count nonconsenting Print intents through a reviewed ID-free endpoint and bounded anti-abuse controls. Requires separate privacy/security assessment, source/API/tests scope, and owner authorization for any Worker/D1/LIVE changes. Do not treat an "anonymous" HTTP request as automatically free of IP/logging/privacy implications.

**Owner gate:** Choose A or approve design exploration of B **before implementing**. The present document makes no choice on the owner's behalf.

## Verified source wiring, not LIVE proof

- js/stats.js: getVisitorId(false) reads localStorage["coloring-pages-visitor-v1"] on getPage; toggleLike and trackPrint call getVisitorId(true). getPage sends the ID in a GET query; Like and Print send it in POST bodies.
- js/detail.js: on "A4 drucken" click, invokes trackPrint before startHtmlPrint; print.html/js/print.js actually renders printable pages. print must never wait for/require telemetry permission.
- cloudflare/stats-worker.js: page status optionally accepts a visitor_id; Like and Print writes require it. The raw ID may be used for rate-limiting; Like rows retain a SHA-256 visitor hash, with no built-in expiry in cloudflare/stats-schema.sql. Print counts are aggregates. This is source behavior; actual Cloudflare retention/settings and deployed versions need separate evidence.
- Existing GET /api/stats/page?visitor_id=... risks ID exposure in URL logs; do not silently change the API in this design lane.

## Proposed minimal consent UX

Use a small contextual disclosure in **German**, not an obstructive page-wide banner. When a user first requests a Like action, show Like-specific permission controls. For Print, make an independent, clearly labeled option beside print actions and in a directly accessible "Datenschutzeinstellungen" panel; **"A4 drucken" always performs printing immediately** even with no permission. Do not interpret a Like/Print click as consent.

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

## Release gates and sources

- Legal review: TDDDG §25 strict necessity vs specific informed consent; GDPR Articles 6, 7 and 13, plus Article 8 if actually offering information society services directly to children; minimize retention and verify data subjects' rights. Review the Cloudflare logs, D1 Like-row retention and cross-border processing against operating facts. Existing Self-Serve DPA incorporation is documented in PR #158 but is **not** legal sign-off.
- Privacy page updates must be reviewed alongside PR #158, which remains Draft/NOT RELEASE READY; no dependency-based merge without separate approval.
- Owner must choose Print counting A/B before implementation; if B, authorize separate API/Worker/source design and later the appropriate LIVE gate. An implementation PR still requires its own scoped approval and exact-head CI/reviews.

Official references, reviewed 2026-10-11:
- [TDDDG §25 — law](https://www.gesetze-im-internet.de/ttdsg/__25.html).
- [DSK *Orientierungshilfe für Anbieter:innen von digitalen Diensten*, v1.2 (2024), paras. 36–39, 59–63, 78–81, 128–136](https://www.datenschutzkonferenz-online.de/media/oh/OH_Digitale_Dienste.pdf).
- [GDPR Articles 6–8, 13 — EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj).
- [EDPB Guidelines 05/2020 on consent](https://www.edpb.europa.eu/documents/guideline/guidelines-052020-on-consent-under-regulation-2016679_en).
