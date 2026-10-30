# Managed runtime categories v2 — issue #436

This source-only public/importer prerequisite enables the later protected ADMIN implementation in RPi5_main#1291. A source merge **does not** authorize or perform runtime initialization, registry writes, importer pin changes or ADMIN rollout.

## Authority and canonical file

The six existing structural IDs are \`tiere\`, \`fahrzeuge\`, \`alphabet\`, \`lernen\`, \`figuren\`, \`jahreszeiten\`, in that order, permanently. Structural IDs cannot be removed or reordered because legacy routes, topic semantics, catalog and SEO rely on them. Rename only their labels; public legacy page title edits require separate review. \`metadata/categories.json\` stays the **immutable v1 seed** for a separately owner-authorized first install, not the runtime truth.

The sole managed file is \`/srv/coloring-pages-content/public/categories.json\` on RPi5. The existing public volume maps this file read-only into nginx at \`/var/lib/coloring-pages/public/categories.json\`; the network-disabled importer uses the already-mounted content root and reads the **same host file**. Nginx returns HTTP 503 if it does not exist; importer fails before content writes on missing, stale, malformed or unsafe data. No image-local fallback exists for the new runtime reader. \`/topics.json\`, the existing six hard-coded category routes, and \`/essen-natur\` are unchanged.

Managed schema:
~~~json
{
  "schema": "rozkalns.coloring-pages.categories.v2",
  "revision": 1,
  "categories": [
    {"id": "tiere", "label": "Tiere"},
    {"id": "fahrzeuge", "label": "Fahrzeuge"},
    {"id": "alphabet", "label": "Alphabet"},
    {"id": "lernen", "label": "Lernen"},
    {"id": "figuren", "label": "Figuren & Helden"},
    {"id": "jahreszeiten", "label": "Jahreszeiten & Feste"}
  ]
}
~~~

Canonical serialization: \`json.dumps(..., ensure_ascii=False, indent=2) + "\\n"\`, UTF-8; 16 KiB maximum. Exactly 3 document keys, positive bounded integer revision (max 2^31-1), 6–64 unique ASCII lowercase slug IDs (1–48 characters), and German Unicode NFC labels (1–80 code points, trimmed, no control characters). IDs cannot be renamed in place. Every mutation increments \`revision\` by exactly one, including label edits. Structural IDs remain in place. No user-controlled path or URLs enter the runtime file.

## Trusted source-free LIVE migration: owner gate

The source helper \`python3 tools/coloring_pages_categories.py seed\` (or image-local \`python3 /usr/local/bin/coloring_pages_categories.py seed\`) prints deterministic seed bytes; it has **no write action**. Under a separately authorized RPi5 deployment and content-publication lock, the trusted operator must validate that the file is absent and seed once, without overwriting a file. No automatic import of arbitrary paths or changes to catalogs/archive/media. Use canonical serialization and strict ACL/ownership checks. Under the shared publication lock, an ADMIN mutation must check the current strong SHA256 / \`If-Match\` precondition (stale = HTTP 412), validate the next revision and full document, refuse structural deletion and reject any ID still referenced by primary/secondary catalog, archive, restorable or pending/queued publication. Stage in the same trusted public directory, fsync bytes, chmod 0644, \`os.replace\`, fsync parent and verify the exact public SHA256. The ADMIN lock, authenticated writer and exact host operator are tracked in RPi5_main#1291, not created by this change.

After **any** post-first-mutation failure, STOP with evidence and do not retry, roll back or clean up without new owner authorization. Nginx has no public write route.

## Importer, legacy contracts, public navigation

Importer reads exactly the mounted v2 registry under trusted publication lock. New ADMIN uses \`--categories-sha256 <64-lowercase-hex>\` tied to its exact validated registry version and first/secondary membership. Importer verifies this precondition and re-reads bytes before the first final media/catalog change. Without registry, all imports fail closed. Older callers without the digest can still use the same managed runtime file under the host lock: this is legacy argument compatibility, **not** a bypass for registry validation. The legacy Chat-to-Drive manifest is still restricted to its original six category IDs; adding custom categories through that separate path needs a separately reviewed manifest contract.

The homepage reads \`/categories.json\` with \`no-store\` and displays new categories as DOM-created text-only links to \`index.html?category=<slug>#neu\`. The URL facet selects matching primary or ordered secondary membership and exposes the German label for search. Custom categories do **not** generate arbitrary nginx routes or sitemap entries: their query facets are not independent SEO landings. Existing six category routes, old links, canonical SEO pages, sitemap, topic behavior and gallery ordering remain unchanged. Label edits to the six static landing pages need separate editorial alignment.

## Sequence and gates

1. Review exact-head source tests and immutable image build in PR #436. Do not merge without a fresh exact-HEAD \`MERGE coloring-pages #<PR> HEAD=<SHA>\` authorization.
2. Before exposing this source in LIVE, separately authorize and prove the safe one-time RPi5 v2 registry seed and public-volume mapping (nginx and importer must resolve the same SHA256). The app-input merge's existing bounded deployment does **not** authorize a host/content permission or registry mutation. A premature public deploy can make \`GET /categories.json\` return 503.
3. After exact immutable digest and runtime verification, review/pin compatible ADMIN importer and source for RPi5_main#1291, with separate backend install/restart authorization. Keep Categories CRUD disabled until then.

No content, LIVE catalog, media binary, archive, registry, or host data is changed by this source PR.
