# Stats Worker Wrangler config v1

Status: **SOURCE ONLY / NO LIVE**.

`cloudflare/wrangler.stats-worker.jsonc` is the application-owned reviewed
Wrangler configuration for Production Worker `coloring-pages-stats-v1`.
It exists to satisfy the separate RPi5_main #1045 version/deployment workflow;
committing this file does not authorize Wrangler authentication, version upload,
deployment, route mutation, secret access, D1 writes or any other Cloudflare
change.

## Reviewed non-secret Production metadata

Read-only Cloudflare Dashboard evidence on 2026-10-17 established:

- Worker: `coloring-pages-stats-v1`
- source entry point: `cloudflare/stats-worker.js`
- source Git blob SHA-1: `dd5a2859d55b9ef2d9fb9a9d8bf0a535d25a5ba4`
- compatibility date: `2026-10-06`
- compatibility flags: none configured
- D1 binding `DB` → database `coloring-pages-stats-v1`
- D1 database ID: `f8ac8f1d-a230-4bc4-af13-557c1b91b273`
- Rate Limiter binding `RATE_LIMITER`
- Rate Limiter namespace ID: `1152026106`
- Rate Limiter policy: `100` requests per `60` seconds
- required secret binding names: `CF_ANALYTICS_API_TOKEN`,
  `VISITOR_HMAC_KEY`

Secret values were not read. Existing plain-text variables remain Dashboard
state and are deliberately omitted from source; `keep_vars=true` preserves
them for the separately reviewed Wrangler versions workflow.

## Deliberate exclusions

The config contains no `route`, `routes`, triggers, cron, queue, plaintext
`vars`, account ID, zone ID or secret values. Existing Production routes stay
outside this config and must not be reconciled by this source change.

The future runtime workflow remains separately gated:

1. fresh exact source/config review;
2. separately authorized Wrangler authentication/runtime;
3. `wrangler versions upload` with `--no-bundle --keep-vars --strict`;
4. capture the exact returned full Version ID;
5. deploy only that exact Version ID at 100% traffic;
6. read-only `HEAD https://ausmalwiese.de/q` verification.

Any LIVE upload/deploy remains a separate explicit owner authorization.
