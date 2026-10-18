# Aggregate Like API (#256)

Source-only backend step toward [simple privacy rules](SIMPLE_PRIVACY_RULES_V1.md).

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
