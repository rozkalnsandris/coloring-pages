# Ausmalbild der Woche — publication-time driven contract (#205)

## Owner requirement and timing

The owner requested **automatic weekly selection every Monday at 00:10 in `Europe/Berlin`**, using pages published daily, rather than a fixed 12-week editorial list. This source design uses **no Cron, server scheduler, new API, extra HTTP request or persistent visitor identifier**.

The homepage calculates an effective Berlin ISO week from its existing clock and already-fetched `catalog.json`. The new week starts at **Monday 00:10:00 Berlin civil time**, including CET/CEST transitions and ISO week-year rollover; before that minute the previous choice is still displayed. The weekly highlight updates at the **next homepage load or refresh**, not by a background write at 00:10. An already-open tab does not switch automatically without navigation/reload; a page visit isn't guaranteed at exactly 00:10. The separate ChatGPT weekly read-only reminder does not change the website.

## Publication-time metadata

The GitHub-owned `tools/coloring-pages-import` appends an immutable-looking UTC `published_at` value (ISO 8601, e.g. `2026-10-22T07:00:00Z`) to **newly imported** catalogue records, before the normal atomic catalogue publication. It preserves existing records byte-for-byte in meaning and **does not backfill dates** for historical records. Timestamp denotes import/catalogue preparation time, not a separately attested RPi5 audit or proof of exact public visibility to the second. It must never come from a user-editable title/filename, file modification time, or the record's list position.

**Integration gate:** GitHub source tests cannot prove that the protected ADMIN publishing operator and its installed importer actually execute this updated code. Before treating automatic rotation as functional in production, separately verify the *actual* import path emits `published_at` on newly published `catalog.json` records after authorized deployment. If ADMIN uses an independent catalogue writer, this source PR does not change it. Existing public catalogue entries currently lack this field; they cannot be assigned a publication date by guessing.

## Selection algorithm

- Filter catalogue entries to unique seven-digit string IDs, a nonempty German title, exact `/media/<ID>/thumb.webp` thumbnail path and strictly formatted, parseable UTC `published_at`.
- Convert each UTC timestamp to **Berlin civil date/time**. For a given Monday 00:10 cutoff, exclude entries published **at or after** the cutoff; this ensures Tuesday/Wednesday/daily additions cannot alter the current week's selection. A page published exactly at Monday 00:10 is eligible only at the *following* Monday cutoff.
- Prefer candidates published in the **preceding seven-day Berlin-civil window** ending at the current Monday 00:10 cutoff. If none exist, consider all older timestamped catalogue records; when possible avoid the previous week's unfiltered deterministic winner.
- Select one item using a deterministic week-key-and-ID hash with ID tie-breaker, independent of JSON ordering or the visitor. This is a reproducible pseudo-random editorial choice, **not** a cryptographically random draw. Catalogue entries added after the cutoff do not influence it.
- Missing, invalid, untimestamped, future-only, withdrawn or unreadable entries lead to a hidden weekly slot when no valid candidate is left. No guessing from catalogue order, no old hard-coded mapping, no duplicate display in the catalogue grid itself.
- Because no durable weekly state is stored, retroactive mutation of earlier `published_at` values or removal of a previously eligible/winning record **can** change or hide the choice. Normal immutable timestamps and append-only daily publications make the result stable during the week. A stronger freeze despite catalogue deletion would require a separately authorized durable weekly decision store, outside this source-only/no-Cron design.

The chosen page uses the published thumbnail, catalogue title, usual `detail.html?id=...` link, and the existing allowlisted campaign. Newest/Popular/Trending, search, filters, activity page counts, source PNG and A4 print stay unchanged. The main homepage fetches `catalog.json` only once, and the weekly code never makes a second request.

## Tests and source/release gates

Source tests cover importer UTC timestamps and untouched legacy entries; Monday 00:09:59/00:10:00 cutovers, autumn/spring DST, cross-year ISO weeks, additions after the cutoff, stable week choice under catalogue reordering, absent/invalid dates, legacy-only and empty catalogue, older-date fallback, and actual HTML/CSS/JS cache hashes.

Source-only authorization permits changes to importer, HTML/JS/CSS, documentation and tests for #205. This **does not** authorize any GitHub merge, RPi5/Admin install, publisher invocation, live data edit, migration, Cloudflare setting, secret or permissions change. A future owner-authorized exact-head merge may trigger only the reviewed bounded application SIMPLE-DEPLOY flow for eligible changed files; installed ADMIN/importer and production `published_at` compatibility still need independent read-only evidence. The PR must not be represented as functioning LIVE based solely on CI.
