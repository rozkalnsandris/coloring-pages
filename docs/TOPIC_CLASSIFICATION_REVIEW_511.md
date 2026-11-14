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

## Post-edit dance Topic review — 2026-11-14 (proposal only)

### Evidence and corrected baseline

- Previous #511 owner-authorized **one-record** LIVE Catalog/Edit for `3706300` was postverified on RPi5. `Fröhlicher Tänzer` remains in `figuren`, with `categories=["figuren"]` and `topics=[]`. All 494 unique IDs remained; an in-memory reverse reconstruction reproduced the exact pre-edit catalogue SHA-256, confirming only `categories` and `topics` changed. Post-edit **historical** catalogue SHA-256: `4906d9382a738a9666bea87f068a2904ea8ad5d41e22dff57aab356cd6fcae2f` (not a guarantee of present LIVE bytes). The existing earlier correction proposal above is **completed**, not a standing LIVE apply authorization.
- Read-only public Opera catalogue on 2026-11-14 had 494 activities, 109 in `figuren`. The public managed Topics v2 registry was revision 2 with 33 Topics; no Topic with ID `tanzen` existed then. This public browser snapshot is **not SHA-bound** to the RPi5 content store, so any future apply requires a fresh immutable catalogue/registry/link check.
- Public `/media/<id>/preview.webp` imagery was inspected individually for all nine entries below. All show recognisable dance poses or a ballerina. Several are near-duplicate poses or a similar male/child character, so nine IDs do **not** imply nine visually distinct designs. No original/print-master inspection was performed.

### Editorial inventory: possible `Tanzen` entries

| Public ID | German title | Artwork checked in Opera | Existing broad category from public catalogue |
|---|---|---|---|
| `3706300` | Fröhlicher Tänzer | Dancing adult, previously misclassified as `autos`; corrected | `figuren` |
| `0678119` | Tanzender Junge | Dancing adult/young male figure, raised arm | `figuren` |
| `0933115` | Coole Tanzbewegung | Dancing male character in cap/goggles | `figuren` |
| `9658233` | Lustiger Tanzsprung | Dancing male character with raised knee | `figuren` |
| `8944600` | Kleiner Tänzer | Dancing male character, dynamic pose | `figuren` |
| `6668623` | Kleiner Tänzer | Dancing boy with music note/microphone | `figuren` |
| `1592942` | Tanzen macht Spaß | Dancing boy in cap | `figuren` |
| `1069719` | Junge mit Tanzschritten | Dancing boy with musical note | `figuren` |
| `6084209` | Kleine Ballerina tanzt | Young ballerina in ballet pose | `figuren` |

The two *Kleiner Tänzer* records have different public IDs and were visually inspected as different compositions. Treat each as one activity, not as a duplicate ID. Reference previews are publicly accessible at `https://ausmalwiese.de/media/<id>/preview.webp`; do not commit media or download/archive binaries as part of this source-only proposal.

**Explicitly excluded:** `9363184` (*Tanzendes Halloween-Skelett*) is in primary `jahreszeiten` and already has explicit Topic `halloween`. Do not forcibly reclassify that seasonal artwork into an evergreen `figuren` Topic solely because its title contains `tanz`.

### Proposed taxonomy decision — requires owner approval

- Proposed **Topic**, not a Category: stable ID `tanzen`, German label **Tanzen**, `kind=evergreen`, linked to existing `figuren` via the protected Category↔Topic registry. A neutral music/dance icon (e.g. `🎶`) and precise `legacy_terms` need explicit owner/registry-schema review. Do not activate broad title-substring fallback until checking false positives on the entire catalogue and seasonal precedence.
- The nine entries above are **candidates for individual owner review and explicit assignment**, not a production apply manifest. Preserve each ID, original title, page structure, primary/secondary Categories where correct, other valid ordered Topics, print/media URLs and publication dates. The corrected `3706300` may receive `topics=["tanzen"]` only **after** the new Topic/link exists and its current before-state is revalidated.
- Distinct illustration styles are limited; review whether user-facing discovery quality benefits from nine similar dance illustrations before release. Do not invent a second Topic for generic music or change unrelated category boundaries.
- The earlier #1395/#1396 bulk classification approval and apply concern different exact snapshots. They **do not** authorize the new `tanzen` registry creation or any of these new metadata writes.

### Independent authorization gates

1. Owner decides whether the proposed evergreen `tanzen` Topic/`figuren` link should exist. Any selected icon/legacy terms and Category↔Topic schema must be reviewed as an exact source proposal, not inferred from a chat or this document.
2. Obtain separately authorized fresh read-only RPi5 category/topic/link snapshots (SHA-256 and revisions), complete catalogue snapshot digest, and validate the nine IDs' actual current memberships/artwork. One public-browser capture is insufficient for a production manifest. Treat drift as a new review, not an automatic rewrite.
3. Create an exact per-ID reviewed before/after manifest (include untouched fields, no duplicates) and obtain separate explicit LIVE owner authorization for registry/link creation and later bounded catalogue edits. Existing protected ADMIN manager and editor are the preferred trusted operators only after installed identities/lock/capability checks. Each authorisation is single-use; no retry/rollback/fallback writes.
4. After authorized LIVE actions, read-only verify the registered Topic and link, nine reviewed memberships, public `figuren` filters and `/detail.html?id=3706300` unchanged print/media links. This document and any docs-only CI are **not** LIVE proofs.

**No mutation is authorized by this source-only evidence.** No Topics, links, catalogue, media, ADMIN, image, runtime or deployment changes are part of this PR.
