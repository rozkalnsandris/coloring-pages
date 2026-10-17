# Report Worker Wrangler deployment source (#249)

This repository owns the application and deployment source for the Ausmalwiese report Worker. The reviewed deployment configuration is `cloudflare/wrangler.report.json`.

**SOURCE ONLY. Nothing in this document authorizes a Cloudflare deployment, secret access, email send or LIVE mutation.**

## Why Wrangler

Cloudflare documents `wrangler deploy` as the normal Worker deployment command. For a first deployment it creates a Worker version and immediately deploys it to 100% traffic. The report path therefore uses Wrangler directly instead of maintaining a custom Cloudflare REST/multipart deployment client.

The config intentionally uses JSON rather than JSONC so the repository's existing Python CI can validate the entire file without adding Node/package-manager dependencies.

## Exact source configuration

- Worker: `coloring-pages-report-v1`
- entrypoint: `cloudflare/report-worker.mjs`
- compatibility date: `2026-10-17`
- `workers_dev: false`
- `preview_urls: false`
- `no_bundle: true`, preserving the reviewed standalone module instead of bundling it
- four exact `zone_name: ausmalwiese.de` routes only:
  - `ausmalwiese.de/api/report`
  - `ausmalwiese.de/api/report/config`
  - `www.ausmalwiese.de/api/report`
  - `www.ausmalwiese.de/api/report/config`

Exact paths deliberately contain no terminal wildcard. Query-bearing URLs therefore must not be silently broadened into the report route.

The Worker source SHA-256 is pinned by the offline test to:

`f3c3f9902666d957abb16c5a29cfc4cb73263ccab2e88400e3281aae7ca92f1b`

## Protected values

Wrangler `secrets.required` declares exactly:

- `TURNSTILE_SITE_KEY`
- `TURNSTILE_SECRET`
- `BREVO_API_KEY`
- `REPORT_TO`

Although the Turnstile site key becomes public through `GET /api/report/config`, it is still supplied through the same protected deployment input so no environment-specific value is committed here.

A future authorized deployment supplies all four values from one protected JSON or `.env` file using `--secrets-file`. Secret input files matching `cloudflare/*.secrets.json` or `cloudflare/*.secrets.env` are gitignored. Prefer a protected file outside the checkout entirely.

Never place real values in source, GitHub issues/PRs, chat, command-line key/value arguments, test fixtures or logs.

## Rate limiting

The config selects two distinct namespace IDs:

- `REPORT_RATE`: namespace `2067894450`, 12 requests / 60 seconds
- `REPORT_DUP`: namespace `2051617019`, 1 request / 60 seconds

These IDs are source-selected candidates, **not proof of account-wide uniqueness**. Before LIVE, a read-only Cloudflare preflight must prove neither ID collides with any other account binding. A collision requires a reviewed source change; do not override the config ad hoc at runtime.

Cloudflare requires Wrangler 4.36.0 or later for Workers Rate Limiting bindings. The trusted RPi5 launcher must pin one exact reviewed Wrangler version at or above that minimum.

## Future deployment shape

After a separate owner LIVE authorization, the trusted launcher may execute only the equivalent of:

    wrangler deploy --config cloudflare/wrangler.report.json --secrets-file <protected-file>

The launcher must bind the exact `coloring-pages` commit, this config, the Worker source digest, exact Wrangler version and target Worker before dispatch.

Before the first mutation it must also prove:

1. correct Cloudflare account and `ausmalwiese.de` zone;
2. the four report routes are free/compatible and Stats routes are unchanged;
3. the two namespace IDs are account-wide unique;
4. all four protected values are available from the approved protected file;
5. Turnstile hostnames/action, Brevo transactional readiness and privacy/operator gates are approved.

After deployment, read-only verification must prove the intended Worker/version, exactly four report routes, required binding names, two rate limits and unchanged `coloring-pages-stats-v1`.

Any ambiguous deploy outcome is STOP. No automatic retry, rollback, cleanup, alternate REST client or dashboard workaround is implied.

## Offline verification

    python3 -m unittest tests.test_report_wrangler_config -v

The normal repository CI also runs this test through `python3 -m unittest discover -s tests -v`.

Official references:

- https://developers.cloudflare.com/workers/wrangler/configuration/
- https://developers.cloudflare.com/workers/wrangler/commands/workers/
- https://developers.cloudflare.com/workers/configuration/secrets/
- https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/
- https://developers.cloudflare.com/workers/configuration/routing/routes/
