# Kita-Pakete — editorial pilot and print-quality contract (#203)

Status: **source-only editorial proposal, not a published pack**. No catalogue IDs, new artwork, archive, landing page, image rights or classroom licensing status are approved by this document. Based on repository source `main@45a96c6d1450272e95da7633df35678c54cd5650`, 2026-10-22.

## Pilot: Herbst — 5 Aktivitäten

A free, teacher-guided seasonal practice sequence aimed at children **3–6** in German Kitas and Vorschulen. The intended print order uses **five distinct activities, six A4 sheets** because the fifth Cut & Paste activity requires a two-page base-and-cutouts set. *Five activities must not be misrepresented as five sheets.* The educator can skip or adapt tracing/cutting according to developmental readiness; adult supervision is needed for scissors and small components.

| Order / sheets | Activity (German) | Learning goal and teacher instruction | Catalogue fit and review |
|---|---|---|---|
| 1 / A4 sheet 1 | **Herbstbild ausmalen** | Recognize autumn objects; choose and name colors. “Male das Herbstbild aus und erzähle, was du siehst.” | Existing `jahreszeiten` entry, simple outlines, no incidental clutter; verify original art/metadata |
| 2 / A4 sheet 2 | **Blätter zählen (1–5)** | Count one-to-one and match numeral to an unambiguous leaf set. “Zähle die Blätter. Kreise die richtige Zahl ein.” | `lernen`; educator verifies counts/answer key before approval |
| 3 / A4 sheet 3 | **H wie Herbst nachspuren** | Trace an uppercase **H**, then a short straight stroke sequence. “Fahre das große H nach.” | `alphabet` or `lernen`; verify letter glyph, baseline, stroke direction and adequate spacing |
| 4 / A4 sheet 4 | **Herbstformen erkennen** | Recognize large circle/triangle/square silhouettes without ambiguous overlaps. “Finde und markiere alle Kreise.” | `lernen`; verify target count and clear unique shapes |
| 5 / A4 sheets 5–6 | **Herbstfigur ausschneiden und kleben** | Assemble a simple shape from pre-drawn components. “Lass dir beim Ausschneiden helfen. Klebe die Teile auf die Vorlage.” | Approved **two-page** Cut & Paste activity only: page 1 base, page 2 detachable cutouts. Physical fit and safety QA required |

This is a *pedagogical specification*, **not** a claim that those five exact worksheets already exist or were published. In particular, never substitute a one-page image for an unapproved two-page Cut & Paste activity merely to fit a five-sheet label. If a complete matching five-activity set is not in the currently published catalogue, **keep the proposed pack unpublished** or visibly offer individual available pages, without pretending the pack has been assembled.

## Existing taxonomy and minimal data contract

The current `metadata/categories.json` includes `jahreszeiten`, `lernen`, and `alphabet`; no new category or database is needed. Catalogue records already have `id`, `title`, `thumb`, `print`, and for multi-page activities `pages[]` with ordered `print` paths.

A later approved *editorial-only* pack definition may be a small reviewed source manifest with ordered activity ID references and an educator-facing description, for example:

```json
{
  "schema": "ausmalwiese.kita-paket.v1",
  "id": "herbst-5-aktivitaeten-v1",
  "title": "Herbst – 5 Aktivitäten",
  "language": "de",
  "age": "3-6",
  "activity_ids": [],
  "expected_activities": 5,
  "expected_sheets": 6,
  "access": "free"
}
```

`activity_ids: []` is deliberately **not a publishable pack**. A later separately approved change must replace it with exactly five *verified* currently published, distinct catalogue IDs in the pedagogical order and verify that their ordered sheet counts sum to exactly six. Do not invent plausible seven-digit IDs, use unpublished drafts, reinterpret `pages[]` as separate activities, or backfill dates/reuse media from an unrelated environment. Media and actual published catalogue are canonical on RPi5; GitHub source alone does not establish LIVE availability.

The pack metadata would reference existing approved activities; it does not duplicate PNG originals or build a ZIP. If any referenced activity or required page disappears, fail closed (withdraw or hide the incomplete pack) until separate editorial review. No silent truncation, fallback to a different page, or automatic regeneration.

## Teacher-facing German text — proposed, not live

**Herbst – 5 Aktivitäten**

