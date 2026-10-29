# Multiple canonical categories per activity (issue #432)

Source-only public/importer prerequisite for `RPi5_main#1281`. This does not activate the ADMIN chip picker, repin its importer image, or authorize publication.

## Catalogue contract

`category` remains the required single primary category for every entry. A new opt-in, ordered `categories` array is supported:

```json
{
  "category": "tiere",
  "categories": ["tiere", "jahreszeiten"],
  "topics": ["weihnachten"]
}
```

When `categories` is present, the importer requires a list of 1–6 distinct exact canonical `metadata/categories.json` IDs, with `categories[0]` equal to `category`. There is one catalogue record, one activity ID, one private original and one derivative set. Existing entries and legacy importer calls without `categories` are preserved unchanged. Invalid or unknown input is rejected before content writes. An explicit topic must have at least one compatible selected category (seasonal = `jahreszeiten`; evergreen = any other).

The CLI keeps `--category <primary>` and adds repeatable `--additional-category <secondary>` options. Only explicitly using the extra option writes `categories`; `--topic` remains independent. The public homepage category filters/counts/search and category landing pages use the full validated membership array, with legacy single-category fallback. A single entry is counted only once per category and never duplicated in one gallery.

## Release dependencies and safety

1. Review source, importer unit tests, public filter checks and exact-head CI in `coloring-pages#432`.
2. Separate explicit `MERGE coloring-pages #<PR> HEAD=<SHA>` is required. The approved app-input auto-LIVE flow remains bounded by `AGENTS.md` and must prove the deployed immutable image/source; a source merge alone is not runtime proof.
3. Only afterward update `RPi5_main#1281` ADMIN jobs/edit/chips with a reviewed pinned importer capability check and a separately authorized RPi5 LIVE install. The current single-category ADMIN must not send additional-category flags before this alignment.
4. No historical entries, production PNGs or LIVE catalogue records are mutated by this source change. Any actual publication still requires a separate owner action.

The direct Chat-to-Drive manifest remains one-category-only until its separate explicit contract is reviewed. Never silently repurpose `categories` as a Drive manifest attribute.
