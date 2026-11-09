# #186 — compact mobile category discovery

Status: **source/UI proposal only; no production or print certification**.
Base: `coloring-pages/main@7336e1807b7ae6ba276b3772ca3ab69f5d014a71`.

## Read-only audit and design choice

- **Keep:** search-first hero, the existing full-size illustration, seven category groups and their topics, newest gallery, popular/trending, native disclosure controls, detail preview, A4 print/PNG actions, consent and legal links. No new tracking, API, framework or print change.
- **Change first:** under 541 px the existing category navigation becomes seven full-width rows. At approximately 412 px it pushes the gallery well below the first screen. Use two compact columns at 361–540 px; an opened native `details` occupies the entire row and shows two columns of topic links.
- **Leave unchanged:** below 361 px use the existing one-column fallback, and above 540 px use existing desktop/tablet grids. A prior mobile-hero sizing correction (#215) stays intact.
- **Reject the bolder alternative:** replacing the hero and category browser with a new filter-chip/navigation system would create more interaction/JS risk, risk losing topic discoverability and redo earlier #186 improvements, without evidence of better completion.

## Before / after responsive wireframe prototypes

412 px baseline:

```text
[ Search .................. ]  [Überrasch mich!]
[               Hero illustration               ]
[ Tiere ........................................ ]
[ Fahrzeuge .................................... ]
[ Figuren & Fantasie ........................... ]
[ Obst & Gemüse ................................ ]
[ Natur & Weltraum ............................. ]
[ Feste & Jahreszeiten ......................... ]
[ Lernen & Basteln ............................. ]
[ Neue Malvorlagen / gallery ................... ]
```

412 px proposed (closed / open):

```text
[ Search .................. ]  [Überrasch mich!]
[               Hero illustration               ]
[ Tiere ............... ][ Fahrzeuge .......... ]
[ Figuren & Fantasie .. ][ Obst & Gemüse ...... ]
[ Natur & Weltraum .... ][ Feste & Jahreszeiten ]
[ Lernen & Basteln .... ]
[ Neue Malvorlagen / gallery ................... ]

Tap/keyboard Enter on "Tiere":
[ Tiere (expanded across both columns) ........ ]
[ Alle Tiere ........... ][ Dinosaurier ........ ]
[ Meerestiere .......... ][ Bauernhof .......... ]
```

1440 px baseline **and** proposed:

```text
[ Brand/nav ................... Search / actions ]
[ Hero/title/search ................ Hero artwork ]
[ Tiere ][ Fahrzeuge ][ Figuren ][ Obst/Gemüse ]
[ Natur ][ Jahreszeiten ][ Lernen ]
[ Neue Malvorlagen / gallery ................... ]
[ Entdecken / trend / popular .................. ]
```

## Bounded responsive prototype QA

A standalone **structural mock** of this category component was rendered with headless Chromium; these measurements are **not claimed as full-site or LIVE screenshots**. Browser viewport 412 px: collapsed category stack height 634 → 336 px; gallery entry top 1089 → 791 px in the mock (about 298 px earlier). Summary hit areas: 82 → 76 px; the open group spans 380 px and its two topic columns fit without horizontal overflow. At 1440 px the baseline and proposed category stack both measured 241 px with four columns; no overflow. Existing topic links still have at least 44 px minimum height.

## Acceptance and remaining QA

- Source tests assert unchanged search/gallery/rankings, native category/topic markup, consent, detail multi-page switcher and A4/PNG actions, plus responsive rules and cache invalidation.
- Since no JS, catalogue handling, detail/print or consent source changed, those user flows are regression surfaces rather than a new implementation claim.
- Before merging: exact-head CI/reviews, real 412/1440 viewport screenshots and keyboard/pointer testing on the integrated pages, category expand/collapse and long labels, multi-page preview, original A4 PNG download/print and privacy-choice flow. No source test alone proves real-browser completion or legal compliance.
