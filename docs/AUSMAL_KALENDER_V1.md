# Ausmal-Kalender #196 — source-only implementation

The mobile-first `kalender.html` contains 12 semantic month sections even without JavaScript. Navigation on public catalogue/detail/Kita pages reaches it. JavaScript hydrates links only from validated current `catalog.json` activity records. It respects explicit `topics` arrays first; legacy entries can match `/topics.json` legacy terms or restrained local title keywords. Missing entries become plain non-links, and unavailable catalogues show an error. Only normal detail links are created; the normal A4 print/PNG flow is unchanged.

Current month/year use `Europe/Berlin`, independent of the device timezone. The Gregorian Easter computus places Easter and Carnival Monday in their actual year-dependent months; no precise country-wide school-start or holiday claims are shown. Mobile navigation, focus states and semantic headings are included. No new API, database, tracking, secrets, host content or external artwork.

GitHub source-only; exact-head CI and review needed. PR merge, deployment and LIVE verification require their normal separate gates.
