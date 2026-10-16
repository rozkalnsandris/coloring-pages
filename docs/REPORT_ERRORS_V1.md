# Fehler melden — source-only report flow (#240)

## Visitor contract

From a valid `detail.html?id=<activity-id>`, a visitor can open **Fehler melden**, choose exactly one of five German-language reasons, pass Cloudflare Turnstile and press **Melden**. No reporter name, email, comments, image uploads or account. Successful API acceptance shows **„Danke! Deine Meldung wurde gesendet.“**; all failure cases remain transparent and never block download or printing. Multi-page activities preserve the currently viewed 1-based `page` index. Operator receives one private email with the reason, activity title and ID, page number and `https://ausmalwiese.de/detail.html?id=<id>&page=<n>`.

Browser entry: `detail.html` + `css/report.css` + `js/report.js` + bounded `js/detail.js` page event and deep-link handling. Server entry: standalone `cloudflare/report-worker.mjs` (no Stats Worker, D1, server-side database or RPi5 backend). Entire implementation is **source-only / not deployed**; the frontend button will not work until a separately approved Worker route, email binding and secrets are correctly configured.

## Worker routing and bindings — not an apply/run instruction

- Route **only** `https://ausmalwiese.de/api/report` (POST) and `/api/report/config` (GET) to the report Worker; route-mask matching must not unintentionally take over `/api/stats/*`, `/catalog.json` or the home/detail/print paths. If `www` stays public, configure the equivalent narrow route or redirect consistently; do not turn report handling into a catch-all.
- `TURNSTILE_SITE_KEY`: public site key registered for the real hostname(s). `TURNSTILE_SECRET`: private secret bound to the Worker (never commit).
- `NOTIFY_OPS`: Cloudflare Email Service `send_email` binding configured with **`destination_address` fixed to one verified operator inbox**. The Worker passes `env.REPORT_TO`, which must exactly match the binding restriction. Never permit arbitrary recipients or custom headers from the request.
- `REPORT_FROM`: sending address on a Cloudflare Email Service **onboarded sending domain**; `REPORT_TO`: destination address verified with Cloudflare. Existing Email Routing forwarding by itself **does not establish sending readiness**. Confirm account/domain and allowed sender/recipient read-only before any LIVE authorization.
- `REPORT_RATE` and `REPORT_DUP`: separate Cloudflare Workers **Rate Limiting** bindings with distinct unique `namespace_id` values. Suggested source configuration: rate `simple: { limit: 12, period: 60 }` per SHA-256 of incoming Cloudflare IP; duplicate `simple: { limit: 1, period: 60 }` for hashed IP + activity ID + page + reason. API windows permit `10` or `60` seconds, are per Cloudflare location, approximately enforced and **not durable once-ever deduplication**. Rate limiting by IP may cause shared Kita networks to hit limits; adjust after evidence. Do not store raw IP in application logs or send in emails.
- Workers `send_email` binding sends using `env.NOTIFY_OPS.send({ from, to, subject, text })`. A returned nonempty `messageId` means **provider accepted the message**, not guaranteed mailbox delivery. No silent success on thrown errors, missing bindings or incomplete API responses.
- Turnstile is verified **on the server** with Siteverify, required `success`, exact `hostname` and `action=report`. Tokens are single-use and expire after five minutes. No client-only security claims.
- No persistent reporter ID, cookie, profile or D1 row is created by this feature. Server handles reason allowlist, activity ID, page number, body limits and catalogue lookup itself and never accepts title, URL or recipient from clients. The public catalogue must remain reachable via the canonical `ausmalwiese.de/catalog.json` without a Worker-route loop. If not, adjust the **reviewed route/config**, not client-controlled URLs.

## Review, legal and operations before activation

1. Verify actual domain/route ownership, public catalogue and Email Service beta availability on this Cloudflare account. Sending to a verified destination is documented as free on Workers Free, subject to platform eligibility and current quotas; do not claim the service is enabled merely because inbound email forwarding exists.
2. Approve accurate German **Datenschutz** disclosure and legal basis: the visitor selects a report reason, activity reference and page; Turnstile/Cloudflare process request metadata for abuse prevention, and an email is generated for the operator. Application code does not persist visitor identity but Cloudflare transport/security systems and the email provider may have independent logs. Define retention/deletion for the operator mailbox (example proposal: delete resolved report emails after 30 days, with exceptions for unresolved issues; needs owner/legal approval). This source change is **not legal sign-off** and does not edit pending legal PRs.
3. Confirm Turnstile widget is accessible and consent/legal implications are approved for a German family-facing website. Test keyboard/tab flow, announcements, mobile width, duplicate/reset challenge, and printing with a missing backend.
4. Deploy Worker/routes/bindings/secret values only with a **fresh separate LIVE/Cloudflare owner authorization**. Validate with a real approved test report and sanitized proof that the mail provider accepted it and that an email arrived (subject, reason, link, no sensitive log output).
5. Email inbox messages are operator-only. Do not automatically turn reports into public GitHub issues. Rate limits and delivered-email volume should be monitored without user-level histories.

## Tests and maintenance

Run `node --test tests/test_report_worker.mjs` locally. `tests/test_report_node.py` runs this suite as part of the existing Python `unittest discover -s tests -v` CI job; Node.js must be present. Tests cover five reasons, multi-page links, malformed data, origin, replayed/invalid challenges, duplicate/rate rejection, email failures, header/title sanitization, config/route fail-closed behavior and structural report UI checks. The Worker sends **no real email** in tests; `fetch` and bindings are mocked. Runtime/browser usability and legal approval still require separate review.

Canonical links:
- https://developers.cloudflare.com/email-service/configuration/send-bindings/
- https://developers.cloudflare.com/email-service/api/send-emails/workers-api/
- https://developers.cloudflare.com/email-service/platform/pricing/
- https://developers.cloudflare.com/turnstile/get-started/server-side-validation/
- https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/
