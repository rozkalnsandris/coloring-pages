# Malen & Lernen — editorial templates and quality gates (#202)

Status: **GitHub-only editorial/specification proposal**, not a worksheet release, published curriculum, artwork or teacher certification. Audited against `coloring-pages@50c1d63dc3a9da8512b6e7a111f40cf123e41a59` on 2026-10-22. No new media, category, catalogue record, application UI, importer behavior, third-party learning content, LIVE or GitHub settings are introduced by this file.

## Scope and existing taxonomy

Ausmalwiese serves German-speaking families, Kitas and Vorschulen. The initial pilot is **original, low-distraction A4 PNG practice worksheets for children approximately 3–6**, with optional adult help and no assumption that every child of the same age can read, count or safely cut independently.

The existing `metadata/categories.json` already supplies `lernen` (**Lernen**) for counting, shapes, number coloring, line connection and pre-writing; and `alphabet` (**Alphabet**) for dedicated letter-tracing exercises. Seasonal themes may inform an illustration, but an educational worksheet is assigned **one canonical category** by its primary learning objective. No new category ID, router, search filter, entitlement, database or separate registration is required for this editorial pilot. If mixed learning content cannot be represented honestly by those existing categories, STOP and request a separate source contract review instead of silently changing classification.

## Four small worksheet templates

Each row is a separate *unpublished proposal*. These are **not** claims of existing catalogue items or owner-approved artwork.

| Pilot worksheet | Age guidance / category | German instructions for a teacher or child | Educational correctness and layout requirements |
| --- | --- | --- | --- |
| **Zähle die Blätter (1–5)** | Roughly 3–5, `lernen` | “Zähle die Blätter. Kreise die richtige Zahl ein.” | One unambiguous group per exercise, e.g. exactly **3** large leaves with answer options **2 · 3 · 4**; do not visually join or hide any leaf. Answer key = **3** for this example. Teacher independently recounts every group and verifies only one option is correct. |
| **H nachspuren** | Roughly 4–6, `alphabet` | “Fahre das große H nach. Schreibe danach ein eigenes H.” | One **uppercase H**, clearly dotted strokes, one consistent baseline / midline grid and sufficient room to hold a writing tool. The uppercase H has two verticals joined by a horizontal stroke; the learner's midline must actually cross that horizontal bar. A decorative dashed separator is **not** a tracing guide. |
| **Formen finden** | Roughly 3–5, `lernen` | “Finde alle Kreise und male sie aus.” | One target shape (circle), distractors (square and triangle), at most 5–7 big, separated examples with visible closed outlines. Provide a checked teacher-only expected count. No oval/ambiguous near-circle that makes scoring subjective. |
| **Linien verbinden** | Roughly 3–6, `lernen` | “Verbinde die zwei gleichen Bilder mit einer Linie.” | 2–3 disjoint pairs of simple different shapes; one unique correct target per source, generous line spacing and no pre-drawn crossing paths that imply a wrong answer. Verify matching is unambiguous, including for children who cannot read the labels. |

Optional later variants are `Malen nach Zahlen` (large numbered regions with a **small, explicit and internally consistent German color legend**) and `Zählen bis 10` only after a separate difficulty review. Do not label ordinary unnumbered coloring pages “Malen nach Zahlen”. For examples such as regions **1 = Rot, 2 = Blau, 3 = Gelb**, every region number must appear in the legend and every legend value must have one unambiguous color; missing numbers, contradictory legends and illegible micro-regions are rejection reasons.

## German alphabet and tracing QA

- Verify the pictured object's **correct German singular/plural spelling** and initial grapheme with a native-proficient reviewer; do not confuse **A – Apfel** with **Ä – Äste**, **Ö**, **Ü** or **ß**. Avoid invented labels merely to fill a letter slot. An initial sound and an initial *letter* are not always equivalent.
- Follow a single per-sheet letter family: one clearly outlined capital letter at the top and repeated capital forms on the tracing lines, **no accidental lowercase glyphs**. Unicode German umlauts must have both dots visibly separated; `ß` is not interchangeable with `B`.
- Trace glyph strokes must align with the handwriting baseline; the dotted writing guide sits at the correct optical midline, including the center bar of A/H where relevant, **not above or below the letter**. Review at **100% printed A4 size**, not by trusting a shrunk browser thumbnail.
- Avoid assigning directional arrows or stroke order unless reviewed by an educator. For younger children, permit pre-writing straight/curved lines as an alternative to full letter tracing.
- Leave space for an actual child's pencil movement. Large contours, readable glyphs and clear line spacing take priority over fitting many exercises onto one sheet.

