# Topic classification review — source-only QA for #511

## Scope and evidence

The public gallery uses the explicit catalogue topics array when present. Only records without that field use the managed Topics v2 legacy title/character terms. The live catalogue and runtime topic registry belong to the RPi5 content store, not GitHub.

A public browser read on 2026-11-14 reported 494 total activities and 109 figure entries. Seven figure entries were displayed under Autos, including a candidate titled Fröhlicher Tänzer. That browser read was NOT bound to a saved catalogue SHA-256 and is NOT evidence of the present catalogue state or proof of an incorrect tag. The original topic metadata must be checked against artwork before any decision.

## Offline audit contract

The new tool at tools/coloring-pages-topic-review accepts a local, owner-authorized, read-only snapshot via --catalog and the matching canonical managed v2 --topics file. --topic is required; --category is optional. For the reported case, choose the canonical topic autos and category figuren. Use both --expected-catalog-sha256 and --expected-topics-sha256 to bind a review to exact bytes.

The report includes the two actual SHA-256 digests, total catalogue count, matched count and the ordered IDs/titles. Each match says whether it came from explicit topics or from legacy title terms. Explicit assignments with no related title/character keyword are marked as manual review candidates; this is NOT proof of a semantic error. A title may legitimately omit a visible element in the artwork.

Only local bytes are read. The tool does not contact the network, inspect images, copy production files, write a report to disk, modify records or propose automatic topic corrections. Registry parsing uses the existing coloring_pages_topics.read_registry fail-closed validation; invalid or stale snapshots yield no partial JSON output. Regression tests use synthetic activities, not production catalogue content.

## Owner-gated next step

Obtain and verify an exact catalogue snapshot through an independently authorized read-only operator path. Confirm ID, current title, full primary/secondary categories, explicit topics and image preview for each candidate. Classify each mapping as correct, wrong or requires more evidence. Any later metadata write needs a separate owner authorization and trusted production operator with lock / immutable identity checks. This PR must not modify LIVE catalogue, topic registry, uploads, media, IDs, titles or deployed code.

The existing title-correction inventory is separately maintained at docs/UI_UX_TITLE_EDITORIAL_511_13.md and is not a current LIVE snapshot.

## Case review — `3706300` (Fröhlicher Tänzer; 2026-11-14)

**Decision status: correction recommended; production apply NOT authorized.**
This case supplements the read-only #511 classification audit. It does not replace the earlier #1395 catalogue-wide review or create a new taxonomy entry.

### Exact public artwork and prior LIVE metadata evidence

- Public detail: https://ausmalwiese.de/detail.html?id=3706300
- Public preview inspected visually in Opera: https://ausmalwiese.de/media/3706300/preview.webp (1000 × 1414 web preview). It shows one smiling, dancing human with outstretched arms and sneakers, **without any car or other vehicle**. The detail page exposes an `Autos` topic badge, confirming the user-visible mismatch.
- Previous bounded owner-authorized RPi5 read-only snapshot: catalogue SHA-256 `9809c5428ee53b8409deb50cb201c71b43d1053bf32631c3e250a78f94078857` (494 activities), managed Topics v2 SHA-256 `804869a4dc44c9761280dc3653524014dcabf74131cfa59805048a275fcf96c4` (revision 2). The bound record contained:
  - ID `3706300`, title `Fröhlicher Tänzer`;
  - primary `category="figuren"` and ordered `categories=["figuren","fahrzeuge"]`;
  - explicit `topics=["autos"]`.
- The public Topics v2 registry inspected in Opera on 2026-11-14 has no `tanzen` Topic. Known `sport` and `berufe` Topics are **not** automatic substitutes for a generic dancer.

The hashes above identify a **historical exact read-only snapshot**, not an assertion that the production catalogue and registries still have those bytes at apply time. Only the public web preview was visually inspected; this is not an inspection of the private print original.

### Proposed one-record correction (owner review required)

| Field | Before (bound snapshot) | After (proposed) |
|---|---|---|
| `id` | `3706300` | unchanged |
| `title` | `Fröhlicher Tänzer` | unchanged |
| `category` | `figuren` | unchanged |
| `categories` | `["figuren","fahrzeuge"]` | `["figuren"]` |
| `topics` | `["autos"]` | remove `autos`; replacement **deferred** until owner decision |

**No unrelated fields may change** (age, difficulty, language, publish order, `pages[]`, previews, print URLs, media or activity identity). `topics=[]` is **not presumed valid for every writer**: the importer requires a non-empty explicit Topics list on new publications, while legacy catalogue entries without Topics remain supported. Confirm how the **installed protected ADMIN Catalog/Edit** represents a cleared Topic selection before choosing exact target bytes. No invalid or empty assignment should be silently forced.

### Topic decision and dependencies

The established #1395 classification policy calls for at least one **meaningful** Topic when justified, while explicitly deferring ambiguous entries rather than assigning arbitrary labels. For this artwork, `autos` is misleading. **Do not label the dancer `sport` or `berufe` merely to fill the Topic field.** Keep the replacement Topic decision as **Needs review** until an appropriate Topic is explicitly approved.

Potential separate follow-up: review the other dance-themed figure previews plus complete current Topic and Category↔Topic link registries. If the repeated subject justifies expansion, propose a new evergreen `tanzen` Topic (label `Tanzen`) linked to `figuren`. Registry/link creation and reassignment need **separate owner-gated LIVE approvals**, and this document does not request a new structural Category.

### Safe future apply and verification gates

1. Obtain separate owner authorization for a fresh bounded RPi5 read-only catalogue, Topics, Categories, link and installed protected ADMIN editor capability check. Bind exact ID and registry SHA/revisions; any drift from historical source fields returns to human review.
2. Obtain explicit owner editorial decision on replacement Topic; validate exact clearing/encoding semantics against installed Catalog/Edit API contract. Prefer the existing guarded single-ID ADMIN editor with strong `If-Match`, CSRF and shared publication lock **only if** that precise edit class is verified. Do not hand-edit the host JSON or invoke a bulk fallback.
3. Require a fresh exact **LIVE mutation authorization** for the one ID, approved before/after fields, current catalogue SHA, exact installed operator and one allowed write. Authorization is consumed on first mutation; later failure/drift means STOP without retry, rollback or cleanup.
4. Read-only postverify: ID `3706300` exists exactly once under `/figuren`, not `fahrzeuge` or `autos`; its `Autos` badge is gone; same ID, title, detailed preview/print paths and publication order. Source CI alone is not LIVE evidence.

**Boundary:** this review is docs-only. No LIVE/catalogue/registry/ADMIN mutation, image change, GitHub merge or deploy.
