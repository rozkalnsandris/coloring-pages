# Malen & Lernen — editorial worksheet pilot (#202)

**Status:** source-only editorial plan. This is not published artwork, a new frontend feature, a new category contract, or permission to import content.

## Scope and classification

Use the existing catalogue, detail and `Drucken` journey. Each independent worksheet is one activity with exactly one canonical category from `metadata/categories.json`:

| Worksheet family | Canonical category | Rationale |
| --- | --- | --- |
| `Buchstaben nachspuren` | `alphabet` (Alphabet) | A letter-form exercise belongs with letter discovery. |
| `Zählen bis 10` | `lernen` (Lernen) | Counting and identifying numerals is an early learning exercise. |
| `Malen nach Zahlen` | `lernen` (Lernen) | Region-to-number and color matching is a learning exercise. |
| `Linien verbinden` / simple forms | `lernen` (Lernen) | Visual matching and pre-writing movement fit learning. |

Do not create a new category, inferred collection, taxonomy ID, site route, topic or schema under #202. Existing navigation can display these activities through `alphabet` and `lernen`. A possible future topic is editorial metadata only, not a prerequisite for this pilot. Do not relabel existing published activities without separate scope.

## Four small worksheet templates

Use original motifs, large uncluttered A4 layouts and short German instructions. The German quoted instructions below are candidate **print-visible** copy; the rest of this file is internal review guidance.

1. **Zählen / Zahl erkennen (ages ~3–5).** Show 1–5 separate, easily distinguishable large objects of the same type; one unambiguous question and three large answer numerals (exactly one correct). Candidate: three apples; choices `2 | 3 | 4`. Instruction: **„Wie viele Äpfel siehst du? Kreise die richtige Zahl ein.“** Answer key: `3`. Extend to 6–10 only after the smaller task is reviewed for legibility and counting accuracy.
2. **Buchstaben nachspuren (ages ~4–6).** One demonstrated uppercase letter, then a few large tracing repetitions on consistent writing guides. Pilot letter: capital `A`. Instruction: **„Spure das große A nach.“** Verify correct stroke geometry, guide height, baseline, start/end and enough hand space. Do not render a guessed letter shape: choose and license-check an appropriate lettering source. Before any later `Ä/Ö/Ü/ä/ö/ü/ß` release, verify genuine glyph forms, diacritics, character spacing and German spelling at actual print size.
3. **Malen nach Zahlen (ages ~4–6).** One simple original butterfly with a few **closed, large** coloring regions. Use only numbers `1`, `2`, `3`; printed key: **„1 = Rot · 2 = Blau · 3 = Gelb“**. Instruction: **„Male die Flächen nach den Zahlen aus.“** All labeled regions must use exactly one number from the key. The legend must remain readable on an uncolored black-and-white printout; intentional key colors are optional, not a replacement for text labels.
4. **Linien verbinden / Formen (ages ~3–5).** A left/right matching worksheet with at most three distinct large shapes and exactly one intended matching partner for each. Instruction: **„Verbinde die gleichen Formen mit einer Linie.“** Avoid ambiguous variants, crossing printed guidance, tightly spaced targets and maze-like complexity. Not included in the first three-sheet pilot.

Keep instructions short, readable in German and understandable with adult guidance. Avoid decorative scenes, dense textures, tiny symbols, extraneous marks, character branding and faces on nonliving objects. No photograph or borrowed copyrighted worksheet is an accepted content source.

## Three-sheet pilot — design only, no PNG generated

| Priority | Proposed German page title | Category | Orientation | Correctness oracle |
| --- | --- | --- | --- | --- |
| 1 | `Drei Äpfel zählen` | `lernen` | portrait | Exactly three apples; only `3` is a correct offered answer. |
| 2 | `Großes A nachspuren` | `alphabet` | portrait | Proper capital A with consistent writing and tracing guides. |
| 3 | `Schmetterling nach Zahlen` | `lernen` | portrait | Every region is closed and has `1`, `2` or `3`; each number matches the printed legend. |

Choose landscape only if a later composition needs it; do not squeeze a wide task into portrait for uniformity. Pilot pages are independent one-page activities, not a multi-page packet. The separate Kita packet idea (#203) is not implemented here.

## Editorial acceptance checklist for each future worksheet

- [ ] **Learning objective:** a 3–6-year-old can identify the requested task; the cognitive load and handwriting motor demands are age-appropriate. The prompt is in natural, correctly spelled German.
- [ ] **Answer correctness:** one independently checked answer/solution; count all shown objects; ensure exactly one correct numeral or shape match; no contradictory arrows/markings. For `Malen nach Zahlen`, every region is closed and every printed number exists in the complete, nonconflicting legend.
- [ ] **Letter accuracy:** checked case, diacritics, form and baseline; trace guides are visually consistent and not so small that tracing becomes impractical. In particular, verify `A` geometry and do not substitute a font missing `Ä Ö Ü ß` for later German tasks.
- [ ] **Visual simplicity:** large separated tasks/closed regions; thick high-contrast outlines; no unwanted decoration or anthropomorphized objects. Color, if present, is intentional and does not hide essential instructions.
- [ ] **Print source:** draft PNG follows `1024×1536` portrait or `1536×1024` landscape. The publication operator must create and validate the actual `2480×3508` or `3508×2480` RGB A4 master at about 300 DPI with exact white background and all four 15 mm/177 px safe bands. Do not mark an AI draft or browser preview as an A4 print PASS.
- [ ] **Physical review:** inspect a real 100% A4 print for child-readable lettering, enough pencil/crayon space, clipped strokes, unambiguous answers, and no accidental marks in margins. Record any correction to the exact version before accepting it.
- [ ] **Ownership and metadata:** confirm original artwork/provenance, accurate natural German title, one existing category, and correct print order. Publishing must use the ordinary approved content flow, not an issue/PR merge.

## Handoff and separate owner gates

1. This issue's deliverable is **only** the taxonomy, template definitions, German copy and three-sheet pilot acceptance plan above. Source CI can check docs; it cannot verify artwork, classroom usefulness or real print quality.
2. Any actual pilot page requires a separately requested original `MAKE` (and optional `EDIT`/`REMAKE`), human visual acceptance and final German title/category review. The owner may use `ZIP` → protected ADMIN upload; ADMIN prepares and validates each approved A4 master before publication. Ordered multi-page sets must follow their own reviewed publishing contract.
3. **No new PNGs, content ingest, IDs, commits of production binaries, page publication, LIVE operation, category mutation or auto-deploy** are authorized by #202. `PUBLISH` remains a fresh exact-version owner gate. A docs-only PR merge must not trigger application redeploy.

References: `AGENTS.md`, `README.md`, `metadata/categories.json`, `docs/MEDIA_STANDARD_V1.md`, `docs/CHAT_IMAGE_COMMANDS_V1.md`; related future content packet #203.
