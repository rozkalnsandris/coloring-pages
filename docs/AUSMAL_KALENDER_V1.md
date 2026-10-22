# Ausmal-Kalender #196 — current source contract

The current calendar is a mobile-first visual seasonal browser rather than a one-result-per-theme text list.

- All 12 months remain directly selectable.
- The current month is selected using `Europe/Berlin`.
- Each theme renders the complete set of matching published catalogue entries as a horizontally scrollable preview shelf.
- Every published preview keeps the normal `detail.html?id=...` → A4 print flow.
- A theme with results exposes a shareable `index.html?topic=<id>#neu` link to the full catalogue filter.
- Seasonal matching prefers explicit reviewed `topics` metadata. Ambiguous observances such as Nikolaus, Advent, Sankt Martin, Muttertag, Ostern and Fasching require explicit topic metadata instead of broad title-only guesses.
- Broader non-ambiguous themes may retain legacy-term fallback for older catalogue entries without `topics`.
- Missing results stay empty and do not expose a misleading “Alle ansehen” link.
- Unavailable catalogues fail visibly without demo cards.

The Gregorian Easter computus keeps Easter and Carnival/Fasching in their year-dependent months. The page does not publish state-specific school-holiday dates or imply nationwide German school-calendar accuracy.

The UI uses semantic HTML, plain CSS and vanilla JavaScript only. Responsive card shelves use native CSS Grid plus horizontal overflow/scroll snapping; no carousel framework, new API, database, account, tracking or external artwork is introduced.

GitHub remains canonical for this source. Merge and any resulting LIVE application release still require the normal owner gate and exact-head CI/review checks.
