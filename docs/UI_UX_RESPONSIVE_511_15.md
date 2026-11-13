# UI/UX audit #511 — finding 15 responsive matrix

Status: **NO_FIX** for the current source. This file records source-level and isolated-browser evidence only; it is not a LIVE-device or full-site certification.

## Scope

Finding 15 asked for explicit checks at 320/360/361/390/412/540/541/768/1440 CSS px and allowed a CSS correction only when an overflow/layout defect was reproduced.

Current behavior is intentional from the #186 follow-up work:
- up to 360 px: one category column, native disclosure;
- 361–540 px: two category columns with the existing topic list moved into a full-width row panel;
- 541–800 px: two category columns, native disclosure;
- desktop: three/four columns according to the existing breakpoints.

The CSS and `js/category-mobile-rows.js` use the same `361–540px` enhancement range.

## Chromium matrix

Environment: Chromium 144.0.7559.96 on Debian GNU/Linux 13, isolated local fixture built from the current category-browser CSS/JS contracts. This is not the integrated public site.

| CSS px | Horizontal overflow | Enhanced row panel | Open first card width | Visible panel width |
| ---: | :---: | :---: | ---: | ---: |
| 320 | no | no | 292 px | — |
| 360 | no | no | 332 px | — |
| 361 | no | yes | 162.5 px | 333 px |
| 390 | no | yes | 177 px | 362 px |
| 412 | no | yes | 188 px | 384 px |
| 540 | no | yes | 252 px | 512 px |
| 541 | no | no | 250.5 px | — |
| 768 | no | no | 358 px | — |
| 1440 | no | no | 286 px | — |

Each of the seven category disclosures was opened separately at every width. No case produced `document.documentElement.scrollWidth > innerWidth`. In the 361–540 px enhancement range, exactly one row panel was visible for the opened disclosure.

## Why no CSS change

The 360→361 and 540→541 transitions are visually significant, but the requested matrix did not reproduce horizontal overflow or broken panel geometry. Changing the breakpoint without a reproduced defect would undo deliberate #186/#474 behavior and would be an arbitrary design change rather than a fix.

Existing overflow safeguards remain important:
- grid columns use `minmax(0, 1fr)`;
- category cards and row panels use `min-width: 0`;
- category copy uses `min-width: 0`;
- long subtopic labels use `overflow-wrap: anywhere`;
- the JS media query matches the CSS enhancement range.

## Limitations / remaining QA

This does not claim:
- integrated LIVE screenshots at every width;
- Android/iOS device coverage;
- 200% browser/text zoom coverage;
- screen-reader or physical-print validation.

Those belong to the final QA/device lanes. A future real-device failure at one of these widths is valid new evidence and should reopen finding 15 with the exact viewport/browser/device.
