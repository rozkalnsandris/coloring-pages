# Ausmalwiese Stats Worker — exact-source deployment procedure (SOURCE ONLY, #213)

Status: **SOURCE-ONLY / NO LIVE WORKER DEPLOYMENT APPROVED**.

**Superseded for the #182 privacy Draft.** PR #183 changes `cloudflare/stats-worker.js`, adds consent/schema behavior and requires a future `CONSENT_TTL_SECONDS` runtime value. Therefore this older seven-binding exact-source contract is intentionally **not** repinned to the Draft Worker. Its guard must stop with `WORKER_BLOB_DRIFT` on the #182 source until a separately reviewed post-#182 deployment/migration contract defines the D1 migration, the additional binding/value, exact Worker bytes and fresh owner LIVE boundary. Do not weaken the guard or treat the old contract as deployable evidence for #182.
 This procedure belongs exclusively to `coloring-pages-stats-v1` and its hard-coded `/q` destination correction. It does not extend the merged application PR #214, authorize a new Worker, perform a Cloudflare write, read credentials, or operate on RPi5 services. The owner must separately authorize and review the final **trusted** LIVE operator and its exact mutation.

## Immutable source gate

- Canonical repository: `rozkalnsandris/coloring-pages`.
- Exact Worker: `cloudflare/stats-worker.js`, **Git blob SHA-1 `dd5a2859d55b9ef2d9fb9a9d8bf0a535d25a5ba4`**.
- Single fixed Worker name: `coloring-pages-stats-v1`; Production only.
- The Worker source encodes `PRINT_QR_HOST="ausmalwiese.de"` and `PRINT_QR_DESTINATION="https://ausmalwiese.de/"`. It retains `DEFAULT_ORIGIN="https://coloring.rozkalns.net"` for the separately managed legacy analytics behavior; **do not silently retarget or change that variable**.
- Machine contract: `deploy/stats-worker-exact-source-v1.json`.
- Safe local source check: `python3 tools/stats_worker_deploy_guard.py --check-contract`. Output `SOURCE_CONTRACT_OK_NOT_LIVE_PROOF` deliberately **does not grant a deployment**.
- CI: `python3 -m unittest tests.test_stats_worker_deploy_guard -v` is optional if namespace import works; the canonical test invocation is `python3 -m unittest discover -s tests -p 'test_stats_worker_deploy_guard.py' -v`. The existing repository CI also discovers these tests.

The guard is deliberately pure and has **no `--apply`, Cloudflare API, Wrangler, credential, token refresh, network access or filesystem-write path**. Its `check_sanitized_inventory` and `compare_sanitized_inventories` functions may validate normalized **independently authenticated trusted LIVE evidence** later. User-provided JSON fixtures, browser screenshots, or offline success cannot supply that authentication.

## What must remain exactly unchanged

These four existing Worker routes (and their account/zone ownership) must be present before **and** after the future code deployment; **do not add, remove, edit or rebind routes**:

1. `coloring.rozkalns.net/api/stats/*`
2. `ausmalwiese.de/api/stats/*`
3. `www.ausmalwiese.de/api/stats/*`
4. `ausmalwiese.de/q`

The seven Production bindings must remain present, type-correct and bound to the **same targets/values**, not merely share names:

| Name | Kind | Identity requirement |
| --- | --- | --- |
| `DB` | `d1_database` | Same D1 database ID, no schema/data writes |
| `RATE_LIMITER` | `rate_limiter` | Same namespace ID and limiter configuration |
| `PUBLIC_ORIGIN` | `plain_text` | Same value (legacy origin) |
| `CF_ANALYTICS_HOST` | `plain_text` | Same value |
| `CF_ZONE_TAG` | `plain_text` | Same value |
| `VISITOR_HMAC_KEY` | `secret_text` | Existing secret preserved, never read or printed |
| `CF_ANALYTICS_API_TOKEN` | `secret_text` | Existing secret preserved, never read or printed |

The guard's normalized snapshot schema requires a full Production version ID, **100% traffic**, four exact routes, and seven exact binding names/kinds. A trusted accessor must internally hash *nonsecret* binding identities and values to 64-character lowercase SHA-256 fingerprints, without returning account IDs, zone IDs, D1 IDs, Rate limiter namespace IDs, variables or other provider metadata. Both secret fingerprints **must be null**: Cloudflare cannot safely prove secret value equality via a standard read-only dashboard inventory; a trusted deployment tool must separately guarantee secret preservation and detect a missing secret binding. Do not hash, read, print or rotate secrets. Pre/post fingerprints must be identical.

## Read-only preflight — ALL mandatory before a LIVE decision

