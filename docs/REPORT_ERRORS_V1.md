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
- has no Brevo, Turnstile, rate-limit, catalog lookup, D1 or Stats dependency.

## Email binding

`cloudflare/wrangler.report.json` declares one Cloudflare Email Service binding:

- name: `EMAIL`
- destination: `info@ausmalwiese.de`

The personal mailbox destination is intentionally not committed to GitHub. `info@ausmalwiese.de` is the project address; LIVE activation must confirm that Cloudflare Email Service can deliver to this address and that the existing Email Routing path forwards it to the owner's verified mailbox.

Cloudflare documentation reviewed 2026-10-18:

- https://developers.cloudflare.com/email-service/api/send-emails/workers-api/
- https://developers.cloudflare.com/email-service/configuration/send-bindings/
- https://developers.cloudflare.com/email-service/configuration/email-routing-addresses/

## Routes

Only these Worker routes are configured:

- `ausmalwiese.de/api/report`
- `www.ausmalwiese.de/api/report`

There is no `/api/report/config` endpoint and no wildcard route.

## LIVE gate

This source does not deploy or send real mail. A separate owner authorization is required to:

1. confirm `ausmalwiese.de` is onboarded for Cloudflare Email Sending;
2. confirm `info@ausmalwiese.de` is an allowed/verified destination for the binding;
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
