# Kita-Pakete V1 — Herbst implementation contract (#203)

Status: **reviewed source implementation target, not merged/LIVE by this document**.

The owner selected the following five already-published catalogue activities on 2026-11-13. Public `catalog.json` was checked immediately before implementation; runtime code still revalidates the current catalogue and fails closed if any member becomes unavailable or changes to an invalid sheet shape.

## Herbst – 5 Aktivitäten

Target: **Empfohlen: 4–6 Jahre**  
Physical size: **exactly 5 A4 sheets**  
Route: **`/kita/herbst`**

| Order | Catalogue ID | Current title | Purpose | Sheets |
| --- | --- | --- | --- | ---: |
| 1 | `7297970` | Kürbis mit Herbstblättern | Ausmalen | 1 |
| 2 | `8611574` | Blaetter Zaehlen | Zählen / Mengen | 1 |
| 3 | `4089571` | Herbstformen Zuordnen | Zuordnen / Wahrnehmung | 1 |
| 4 | `1481910` | H Wie Herbst Nachspuren | Buchstabe / Vorstufe Schreiben | 1 |
| 5 | `2472924` | Eichel Ausschneiden Zusammenbauen | Ausschneiden & Kleben | 1 |

Editorial instructions:
1. „Male das Herbstbild aus und erzähle, was du entdeckst.“
2. „Zähle die Blätter und trage die Anzahl ein.“
3. „Verbinde die gleichen Herbstformen miteinander.“
4. „Spure das H nach und probiere es anschließend selbst.“
5. „Schneide die Eichelteile mit Begleitung aus und setze sie zusammen.“

## Source design

- `/kita` presents **Fertige Kita-Pakete** as the primary differentiated path while keeping the ordinary catalogue/examples.
- `/kita/herbst` is a static application route served from reviewed source.
- `js/kita-packages.mjs` stores only editorial package metadata and ordered catalogue IDs. It does **not** duplicate print URLs, thumbnails or full catalogue records.
- The package page fetches fresh `/catalog.json`, resolves the five IDs in fixed order, and renders current catalogue titles/thumbnails through the existing catalogue-card renderer.
- The shared `print-basket-selection.mjs` model validates the package against the existing five-sheet limit. Missing/invalid members keep the whole-package action disabled; valid individual activities remain accessible.
- The explicit **„5 Seiten auswählen“** action replaces the current tab-scoped `Meine Drucksammlung` with the reviewed package order and opens the existing basket dialog. The page clearly states that the current selection is replaced.
- Existing coverless full-quality PNG ZIP remains the only enabled whole-package output.
- `BOOK_OUTPUT_RELEASE.combinedPrint` remains **false** under #508. The package must not enable or advertise a working one-click combined print action before that gate passes.
- No new backend, database, account, tracking identifier, PDF path or server-side ZIP is introduced.

## Safety and rights boundaries

This source change does not republish artwork and does not modify production media. Current RPi5/public catalogue data remains canonical for published files. The package page does not make new redistribution/resale/classroom-license claims; any broader institutional-use wording needs separate legal review.

The existing source/merge/LIVE boundaries remain unchanged: Draft PR → exact-head CI/review → explicit owner merge gate. No merge or LIVE action is authorized by this document.
