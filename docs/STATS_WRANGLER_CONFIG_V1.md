# Stats Worker Wrangler config v1

Status: **SOURCE-ONLY / PINNED FOR PRIVACY WORKER / NO LIVE AUTHORITY**.

`cloudflare/wrangler.stats-worker.jsonc` remains the reviewed Production
configuration for Worker `coloring-pages-stats-v1`. The file itself is unchanged, but
the privacy deployment contract v2 now pins it together with the merged Worker and both
D1 SQL artifacts.

## Exact pinned source

- Worker blob:
  `94e802ce145dd75f5701c4c9274a4ac7959c7f5e`
- Wrangler config blob:
  `3733263a391274f2b6b0f2023c8656565bde8e1a`
- Additive Like-cookie migration:
  `b5346c05cb27de1010dab2027b0b923e999af775`
- Later legacy `daily_visitors` cleanup:
  `a7cffb110adfceb5c1ff4dcd17a7009c549976a5`
- Machine contract:
  `deploy/stats-worker-exact-source-v2.json`

The config fixes:

- Worker name `coloring-pages-stats-v1`;
- entry point `cloudflare/stats-worker.js`;
- compatibility date `2026-10-06`;
- `workers_dev=false`;
- `keep_vars=true`;
- D1 binding `DB`;
- Rate Limiter binding `RATE_LIMITER` with the reviewed namespace/policy;
- required secret binding names `CF_ANALYTICS_API_TOKEN` and
  `VISITOR_HMAC_KEY`.

Secret values are not in repository source and must never be read into chat/logs.

## Deliberate exclusions

The config has no:

- `route` / `routes`;
- Cron trigger;
- custom domain;
- plaintext `vars`;
- account/zone identifier;
- secret value.

Existing Production routes therefore remain outside this source config. Cloudflare
documents that dashboard routes should not be declared in Wrangler when they are to stay
dashboard-managed, and `workers_dev=false` prevents a workers.dev route from being
created by this config.

`keep_vars=true` is specifically for preserving dashboard-managed plain-text variables.
Cloudflare documents Worker secrets separately: deployments do not delete existing
secrets merely because the secret values are absent from this file.

D1 and Rate Limiter are explicit nonsecret bindings in the config and are part of the
exact source contract. Any mismatch in their trusted LIVE identity is a STOP.

## Future ordered use

No command in this document is an authorization.

After a separately authorized/verified additive D1 migration:

1. refresh exact GitHub source/config and trusted LIVE Worker inventory;
2. upload one exact Worker version using the pinned config with fail-closed/strict
   behavior;
3. capture the returned full Version ID;
4. deploy only that exact Version ID to 100% traffic;
5. read back active version, traffic, routes and bindings;
6. verify bounded runtime behavior;
7. handle Cron activation under a separate settings gate;
8. handle legacy `daily_visitors` cleanup under a separate D1 gate.

Cloudflare's versions model keeps upload and deployment as independent operations.
Uploading a version is already a mutation even though it does not yet receive Production
traffic.

The config intentionally does not contain the expiry Cron. Cloudflare Cron Triggers are a
separate trigger/settings surface and run on UTC schedules.

## Boundary

This source file and documentation do not authorize:

- Wrangler authentication;
- D1 execution;
- Worker version upload/deployment;
- route/domain mutation;
- Cron mutation;
- secret access/change;
- Cloudflare settings;
- LIVE verification writes;
- retry/rollback/cleanup.

See `docs/STATS_WORKER_EXACT_SOURCE_DEPLOY_V1.md` for the complete ordered gate.
