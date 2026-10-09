# Sitemap publisher handoff v1 — source only

## Ownership and purpose

This is a **non-executable source handoff**, not deployment configuration.
The machine-readable companion is
`deploy/sitemap-publication-handoff-v1.json`. It freezes the source-side
generator identity and required safety properties for a separate
`rozkalnsandris/RPi5_main` operator review. It does not grant host filesystem
authority or make consumer-provided paths or flags trusted RPi5 runtime inputs.

The Coloring Pages repository owns the deterministic read-only
`tools/coloring-pages-sitemap` generator. Its reviewed Git **blob SHA-1** is
`5644c8fd366c0c57f6339fddd163c5091ea134c5` and must be independently checked by the host owner before use. A
later consumer change to this blob must force an explicit review/repin; merely
merging a new `coloring-pages/main` is not an authorization to adopt a
different generator. The normal generator writes XML only to stdout; the
`--verify-sitemap` mode reads a staged XML candidate and produces no file.

## Production boundary verified on 2026-10-09 (historical evidence)

- Canonical host data: `/srv/coloring-pages-content/public/catalog.json`.
- Proposed generated filename: `/srv/coloring-pages-content/public/sitemap.xml`.
- The already-deployed nginx exact route prefers that public file and otherwise
  serves the image-bundled static two-URL fallback.
- Existing Drive ingest operator source: `RPi5_main/ops/bin/coloring-pages-drive-ingest`.
- Existing advisory lock:
  `/srv/coloring-pages-content/state/drive-ingest/.lock` acquired using
  nonblocking exclusive `fcntl.flock` by the existing ingestion operator.
- At the observed checkpoint the catalogue contained 135 unique activities;
  `public/sitemap.xml` did not exist, and the public fallback had 2 URLs.

These are point-in-time observations, **not** trusted future authorization,
source pins, assumptions about the next catalogue, or a host write plan.
A publication operator must recheck fresh identities, bytes, device IDs,
health and runtime state within its own reviewed authorization.

## Required host-owned publication sequence

1. Select only host-owned fixed paths, one reviewed execution identity,
   an independently pinned generator blob and one fixed, approved public target.
   Reject unsafe symlinks/parents, wrong UID/GID/modes, changed device IDs and
   a missing or unsafe trusted lock inode. Do not obtain executable argv, host
   paths or write authority from this consumer-side JSON.
2. Exclude **all** catalogue writers and acquire the **same** existing
   Drive-ingest advisory lock, not a newly named lock. `flock` is advisory:
   taking this lock does **not** serialize writers which ignore it. Before
   activation, RPi5_main must prove every enabled importer/publication path
   respects this lock or separately arrange a reviewed quiescent state.
3. While exclusion remains in force, read the current catalogue as a validated
   regular file and freeze its **raw-byte** SHA-256. Validate the full catalogue,
   IDs, renderability and canonical URL set using the pinned generator with
   `--catalog` and `--expected-catalog-sha256`.
4. Stage the generated XML on the **same filesystem and destination directory**
   under a fixed, operator-owned, exclusive-create temporary name. Validate
   nonempty bounded bytes, strict UTF-8/XML parsing, URL count and **exact**
   byte equality using `--verify-sitemap` with the same catalogue hash.
   No dynamic path, shell command, provider secret or external network call
   is part of the generation step.
5. Still holding writer exclusion, immediately check the published catalogue
   raw-byte SHA-256 again, plus the staged candidate identity. If anything has
   drifted, **STOP before replacement**. Flush and `fsync` the staged bytes,
   atomically replace only the approved `public/sitemap.xml` using the
   reviewed same-filesystem operation, and `fsync` the directory as required
   by the operator's durability policy. A missing old sitemap uses the already
   present static fallback until publication; no automatic rewrite, unlink,
   rollback or cleanup follows an ambiguous post-mutation failure.
6. Verify local/public `/sitemap.xml` HTTP 200, cache policy, XML, expected
   URL count and exact URL-set match to the currently published catalogue.
   A sitemap submission to Google Search Console is **not** part of this
   authority. Future catalog changes require a separately approved freshness
   strategy; a one-time generated file is not automatically kept current.

## Explicit non-authority

This source handoff cannot install an RPi5 operator, mutate production
content, schedule recurring publication, restart a container/service, change
permissions, read secrets, change Cloudflare, or submit to Google Search
Console. The host owner must review an implementation and its negative/failure
tests in `RPi5_main` and seek a new **exact owner LIVE gate** for any
installation or publication. Existing `PUBLISH` approval covers only the
approved image/manifest ingest, never this sitemap write.

## Official references

- Google Search Central:
  https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- Linux advisory `flock` behavior:
  https://man7.org/linux/man-pages/man2/flock.2.html
- Python atomic file replacement:
  https://docs.python.org/3/library/os.html#os.replace
