# Aggregate Like API (#256)

Source contract for the backend and frontend steps toward
[simple privacy rules](SIMPLE_PRIVACY_RULES_V1.md). Source is not deployment evidence.

## Request and result

`POST /api/stats/like-aggregate` accepts only JSON `{"page_id":"1234567"}`,
up to 256 bytes, with no query string or additional properties. Page IDs follow
the existing Stats API format. The request must use an allowed public host,
its exact same Origin, `Sec-Fetch-Site: same-origin`, and JSON content type.

A confirmed write returns HTTP 201 with `page_id`, `reacted:true`,
`like_count` and `print_count`. The Like total includes existing active and
archived counts. This counts reactions, not unique people; repeat submissions
can increment again. There is no cross-visit recognition or unlike operation.

The handler never reads or sets a Like cookie, accepts a visitor credential,
or creates a per-reaction/session row. It uses the existing Rate Limiter with
the transient Cloudflare request IP; the IP is not bound to D1. This is abuse
control, not an exact global quota or a claim that HTTP processing is anonymous.

Invalid requests return 400 or 403. A rejected rate limit returns 429.
Missing/failed abuse control or an unconfirmed database result returns 503.
Responses are not cached. An uncertain response must not cause automatic resend:
a write may already have committed even if its confirmation was lost.

## Accounting and release order

The existing D1 batch increments `page_stats.like_count` and reads the combined
total in one transaction. Existing active votes, archived totals and print counts
are preserved. The existing `archived_like_totals` schema must already be present;
this change adds no table, migration, binding, route pattern or Cron requirement.

First prepare and verify the exact backend release under the existing deployment
contract. Then switch the frontend to aggregate Like and Print, block repeat
clicks within the current page view, and reconcile #158 with actual behavior.
Retire stale personalized writes at that coordinated cutover. This backend step
keeps legacy/cookie APIs working and does not complete the privacy transition.
Historical records are not removed or reclassified here.

Offline tests execute the real Worker handler with SQLite-backed D1-shaped batch
results. They cover request bounds, all three hosts, identifier rejection, rate
limits, counter preservation, transaction rollback and uncertain outcomes.
Production D1/runtime behavior still requires separately authorized verification.

## Frontend cutover candidate

The updated shared client sends only the page ID to aggregate Like and only the
page ID plus an allowlisted campaign to aggregate Print. These writes and the
public page-total read omit credentials. Internal admin reads retain credentials
for Cloudflare Access. The client no longer reads or creates a persistent visitor
ID and does not fall back to the personalized endpoints.

The heart shows the total, accepts one attempt per page view, and shows `Danke!`
only after a confirmed result. In-flight clicks, success, timeout and uncertain
results all leave it disabled until reload. An initial failed count read may be
retried safely before any reaction. Reload can allow another reaction; these are
action totals, not unique people. Printing still opens if telemetry fails.

Old browser storage and historical server records are left untouched, including
any legacy erasure proof. This is not a data cleanup or a claim of completed
retirement. Legacy personalized-write fencing and #158 reconciliation remain
part of the coordinated release.

**Merge/release hold — not release ready:** source CI alone does not prove
that the aggregate Stats Worker endpoint and the required `archived_like_totals`
D1 schema are active in production. Obtain separately authorized, exact-runtime
read-only evidence of both before requesting a merge. Changes to `js/**`,
`index.html` or `detail.html` are eligible application-image inputs under
`AGENTS.md`: a later, explicitly owner-authorized exact-head `MERGE` may trigger
only the repository's bounded GHCR → `:production` → RPi5 SIMPLE-DEPLOY →
`/health` + `/ready` flow for `coloring-pages-public-rpi5`. This does not grant
a separate manual LIVE, Worker/D1, migration, permissions or settings action.
Reconcile legal Draft PR #158 and stale personalized writes separately; this
source-only PR does not perform any release or data cleanup.


## Personalized route retirement candidate

After the aggregate frontend was deployed and verified on 2026-10-23, the next
source-only #256 step retires creation and recognition through the stale
personalized API surface:

- legacy POST `/api/stats/like` and `/api/stats/print` return HTTP 410;
- `GET /api/stats/page` rejects a `visitor_id` query instead of hashing or
  looking up a personal Like state;
- cookie `session`, `state`, `consent` and `choice` routes return HTTP 410;
- existing `/api/stats/like/forget` and `/api/stats/erase-likes` erasure
  paths remain available while legacy pseudonymous records may still exist;
- aggregate Like/Print, historical totals and the bounded expired-session archive
  logic are unchanged.

This source change performs no D1 deletion, migration or cleanup and does not
deploy the Worker. The current trusted RPi5 exact-deploy runtime is pinned to the
previous Worker blob and must be separately repinned/reviewed before any exact
owner-authorized Cloudflare LIVE transition. Pre-existing D1 schema must be
verified read-only before such a transition. No automatic retry, rollback or
cleanup is authorized.
