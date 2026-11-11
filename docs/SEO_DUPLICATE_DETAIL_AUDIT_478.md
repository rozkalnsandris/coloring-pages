# SEO #478 — duplicate-title detail audit and safe canonical policy

## Evidence and current limit (2026-11-11)

Read-only browser inspection of the public `https://ausmalwiese.de/catalog.json`
found **477 catalogue activities**, **20 exact normalized-title groups** covering
**42 activities**. Title normalization folds case, Unicode compatibility and
repeated whitespace; the tool in this change can reproduce the inventory from
an explicitly supplied local catalogue snapshot. This is a dated observation,
not a pinned LIVE file SHA or a claim that all matching images are identical.

Google Search Console's earlier crawl reported a Google-selected canonical
`detail.html?id=9115775` for `detail.html?id=5831978`; those two public pages
show the same title (`Vogelscheuche im Kürbisfeld`) but **visibly distinct**
scarecrow drawings. The Halloween variant has a checked shirt and neckerchief;
the Herbst variant has a plain shirt with a patch. Their published preview and
print URLs are separately addressed by ID; distinct paths alone do not prove
byte-unique artwork. Neither activity may be collapsed to the other on the
strength of its title or Google's clustering decision.

Current `js/detail.js` sets a self-canonical only after a valid, renderable ID
is found. `detail.html` contains no blanket canonical, `print.html` is
intentionally `noindex`, and confirmed missing detail IDs gain `noindex`
only after a successful catalogue fetch. These are correct conservative
behaviours and should not be weakened to make the Search Console report greener.

## Read-only inventory

The **20 candidate groups** in the public snapshot are listed below by
normalized title. In total they cover 42 published activities. This inventory
is for editorial review; it must not directly drive redirects, `noindex`,
artwork deletion, catalogue changes, or ID migrations.

| Same title (normalized) | Published IDs |
| --- | --- |
| Christbaumkugel mit Stern und Schneeflocken | 1182412, 1191110 |
| Christbaumkugel mit Schleife und Sternen | 2326012, 6077744 |
| Kleiner Tänzer | 8944600, 6668623 |
| Gartenzwerg | 7724366, 7430396 |
| Martinsgans | 3036827, 0865012 |
| Sankt Martin auf dem Pferd | 6194556, 6063157 |
| Karotte | 1487509, 5999472 |
| Paprika | 9392202, 2849661 |
| Sankt Martin teilt seinen Mantel | 5504139, 5582332 |
| Vogelscheuche im Kürbisfeld | 9115775, 5831978 |
| Entchen im Herbstregen | 1291018, 4258544 |
| Fröhlicher Halloween-Kürbis | 3912267, halloween-kuerbis-001 |
| Fröhlicher T-Rex | 9386972, 7314826 |
| Fröhlicher Stegosaurus | 1925919, 6142087 |
| Fröhlicher Triceratops | 7016404, 3829591 |
| Fröhlicher Muldenkipper | 7547459, 5980971 |
| Fröhlicher Elefant | 9642164, 3255181, 9333274 |
| Fröhlicher Affe | 6930730, 6939374 |
| Fröhlicher Langhals-Dinosaurier | 3706403, 8504217, 2397696 |
| Blockiger Abenteurer mit Spitzhacke | cp-000002, figuren-001 |

## Decision rule

1. **Distinct artwork** — keep each valid activity ID and its own self-canonical
   and sitemap URL. Give genuinely different pictures a truthful, naturally
   differentiating German title and description through the protected content
   editorial workflow, backed by a visual check. Multiple topics/categories
   may point to one actual activity, but two different activities must not be
   merged merely because of a shared topic or title.
2. **Verified byte/visual duplicate artwork** — first inventory all linked
   topics/categories, print-basket references, inbound detail/print/media URLs,
   likes/views, and immutable media versions. Propose one canonical surviving
   activity and an old-to-surviving permanent URL compatibility plan. A 301/308
   redirect is appropriate only after a separately reviewed owner-authorized
   retirement of the redundant activity. Do not rewrite a public catalogue or
   redirect a valid distinct picture as part of a source-only SEO task.
3. **Unverified** — preserve both URLs, keep self-canonicals, and mark for
   editorial image review. Title-only collision must never imply an image match
   or trigger a redirect, `noindex`, deletion, or forced canonical.

## Reproduce safely

Use the read-only, dependency-free Python helper on a **trusted exported copy**
of `catalog.json` (never auto-fetch LIVE or write to the protected catalogue):

```text
python3 tools/coloring-pages-seo-title-audit --catalog /path/to/catalog.json
```

Optionally supply `--expected-catalog-sha256 <exact-64-hex>` to reject a drifted
snapshot before displaying anything. The script prints JSON to stdout and
**never downloads media or writes output files**. `artwork_identity` always
remains `unverified`; a human/authorized content review must compare the actual
preview and printable image bytes/visuals before content changes.

## Owner-gated follow-up

The next effective SEO change is **editorial differentiation of verified
non-identical same-title pages**, beginning with the two scarecrow variants.
This changes production catalogue metadata, so it is deliberately **not**
performed by #478's source-only AUTO-RUN FULL authorization. Obtain a separate
bounded production-content edit authorization with exact activity IDs, existing
and proposed German titles, preservation of IDs/media/topics/stats, and a
fresh installed operator/runtime preflight. Do not use a GitHub source PR as
an alternate transport for protected LIVE catalogue writes.

If later proven byte-identical items require consolidation, prepare a separate
reviewed migration/redirect contract and request its own exact owner gate.
Do not click Search Console Validate Fix or Request Indexing until a verified
production change actually ships.

References:
- https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- https://developers.google.com/search/docs/crawling-indexing/canonicalization-troubleshooting
- https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics
- https://developers.google.com/search/docs/crawling-indexing/301-redirects