## Fixed print and accessibility contract

An original image is prepared and owner-reviewed as a white-background PNG draft at the configured source generation size (`1024×1536` portrait or `1536×1024` landscape), with thick black outlines and intentionally colored cues only when pedagogically necessary. No tiny shading, textures, watermarks, personal data, child photographs or third-party characters without provenance.

The approved publication process, **not this spec**, prepares and validates an A4 master: `2480×3508` portrait or `3508×2480` landscape, RGB/no alpha, approximately 300 DPI, aspect-ratio-preserving artwork with **15 mm exact-white margin** on each side. The public `print.png` is the canonical full-resolution browser print/download source. A preview or `thumb.webp` is never a print master; do not re-encode print output as JPEG/PDF or stretch a worksheet to fill A4.

Before publishing, verify at 100% paper size that strokes/dots do not vanish, text and control marks are legible, orientation is correct, each target can be colored/written without touching unrelated outlines, and no decoration is mistaken for an answer. For the site UI, keep the ordinary gallery → detail → `Drucken` path, descriptive titles/alt text, keyboard accessible actions, responsive thumbnails and visible German instructions. Physical or human learning-correctness checks cannot be proved by CI alone.

## Proposed first content pilot and independent QA

The smallest useful pilot is **four separate original single-page A4 worksheets** corresponding to the four table rows. Do not automatically combine them into a composite image, a five-ID `Kita-Paket`, or a multi-page activity. A separate, explicitly approved worksheet can be multi-page only when the standard ordered 2–12-page publication contract applies; `pages[]` must be treated as one activity with its actual sheet count.

1. **Art/editorial gate:** an editor checks every exact PNG's spelling, counts, number legend, matching pairs, tracing baselines, difficulty and unambiguous answer key. Record a concise QA receipt for each worksheet (worksheet type, expected answer if any, German proofreader, date, exact reviewed version). Do not call unreviewed examples verified.
2. **Rights/quality gate:** verify original artwork and rights to distribute for family and Kita use; inspect content for age appropriateness, white safe area and print master. No personal names, student information, or implied endorsements.
3. **Technical gate:** prepare each exact approved PNG through the existing ADMIN or fresh-owner-authorized direct `PUBLISH` workflow. Validate exact A4 raster, safe margins, hashes and current category before allocating/committing immutable random seven-digit catalogue IDs. Do not mint placeholder IDs in this document or repository.
4. **Public availability gate:** only after the actual separately authorized publication, verify HTTP detail, preview and original-resolution `print.png` from real LIVE evidence. A GitHub PR/CI pass never establishes a published educational worksheet.

## Relationship to Kita-Pakete #203 and other features

The merged `docs/KITA_PAKETE_EDITORIAL_203.md` proposes **“Herbst – 5 Aktivitäten”**, including counting, uppercase H tracing and shape recognition. These are editorial slots, not already published media. They may reuse future reviewed worksheets from this pilot only after category, theme and exact LIVE availability align. #203's fifth activity is a two-page Cut & Paste, so the proposed five-activity pack contains **six A4 sheets**; do not silently count it as five. #197's separately researched immutable full-quality ZIP bundle and #206's separate five-sheet visitor basket are technical dependencies, **not** permission to package or publish this pilot.

## Acceptance checklist / STOP conditions

- [ ] Single existing category chosen correctly for each activity (`lernen` or `alphabet`).
- [ ] Every German instruction and word/picture pairing proofread.
- [ ] Unique correct answers checked independently for counting, number coloring and matching; no misleading alternate answer.
- [ ] Capital-letter form, umlaut glyphs and dashed tracing lines aligned at actual print size.
- [ ] Four **separate** original, age-appropriate worksheets approved visually; no watermark, third-party provenance gap or copied artwork.
- [ ] Exact A4 PNG, orientation, 15 mm safe zone and approximately 300 DPI validated per page.
- [ ] Media/publication authority obtained independently for each exact activity or clearly identified ordered set. No unauthorized mass import or upload.
- [ ] Current public catalogue and detail/`Drucken` route checked after publication.
- [ ] No GitHub `MERGE`, RPi5, LIVE, content import, Drive, Cloudflare, payments, settings, permissions or credentials changes are inferred from this editorial source PR.

**State of issue #202 after this document:** editorial taxonomy and first-pilot quality gates prepared **for review**. Actual worksheet artwork, educator review, publication and any new runtime feature remain separate future work. Do not mark this specification as a completed LIVE feature.
