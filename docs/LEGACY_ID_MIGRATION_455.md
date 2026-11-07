# Legacy catalogue ID normalization — issue #455

## Purpose and authority

Ausmalwiese now allocates new publication IDs as random seven-digit codes. A reviewed
2026-11-07 catalogue snapshot contained 477 activities and 30 older IDs such as
`cp-000001` and descriptive slugs.

This document prepares a **one-time migration only**. It does not change the normal
`metadata/id-policy.json` rule: existing legacy IDs stay immutable until a separately
reviewed cutover is explicitly authorized, and the importer never becomes a general
rename tool.

Nothing in this source change renames catalogue records, originals, derivatives,
Stats data, URLs, files, services, workers or host state. It also deliberately avoids
application-image inputs such as `deploy/nginx.conf` and `js/**`: issue #455 forbids
deploy, while this repository's normal application merge lane may auto-deploy those
inputs.

## Google / URL migration constraints

Google Search Central treats changed URLs as a site move. The migration therefore
must:

1. freeze an exact old → new URL mapping;
2. activate permanent **server-side 301/308** redirects before old URLs disappear;
3. avoid redirect chains and irrelevant mass redirects;
4. update internal links, canonical URLs and sitemap entries to only the new URLs;
5. keep old redirects for at least one year, preferably indefinitely while inbound
   links/users may still rely on them;
6. change the ID/URL identity separately from unrelated design or taxonomy work.

Google also recommends readable words rather than long opaque IDs when possible.
The seven-digit migration is therefore an internal consistency decision, not an SEO
benefit by itself.

Official references:

- https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes
- https://developers.google.com/search/docs/crawling-indexing/301-redirects
- https://developers.google.com/search/docs/crawling-indexing/url-structure

## Read-only planner

`tools/coloring-pages-legacy-id-plan` reads one exact catalogue snapshot and writes
only to stdout.

Example **planning syntax only** (not LIVE authority):

```text
python3 tools/coloring-pages-legacy-id-plan \
  --catalog /approved/read-only/catalog.json \
  --expected-catalog-sha256 <64-lowercase-hex> \
  --expected-legacy-count 30
```

The planner:

- requires the exact raw catalogue SHA-256;
- validates unique, path-safe catalogue IDs and ID-bound public media paths;
- identifies exactly the non-seven-digit IDs;
- allocates unique random seven-digit candidates with collision checks against both
  the existing catalogue and current batch;
- preserves catalogue indices/order as evidence but does not rewrite the catalogue;
- enumerates exact detail, print and media old→new redirects;
- emits a bounded `DRY_RUN_ONLY` v1 manifest with its own canonical SHA-256;
- stops on stale hash, unexpected legacy count, duplicate ID, unsafe path, collision
  exhaustion or malformed input.

The manifest can later be verified against the same catalogue:

```text
python3 tools/coloring-pages-legacy-id-plan \
  --catalog /approved/read-only/catalog.json \
  --expected-catalog-sha256 <catalog-sha> \
  --expected-legacy-count 30 \
  --verify-manifest /approved/read-only/plan.json
```

It can also render a **source candidate**, not active server configuration:

```text
python3 tools/coloring-pages-legacy-id-plan \
  --catalog /approved/read-only/catalog.json \
  --expected-catalog-sha256 <catalog-sha> \
  --expected-legacy-count 30 \
  --render-nginx-snippet /approved/read-only/plan.json
```

The generated snippet contains exact map entries only. A later application PR must
review and implement 308 behavior for `detail.html?id=<old>`,
`print.html?id=<old>` and every old `/media/<old>/...` URI. Unknown aliases must
fall through to existing not-found behavior. Do not mount or `include` a host-writable
text file directly as NGINX configuration.

## Dependency inventory

The exact approved mapping is a shared cutover identity. Every ID-keyed surface must
be reconciled before the first production rename:

| Surface | Current behavior | Required cutover behavior |
| --- | --- | --- |
| Catalog + originals + derivatives | ID is record and directory identity | one-to-one rename under one host transaction; bytes/order/metadata preserved |
| Detail + print URLs | query parameter is catalogue ID | permanent old→new server redirect before old ID disappears |
| Media URLs | `/media/<id>/...` | permanent exact old URI→new URI redirects; no chain |
| Internal links + canonical | generated from fresh catalogue ID | automatically new after catalog cutover; verify no old IDs emitted |
| Sitemap | generator emits IDs from catalogue | regenerate/publish only new IDs after cutover |
| Print basket | LocalStorage stores activity IDs | translate old saved IDs through the exact alias map before reconciliation; do not silently drop selections |
| Aggregate Like/Print | Worker state keyed by `page_id` | migrate or alias counts so totals do not reset |
| Error reports | report payload contains current activity ID | new detail emits new ID; historical reports remain historical |
| GoatCounter | logical path contains seven-digit ID for current pages | new traffic uses new ID; historical analytics are not rewritten |
| ADMIN archive/jobs/state | may contain ID-keyed references | fresh RPi5 inventory and migrate/alias inside reviewed one-shot operator |

The machine-readable companion is
`deploy/legacy-id-migration-handoff-v1.json`.

## Cutover order

A safe later program is intentionally split:

1. **Read-only plan:** fresh catalogue, exact SHA, exact legacy set, allocate candidates,
   owner reviews and freezes manifest digest.
2. **Application compatibility source:** separately reviewed app PR installs the exact
   server redirects and basket alias compatibility. Merge/deploy happens before data
   movement and is verified with synthetic aliases only.
3. **Dependent-state source:** prepare any Worker/D1 and ADMIN/RPi5 migration logic;
   prove counts/state preservation and exact mapping.
4. **Owner LIVE gate:** one exact mapping, host, operator SHA, catalogue SHA and
   dependent-state preconditions.
5. **One-shot data migration:** under the existing publication lock validate everything
   before first mutation, then atomically update bounded state/directories/catalog.
6. **Postverify:** old URLs 308 directly to new, new detail self-canonical, media works,
   basket survives, Like/Print totals preserved, sitemap has only new IDs, catalogue
   count/order/content unchanged.

Any drift before first mutation stops the run. Any uncertainty after first mutation
stops without retry, rollback, cleanup or per-ID fallback.

## Baseline test fixture

The regression suite contains all 30 non-seven-digit ID forms observed in the pinned
catalogue review, but it contains no production images or private runtime dump.
Tests also cover collisions, leading-zero IDs, multi-page media paths, tampering,
stale catalogue hashes, unsafe IDs/paths, wrong legacy count and exact NGINX map
candidate generation.

The pinned snapshot is planning evidence only. Before any exact mapping is approved,
the future operator must read a fresh canonical RPi5 catalogue and independently
revalidate its SHA, ID set and dependent runtime state.
