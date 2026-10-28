# German legal pages — current aggregate model review

Status: **DRAFT / SOURCE REVIEW ONLY / NO LEGAL CERTIFICATION**

Issue: #256  
Draft PR: #158  
Source reconciliation baseline: `d1ea05c56bc77c5070f87966bf8f17ae4a4f85b4`  
Last owner-provided LIVE application evidence: `a57e61e3ee022c07cb9dbd6adad29155ff8b885a`  
Review date: 2026-10-28

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
| Browser payload | #391 at `d8f0f6ea5116ec8188684d76bf4d2d75ff62ef6f` | Proposed automatic page-ID-only fetch; not deployed by this PR |
| Retention preference | Owner selected **12 months** on 2026-10-28 | Source requirement only; no retention configuration or deletion operation performed |
| Collection direction | Owner retained automatic measurement and requested basis assessment on 2026-10-28 | No consent UI redesign, no legal conclusion or public activation authority |

The page-ID-only client omits fetch credentials and referrer and keeps its
per-page attempted-ID set only in memory. The adapter sends a new loopback
request with no client IP/UA/referrer forwarding. These are narrow source
properties. The browser-to-Cloudflare connection still processes transport
information; they do not establish that all request processing is anonymous.

### Applicable requirements and unresolved decisions

| Requirement | Assessment | Remaining action |
| --- | --- | --- |
| TDDDG §25 / ePrivacy Art. 5(3) | No cookie is not a sufficient exemption analysis | Assess the automatic JavaScript page-ID transmission and any applicable exception; do not silently treat audience measurement as necessary for printing |
| GDPR Arts. 5/6 | Minimized aggregate target; personal-data processing at transport/edge remains relevant | Document purpose, necessity, alternatives and balancing for the actual flow; if consent is selected, assess its implementation and the child-user context |
| GDPR Art. 13 | Draft contact/rights text exists; no current public GoatCounter notice | Complete the actual purposes/basis, recipients/transfers and retention disclosure before collection |
| Retention | 12-month target selected, enforcement unverified | Define calendar-month versus day-based cutoff, cleanup timing/failure monitoring, aggregate-table coverage and backup/restore treatment; verify before making a live retention promise |
| GDPR Arts. 28/32 and transfers | Existing Cloudflare dependency, not a new GoatCounter SaaS recipient | Confirm applicable provider terms/transfer mechanism and actual logging/security settings; do not infer account state from generic documentation |
| Release governance | Private install and two read-only operations completed | Fresh health and remaining bounded runtime evidence, public-gate decision, then exact separate merge/LIVE authorizations |

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

### Automatic-collection basis assessment

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
12-month target, private admin/API and fail-open printing reduce intrusion.
Remaining evidence gaps are edge/origin processing, retention enforcement,
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

### Release-copy staging

The public draft now says only that GoatCounter is being prepared and public
collection is not active. It must be replaced before activation, after the gates
above are resolved. The intended active notice should state, in plain German:

- which template-open event is counted and that the body contains its template ID;
- that counts are page/time aggregates rather than unique-person counts;
- the verified absence of persistent visitor recognition in this feature;
- actual transport/security processing, its recipients and established basis;
- the **12-month** aggregate policy with its verified deletion semantics and
  distinct log/backup criteria, plus applicable rights.

Do not publish a fabricated legal basis, claim guaranteed immediate deletion,
or infer completed log/backup checks from synthetic database tests. The owner's
retention preference is not authorization to edit the running database, add a
timer, delete data or change backups. It creates no new public tracking consent.

This source update also reconciles #158 with application main
`a0c40232cc32eb8880868bd6bd5368fdf4491829`; current asset versions are preserved
while legal footer links are retained. #391 and the ingress write remain held.

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
4. Any eventual merge of application inputs still requires exact owner MERGE
   authorization and then only the bounded SIMPLE-DEPLOY path in `AGENTS.md`.
5. This engineering review is not legal certification; the owner remains
   responsible for the final published legal notice.
