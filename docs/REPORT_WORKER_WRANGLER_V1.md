# Report Worker Wrangler deployment source (#264)

This repository owns the application source and Wrangler configuration for the minimal Ausmalwiese **Fehler melden** Worker.

**SOURCE ONLY. This document does not authorize Cloudflare deployment, email sending, DNS changes or LIVE mutation.**

## Exact configuration

- Worker: `coloring-pages-report-v1`
- entrypoint: `cloudflare/report-worker.mjs`
- compatibility date: `2026-10-18`
- `workers_dev: false`
- `preview_urls: false`
- `no_bundle: true`
- exactly two narrow routes:
  - `ausmalwiese.de/api/report`
  - `www.ausmalwiese.de/api/report`
- exactly one `send_email` binding:
  - name: `EMAIL`
  - destination: `info@ausmalwiese.de`

There are no Report secrets, `vars`, rate-limit bindings, Turnstile bindings or `/api/report/config` route.

The Worker source SHA-256 is pinned by `tests/test_report_wrangler_config.py`.

## Why this is smaller

The previous source required Brevo, four protected values, Turnstile, two rate-limit bindings, a config endpoint and a separate Stats no-effect verification path.

The #264 target removes all of that. Cloudflare Email Service provides the only external transport through the Worker binding.

The project does not commit the owner's personal mailbox address. LIVE setup must confirm that the project destination `info@ausmalwiese.de` is valid for Email Service and reaches the already verified mailbox through Email Routing.

## Future deployment

After separate owner LIVE authorization, deploy only the exact reviewed Worker/config. No secrets file is required for this Report Worker.

Minimum preflight:

1. exact reviewed `coloring-pages` commit and Worker/config blobs;
2. correct Cloudflare account/zone;
3. `ausmalwiese.de` onboarded for Email Sending;
4. `EMAIL` destination accepted by Cloudflare;
5. two exact report routes do not overlap unrelated routes.

Minimum post-deploy proof:

1. exact Report Worker version is active;
2. exactly the two report routes are present;
3. exactly one `send_email` binding named `EMAIL` is present;
4. one owner-approved test POST returns success;
5. the test email arrives.

There is no Stats snapshot or Stats credential/API prerequisite.

## Offline verification

`python3 -m unittest tests.test_report_wrangler_config -v`

Normal CI also runs the Node Worker suite through `tests/test_report_node.py`.

Official references reviewed 2026-10-18:

- https://developers.cloudflare.com/email-service/api/send-emails/workers-api/
- https://developers.cloudflare.com/email-service/configuration/send-bindings/
- https://developers.cloudflare.com/workers/wrangler/configuration/
