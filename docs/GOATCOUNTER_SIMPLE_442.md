# GoatCounter SIMPLE (#442) — prepared source, collection OFF

Purpose: estimate visits/sessions, acquisition sources, Instagram campaigns and most-viewed catalog pages. Keep legacy js/stats.js Like/Print engagement separately. A session is not a uniquely identified natural person.

## One small integration

- Public index.html and detail.html load js/goatcounter-simple.js with data-goatcounter-simple="off". This is intentionally **disabled**: merging source alone makes no outbound GoatCounter request and cannot activate public collection.
- **Only after separately authorized route and legal checks:** change the two script attributes to "enabled" under an exact reviewed application change; do not silently activate counting from this source PR.
- The wrapper uses GoatCounter's unmodified official stable count.v5.js, pinned to the documented SHA-384 integrity hash. It would count to https://ausmalwiese.de/count. No live public /count ingress has been verified, and this PR does not create one. The GoatCounter admin/reports/API remain private. The external script origin and CSP require review, or alternatively host the identical pinned upstream script as a static first-party asset in a separately reviewed change.
- Manual no_onload/no_events ensures that a detail request counts only after js/detail.js has verified a seven-digit ID against catalog.json. Each document sends at most one attempt: / for the homepage or /ausmalbild/1234567 for a published page. Missing or invalid IDs do not count. The referrer passed is limited to an origin (or one of the explicitly allowed Instagram labels). This wrapper never reads or sends a raw IP.
- IMPORTANT: upstream count.js may also derive campaign query parameters from the browser URL independently of the wrapper's safe path/referrer overrides. Before enabling, review the exact outgoing request including unexpected UTM, page query and referrer data; do not claim total URL sanitization from this source module alone.
- Preserve GoatCounter's standard bot/session filters, user opt-out and approximately eight-hour session grouping. Raw IP/User-Agent are used transiently by the collector for session estimation, not stored as raw values by the standard default database. Avoid turning on detailed individual-pageview storage or raw IP logging without a separate decision.

## Owner gates

1. Review and separately authorize exactly the minimal first-party HTTPS /count ingress to the existing private GoatCounter, including CSP, origin IP forwarding, existing Cloudflare/RPi5 service binding, and protected admin isolation. No RPi5/Cloudflare/secrets/runtime access or modification is granted by this source PR.
2. Finish accurate German privacy notice/actual-flow assessment in draft coloring-pages PR #158, including the behavior of existing js/stats.js and upstream count.js. Do not assume absence of cookies alone proves all uses are compliant.
3. Obtain explicit exact-head MERGE authorization for this PR. It leaves counting OFF. Later enable those attributes under a separate explicitly reviewed application PR only after ingress and notice approval.
4. After separately authorized launch, verify in the protected GoatCounter dashboard: estimated visits/sessions, referrers, countries, campaign labels, and per-ID page rankings, with bot/owner exclusion and site Like/Print non-regression. No public test hit is permitted by this plan.

No part of this change activates/overwrites the older ARM64 origin derivative, Unix collector, GitHub GHCR publication, Docker deployment, Cloudflare tunnel/routes, production data or permissions.

Official references:
- https://www.goatcounter.com/help/start
- https://www.goatcounter.com/help/js
- https://www.goatcounter.com/help/path
- https://www.goatcounter.com/help/sessions
- https://www.goatcounter.com/help/campaigns
- https://www.goatcounter.com/help/countjs-versions
