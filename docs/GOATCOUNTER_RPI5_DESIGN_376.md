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

## Strict v2.7.0 collection flags — source evidence, 2026-10-25

The upstream `v2.7.0` **Git tag resolves to commit
[`7e91d8a9bdbb0dd48496e498c5680f8f3477a1b4`](https://github.com/arp242/goatcounter/commit/7e91d8a9bdbb0dd48496e498c5680f8f3477a1b4).
This pins the reviewed **source**, not a downloaded/reviewed image digest,
RPi5 binary, instance configuration or actual runtime proof.

Source inspection adds a critical configuration trap to the bot finding:

- [`settings.go`](https://github.com/arp242/goatcounter/blob/v2.7.0/settings.go)
  defines `CollectNothing = 1`, `CollectReferrer = 2`,
  `CollectUserAgent = 4`, `CollectScreenSize = 8`,
  `CollectLocation = 16`, `CollectLocationRegion = 32`,
  `CollectLanguage = 64`, `CollectSession = 128` and
  `CollectHits = 256`. In `SiteSettings.Defaults()`, **`Collect = 0`
  triggers defaults**, enabling referrer, User-Agent, screen size, country,
  region **and session** collection. A site setting of `0` is **unsafe
  for this design**; the candidate no-optional-dimensions value is the
  explicit `CollectNothing = 1` sentinel. Do not set a raw database value
  on LIVE; this is a source-level requirement for a reviewed, supported
  settings path and separate authorized runtime configuration.
- [`handlers/api.go`](https://github.com/arp242/goatcounter/blob/v2.7.0/handlers/api.go)
  uses `no_sessions:true` to allow backend hits without an explicit session,
  browser or IP. **This does not turn off the site's
  `CollectSession` flag.** The inbound JSON includes many other fields
  (`bot`, `user_agent`, `ref`, `query`, `ip`, `session`,
  `location`, `created_at`, `size`, `title`, `event`).
  The planned adapter must build the only two allowed top-level keys
  `no_sessions` and `hits`, with exactly one inner key `path`,
  **from a validated catalog ID**; never proxy caller JSON.
- [`memstore.go`](https://github.com/arp242/goatcounter/blob/v2.7.0/memstore.go)
  calls `session()` if `CollectSession` is enabled, regardless of the
  `no_sessions` request hint. It can persist a session map to the
  database's `store` table on shutdown. With Sessions disabled, its
  ordinary-hit path instead sets `FirstVisit=true` and clears session
  identity, which is consistent with **each accepted event being counted**.
  In the upstream code, the bot insertion path precedes these settings
  checks; `CollectNothing=1` is not a global safeguard against bot rows.
- [`db/schema.gotxt`](https://github.com/arp242/goatcounter/blob/v2.7.0/db/schema.gotxt)
  defines aggregate `hit_counts` (per hour/path) and `hit_stats`
  (per day/path), in addition to individual `hits` and `bots` tables
  and optional-dimension tables. Database configuration and actual rows must
  be inspected after **synthetic** test events to prove aggregate-only
  counting.

### Required isolated acceptance cases (not executed yet)

Only against an independently created **non-production** instance and
synthetic IDs such as `0427183`; do not access installed LIVE SQLite,
process environment, real user data, or production logs under this design PR.

| Case | Controlled input or setting | Necessary result |
| --- | --- | --- |
| Defaults trap | New site or test site configured with `Collect = 0` | Test **rejects** configuration: settings defaults turn on optional dimensions and Sessions. |
| Minimal settings | Supported UI/API sets all optional Data collection flags OFF; inspect resulting effective `Collect` | Effective value is exactly `CollectNothing = 1`, not zero, and remains so after restart. |
| No sessions | Two API hits for the same published page with `no_sessions:true`, with Sessions OFF | Two accepted pageview events, not a made-up unique-person count or a shared synthetic session. |
| Strict outbound schema | Simulated public request for existing ID `0427183` | Internal body exactly `{"no_sessions":true,"hits":[{"path":"/coloring-page/0427183"}]}`; no copied IP, User-Agent, headers, query or referrer. |
| Reject extra fields | Simulated browser body with `bot`, `ip`, `user_agent`, `session`, `ref`, `query`, `created_at` or arbitrary keys | Reject **before** generating GoatCounter API JSON; no partial acceptance, secret or metadata logging. |
| Invalid/unpublished IDs | Non-7-digit, unknown or removed catalog ID; plus a valid catalog ID with a leading zero (`0427183`) | Unknown/invalid/removed IDs rejected; a valid published `0427183` is accepted and preserved as a **string**, never parsed as an integer. |
| Bot persistence | Synthetic bot-marked/spoofed-UA browser requests pass through the proposed *adapter*; also verify the sole permitted backend route in a sealed instance | Adapter **rejects** these payloads before the GoatCounter API; ordinary accepted events leave `bots` empty. **STOP** if any prohibited bot/UA rows persist. Public `/count` and untrusted/direct `/api/v0/count` are unreachable. |
| DB minimization | After persist/cron, restart and retention cycle inspect `hits`, `bots`, `store.session`, and all browser/location/referrer/device tables | No persistent visitor/session rows or individual events and no extra per-client dimensions; aggregate `hit_counts`/`hit_stats` may contain only allowed logical path/time/count data. |
| Operational privacy | Inspect sanitized offline Nginx/Cloudflare edge/log/storage/backup acceptance evidence | No prohibited analytics logging or durable client metadata; existing essential security processing documented separately. No secrets/raw records in reports. |
| Failures and double-counting | API 202/4xx/5xx, ambiguous response, CDN cache, back/forward, refresh, prefetch, disabled JS | Visitor browsing/printing always works; no automatic repeat after ambiguous success; no false unique-person claim; event-count limitations disclosed. |

**Gate interpretation:** Source inspection alone does not certify that a
stock GoatCounter `v2.7.0` deployment is aggregate-only. The above tests
must be run on the actual *pinned* runtime before approving collector
source or authorizing any host installation. The DSK/EDPB/GDPR/TDDDG
assessment of the chosen first-party browser request remains an independent
pre-activation decision; lack of IP **storage** does not mean no IP
**processing** in the normal network path.

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

## Verified upstream and German guidance for the next isolated runtime gate (2026-10-25)

**External evidence checked for this specific design — not legal approval:**

- [GoatCounter backend](https://www.goatcounter.com/help/backend)
  documents authenticated `POST /api/v0/count` with `no_sessions:true`
  and a logical `hits[].path`. Only a trusted first-party backend
  should build that JSON from the already-validated catalog ID. The
  frontend must not send arbitrary GoatCounter API fields, user headers
  or the secret token.
- [GoatCounter API documentation](https://www.goatcounter.com/api.html)
  describes `202 Accepted` for accepted counting requests, **not
  durable SQLite persistence**; the `v2.7.0` handler
  [source](https://github.com/arp242/goatcounter/blob/v2.7.0/handlers/api.go)
  states that pageviews are persisted in the background, approximately
  every 10 seconds. The test plan must distinguish HTTP acceptance,
  successful persistence and ambiguous/time-out results. **Never
  automatically repeat a request after an ambiguous response.**
- [Sessions and visitors](https://www.goatcounter.com/help/sessions)
  explains that default session tracking uses an IP + User-Agent
  in-memory mapping for up to eight hours. For our *pageview-event*
  metric, turn off site **Sessions** (and Individual pageviews and all
  ancillary dimensions) as well as passing `no_sessions:true`.
  The source-level `CollectNothing=1` vs `Collect=0` default trap
  above remains mandatory to check after instance creation and restart.
- [DSK Orientierungshilfe Digitale Dienste v1.2, November 2024,
  pp. 24–26, paras. 88–95](https://www.datenschutz-berlin.de/fileadmin/user_upload/pdf/publikationen/DSK/2024/2024_DSK-OH_Digitale-Dienste.pdf)
  discusses pure per-page counting as distinct from detailed visitor
  analytics. **It explicitly refuses to declare all
  `Reichweitenmessung` categorically consent-free**: the precise
  collection method and *purpose* determine whether an exception is
  available. Even the simplest visitor count is not per se an
  indispensable feature requested by visitors (para. 90).
- [TDDDG §25](https://www.gesetze-im-internet.de/ttdsg/__25.html)
  separately regulates storage in/access to an end-user device;
  [GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)
  governs processing of personal data in any collection/transport
  chain. A cookie-free first-party event does **not** establish that
  every browser-to-Cloudflare-to-RPi5 operation is exempt from consent
  or a legal basis. Review the precise browser event, legitimate
  interests/children's rights if relied on, data retention, notice and
  transport/access/error logs before enabling public traffic.

**Executable isolated-runtime acceptance sequence is still missing.**
Before building a first-party collector or requesting RPi5 installation,
a separate source/test PR must use a pinned immutable upstream artifact
in an **ephemeral non-LIVE environment**, create *synthetic* site/user
credentials and an isolated SQLite database, set/verify
`CollectNothing=1`, submit only the backend allowlisted test payload,
wait for confirmed background persistence, shut down cleanly and
checkpoint SQLite, and run
`tools/goatcounter_offline_privacy_probe.py` against an actual
**synthetic** database copy. Confirm the normal two-view count,
bot-marked input rejection at the adapter boundary, disabled session
state, empty individual-hit and bot tables, and no unintended retained
User-Agent/referrer/location data, files, logs, backups or sidecars.
A test showing `202` or an all-green Python *mock* alone is
**insufficient**; report `STOP` on any mismatch instead of weakening
the privacy contract.

**Governance reconciliation:** The owner closed #368 as superseded
on 2026-10-25 and chose GoatCounter as a *planned* future replacement.
`AGENTS.md` now records that choice while retaining the hard gate
against activating **any** GoatCounter process/storage on RPi5 without
an independently reviewed, explicitly owner-authorized LIVE scope.
No Cloudflare/Worker/D1, RPi5, actual visitor data, privacy policy
text or live site settings are changed by this documentation.

## Runnable isolated GoatCounter v2.7.0 runtime check — opt-in, not run yet

Source-only harness:
[`tools/goatcounter_isolated_runtime_probe.py`](../tools/goatcounter_isolated_runtime_probe.py).
Disconnected unit tests:
[`tests/test_goatcounter_isolated_runtime_probe.py`](../tests/test_goatcounter_isolated_runtime_probe.py).

The harness is **not automatically executed by CI**; CI only exercises
the harness's mocks and Python structural probe. It needs a **separately
obtained, independently authenticated** Linux GoatCounter `v2.7.0`
binary and its already-reviewed exact 64-character SHA-256. The harness
checks the digest and `goatcounter version -json`, but merely matching
a caller-provided digest **does not establish trusted provenance**.
It must not download binaries, build Go dependencies or use production
services to complete the test.

The harness refuses root and the `rpi5` host. When explicitly
invoked by a non-root operator **on a disposable, authorized test host**
with an isolated network namespace permitting only loopback, it creates
one `0700` private system-temp directory and synthetic local SQLite
DB; creates a disposable test site, user and count-only API token;
sets the isolated site's `CollectNothing=1`; binds GoatCounter only to
`127.0.0.1`; sends exactly **two** synthetic API pageview requests
for fixed ID `0427183`; then sends SIGINT and **requires the
GoatCounter process to exit with status 0** before running the
structural fixture audit. This replaces the former arbitrary 3-second
delay: the [v2.7.0 `cmd/goatcounter/serve.go` shutdown path](https://github.com/arp242/goatcounter/blob/v2.7.0/cmd/goatcounter/serve.go)
runs `cron.TaskPersistAndStat()` on graceful shutdown. Unexpected
process exits, nonzero exit codes and shutdown timeouts now produce
stable `STOP` results; HTTP `202 Accepted` alone cannot yield PASS.
The cleanup-and-check behavior has disconnected regression tests.
Its HTTP client
explicitly disables inherited proxy settings, **clears urllib's
automatic `Python-urllib/...` User-Agent header**, and rejects all HTTP
redirects so an internal bearer token cannot be forwarded to another
destination. The original harness configured only its JSON body and
did not suppress urllib's implicit User-Agent or its default redirect
handler; the regression unit tests now enforce both transport gates.
Responses, test tokens, internal errors and database rows are not printed.

An example invocation **only after trusted binary acquisition,
checksum verification and external sandbox authorization**:

~~~sh
python3 tools/goatcounter_isolated_runtime_probe.py \
  --binary /isolated/verified/goatcounter \
  --expected-binary-sha256 VERIFIED_64_LOWERCASE_HEX_SHA256
~~~

The Python harness does not itself create an OS network namespace or
firewall; this separation must be imposed by the external disposable
test environment. It cannot certify security of an untrusted binary.
`GOATCOUNTER_ISOLATED=PASS_SYNTHETIC_GOATCOUNTER_RUNTIME_ONLY_NOT_LIVE_OR_LEGAL_PROOF`
means only that a **real supplied** version-checked binary accepted
these synthetic requests and its SQLite snapshot met the narrow
structural invariants. Otherwise it emits a fixed `STOP` code.
Neither an HTTP `202` nor green unit tests constitute this PASS.

**v2.7 schema blocker corrected:** The actual tag's
[`db/schema.gotxt`](https://github.com/arp242/goatcounter/blob/v2.7.0/db/schema.gotxt)
also defines a `version` migration-history table (in addition to
the earlier enumerated visitor/statistics tables). The verifier now
requires it and the expected final v2.7 migration marker
`2025-12-12-1-ref-scheme`; it rejects unknown or malformed migration
names. The earlier synthetic-only fixture had omitted this table and
could never have passed against a real unmodified v2.7 SQLite schema.

**Remaining release blockers:** This harness has **not yet been run
with an actual GoatCounter binary**. Even a future synthetic PASS is
not a full audit of startup/error/access logs, unusual/malicious
bot-shaped events, dynamic proxies, SQLite free pages, backups,
real-user HTTP processing, site permissions or German GDPR/TDDDG
lawfulness. Those independent reviews and separate owner permissions
are required before *any* RPi5/LIVE operation or first-party tracker
deployment.

## Pinned v2.7.0 lookup-table reconciliation (source-only)

A further review of upstream
[`db/schema.gotxt`](https://github.com/arp242/goatcounter/blob/v2.7.0/db/schema.gotxt)
and
[`db/languages.sql`](https://github.com/arp242/goatcounter/blob/v2.7.0/db/languages.sql)
shows that the real SQLite schema contains **25 tables**, including
`iso_3166_1`, which the previous synthetic inventory omitted.
Moreover, a normal v2.7.0 SQLite startup
([GoatCounter `connectDB`](https://github.com/arp242/goatcounter/blob/v2.7.0/cmd/goatcounter/main.go))
populates `languages` with **7,086 static language names** plus the
empty-code `(unknown)` sentinel. These reference rows are **not
visitor-language observations**, so rejecting every `languages`
row would be incorrect; accepting arbitrary content would also
weaken the minimal-data gate.

The offline verifier now requires all 25 pinned tables, an empty
`iso_3166_1` table in this no-geo synthetic test, and precisely the
one known `locations` sentinel (location ID 1, unknown country and
empty region). It verifies the unknown-language sentinel, reference
code/label shapes and either one row (the deliberately minimal
synthetic unit fixture) or exactly **7,087 rows** (the pinned release's
normal language lookup size). Added negative tests reject extra
locations, unexpected country lookup rows, injected sentinels,
invalid language entries and unreviewed language-row counts.
One positive test builds **only synthetic** 7,086-entry reference
shape; it does not copy upstream language data.

This is a **structure/count check, not a cryptographic identity check**
of every upstream language name. It does not assert that reference
tables can never hold unexpected data, nor replace inspection of the
actual v2.7.0 executable and its SQLite bytes. Failing any static
lookup condition means `STOP`, not permission to delete data,
disable safety checks or enable LIVE tracking.

## Executable synthetic SQLite preflight (source-only)

A **read-only structural verifier** now exists at
[tools/goatcounter_offline_privacy_probe.py](../tools/goatcounter_offline_privacy_probe.py)
with synthetic negative tests at
[tests/test_goatcounter_offline_privacy_probe.py](../tests/test_goatcounter_offline_privacy_probe.py).
These files neither download nor start GoatCounter, make network requests,
read RPi5, load real events or install production telemetry. The existing
GitHub CI runs their Python standard-library unit tests.

The test fixture must be created **from synthetic requests only**, in a
fresh, disposable copy of the upstream GoatCounter v2.7.0 database **after
the isolated process has stopped and the SQLite WAL is checkpointed**.
The command reads one fixed filename (goatcounter-test.sqlite3) from a
top-level system temporary directory named goatcounter-offline-*.
The directory must include .ausmalwiese-goatcounter-offline-only containing
exactly AUSMALWIESE_GOATCOUNTER_SYNTHETIC_V1 followed by a newline.
It refuses symlinks, unknown/missing tables, WAL/SHM sidecars and
non-isolated path shapes. Do not construct this marker for production
files; never copy a live DB, credentials or client logs into a test fixture.

Example **after a separate, permitted isolated synthetic test has
produced such a directory** (replace its synthetic temporary path):

~~~sh
python3 tools/goatcounter_offline_privacy_probe.py \
  --synthetic-test-root /tmp/goatcounter-offline-example \
  --expected-page-id 0427183 \
  --expected-views 2
~~~

The probe checks the pinned v2.7.0 table inventory, CollectNothing=1
setting, no per-event hits/bots, no session store rows, no stored
User-Agent/device/campaign/location dimensions, exactly one empty
referrer sentinel, and no other paths beyond the exact seven-digit
synthetic public page ID. It also validates aggregate page/time/count
rows against the expected total and **against one another**.

**v2.7.0 source-specific adjustment:** [cron/ref_count.go](https://github.com/arp242/goatcounter/blob/v2.7.0/cron/ref_count.go)
continues creating `ref_counts` rows for the empty-referrer sentinel
(`ref_id=1`) even when referrer collection is disabled. These are
acceptable *only* if they contain no additional dimension and match
`hit_counts` exactly for each hour and page. Any other referrer or
different total fails closed. [cron/hit_stat.go](https://github.com/arp242/goatcounter/blob/v2.7.0/cron/hit_stat.go)
stores `hit_stats.stats` as a **24-integer JSON array**, one count
per hour of the day. The revised probe rejects missing/malformed arrays,
non-integer values, duplicates and any disagreement with `hit_counts`.
The original synthetic test fixture's `{}` value was not a realistic
upstream representation; it has been corrected.

The verifier prints only
`PASS_STRUCTURAL_SYNTHETIC_ONLY_NOT_RUNTIME_OR_PRIVACY_PROOF`
or a stable STOP code, never database values. It checks *structural
consistency*, not the installed GoatCounter binary or all traffic routes.

**Crucial boundary:** The included unit tests fabricate a minimal
23-table *shape* for exercising the checker. Passing these tests is
**not** proof the real GoatCounter v2.7.0 binary behaves the same way.
The structural verifier parses **only** the v2.7.0 24-count
`hit_stats.stats` array. It cannot prove that SQLite free pages never held
identifiers, that other columns/configs did not contain unknown metadata,
or that the process/proxy/CDN, backups and logs are free of personal
data. It cannot establish German consent requirements. A positive output
must not be called "no IP storage verified". A separately approved,
reproducible actual **isolated** GoatCounter runtime test,
production-edge analysis and legal review remain **STOP gates before
enabling tracking**.


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
