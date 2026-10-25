# GoatCounter on RPi5: minimal first-party pageview design (#376)

**Status: DESIGN CANDIDATE / NO IMPLEMENTATION OR LIVE AUTHORITY (2026-10-25).**
**Owner scope:** `START coloring-pages` following the design-only issue creation authorization
`AUTHORIZE DESIGN coloring-pages GOATCOUNTER-RPI5 FIRST-PARTY-PAGEVIEWS-ONLY NO-SESSION NO-IP-STORAGE SOURCE-ONLY NEW-ISSUE NO-MERGE NO-LIVE`.
**Reviewed repository baseline:** `coloring-pages/main=e85105458d03e964fdaa2fb6b79e695398f42618`.
This document is a proposal under #376, **not** acceptance of new collection or
a claim of German legal compliance.

## Conflict and owner architecture gate

- Current issue [#368](https://github.com/rozkalnsandris/coloring-pages/issues/368)
  explicitly requires Cloudflare-only Traffic and **no RPi5 traffic storage**.
  It remains OPEN. This design intentionally does not supersede its requirements.
- The design-only #376 authorization created an issue; the subsequent START permits
  this **docs-only source candidate**, but is **not** permission to implement
  or install a tracker. A new explicit, recorded **owner choice** is required
  to replace/supersede the #368 architecture **before implementation code**.
- No changes to application inputs, `cloudflare/stats-worker.js`, D1,
  `RPi5_main`, Cloudflare settings, LIVE containers, public pages,
  `stats.html`, or existing Like/Print/QR/campaign counts are in this scope.
  No historic data is overwritten, reclassified, migrated or deleted.

## User goal and metric contract

The desired question is **which coloring pages are opened, and how often**.
The minimal metric is **accepted pageview events**, not unique visitors,
people, sessions, Cloudflare HTTP requests or proven physical prints.

| Dimension / display | Proposed | Strict exclusion |
| --- | --- | --- |
| Public coloring-page ID | One validated **7-digit** ID from the current catalog, shown with title/category at read time | Arbitrary URLs, page titles sent by clients, query strings, UTM/referral tokens |
| Aggregation | Logical path, hourly or daily bucket, accepted count | Individual event rows, exact per-user timestamps, identification |
| Dashboard | Day, 7 days, 30 days, all-time pageview events and TOP coloring pages | Unique users, visits, browsers/devices, location, referrers, sessions |
| Visitor-side state | None created/read by analytics | Cookies, `localStorage`, fingerprint, IP/HMAC-derived visitor ID |
| Existing engagement | Keep separate and unchanged | Conflating print-intent, likes, QR and pageviews |

A page reload may count again; prefetches, disabled JavaScript, network
failures, ad blocking, automation and duplicate sends can cause deviations.
Do **not** fabricate deduplication, unique-user counts or guaranteed
anti-bot accuracy. Unavailable measurements must be `N/A`, not `0`.

## Proposed architecture (not deployed)

```text
Browser visiting https://ausmalwiese.de/detail.html?id=1234567
  |
  | page is rendered; first-party request with {page_id:"1234567"}
  | no tracker SDK, cookies, device/storage ID or campaign/referrer fields
  v
Cloudflare edge (ordinary networking metadata still processed)
  |
  v
RPi5 public app / narrowly scoped same-origin collection adapter
  | validate method, origin, payload schema, size, known current catalog ID
  | canonicalize to "/coloring-page/1234567"
  | discard original URL/query, request IP and ALL unapproved headers
  | never write raw analytics request logs or sensitive error traces
  v
Private/loopback GoatCounter API (not publicly exposed)
  | POST /api/v0/count; authenticated internal bearer token
  | {"no_sessions":true,"hits":[{"path":"/coloring-page/1234567"}]}
  v
GoatCounter + isolated SQLite data store, proposed aggregate-only settings
  |
  v
Protected ADMIN read-only aggregate API -> pageview chart and ranking
```

This candidate favors a server-side GoatCounter API over loading its public
`count.js` in visitors' browsers. **Do not put an API token in HTML/JS.**
Use a strictly bounded event endpoint with `credentials:"omit"` and a
body containing only the allowlisted page ID; never pass the browser's raw
headers, query parameters or referrer to GoatCounter. Do not treat this
as proof that upstream Cloudflare, reverse proxies or the web transport never
see an IP address. Account for static HTML caching: origin request logs
alone cannot reliably count client-rendered visits when a CDN serves a hit.

The exact collection endpoint, cross-repo ownership and authentication
mechanism require separate source review. This design does not authorize
installing a private service or exposing even a new internal port on RPi5.

## GoatCounter upstream evidence and unverified release gate

Evidence reviewed against upstream documentation on 2026-10-25:

1. [Backend events](https://www.goatcounter.com/help/backend) and
   [JSON API](https://www.goatcounter.com/help/api) document
   `POST /api/v0/count`, `no_sessions:true`, and a `hits` array with
   logical `path` values. It accepts server-side counting without the
   public JS tracker.
2. [Sessions and visitors](https://www.goatcounter.com/help/sessions)
   documents disabling Sessions in `Settings -> Data collection -> Sessions`.
   Otherwise GoatCounter uses an in-memory mapping derived from IP and
   User-Agent for up to eight hours. This is **not desired here**.
3. [Release notes](https://github.com/arp242/goatcounter/releases/tag/v2.6.0)
   state that per-event `hits` records became disabled by default in v2.6.0;
   explicitly keep `Settings -> Data Collection -> Individual pageviews`
   **OFF** and verify against actual database behavior. New installations
   and upgrades may behave differently.
4. [GoatCounter privacy documentation](https://www.goatcounter.com/help/privacy)
   says additional **aggregate** tables may store browser, system, country,
   language, width and referrer dimensions. Disable **all** that are outside
   this page-ID-only design and test the resulting schema, not just UI toggles.
5. [v2.7.0 release](https://github.com/arp242/goatcounter/releases/tag/v2.7.0)
   added a separate `bots` table retaining bot pageviews for about 30 days.
   This is a **release blocker until inspected**: identify columns, whether
   it contains per-request records and whether it can be disabled so storage
   remains within the agreed aggregate-only scope. **Do not claim v2.7.0 is
   compliant by default.** If stock GoatCounter cannot satisfy this
   requirement, STOP and return with options; do not silently weaken it.
6. [GoatCounter upstream README](https://github.com/arp242/goatcounter)
   describes self-hosting using SQLite/Docker. A reviewed immutable image
   digest, release source/tag identity, supported RPi5 platform and license
   obligations are **not yet established**.

**Unresolved:** No exact release binary/image, SQLite schema, default
settings, `bots` table or request-handling implementation was executed or
inspected in an isolated test. Do not promote an upstream marketing/privacy
statement to a verified `no-IP-storage` guarantee.

## German privacy and data handling gate

- [TDDDG §25](https://www.gesetze-im-internet.de/ttdsg/__25.html):
  assess actual information storage/access on the visitor's terminal.
  `No cookies` alone is insufficient; an additional browser-side analytics
  request/pixel can have its own terminal-access implications. Review the
  exact first-party request mechanism before deciding whether consent is
  required; do not display a meaningless banner.
- [EDPB Guidelines 2/2023](https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-22023-technical-scope-art-53-eprivacy-directive_en)
  discuss technical scope of terminal access, including pixels and tracking
  mechanisms. The user-facing JS does not automatically become exempt merely
  because a backend stores aggregate counts.
- [GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng):
  evaluate any personal data **processed transiently** by Cloudflare,
  transport, proxy, application, authentication, abuse controls and backups.
  Document purpose/necessity and lawful basis (Art. 6), minimization,
  retention, recipients, transfers and information duties (Art. 13).
  If legitimate interests are considered, record balancing with children's
  interests. A count without an IP column does not make all upstream
  processing non-personal.
- [DSK OH Digitale Dienste (November 2024)](https://www.datenschutzkonferenz-online.de/orientierungshilfen.html):
  examine actual first-party analytics implementation and exceptions.
  No claim of regulator approval, legal certification or blanket
  consent exemption is made here.
- Reconcile the German `Datenschutzerklärung` only after a reviewed
  implementation and actual dataflow proof, in coordination with open
  [legal PR #158](https://github.com/rozkalnsandris/coloring-pages/pull/158)
  and privacy [#256](https://github.com/rozkalnsandris/coloring-pages/issues/256).

## Pre-implementation test and RPi5 acceptance matrix

| Gate | Evidence required before production |
| --- | --- |
| Immutable upstream identity | Pin a specific tagged GoatCounter release and digest; verify supported architecture, license, migrations and security advisory status. |
| Controlled API payload | Test accepted ID maps only to a canonical logical path; reject invalid/unpublished IDs, unknown fields, query/referrer payloads, oversized bodies and untrusted origins. |
| Browser-side privacy | Assert no new analytics cookies, localStorage/fingerprint, third-party `count.js`, referrer/UTM forwarding or persistent visitor IDs; verify full page still loads if collection fails. |
| No individual storage | Fresh isolated SQLite schema/data check after normal, repeated and bot-shaped events; inspect `hits`, `bots`, aggregate tables, diagnostic logs and error traces; verify no IP/UA/referrer/device/location/session or event-level rows survive. |
| Sessions/retention | Prove `no_sessions:true` behavior and Sessions OFF; Individual pageviews OFF; verify actual retention and aggregate rollover. |
| Reverse proxy / transport | Check CDN, Nginx/application access/error logs, headers, forwarded IPs, request buffering, monitoring, systemd/docker logs, SQLite WAL, backups and exports for unintended retention; never output protected data in proof. |
| Accuracy semantics | Test each accepted detail-open counts once per intended emission; reloads count again; no pageview claimed if request is unconfirmed; handle duplicate/ambiguous responses without automatic retry. |
| Protection/availability | Internal-only GoatCounter admin/API, protected ADMIN read endpoint, least privilege, bounded CPU/RAM/disk and startup/health; visitors can browse/print if analytics is down. |
| Disaster recovery | Define authorized backup/restore, migration and rollback **plans**; no test runs, backups or rollback on LIVE without independent authority. |
| Governance / rollout | Explicit decision on #368 architecture, reviewed source/test PRs, exact-head CI/reviews, separate RPi5_main owner authorization for install/data store/exposure; Cloudflare token/settings and LIVE remain out of scope here. |

### Decision needed before implementation

An explicit owner architecture decision must say whether to **replace the
Cloudflare-only Traffic source** in #368 with first-party, RPi5-hosted,
aggregate pageview counting, and which existing Traffic fields should remain
N/A or be removed. It must not be inferred from opening #376, START, this
doc PR, or a successful source CI.

If this direction is accepted, subsequent work must be scoped into separately
reviewed `coloring-pages` application/ADMIN source and `RPi5_main`
host/service integration, with independent deployment gates. Until then,
**Cloudflare-only remains authoritative**, the old Traffic panel remains
unchanged, and #376 is a design candidate only.
