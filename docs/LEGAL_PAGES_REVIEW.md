# German legal pages — current aggregate model review

Status: **DRAFT / SOURCE REVIEW ONLY / NO LEGAL CERTIFICATION**

Issue: #256  
Draft PR: #158  
Source reconciliation baseline: `d1ea05c56bc77c5070f87966bf8f17ae4a4f85b4`  
Last owner-provided LIVE application evidence: `a57e61e3ee022c07cb9dbd6adad29155ff8b885a`  
Review date: 2026-10-25

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
