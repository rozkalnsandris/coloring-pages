# GoatCounter on RPi5: minimal first-party pageview design (#376)

**Status: DESIGN CANDIDATE / NO IMPLEMENTATION OR LIVE AUTHORITY (2026-10-25).**
**Owner scope:** `START coloring-pages` following the design-only issue creation authorization
`AUTHORIZE DESIGN coloring-pages GOATCOUNTER-RPI5 FIRST-PARTY-PAGEVIEWS-ONLY NO-SESSION NO-IP-STORAGE SOURCE-ONLY NEW-ISSUE NO-MERGE NO-LIVE`.
**Reviewed repository baseline:** `coloring-pages/main=e85105458d03e964fdaa2fb6b79e695398f42618`.
This document is a proposal under #376, **not** acceptance of new collection or
a claim of German legal compliance.

**Update (2026-10-25):** Owner merged design PR #377 as `main=1cb3b0e67d20c6851592817ea5973992b9dbf707`, then explicitly closed #368 (`not_planned`) in favor of this **planned** GoatCounter direction. No GoatCounter service is installed or deployed; the existing LIVE Cloudflare-backed frontend is not replaced. The actual LIVE transition date is unset.

## Recorded owner architecture choice and safety boundary

- [Issue #368](https://github.com/rozkalnsandris/coloring-pages/issues/368) was closed on 2026-10-25 as **not planned / superseded**, after explicit owner direction to move the **future** Traffic architecture from Cloudflare-only to first-party, RPi5-hosted GoatCounter pageview counting. This does **not** complete #368's original Cloudflare-only acceptance criteria.
- [Issue #376](https://github.com/rozkalnsandris/coloring-pages/issues/376) remains OPEN. The original `AUTHORIZE DESIGN ... NEW-ISSUE` permitted issue creation only; the subsequent START created the design document through owner-approved docs-only [PR #377](https://github.com/rozkalnsandris/coloring-pages/pull/377). Neither authorizes installation, telemetry activation, LIVE or production data access.
- The explicit **architecture-selection gate is satisfied**, but product implementation requires separately scoped and reviewed source work after release-specific privacy/retention evidence. Any install, database, logging, service or network mutation on RPi5 requires a separate exact-owner LIVE gate in `RPi5_main`; no generic merge or `turpini` can grant it.
- Scope of this follow-up: **source-only read-only upstream analysis and documentation**. Do not touch deployed app, Stats Worker, D1, Like/Print/QR/campaign aggregates, public tracking code, any RPi5 service, secrets, settings, or historical traffic data.

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
   added a `bots` table. **Read-only v2.7.0 source inspection below verifies
   event-level bot records including raw User-Agent and timestamp.** A Sessions
   OFF / Individual pageviews OFF setting does not itself prove this table
   remains empty. Isolated runtime/schema verification is a release blocker.

6. [GoatCounter upstream README](https://github.com/arp242/goatcounter)
   describes self-hosting using SQLite/Docker. A reviewed immutable image
   digest, release source/tag identity, supported RPi5 platform and license
   obligations are **not yet established**.

## v2.7.0 source verification — read-only, 2026-10-25

The following is actual code inspection of GoatCounter tag `v2.7.0`,
**not** execution, an immutable container image audit or an RPi5 LIVE check.

| Versioned upstream file | Verified code behavior | Consequence |
| --- | --- | --- |
| [`db/migrate/2025-06-21-1-bots.gotxt`](https://github.com/arp242/goatcounter/blob/v2.7.0/db/migrate/2025-06-21-1-bots.gotxt) | The `bots` table columns are `site_id, path, bot, user_agent, created_at`. Migrates old bot hits into this table. | Bot records are **individual requests**, not merely aggregate counters. |
| [`memstore.go`](https://github.com/arp242/goatcounter/blob/v2.7.0/memstore.go) | `Persist()` inserts `Hit.Bot>0` into `bots` before `processHit()` applies `CollectHits`, `CollectUserAgent` and `CollectSession` flags. | Disabling Individual pageviews, User-Agent statistics and Sessions cannot **on their own** prevent bot-record storage. |
| [`handlers/api.go`](https://github.com/arp242/goatcounter/blob/v2.7.0/handlers/api.go) | API `/api/v0/count` populates `Hit.Bot` from supplied `bot` and classification of supplied `user_agent`; `no_sessions:true` permits requests without `session` or `user_agent` + IP. | Strict backend-only `{no_sessions:true,hits:[{path:"/coloring-page/<7-digit-id>"}]}` **may** avoid this branch; requires isolated proof and allowlist enforcement. |
| [`cron/tasks.go`](https://github.com/arp242/goatcounter/blob/v2.7.0/cron/tasks.go) | A job deletes `bots` rows older than 30 days. | Shorter retention is **not** proof that raw event rows are acceptable. |
| [`db/schema.gotxt`](https://github.com/arp242/goatcounter/blob/v2.7.0/db/schema.gotxt) | Contains both `hits` and `bots` tables. | Measure actual persisted rows, not only UI checkboxes or schema names. |

**Conservative result:** The proposed strictly validated backend API body sends
no bot flag, User-Agent, session or IP. Versioned source suggests these calls
would not enter the `Hit.Bot>0` branch; however, regular `/count` endpoint,
other requests, proxy forwarding and logs are not thereby excluded. This is
not yet a tested no-IP/no-individual-data configuration. Reject all fields
outside a canonical page ID before constructing the GoatCounter request;
do not forward client headers. No automatic resend after ambiguous results.

**Remaining blockers:** Pin a specific immutable release/image and verify
RPi5 compatibility; run isolated normal/bot/invalid-event cases and inspect
populated SQLite `hits`, `bots`, aggregate tables, error/access logs, WAL,
exports and backups. Verify that all stored analytics information meets the
owner's count-only scope. Independently document GDPR/TDDDG assessment; never
assert a blanket consent exemption or conflate lack of IP **storage** with
lack of transient IP **processing**.

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
| Governance / rollout | #368 closure records the intended architecture switch, **not** a LIVE switch. Require reviewed source PRs and exact-head CI/reviews, isolated GoatCounter storage/legal evidence, and a separate exact RPi5_main owner gate for install, data store and exposure. Cloudflare tokens/settings and LIVE remain out of scope here. |

### Implementation and LIVE gates after the architecture decision

**Already recorded:** On 2026-10-25 the owner selected GoatCounter for the
**planned** Traffic replacement and closed #368. No future switch date was
specified and the existing Cloudflare-backed production UI is unchanged.

**Still required:** Complete upstream version-specific storage proof and
German legal/privacy assessment first. Then separate one-scope source/test PRs
in `coloring-pages` and reviewed `RPi5_main` service design, followed
by independently authorized LIVE installation, protections and verification.
Do not install, enable pageview counting, merge code, reconfigure Cloudflare,
remove old analytics, or alter historical data under this docs review.
