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

## Multiple canonical topics per activity (issue #434)

The importer now accepts ordered, unique explicit topics for one existing activity, without creating duplicate catalogue entries, originals or derivative sets. Its legacy single `--topic <id>` behavior remains unchanged; to add more, supply `--topic <primary>` and repeat `--additional-topic <id>` for each additional canonical ID. Bare `--additional-topic` without a primary, duplicates, unknown IDs, invalid types and missing category kinds are rejected before any published content writes. The programmatic importer also accepts `topics: [id, ...]` (1–21 canonical unique IDs, bounded by the current registry), optionally paired with a matching `topic` primary. No topic key continues to produce no `topics` catalogue property.

A saved catalogue entry uses `"topics": ["bauernhof", "weihnachten"]` in exact selection order. Each **seasonal** topic requires `jahreszeiten` among its selected categories; each **evergreen** topic requires at least one other category. A mix requires both. The existing public home and category gallery filters already iterate every explicit `topics[]` membership and only count each page once in each topic; legacy title-based fallback remains for older records without explicit topics.

This is a source-only upstream prerequisite for `RPi5_main#1287`. The protected ADMIN currently accepts one `topic` only; it must be updated and its immutable importer image repinned through independently reviewed source and separate exact LIVE approval. No ZIP publication or LIVE changes are authorized here. Reference: Python `argparse` repeatable `action="append"` and JSON Schema `uniqueItems`.
