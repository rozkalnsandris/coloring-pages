# Ausmalbild der Woche — source contract (#205)

## Editorial ownership and activation

The feature is deliberately **inactive by default**. `js/weekly-feature.js` contains a finite `CURATED_WEEKS` object, initially empty. No publication ID is inferred from a title, image, test fixture or GitHub source. A responsible Ausmalwiese editor must separately confirm each exact 7-digit ID against the **currently published** catalogue, approve its title/preview, and submit the dated week-to-ID mapping for normal source review. An issue or this scaffold is not editorial approval.

Maintain a rolling **8–12 ISO weeks** when the editor wants the feature active; refresh the mapping through reviewed source PRs before it expires. Reusing the same ID in consecutive weeks should be avoided by the editor. Past entries may be retained for provenance until an ordinary approved source change removes them. No scheduled job, remote edit, content import or automatic selection is authorized. If there is no editorial selection or the schedule ends, the slot stays hidden and the normal catalogue remains unchanged.

Example format only (not an approved published ID): `"2026-W44": "1234567"`. **Do not copy this placeholder into the live curated map.**

## Runtime behavior

- Compute the current ISO week **and ISO week-year** from the calendar date in `Europe/Berlin`, including the local midnight boundary and cross-year weeks.
- At most one ID can be configured for an ISO week. Show the slot only if that exact ID appears in the already-fetched `catalog.json` array with a nonempty title and thumbnail. Missing, expired, unpublished and invalid mappings all fail closed to a hidden slot; never substitute a random or guessed drawing.
- Reuse the published catalogue thumbnail, German title and standard `detail.html?id=...` flow, carrying forward only the existing allowlisted `campaign=dortmund-01` parameter. The print/original PNG contract remains untouched.
- A separate compact callout is used instead of cloning a `coloring-card`. It does not alter Newest, Popular, Trending, search, counts or the number/order of catalogue cards.
- `js/app.js` calls the small feature module with the **same** catalogue array after its existing fetch. No extra HTTP request, API, cookie, visitor recognition, scheduler or timer.
- Semantic heading, descriptive links, alt text, focus style, mobile responsive layout and `hidden` ensure accessible fallback. A failed optional feature render must not block the catalogue.

## Release gate

Source work and offline tests do not prove any specific ID is published or authorize an editorial choice. A source PR touching `index.html` or `js/**` requires separately authorized exact-head merge and follows only the existing bounded application release rules. No GitHub merge, LIVE, Cloudflare or RPi5 mutation is part of the feature's source preparation.