“Fünf einfache Herbst-Aktivitäten zum Ausmalen, Zählen, Nachspuren, Formenfinden und Ausschneiden. Für Kinder von etwa 3 bis 6 Jahren, mit Begleitung durch Erwachsene. Das Bastelblatt besteht aus zwei Druckseiten. Insgesamt: **6 A4-Druckseiten**.”

Labels for a future approved pack page: **“Aktivitäten einzeln ansehen”**, **“Druckvorlage öffnen”**. Only after a separately approved, actually hosted and verified ZIP exists: **“Alle 6 A4-PNGs als ZIP herunterladen”**. Do not show an enabled ZIP button, an invented file size, or **“Alles drucken”** before the corresponding functional and tested capability exists.

## Print and packaging boundaries

The already deployed **single-activity** flow opens `detail.html?id=<catalog-id>` and prints using existing `print.html` for the activity's own `pages[]`. It **does not** combine different activities into one print job. Until a separately reviewed cross-activity print implementation exists, offer a sequential per-activity teacher workflow: choose activity, open its detail, print/download its existing full-quality `print` PNG page(s), then go to the next. Preserve the ordered base/cutout sheets.

Use the common free static-bundle design from merged #197 (`docs/BUNDLE_PNG_ZIP_RESEARCH_197.md`) if later packaging is approved. That research recommends an **offline-prebuilt, verified immutable ZIP containing the *unchanged public full-quality print PNG bytes*** (ZIP STORE; never watermarked `preview.webp`, thumbnail, private master, JPEG or PDF). #197's example 10-sheet product and #206's five-sheet interactive basket are **different product constraints**: neither silently changes this educational pilot's honest **six-sheet** count. Agree the pack-size and shared implementation before creating anything. A separately authorized publisher must check each selected PNG SHA-256/byte size, ordered archive members, actual source availability, cancellation/failure handling, and public final ZIP verification.

Print fidelity follows `docs/MEDIA_STANDARD_V1.md`: exact A4 masters **2480×3508 portrait / 3508×2480 landscape**, approximately 300 DPI, exact-white 15 mm safe margin, image aspect ratio unchanged. Neither a ZIP nor any HTML preview may downscale or re-encode print members. Cut & Paste needs its separate two-page assembled-fit + human print/cut/glue acceptance gates; documentation is not physical QA.

## Editorial acceptance checklist

- [ ] Owner/teacher confirms theme, language, activity progression and age suitability.
- [ ] For each of five positions, verify one *actual* published activity ID in the fresh production catalogue, exact German title, category, ordered sheet count, full-quality public print URLs, availability, original/licensed provenance, and classroom-use rights.
- [ ] Educator checks mathematically correct counting answer, clear shapes, correctly formed/traced uppercase H, usable handwriting lines and child-suitable scissor skills; no errors in German instructions.
- [ ] Verify exact print order **1, 2, 3, 4, 5a base, 5b cutouts**, portrait/landscape handling and A4 safe bounds. Two-sheet Cut & Paste must pass assembled geometry and actual physical QA.
- [ ] Validate desktop/mobile accessible navigation, keyboard focus, semantic headings, correct empty/missing page messaging, free/single-page alternatives. Do not claim one-click all-pages print without technical validation.
- [ ] Show ZIP CTA only after separate actual ZIP publication and hash/HTTP verification. No PDF, paid checkout, visitor tracking, new account, or RPi5 service as part of this editorial pilot.
- [ ] Obtain rights/legal confirmation for **Kita/classroom use and packaging/redistribution**. Free personal downloads do **not** automatically permit resale, rehosting or commercial redistribution.

## Future gates and dependencies

#203 owns the **education/editorial pack** and does not develop a parallel ZIP/print system. #202 owns the worksheet templates and educational answer-correctness standards. Merged #197 owns the reusable static bundle architecture; #206 owns a different visitor-built five-sheet print basket. #199 can reuse the resulting reviewed export model. None currently constitutes permission to publish this pack, create new content, or alter LIVE.

Next scope, only if separately authorized: (1) editorial five-ID verification and rights review; (2) choose sequential print links versus a separately implemented common ZIP packer; (3) source PR for any actual pack manifest/page, tests and CI/review; (4) explicit exact-head merge and distinct owner authorization for actual content/ZIP staging, RPi5 access or public availability. This research change alters **only this Markdown document**, no settings, secrets, LIVE services, merged code, or public content.

**Do not mark #203 as a launched Kita-Paket on the strength of a documentation PR.**