1. Verify current clean GitHub source base/head, exact Worker's Git blob hash, one specific issue/PR, exact-head CI, reviews and review threads. Do **not** infer active Worker bytes from GitHub or the application Docker receipt.
2. Independently resolve the **correct Cloudflare account and both relevant zones**, current active Worker version(s)/traffic shares, route ownership, seven binding types, nonsecret target/value identities, existing Worker settings including `compatibility_date`, and the registered runtime deployment procedure. Use a separately approved trusted authenticated read boundary; no direct access to Wrangler OAuth cache, arbitrary shell token readers or printed credentials.
3. Validate the sanitized inventory in memory with the guard, and bind an immutable before-state: Worker identity, active full version ID, four route owners, seven binding kinds and nonsecret fingerprints, exact source blob and reviewed deployment config. Reject unexpected or unaccounted-for settings, additional bindings/routes, unknown traffic split, unavailable secret-preservation guarantee, or any divergence. Browser UI evidence is useful **cross-checking** but not sufficient to bind a mutation by itself.
4. Prepare a **single Worker** deployment config in an approved protected context, using the exact independently verified D1 ID and rate-limiter namespace/config, the existing compatibility date and the exact Worker entry point. Bind the existing five nonsecret name/value or identity fields only as required by the chosen provider-supported command; do not put secret values in config, CLI, repository, logs or chat. The four routes are **not** new triggers to deploy. Assert no other Worker, cron, custom domain, Worker route, D1/schema, Access, DNS, WAF, secret, variable or settings change is requested.
5. Verify the chosen supported Wrangler/API deploy behavior, including that the config will **retain the existing D1 and rate-limiter bindings, all three plain-text variables and both secrets, and will not reconcile the routes**. `wrangler deploy --keep-vars` alone is **not sufficient**: Cloudflare documents `--keep-vars` for variables and separately requires explicit non-inheritable bindings. Omitted D1 or rate-limiter definitions are a STOP, not a default. A missing or unreviewed exact runtime operator/config is a STOP **before any upload**.
6. Obtain a **new exact owner LIVE authorization** naming repository/head and Worker Git blob, current active version, same account and target, approved config identity, four routes/seven bindings, allowed one-time upload/deployment mutation and pre/post proof. The prior owner SOURCE or REVIEW instructions do **not** approve this step.

## One bounded future execution (NOT authorized or performed by this PR)

The separately reviewed trusted operator must freeze all proof **before its first mutation**. Choose **one** already reviewed provider-supported exact-worker code deployment method; no generic `wrangler deploy` command is provided here because its configuration and binding-preservation semantics have not been LIVE-attested. In particular, do not use a silent `wrangler versions upload` followed by an unreviewed second promotion: uploading a version is already a mutation requiring owner authority.

The approved operator must:
- Prove again that the before-state is unchanged immediately prior to its **single exact upload/deploy dispatch**.
- Upload/deploy only the reviewed `cloudflare/stats-worker.js` blob for `coloring-pages-stats-v1`, with the exact immutable configuration, unchanged bindings and untouched routes. First mutation consumes the owner LIVE authorization.
- Read back Production active full version ID, 100%-traffic status, four routes, seven names/kinds, identical nonsecret target/value fingerprints and secret binding presence through the trusted sanitized read boundary. The before/after pure comparison is an additional check, **not** replacement for trusted provenance.
- Verify exact Worker runtime behavior independently: `HEAD https://ausmalwiese.de/q` yields HTTP 302 with `Location: https://ausmalwiese.de/`, `Cache-Control: no-store`; query-controlled redirects do not work. `GET /q` is a production D1 increment, so any GET/counter proof needs an **explicitly separately scoped analytics-write authorization**; do not run it in a read-only preflight. Preserve HEAD, bot and prefetch exclusions, D1 counter behavior and Stats GET APIs on all three public hosts.
- Stop on the first error, timeout, unknown identity, post-write mismatch or uncertain result. **NO retry, rollback, cleanup, alternate token/provider path, reupload or host/Cloudflare side effect** without a new exact owner decision. Report mutation state and failure layer.

## Current read-only evidence (not a deploy attestation)

On 2026-10-17 the Cloudflare account dashboard showed a Production Worker with four Routes and seven binding names/types. A past deployment appeared as `e47f145f` in the dashboard and was older than the source merge. The public `HEAD https://ausmalwiese.de/q` returned `302 Location: https://coloring.rozkalns.net/`. These are **point-in-time** observations, not an immutable full version ID, trusted account binding, or preflight approval. A dedicated RPi5 Worker-settings read credential has not been verified as installed. No credentials or settings are changed by this proposal.

## Source acceptance and exclusions

- Positive and adversarial offline tests must cover exact Worker blob, QR target, four Routes, seven binding kinds, unknown/duplicate binding rejection, secret-value refusal, 100%-traffic version identity, and nonsecret binding fingerprint drift.
- This file and the guard are source/tests/docs only; they are not an application-image input and do **not** trigger SIMPLE-DEPLOY.
- No LIVE Worker upload, D1 write, Cloudflare route/setting/secret update, catalogue ingestion, sitemap publication, old-host redirect, manual service action, credential access, retry, cleanup, or merge is permitted here.
- If this source procedure is incomplete for the eventual trusted runtime, the result is **SOURCE READY / LIVE STOP**, not permission to improvise.

Official documentation:
- [Cloudflare Workers versions & deployments](https://developers.cloudflare.com/workers/versions-and-deployments/)
- [Cloudflare deployment management](https://developers.cloudflare.com/workers/versions-and-deployments/deployment-management/)
- [Wrangler commands and `--keep-vars`](https://developers.cloudflare.com/workers/wrangler/commands/workers/)
- [Wrangler binding configuration](https://developers.cloudflare.com/workers/wrangler/configuration/)
