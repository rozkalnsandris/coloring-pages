# Mobile category row panel — follow-up to #186 / PR #473

Status: source-only proposal. No LIVE or print verification implied.

## Problem and selected behavior

User Android screenshots showed two regressions: opening one `details` caused every category to become full-width after #473, while the earlier grid layout left empty cells around full-span disclosures. The mobile design should keep **two equal-width cards** at all times (361–540 px) and show the opened category's **original** topic list in a full-width panel **below that pair**. Later cards must stay paired.

This small vanilla JS progressive enhancement retains native `details name="category-browser"` and moves the existing list node (not a clone), so links, topic filters and click handlers remain intact. It adds `aria-controls` and `aria-labelledby`, restores the list when the viewport leaves mobile, and pairs newly managed categories correctly when runtime registry entries change. It does not touch catalog, data, printing, tracking, or category registry.

Do not use `grid-auto-flow: dense` (visual order can differ from keyboard order) or `display: contents` on semantic details. Sources: [MDN CSS Grid accessibility](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Grid_layout/Accessibility), [MDN details](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/details), [W3C disclosure pattern](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/), [MDN Node.appendChild](https://developer.mozilla.org/en-US/docs/Web/API/Node/appendChild).

## Isolated fixture QA (not integrated / LIVE)

Using local headless Chromium, widths 340, 412, 540, 800, 1440 px showed no horizontal overflow. At 412 px, eight closed cards remained 186 px wide; after opening `Tiere`, the cards remained 186 px and the topic panel occupied 380 px. At 540 px the cards stayed 250 px with a 508 px topic panel. Outside the affected breakpoint, cards and native disclosure remained unchanged. This does not verify the full app or printing.

Before merge: exact-head CI/review/threads; integrated viewport screenshots and interactions at 340/412/540/800/1440, keyboard Enter/Space/Tab, topic links and deep links, managed category additions, page resize, gallery/detail/A4 original printing, consent.

Files: `css/home-discovery.css`, `js/category-mobile-rows.js`, `index.html`, `tests/test_compact_category_discovery_186.py`, `tests/test_category_mobile_rows.py`.
