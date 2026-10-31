# Managed runtime Topics v2 — issue #438

Source-only prerequisite for protected `RPi5_main#1294` compact Topics manager.

## One shared runtime registry

- The trusted RPi5 file is `/srv/coloring-pages-content/public/topics.json`; public nginx reads it read-only at `/var/lib/coloring-pages/public/topics.json`. The network-disabled importer mounts and reads the **same content-root file**. An absent file yields HTTP 503 rather than a fallback.
- Immutable `metadata/topics.json` (`topics.v1`) is the seed only. `tools/coloring_pages_topics.py seed` prints deterministic v2 JSON and **never writes to LIVE**. A separately owner-authorized operator must install it under the publication lock, no overwrite.
- Managed schema: `rozkalns.coloring-pages.topics.v2`, `revision` in 1–2147483647 and 1–128 ordered topic entries. Immutable ASCII slug IDs (1–48), NFC labels (1–80), bounded Unicode icon/emoji (1–12, no markup or controls), exact `seasonal|evergreen` kind, 0–32 distinct NFC `legacy_terms` (each 1–64). Seasonal entries require valid `active_from` and `active_to` `MM-DD`, including leap day and year-wrap; evergreen entries forbid these keys. No unknown keys.
- Canonical serialized bytes = UTF-8 `json.dumps(..., ensure_ascii=False, indent=2) + "\n"`, maximum 64 KiB. Read-only helper requires regular file, nonwritable group/other, no symlink, exact canonical bytes; SHA-256 is over those bytes. Preserve all existing topic IDs/labels/icons/keywords/kinds/dates/ordering.

## Importer and public contract

- Importer reads Topics v2 for *every import*, including no-topic legacy entries, before image/content processing; optional `--topics-sha256` binds exact ADMIN snapshot. A missing option never bypasses valid registry enforcement. Under the host publication lock it re-reads Topics SHA-256 before the first permanent originals/media/catalog mutation.
- Ordered primary/secondary topics require valid IDs. Seasonal topics require the `jahreszeiten` category; evergreen topics require a non-seasonal category. Existing catalog/media/legacy records are untouched.
- Public `/topics.json` exposes only the live file, no-cache/no-store, with topic chips and filters in `js/app.js` accepting the bounded v2 schema. A changed registry affects discovery without rebuilding. No arbitrary URL/route or write API is exposed.
- Protected ADMIN editor is a separate issue `RPi5_main#1294`: CSRF, fixed allowlisted write actions, strong `If-Match` (stale 412), publication lock, atomic file stage/fsync/replace, reference/queued-job and archive safeguards, no ID rename or referenced-kind change, no silent catalogue reassignment.

## Owner-gated rollout

**Do not merge or auto-deploy this public endpoint until the shared runtime file, immutable importer volume mount and protected ADMIN v2 compatibility are coordinated and separately authorized.** Old ADMIN expects `topics.v1`. A premature source deployment can turn public Topics into HTTP 503 or break Add pages. Host seed/migration, importer repin, backend restart, production image, media/catalog data, permissions, secrets, Access settings and manual LIVE operations are **not authorized** by this PR. After first mutation failure, STOP without retry, rollback or cleanup.

References: `coloring-pages#436`, `RPi5_main#1291`, `RPi5_main#1294`, OWASP Input Validation Cheat Sheet, RFC 9110 §13.1.1 strong If-Match.
