# Ausmalbild der Woche — source contract (#205)

## New owner requirement — 2026-10-22 (release HOLD)

The owner now wants **a new pick every Monday at 00:10 Europe/Berlin**, reflecting the coloring pages published daily. The finite 12-week `CURATED_WEEKS` map below was selected before this requirement and **must not be treated as the agreed future behavior or merged as the finished feature**. GitHub PR #317 is held for redesign.

A separate ChatGPT weekly task is scheduled for Mondays at 00:10 Europe/Berlin to read the public catalogue and propose a fresh selection. **It does not and must not write production or GitHub, merge or publish content**. A scheduled proposal sent to the owner is not itself an updated homepage.

Current public `catalog.json` has no `published_at` or equivalent per-entry timestamp. It is newest-first, but that ordering alone does not prove the exact publication date or preserve a once-per-week selection as new pages arrive. An on-page random selection from the current newest entries may change during the same week and is not a correct implementation of the fixed Monday 00:10 cutover.

A fully automatic, consistent homepage needs separately reviewed source support for a **durable weekly choice** and a **trustworthy publication-time boundary** (or another owner-approved source of immutable publication state). The simple future-compatible design is to record immutable UTC `published_at` for newly imported entries and deterministically pick one eligible entry published before the Berlin Monday 00:10 cutoff, using the same already-fetched catalogue. The midnight, DST, ISO week-year, no-new-entries, missing-ID and weekly-consistency cases require tests. Existing entries have no timestamp; do not backfill them by guessing. Importer/ADMIN/catalog contract changes are **outside the frozen current PR #317 source scope** and require a separate scoped source decision before implementation.

Until that contract is reviewed and implemented, keep the existing code as an unmerged candidate, not as a production automatic picker. No direct `main` mutation, cron, runtime/server write or LIVE authorization is inferred.


## Editorial ownership and activation

On 2026-10-22, the owner explicitly delegated random editorial selection for #205. The 12 source-only selections below were drawn without replacement from the read-only public `https://ausmalwiese.de/catalog.json` response (400 entries; 344 records had a seven-digit ID and matching thumb/print paths). `js/weekly-feature.js` now includes those **exact** 12 ISO-week mappings, preserving leading zeroes. This is a curated PR candidate, not a claim that the PR is merged, LIVE is deployed, the thumbnail/print bytes were independently validated or the catalogue will remain unchanged.

Maintain a rolling **8–12 ISO weeks** when the editor wants the feature active; refresh the mapping through reviewed source PRs before it expires. Reusing the same ID in consecutive weeks should be avoided by the editor. Past entries may be retained for provenance until an ordinary approved source change removes them. No scheduled job, remote edit, content import or automatic selection is authorized. If there is no editorial selection or the schedule ends, the slot stays hidden and the normal catalogue remains unchanged.

## Source-only editorial mapping (22 October 2026)

| Berlin ISO week | Published catalogue ID | Catalogue title |
|---|---|---|
| `2026-W43` | `3398005` | Fröhliches Auto |
| `2026-W44` | `0662291` | Einhorn als Polizist |
| `2026-W45` | `3589168` | Halloween-Otter mit Schal |
| `2026-W46` | `3853527` | Alpaka |
| `2026-W47` | `9823291` | Eishockeyspieler beim Bully |
| `2026-W48` | `2468053` | Fröhliche Mumie mit Süßigkeiten |
| `2026-W49` | `3534071` | Gemüsekorb |
| `2026-W50` | `5755734` | Kind mit Laterne zu Sankt Martin |
| `2026-W51` | `8367735` | Ente |
| `2026-W52` | `1291018` | Entchen im Herbstregen |
| `2026-W53` | `2584849` | Fröhlicher Fuchs |
| `2027-W01` | `7547459` | Fröhlicher Muldenkipper |

These IDs were chosen randomly from public catalogue **listings**, not by image recognition or by inventing publication status. The current week is `2026-W43`. The feature ends after `2027-W01` unless a new approved source update extends the mapping. The runtime checks the ID against the current catalogue again and hides a missing/unpublished item.


## Runtime behavior

- Compute the current ISO week **and ISO week-year** from the calendar date in `Europe/Berlin`, including the local midnight boundary and cross-year weeks.
- At most one ID can be configured for an ISO week. Show the slot only if that exact ID appears in the already-fetched `catalog.json` array with a nonempty title and thumbnail. Missing, expired, unpublished and invalid mappings all fail closed to a hidden slot; never substitute a random or guessed drawing.
- Reuse the published catalogue thumbnail, German title and standard `detail.html?id=...` flow, carrying forward only the existing allowlisted `campaign=dortmund-01` parameter. The print/original PNG contract remains untouched.
- A separate compact callout is used instead of cloning a `coloring-card`. It does not alter Newest, Popular, Trending, search, counts or the number/order of catalogue cards.
- `js/app.js` calls the small feature module with the **same** catalogue array after its existing fetch. No extra HTTP request, API, cookie, visitor recognition, scheduler or timer.
- Semantic heading, descriptive links, alt text, focus style, mobile responsive layout and `hidden` ensure accessible fallback. A failed optional feature render must not block the catalogue.

## Release gate

The owner's delegated random selection and read-only public catalogue listing support the editorial source mapping, **not** confirmation of real RPi5 runtime, production image version or ongoing availability. A source PR touching `index.html` or `js/**` requires separately authorized exact-head merge and follows only the existing bounded application release rules. No GitHub merge, LIVE, Cloudflare or RPi5 mutation is part of this source-only change.
