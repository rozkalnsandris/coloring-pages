# German legal pages — current aggregate model review

Status: **DRAFT / SOURCE REVIEW ONLY / NO LEGAL CERTIFICATION**

Issue: #256  
Draft PR: #158  
Source reconciliation baseline: `a0c40232cc32eb8880868bd6bd5368fdf4491829`  
Last owner-provided LIVE application evidence: `a57e61e3ee022c07cb9dbd6adad29155ff8b885a`  
Review date: 2026-10-29

## GoatCounter public-release assessment

**Requires further review; public collection remains disabled.** This is an
engineering-supported compliance assessment, not legal certification. The
existing draft already contains the controller's supplied contact details and
aggregate Like/Print wording. Earlier cookie-design comments are historical;
do not restore the superseded age gate or persistent Like consent system.

### Verified facts and their limits

| Item | Evidence | Limit |
| --- | --- | --- |
| Private GoatCounter v2.7.0 installation | [RPi5_main #1269 receipt](https://github.com/rozkalnsandris/RPi5_main/pull/1269#issuecomment-6464118635), source `45eb529a8963ea65fc09a8511f78bc847c9ae9bc` | Installation-time health, CollectNothing=1 and count-only token; no public events sent |
| Exact tunnel-route operator | RPi5_main #1271 merged at `9b681d0f4b0f19125982efa94a7d54ee55fbd91a` | Source readiness, not exposure authority |
| Tunnel baseline | [Sanitized receipt](https://github.com/rozkalnsandris/RPi5_main/pull/1271#issuecomment-6469926967) | Exact two path routes absent, no transformer conflicts |
| Worker routes | [Sanitized receipt](https://github.com/rozkalnsandris/RPi5_main/pull/1271#issuecomment-6470127560) | Five routes, zero matching the two HTTPS pageview URLs; not proof about every edge feature |
| Superseded browser payload | #391 at `d8f0f6ea5116ec8188684d76bf4d2d75ff62ef6f` | Historical automatic page-ID-only fetch; superseded by the selected origin-request direction, not deployed |
| Retention configuration | [RPi5_main #1273 execution receipt](https://github.com/rozkalnsandris/RPi5_main/pull/1273#issuecomment-6490759307), source `ecdf39a2643ff6a5b4a9c52f1d1b19aa6e07ce1d` | Native `data_retention=365` persisted and read back on 2026-10-29; empty analytics and private service health verified; not a future deletion-cycle or backup-erasure proof |
| Collection direction | Owner selected automatic origin detail-request counting on 2026-10-29; architecture in [#419](https://github.com/rozkalnsandris/coloring-pages/pull/419) | No additional GoatCounter browser request; implementation, actual-flow assessment and public activation remain outstanding |

The superseded page-ID-only client omits fetch credentials and referrer and keeps its
per-page attempted-ID set only in memory. The adapter sends a new loopback
request with no client IP/UA/referrer forwarding. These are narrow source
properties. The browser-to-Cloudflare connection still processes transport
information; they do not establish that all request processing is anonymous.

### Applicable requirements and unresolved decisions

| Requirement | Assessment | Remaining action |
| --- | --- | --- |
| TDDDG §25 / ePrivacy Art. 5(3) | No cookie is not a sufficient exemption analysis | Assess the selected ordinary-request server flow and remaining browser telemetry; do not carry over a browser-candidate conclusion or assume that server counting is automatically cleared |
| GDPR Arts. 5/6 | Minimized aggregate target; personal-data processing at transport/edge remains relevant | Document purpose, necessity, alternatives and balancing for the actual flow; if consent is selected, assess its implementation and the child-user context |
| GDPR Art. 13 | Draft contact/rights text exists; no current public GoatCounter notice | Complete the actual purposes/basis, recipients/transfers and retention disclosure before collection |
| Retention | Owner's 12-month preference implemented as a 365-day native threshold under exact authorization | Disclose daily cleanup cadence, calendar/downtime limits and separate backup/restore treatment; future cleanup success still needs operational observation |
| GDPR Arts. 28/32 and transfers | Existing Cloudflare dependency, not a new GoatCounter SaaS recipient | Confirm applicable provider terms/transfer mechanism and actual logging/security settings; do not infer account state from generic documentation |
| Release governance | Private install, route checks and private retention operation completed | Remaining bounded processing evidence, public-gate decision, then exact separate merge/LIVE authorizations |

The [final EDPB Guidelines 2/2023, sections 3.1–3.2](https://www.edpb.europa.eu/system/files/documents/2024-10/edpb_guidelines_202302_technical_scope_art_53_eprivacydirective_v2_en_0.pdf)
cover tracking instructions and local processing beyond cookies. Applying their
scope to this particular first-party payload needs assessment; the document
does not itself decide the exception for this deployment. The German
[§25 TDDDG](https://www.gesetze-im-internet.de/ttdsg/__25.html) sets consent and
specified exceptions for terminal storage/access. A GDPR legitimate-interest
basis does not by itself settle that separate terminal-access question.

Under [GDPR Arts. 6, 8 and 13](https://eur-lex.europa.eu/eli/reg/2016/679/oj),
the basis and notice must fit the actual processing. Child interests matter to
balancing; Article 8's special consent conditions depend on its own triggers.
This is not a reason to reinstate a blanket 18+ browsing/printing restriction.
Qualified legal review is recommended for the unresolved automatic-collection
scope/exception and basis before public activation; no sign-off is asserted.

### Automatic-collection basis assessment — historical browser candidate

**Purpose (proposed):** understand which public templates are opened so the
operator can maintain and improve the catalogue. Count template opens, not
people; no advertising profile, cross-site tracking or identification is needed.
This is a specific operational interest, but stating it does not establish
necessity or override the rights of users, including children.

**Necessity and alternatives:** compare the new client request with aggregate
counts already available through the existing Stats/Cloudflare flow and with
counting an ordinary content request on the server. #391 currently leaves the
Stats view call in place. Before claiming the additional collection necessary,
document whether the systems count different events or whether GoatCounter will
replace the redundant metric. No old analytics endpoint or dataset is retired by
this PR. A server-side alternative is not automatically exempt either; evaluate
its actual data flow and accuracy rather than assuming a legal shortcut.

**Balancing safeguards:** page-ID-only body, no persistent recognition,
no client IP/UA/referrer forwarded to GoatCounter, aggregate-only storage target,
365-day native threshold, private admin/API and fail-open printing reduce intrusion.
Remaining evidence gaps are edge/origin processing, future cleanup observation,
request failure/log paths and effective rights handling. The preschool content
means foreseeable child use must be considered, not dismissed by calling the
site an adult service. A simple notice alone does not resolve these gaps.

**Two separate conclusions:** Article 6(1)(f) is a candidate GDPR basis to assess,
not an approved basis in this report. Independently, the optional automatic
JavaScript request requires a reasoned §25 scope/exception assessment. The
ability to browse/print without telemetry means a strict-necessity exception
cannot simply be inferred from the site's primary service. EDPB guidance on
scope does not establish a specific exception for this page-ID-only flow.
Retaining the automatic design is a product direction, not a waiver of either
assessment. Current conclusion: **basis not yet established for activation**.

### Concrete collection alternatives — source review on 2026-10-29

The owner selected **automatic origin detail-request counting** on 2026-10-29.
The [selected architecture and rollout plan (#419)](https://github.com/rozkalnsandris/coloring-pages/pull/419)
replaces the additional browser request with an internal Nginx mirror over a
private Unix socket. This records the decision; integration is not deployed.
The browser-candidate assessment above is historical and is not a conclusion
about the selected server flow. PR #391 is superseded and must not be merged.

| Candidate | What it measures | Engineering implications |
| --- | --- | --- |
| Superseded #391 browser POST | One attempted event after a known detail entry resolves | Additional automatic client request; current TDDDG assessment remains unresolved. Stats view still runs alongside it. |
| Selected: origin-side counting of ordinary detail GETs | Eligible detail HTML requests received by the origin | No new analytics request from the browser. Does not prove rendering, includes automation, and can miss responses served entirely by browser/CDN caches. |
| Edge-side counting of ordinary detail GETs | Requests reaching the selected Cloudflare route | Can observe CDN-served requests, but adds a Worker/route/transport design and still misses browser-cache restores. This is a larger runtime change. |

At main `a0c40232cc32eb8880868bd6bd5368fdf4491829`,
`deploy/nginx.conf` sets `Cache-Control: no-cache` for HTML; that requests
revalidation rather than prohibiting storage. It is source evidence, not an
inspection of live edge overrides or actual request coverage.
[Cloudflare's cache documentation](https://developers.cloudflare.com/cache/performance-review/cache-analytics/)
distinguishes responses served without contacting the origin; its
[cache-control reference](https://developers.cloudflare.com/cache/concepts/cache-control/)
explains revalidation. Do not silently label origin requests as all rendered opens
or disable caching merely to inflate measurement coverage.

[GoatCounter documents backend API collection](https://www.goatcounter.com/help/backend).
[Nginx mirror](https://nginx.org/en/docs/http/ngx_http_mirror_module.html) can
create background subrequests, but a real integration would need a reviewed
container-to-host path, method/status eligibility, seven-digit current-catalog
validation, body/header minimization, and timeout/failure tests. The existing
loopback adapter cannot simply be addressed as the host's localhost from an
isolated container. Do not copy the upstream mirror example's original-URI or
client-header forwarding into this privacy-minimized design.

The existing `POST /api/stats/view` has two effects in
`cloudflare/stats-worker.js`: it increments `daily_views` and, for an allowlisted
campaign, also records a `detail` campaign event. `overviewStats` reads the former;
campaign reporting reads the latter. Removing the client call without a
replacement decision would alter existing campaign reporting. #391's regression
test currently deliberately preserves that call. A future cutover must explicitly
resolve this coupling, the pageview read/display path and historical cutover
labels; do not implement an unreviewed endpoint removal in a legal-docs change.

**Legal assessment limit:** removing the dedicated browser request can reduce
the terminal-access issue associated with that additional script, but it is not
blanket legal clearance. Ordinary-request metadata, logs, purposes, recipients,
retention and any remaining browser telemetry still require assessment. The
[DSK OH Digitale Dienste v1.2, paragraphs 77–79](https://datenschutz.sachsen-anhalt.de/fileadmin/Bibliothek/Landesaemter/LfD/Informationen/orientierungshilfen/OH_Digitale_Dienste.pdf)
requires a concrete user-oriented function and technical necessity for the
exception; useful audience measurement is not automatically part of browsing
and printing. Keep the public hold until the selected flow is assessed.

### Release-copy staging

The public draft now says only that GoatCounter is being prepared and public
collection is not active. It must be replaced before activation, after the gates
above are resolved. The intended active notice should state, in plain German:

- which eligible origin detail HTTP request is counted, with its template ID in
  an internal server message; distinguish requests from successful renders and
  explain cache, bot, repeated-request and delivery-failure limits;
- that counts are page/time aggregates rather than unique-person counts;
- the verified absence of persistent visitor recognition in this feature;
- actual transport/security processing, its recipients and established basis;
- the **365-day threshold** implementing the owner's 12-month preference, daily
  cleanup and its calendar/downtime limits, distinct log/backup criteria and rights.

Do not publish a fabricated legal basis, claim guaranteed immediate deletion,
or infer completed log/backup checks from synthetic database tests. The owner's
retention preference alone is not runtime authorization. The separate exact
Composite Live operation completed the one native-setting update and service
stop/start on 2026-10-29. That authorization is consumed; it does not authorize
future database changes, deletion tests, backups or public tracking.

This source update also reconciles #158 with application main
`a0c40232cc32eb8880868bd6bd5368fdf4491829`; current asset versions are preserved
while legal footer links are retained. #391 and the public pageview ingress
write are superseded by #419; public server collection still remains held.

## Current factual source/runtime model

- Public frontend `js/stats.js` uses `/api/stats/like-aggregate` and
  `/api/stats/print-aggregate` without a persistent browser visitor ID.
- Public page-total reads omit credentials. Aggregate Like/Print writes carry
  page ID and, for Print when allowlisted, a shared campaign ID.
- The deployed Worker uses `CF-Connecting-IP` only as the transient Rate
  Limiter key for aggregate Like/Print and does not write that IP into D1 as a
  reaction/print identifier.
- D1 aggregate counters are page/day/campaign summaries. They are not a unique
  person count.
- Internal traffic analytics query Cloudflare HTTP analytics; the retired daily
  IP-HMAC visitor metric is reported as unavailable, not zero.
- Owner-provided read-only RPi5 evidence on 2026-10-23 verified application
  source `a57e61e3ee022c07cb9dbd6adad29155ff8b885a`, immutable image
  `sha256:6feb0cf345b14eda00945ea7262d05d945213bfd964e435fddb771b021443410`,
  `/health=200`, `/ready=200`, and the public page-stats query using
  `archived_like_totals`.
- Legacy personalized Like/Print routes and historical pseudonymous D1 records
  are a separate transition concern. The current frontend does not call them,
  but this PR does not delete, migrate, disable or reclassify them.

## Public-copy decisions

The public notice is deliberately shorter than the historical draft.

- Remove the superseded 18+/adult-only Like gate, 180-day Like cookie,
  consent-settings UI and cookie-session claims.
- Do not claim that all HTTP processing is anonymous.
- Describe aggregate Like/Print behavior and transient IP-based abuse control
  factually.
- Use Art. 6(1)(f) DSGVO only for the documented operational/security/abuse
  purposes and include the Art. 21 objection right.
- Keep legacy data transparent as an unresolved transition instead of inventing
  a deletion date.
- Do not publish stale account-plan, Workers Logs/Traces, D1 Time Travel or
  Web Analytics retention snapshots as current facts.
- Keep provider-specific retention wording criterion-based where current
  account/runtime evidence is not frozen.

## Official references checked

- GDPR, especially Arts. 6, 13, 21 and 77:
  https://eur-lex.europa.eu/eli/reg/2016/679/
- DDG §5:
  https://www.gesetze-im-internet.de/ddg/__5.html
- TDDDG §25:
  https://www.gesetze-im-internet.de/ttdsg/__25.html
- Cloudflare Workers Rate Limiting:
  https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/
- Cloudflare HTTP headers / CF-Connecting-IP:
  https://developers.cloudflare.com/fundamentals/reference/http-headers/
- Cloudflare Data Processing Addendum:
  https://www.cloudflare.com/cloudflare-customer-dpa/

## Remaining gates

1. Source tests and exact-head CI/review for this reconciled Draft PR.
2. Separate source retirement of stale personalized write routes under #256.
3. No D1 cleanup, legacy-record deletion, Cloudflare settings change or manual
   LIVE action is authorized by this PR.
4. Any eventual merge requires exact owner MERGE authorization. Under the
   owner's current session instructions, runtime/deployment also requires a
   separate explicit authorization with the exact target and scope.
5. This engineering review is not legal certification; the owner remains
   responsible for the final published legal notice.
