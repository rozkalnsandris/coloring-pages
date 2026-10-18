# Fehler melden — minimal source-only report flow (#264)

## Visitor contract

On a valid `detail.html?id=<activity-id>`, the visitor opens **Fehler melden**, selects one of five fixed German reasons and presses **Melden**. The browser sends only:

- activity `id`
- current 1-based `page`
- fixed `reason` code

No name, email address, free text, upload, Turnstile token, cookie, persistent reporter ID or Stats state is sent.

Success shows **„Danke! Deine Meldung wurde gesendet.“**. Failure shows the existing generic retry message and never blocks printing or downloading.

## Worker contract

`cloudflare/report-worker.mjs` has one function only:

`POST /api/report` -> validate bounded JSON -> send one plain-text email through `env.EMAIL.send()`.

The Worker:

- accepts only the exact same-origin apex/www request;
- rejects unsupported fields;
- limits JSON body size;
- builds the detail link from validated `id` and `page`;
- uses fixed sender `info@ausmalwiese.de`;
- never accepts sender or recipient from the visitor;
- returns `200 {"ok":true}` only after the Email Service binding resolves;
- returns `503 {"ok":false}` if the binding is missing or sending fails;
- on an Email Service send exception, writes exactly one structured error log with only `event: "report_email_send_failed"` and a sanitized provider `code`;
- accepts that code only when it is a bounded uppercase `E_[A-Z0-9_]+` token (maximum 64 characters), otherwise logs `UNKNOWN`;
- never logs the provider error message/stack, request payload, activity ID/page/reason, sender/destination, headers, IP or URL;
- has no Brevo, Turnstile, rate-limit, catalog lookup, D1 or Stats dependency.

## Email binding

`cloudflare/wrangler.report.json` declares one Cloudflare Email Service binding:

- name: `EMAIL`
- destination: `INFO@ausmalwiese.de`

The personal mailbox destination is intentionally not committed to GitHub. `INFO@ausmalwiese.de` is the same project destination mailbox, using uppercase local-part casing only as a narrow workaround for the open Cloudflare Email Service lowercase `info@ZONE` rejection reported in `cloudflare/developer-platform#65`. The Worker sender remains `info@ausmalwiese.de`, and no other email behavior changes. LIVE activation must still confirm delivery through the existing Email Routing path.

Cloudflare documentation reviewed 2026-10-18:

- https://developers.cloudflare.com/email-service/api/send-emails/workers-api/
- https://developers.cloudflare.com/email-service/configuration/send-bindings/
- https://developers.cloudflare.com/email-service/configuration/email-routing-addresses/
- https://developers.cloudflare.com/workers/observability/logs/workers-logs/

The Email Service Workers API documents thrown errors with machine-readable `code` and human-readable `message`. This Worker deliberately records only the sanitized code. Workers Logs recommends structured JSON objects so the fixed `event` and `code` fields remain queryable without storing provider messages or visitor-derived report data.

## Routes

Only these Worker routes are configured:

- `ausmalwiese.de/api/report`
- `www.ausmalwiese.de/api/report`

There is no `/api/report/config` endpoint and no wildcard route.

## LIVE gate

This source does not deploy or send real mail. A separate owner authorization is required to:

1. confirm `ausmalwiese.de` is onboarded for Cloudflare Email Sending;
2. confirm `INFO@ausmalwiese.de` resolves to the same allowed/verified project destination for the binding;
3. deploy the exact reviewed Worker/config;
4. send one approved test report;
5. verify that the email actually arrives in the intended mailbox.

No Stats pre/post snapshot is part of this flow.

## Tests

Run:

`node --test tests/test_report_worker.mjs`

and:

`python3 -m unittest tests.test_report_wrangler_config -v`

The tests mock the Email Service binding and send no real email.
