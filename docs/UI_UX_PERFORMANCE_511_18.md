# UI/UX audit #511 — finding 18 performance/network evidence

Date: 2026-11-13. Baseline source: `69a77582da575df3bc506d759f9f36005659a861`.

## PageSpeed Insights baseline

A fresh PageSpeed Insights mobile report for `https://ausmalwiese.de/` was captured on 2026-11-13 at 16:13 GMT+1.

Lab environment shown by PageSpeed:
- Lighthouse 13.6.0;
- emulated Moto G Power;
- Slow 4G throttling;
- HeadlessChromium 157.0.8103.38;
- single-page initial-load session.

Lab results:
- Performance: **97**;
- FCP: **0.9 s**;
- LCP: **2.3 s**;
- TBT: **30 ms**;
- CLS: **0**;
- Speed Index: **3.7 s**.

The report listed opportunities for cache lifetime (estimated 146 KiB), image delivery (estimated 544 KiB), and render-blocking requests (estimated 720 ms), plus one long main-thread task. These are lab estimates, not production guarantees.

The “Discover what your real users are experiencing” section reported **No Data**. Therefore this audit does not claim CrUX LCP/INP/CLS field percentiles for Ausmalwiese.

## Reproduced network duplication in source

The current public browse surfaces loaded the same `/catalog.json` more than once during page startup:

- homepage: `js/app.js` plus `js/print-basket-ui.mjs`;
- detail: `js/detail.js` plus `js/print-basket-ui.mjs`;
- category pages: `js/category.js` plus `js/print-basket-ui.mjs`.

All startup readers used `no-store`, so browser HTTP caching was not a reliable deduplication mechanism.

The basket ZIP export has a different contract: immediately before staging an export it deliberately re-fetches `/catalog.json` with `cache: "no-store"`, `credentials: "omit"`, `redirect: "error"`, and an abort signal, then verifies the selected page order and print URLs. That fresh revalidation is a safety/freshness gate and must not be memoized.

## Bounded change

This lane uses one page-scope `globalThis.__ausmalCatalogPromise` shared by homepage/detail/category/basket startup consumers. Each consumer keeps its existing direct fetch as an isolated fallback, so dependency-free VM tests and partial page surfaces remain usable without a new bootstrap script. The first consumer starts the same-origin `no-store` request; the others reuse that Promise. A failed request clears the shared slot so a later explicit user action is not permanently poisoned.

Homepage hydration starts categories, topics and catalogue loading together with `Promise.all`; the category-topic projection still waits for the exact registry bytes/hashes it validates. No extra JavaScript resource is added solely for catalogue sharing.

The basket ZIP freshness fetch remains direct and unchanged.

## Category pagination alignment

Category landing pages previously replaced their static seed with every matching catalogue entry in one DOM render. On a large category such as Tiere this meant dozens of cards were created at once even though the homepage already used a 20-item batch contract.

The category controller now uses the same **20-item** batch size. The visible total remains the full filtered result count; “Mehr anzeigen” reveals the next batch. Topic, age/difficulty and Back/Forward filter changes reset the batch to 20. Keyboard activation moves focus to the first newly revealed card, including when the final batch hides the button.

This changes only client-side rendering volume. Catalogue order, category/topic membership, canonical URLs, metadata filters and print assets are unchanged.

## Deliberately not changed

The 97 mobile Lighthouse score and 2.3 s lab LCP do not justify a framework rewrite, aggressive image-quality changes, or broad renderer refactoring. Image-delivery and render-blocking opportunities may be evaluated separately with exact resource evidence. Field-data optimization should wait until CrUX data exists or another trustworthy production telemetry source is available.
