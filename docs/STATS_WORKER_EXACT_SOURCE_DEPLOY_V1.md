# Ausmalwiese Stats Worker — exact-source privacy deployment contract

Status: **SOURCE READY CONTRACT / NO LIVE AUTHORITY**.

This document defines the source-side deployment contract after merged privacy backend
PR #183. It does not deploy Cloudflare, mutate D1, install a Cron Trigger, read
credentials, change routes, or authorize LIVE.

## Immutable source set

Canonical repository: `rozkalnsandris/coloring-pages`.

The machine contract is
`deploy/stats-worker-exact-source-v2.json` and pins all four artifacts:

| Artifact | Git blob SHA-1 |
| --- | --- |
| `cloudflare/stats-worker.js` | `94e802ce145dd75f5701c4c9274a4ac7959c7f5e` |
| `cloudflare/wrangler.stats-worker.jsonc` | `3733263a391274f2b6b0f2023c8656565bde8e1a` |
| `cloudflare/stats-cookie-like-migration.sql` | `b5346c05cb27de1010dab2027b0b923e999af775` |
| `cloudflare/stats-remove-daily-visitor-hmac.sql` | `a7cffb110adfceb5c1ff4dcd17a7009c549976a5` |

Safe offline source check:

`python3 tools/stats_worker_deploy_guard.py --check-contract`

Expected success marker:
`SOURCE_CONTRACT_OK_NOT_LIVE_PROOF`.

The guard is deliberately pure: no Wrangler invocation, network request, credential
read, Cloudflare API, D1 write, deploy, retry, rollback or cleanup path exists in it.

## Fixed Worker boundary

Target Worker: `coloring-pages-stats-v1`, Production only.

The future runtime must preserve exactly these four existing routes:

1. `coloring.rozkalns.net/api/stats/*`
2. `ausmalwiese.de/api/stats/*`
3. `www.ausmalwiese.de/api/stats/*`
4. `ausmalwiese.de/q`

The seven existing Production bindings remain present and type-correct:

- `DB` — D1 database
- `RATE_LIMITER` — Rate Limiter
- `PUBLIC_ORIGIN` — plain text
- `CF_ANALYTICS_HOST` — plain text
- `CF_ZONE_TAG` — plain text
- `VISITOR_HMAC_KEY` — secret
- `CF_ANALYTICS_API_TOKEN` — secret

`VISITOR_HMAC_KEY` is retained only as an existing secret binding during the
compatibility/deployment transition. The merged Worker no longer derives or stores the
custom daily visitor HMAC. Secret values must never be read, printed, fingerprinted or
committed.

The sanitized inventory contract requires the exact four routes, seven binding names and
kinds, one full Worker Version ID at 100% traffic, and trusted internal SHA-256
fingerprints only for nonsecret binding identities/values.

## Required ordered LIVE gates

These are **future gates**, not authority granted by this source PR.

### Gate A — additive D1 migration

Before the privacy Worker can serve the new cookie endpoints, separately authorize and
apply only the pinned
`cloudflare/stats-cookie-like-migration.sql`.

It adds `like_cookie_sessions` and `archived_like_totals`. Do not apply the legacy
`daily_visitors` cleanup in this gate.

Cloudflare documents D1 SQL-file execution and migrations as separate database
operations. Worker versions do not track D1 storage/schema state, so a Worker version
cannot prove this migration was applied.

After the mutation, perform read-only schema verification. On any error or ambiguous
result: STOP; no retry, rollback or alternate path without a fresh owner decision.

### Gate B — exact Worker version upload and deployment

Only after Gate A is verified may a separately authorized trusted operator use the
pinned Wrangler config and exact Worker bytes.

Cloudflare separates a Worker **version** from a **deployment**:
`wrangler versions upload` creates a version without sending it to Production traffic;
`wrangler versions deploy` controls which version receives traffic. Uploading a version
is already a Cloudflare mutation.

The future owner authorization must therefore name at minimum:

- repository/main SHA and exact Worker blob;
- exact Wrangler config blob;
- current active full Worker Version ID;
- Worker name/environment;
- the four routes and seven binding names/kinds;
- approved upload plus exact-version 100% deployment;
- required pre/post read-only evidence.

The config explicitly carries D1 and Rate Limiter bindings. It deliberately has no
route/cron keys and has `workers_dev=false`. `keep_vars=true` preserves dashboard
plain-text variables; Cloudflare documents that Worker secrets are not deleted by a
deployment merely because they are omitted from the config.

Use strict/fail-closed deployment behavior. If remote state, binding identity,
compatibility settings, traffic share or route ownership differs from the frozen
preflight: STOP before upload.

### Gate C — read-only runtime verification

After the exact version is at 100% traffic, independently verify:

- active full Version ID;
- 100% traffic;
- same four route owners;
- same seven binding names/kinds;
- unchanged nonsecret target/value fingerprints;
- presence of both secret binding names without reading values;
- expected Stats GET behavior on the three public hosts;
- `HEAD https://ausmalwiese.de/q` remains a no-count redirect with
  `Location: https://ausmalwiese.de/` and `Cache-Control: no-store`;
- new Like-cookie and aggregate-Print routes are reachable only as designed.

Do not use write endpoints merely as a read-only proof. Any test that changes engagement
or analytics counters needs separately scoped write authority.

### Gate D — expiry Cron Trigger

The merged Worker includes a `scheduled()` handler, but source alone does not install a
Cron Trigger.

Cron activation is a separate Cloudflare settings mutation and requires a fresh exact
owner gate after the Worker is active and verified. Cloudflare Cron Triggers execute in
UTC. The exact schedule and maximum accepted cleanup delay must be reviewed before the
trigger is created.

### Gate E — legacy daily visitor cleanup

Only after the new Worker is confirmed not to read or write `daily_visitors` may a
separate exact D1 cleanup gate apply the pinned
`cloudflare/stats-remove-daily-visitor-hmac.sql`.

That file drops only the legacy `daily_visitors` table. It does not remove the
`VISITOR_HMAC_KEY` Worker secret; secret/settings cleanup is yet another separately
authorized Cloudflare settings decision.

## Fail-closed rules

- Refresh GitHub exact head/main, CI, reviews and threads before every mutation gate.
- Refresh trusted Cloudflare/D1 state immediately before the first LIVE mutation.
- First mutation consumes that gate's authorization.
- After a mutation, any error, timeout, drift or ambiguous result means STOP.
- No automatic retry, rollback, cleanup, reupload, alternate token/provider path or
  settings repair.
- GitHub source/CI never proves deployed Worker bytes, D1 schema, Cron state or
  production health.
- This source contract is not legal sign-off.

## Current source conclusion

The old v1 contract intentionally failed on the privacy Worker with
`WORKER_BLOB_DRIFT`. Contract v2 now positively pins the merged privacy Worker,
Wrangler config, additive migration and later legacy-cleanup migration.

Passing the offline guard means only:

**SOURCE CONTRACT MATCHES — LIVE STILL REQUIRES SEPARATE OWNER AUTHORIZATION.**

Official Cloudflare references:

- Workers Versions & Deployments
- Deployment management
- Wrangler Workers commands/configuration
- D1 Wrangler commands
- Cron Triggers
