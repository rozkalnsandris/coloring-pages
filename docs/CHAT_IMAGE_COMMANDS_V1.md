# Chat image commands v1

## Goal

Make the normal owner workflow for creating and publishing one coloring activity as short as possible while preserving the existing media and content-ingest trust boundaries.

Normal happy path:

```text
MAKE lapsa
→ ChatGPT generates one coloring-page PNG draft
PUBLISH
→ owner approves the exact latest draft
→ deterministic CPU/Pillow white cleanup + A4 print-master preparation
→ read-only validation with exact print-master SHA-256 + byte size
→ determine one valid category
→ freeze page ID + validated print-master SHA-256 + byte size + category
→ prebuild + validate manifest
→ Drive staging
→ trusted RPi5 verify/import
→ required public verification
→ PASS and stop
```

`UPSCALE-PRINT` and `VALIDATE-PRINT` remain available as optional manual inspection/debug commands, but they are no longer required owner steps in the normal publication path.
The commands below are a project conversation convention. They do not replace GitHub policy, the media standard, or the Chat-to-Drive ingestion contract.

## Commands

### `MAKE <subject>`

Immediately generate one new coloring-page candidate using everything after `MAKE` as the subject or scene.

Examples:

```text
MAKE lapsa
MAKE lapsa mežā pie sēnēm
MAKE ugunsdzēsēju mašīna pie stacijas
MAKE random
```

`MAKE random` is a special case: ChatGPT chooses the subject/scene itself and immediately generates a project-suitable coloring-page candidate. It must not ask the owner to choose a topic first. The random choice still follows the complete default generation contract below, including the 3–6 age target, canonical canvas sizing/orientation, simple printable composition and protected-character rule. `random` never means a generic illustration outside the coloring-pages project.

Default generation contract:

Interpretation rule:

- everything after `MAKE` defines the requested content; treat it as the complete brief, not merely inspiration for a richer scene;
- do not invent extra scenery, props, characters, decorations, facial features, text or story elements unless they are required to satisfy the request;
- when the request is short, prefer the simplest valid interpretation.

Prompt-construction rule:

- before calling image generation, reduce the request to a concise internal brief ordered as: **purpose/subject → composition/orientation → line-art style → constraints/exclusions**;
- prefer a short, explicit prompt over a long descriptive prompt;
- state important exclusions directly, especially no extra text, no logos/watermarks, no unwanted background elements and no unrequested facial features;
- use the image-generation output-size control for the chosen canonical canvas whenever that control is available instead of relying only on prompt wording.

Preschool simplicity profile (default for ordinary coloring pages):

- primary age target: 3–6 years;
- one clear focal subject by default;
- clean white background by default;
- add no supporting elements unless they materially help identify the requested subject/scene;
- when supporting context is genuinely needed, use at most **two** large, simple supporting elements by default;
- no decorative filler: no extra clouds, grass tufts, bushes, fences, stars, sparkles, stones, flowers, signs, textures, repeated tiny objects or scenery added merely to make the page look fuller;
- use large simple silhouettes and a small number of large closed coloring regions;
- thick, clean, high-contrast contours;
- minimal interior line divisions;
- avoid cross-hatching, texture hatching, dense patterning, tiny repeated detail, complex wheel/engine/mechanical detailing, or ornamental clutter;
- keep ample white space around the subject;
- keep the complete subject visible and uncropped.

Faces and anthropomorphism:

- animals/people may have simple expressions when appropriate;
- **inanimate subjects** such as vehicles, buildings, tools, furniture and household objects must have **no eyes, mouth, face or anthropomorphic expression by default**;
- add eyes/mouth/faces to an inanimate subject only when the owner's request explicitly asks for a character, a face, or a smiling/cartoon version;
- never infer a face merely from words such as `cute`, `child-friendly`, `cartoon` or `random`.

Canvas/orientation:

- output PNG on either exact `1024×1536` portrait (2:3) or exact `1536×1024` landscape (3:2);
- the selected dimensions describe the whole page/canvas, not the subject;
- choose orientation from the natural shape of the requested composition;
- wide subjects such as cars, tractors, trains, buses, fire engines, ambulances and aircraft normally use landscape;
- do not shrink a wide subject into portrait merely to make room for scenery;
- important artwork must stay inside comfortable page margins.

Color/style:

- ordinary coloring pages default to black line art on white;
- no unnecessary grayscale shading or filled dark backgrounds;
- preserve intentional color only when the requested worksheet/activity requires color;
- no watermark;
- no unnecessary text; letters, numbers, labels or captions appear only when explicitly requested or intrinsically required by the learning activity.

Worksheets/activities:

- for mazes, matching, cutting, tracing and similar tasks, include only the elements necessary to perform the activity;
- decorative scene elements do not count as task content and should be omitted;
- optimize for a preschool child being able to understand the task visually without extra explanation.

### `CUT <subject>` — two-page Cut & Paste draft (short alias)

`CUT Fledermaus` is shorthand for `MAKE Cut & Paste Fledermaus`. The default flow is deliberately simple: **(1) ChatGPT creates one original colored character concept with ImageGen, (2) the owner vectorizes it externally and returns the SVG file(s), (3) from that handoff onward ChatGPT uses only the supplied SVG geometry to build the two A4 sheets.** Do not redraw or regenerate the accepted character with ImageGen after SVG handoff. Page 1 contains only the base/body; page 2 contains only the detachable parts. No small assembled reference is printed on page 1. Preserve the SVG shapes, colors and proportions; use translation and, when required for physical fit, one consistent uniform scale across the complete activity. Use [Cut & Paste production playbook](CUT_PASTE_PLAYBOOK_V1.md) for print alignment and physical checks. `CUT` is an **authoring convention**, not a production publishing/external action. Cut & Paste has no global publication hold. Publication still requires a fresh owner `PUBLISH` for the exact final two-page version after the required art/geometry/print/physical QA. This does not modify standard single-page `MAKE`.

**Obligāta secība pirms CUT A4 finalizācijas:** vispirms ImageGen izveido tikai māksliniecisko konceptu. Kad īpašnieks atsūta vektorizēto SVG, tas kļūst par autorēšanas avotu un ImageGen šai versijai vairs netiek izmantots. No SVG nosaki pamatni, griežamās detaļas, kopīgo mērogu un paredzētos līmēšanas enkurus; aprēķini `ASSEMBLED_FIT` pilnam salikumam. Pēc vietnes faktiskās `js/print.js` transformācijas tam jāietilpst portreta A4 `x=17..193 mm` (**max 176 mm platumā**), `y=17..256 mm` (scale=1.0). Divas atsevišķi derīgas A4 lapas NAV saliktā objekta tests. Tikai ImageGen rastrs = `ART_CONCEPT_ONLY / ASSEMBLED_FIT=UNVERIFIED`. Pārsniegts izmērs vai nav mērījuma = `ASSEMBLED_FIT=FAIL / STOP`; labo SVG-derived kopīgo mērogu/enkurus un atvasini abas lapas no jauna. [Precīzs pre-export līgums](CUT_PASTE_PLAYBOOK_V1.md).

Two-page **Cut & Paste** special case (only when explicitly requested with `MAKE Cut & Paste <subject>` or equivalent wording; ordinary `MAKE` remains one standard coloring-page draft):

- Create one coherent character concept with ImageGen, then wait for the owner-provided SVG handoff. After handoff, define the base and each detachable part from those SVG vectors only; no ImageGen redraws for that accepted version.
- Render exactly two ordered worksheet drafts: **page 1 = base/body only; page 2 = detachable cut parts only.** Do not print a small assembled example on page 1. A diagnostic assembly may exist separately for QA, but it is not part of either worksheet page.
- Current Ausmalwiese `js/print.js` applies `fitA4InkBounds` with real A4 visible-ink limits **x=17..193 mm, y=17..256 mm** (portrait). Keep all printed ink inside that rectangle at `scale=1.0`; A4 is 297 mm high, so **41 mm** stays below the drawing for footer/gap/paper safety.
- At 300 DPI, use `px = mm × 300 / 25.4` as the raster estimate: the 15 mm white band is about **177 px**, the 17 mm ink boundary about **201 px**, and the 256 mm lower boundary about **3023 px**. The browser computes the exact physical fit with its own `297/3508` and `210/2480` ratios; validate that `print.js` returns **scale exactly 1.0** even with pixel rounding.
- Preserve the supplied SVG shapes, colors and proportions across both pages. Prefer translation only. If the complete assembled figure cannot fit, one **uniform shared scale** may be applied consistently to the base and every detachable part; never shrink only one sheet or one wing/part independently.
- Image generation supplies only the pre-vectorization art concept. Exact millimetre positions and final A4 rasterization are a **deterministic SVG authoring/export and QA task**. `PUBLISH` remains a separate owner command and must validate the **exact final** pages; physical cutting/gluing and owner visual review remain human gates.
- Detailed bounds and print proof: [Cut & Paste A4 placement](CUT_PASTE_A4_PLACEMENT_V1.md), [Cut & Paste assembly](CUT_PASTE_ASSEMBLY_V1.md), and [Cut & Paste QA](CUT_PASTE_QA_V1.md).

Examples of the default interpretation:

- `MAKE dino` → one simple dinosaur, white background, no scenery;
- `MAKE traktors` → one simple tractor, no eyes, no mouth, white background;
- `MAKE ātrā palīdzība` → one recognizable ambulance, no face and no decorative city scene unless requested;
- `MAKE lapsa mežā pie sēnēm` → one fox plus only the minimum large forest cues needed to satisfy “mežā pie sēnēm”, not a dense forest scene;
- `MAKE random` → choose a simple original subject that naturally works as a mostly isolated preschool coloring page; do not use `random` as permission to create a busy scene.

Originality/public-use rule:

- create an original illustration suitable for public project use;
- if the requested subject would require directly copying a protected branded character, preserve the general role/theme but create an original character instead.

The canonical import gates remain in `docs/MEDIA_STANDARD_V1.md`. A generated candidate is not published merely because it was generated.

If the requested subject would require directly copying a protected branded character, preserve the theme or role but create an original character instead for the public catalogue.

### `REMAKE`

Generate a new composition for the same subject using the same project art standard and preserve the current canonical portrait/landscape canvas unless the owner requests an orientation change.

A wide vehicle or other horizontal composition should normally use the exact `1536×1024` landscape canvas; a vertical composition uses `1024×1536` portrait.

`REMAKE` does not approve or publish either the old or new image.

### `EDIT <instruction>`

Edit the exact latest generated coloring-page candidate according to the instruction while preserving unrelated parts of the image where practical.

Examples:

```text
EDIT mazāk detaļu fonā
EDIT resnākas kontūras
EDIT noņem mākoni labajā augšējā stūrī
```

The edited result becomes the latest draft candidate. Preserve its current exact `1024×1536` portrait or `1536×1024` landscape canvas unless the owner requests an orientation change; do not use automatic output sizing. `EDIT` is not publication approval and invalidates any earlier manually prepared/validated print master.

`REMAKE` likewise invalidates any earlier manually prepared/validated print master for the affected page/set. A later `PUBLISH` always prepares and validates fresh print master(s) from the exact latest draft/set.

### `UPSCALE-PRINT` (optional manual inspection)

This command is optional. Transform the exact latest generated draft/page set without asking the image model to generate or redraw anything. Normal publication invokes the same preparation automatically inside `PUBLISH`.

Use `tools/coloring-pages-print-master prepare <draft.png> <print-master.png>` or an exact equivalent execution of that reviewed helper. The helper:

- accepts PNG only;
- composites transparency onto white;
- normalizes near-neutral bright AI whites to exact `#FFFFFF`;
- preserves source aspect ratio;
- reserves a 15 mm exact-white artwork-safe margin from every A4 edge (177 px at 300 DPI), then centers the resized artwork on an exact `2480×3508` portrait or `3508×2480` landscape white A4 canvas, matching the draft orientation;
- uses Pillow `Resampling.LANCZOS`;
- applies the reviewed conservative `UnsharpMask(radius=0.45, percent=35, threshold=3)`;
- performs a final near-white normalization after resampling;
- writes PNG with 300×300 DPI metadata;
- never overwrites the source draft.

This is deterministic interpolation/print preparation, not AI detail recovery. It grants no content publication authority.

For an ordered multi-page activity, every page must receive its own print master and the page order must remain unchanged.

### `VALIDATE-PRINT` (optional manual inspection)

This command is optional. Read-only validate the latest manually prepared print master(s) with `tools/coloring-pages-print-master validate <print-master.png>`. Normal publication invokes this validation automatically inside `PUBLISH`.

PASS requires:

- PNG;
- exact `2480×3508` portrait or `3508×2480` landscape geometry;
- complete 15 mm exact-white artwork-safe bands on every page edge;
- RGB/no alpha;
- approximately 300×300 DPI metadata;
- exact `#FFFFFF` across the complete outer page border.

The validator prints exact byte size and SHA-256. A manual validation failure is diagnostic only and grants no publication authority; normal `PUBLISH` still prepares and validates fresh print master(s) itself. A later `EDIT` or `REMAKE` invalidates any earlier manual PASS, but no manual `UPSCALE-PRINT → VALIDATE-PRINT` rerun is required before `PUBLISH`.

`OK` is intentionally not a publication command. It is treated only as a normal conversational acknowledgement so it cannot accidentally authorize content ingestion.

### `PUBLISH`

`PUBLISH` is the single normal publication command. It is explicit owner approval of the exact latest generated draft page or exact ordered draft set in the current conversation. The lower-resolution generation draft is never the published byte identity: `PUBLISH` first derives and validates fresh A4 print master(s) deterministically.

`PUBLISH` is self-bootstrapping. It must not require `START coloring-pages`, `SYNC coloring-pages`, a second generic `PUBLISH`, or a new conversation/session as a routine prerequisite. The command itself performs the minimum-sufficient fresh repository/rules/runtime preflight needed for publication and then continues immediately when the required capabilities are available.

`PUBLISH <descriptor>` has the same authority when the descriptor unambiguously identifies one draft/version in the current conversation. For example, `PUBLISH traktors ar acīm bez mutes` approves that exact unambiguous draft and must not be converted into a request for the owner to send `PUBLISH` again.

Before saying that Drive, RPi5, a connector, plugin, app, remote action or other required publication tool is unavailable, inspect the capabilities actually exposed in the current conversation. Treat that discovery as read-only preflight. Do not infer current unavailability from a previous turn, another ChatGPT surface, Memory, or an earlier error. When an applicable connected action exists, use it rather than stopping with a generic "tools are unavailable" response.

If a required action remains genuinely unavailable after fresh capability discovery, STOP before the first mutation and report the exact missing capability plus the minimum owner action needed to make it available. Also state explicitly whether any mutation occurred and whether the `PUBLISH` authorization was consumed. Do not redirect to `START` as a substitute for missing publication tooling.

The `PUBLISH` chain is sequential and fail-closed:

1. prepare every exact latest draft with `tools/coloring-pages-print-master prepare` (or an exact reviewed equivalent);
2. validate every prepared master with `tools/coloring-pages-print-master validate`;
3. if any preparation or validation fails, STOP before the first Drive/content mutation;
4. choose exactly one valid category;
5. read fresh LIVE catalogue state and allocate one random seven-digit new-publication ID from `metadata/id-policy.json`; the candidate must be absent from the LIVE catalogue and distinct from any other candidate already allocated in the same local publish batch before any mutation;
6. freeze that activity/page ID, the ordered page count, SHA-256 and exact byte size of every validated print master, category and required catalogue metadata;
7. fully materialize and locally validate the complete v1/v2 manifest;
8. before the first Drive mutation, freshly verify only the existing Drive ingest/import runtime: the installed Drive ingest operator must match current `RPi5_main/main` source and its pinned `tools/coloring-pages-import` consumer blob must match the current ingestion/importer contracts; any mismatch means STOP before the first Drive write and requires separately reviewed source/LIVE repair;
9. materialize the exact prepared PNG page(s) and already-built manifest as runtime-generated top-level file references for the connected Google Drive upload action. The connector boundary must receive `file_uri` references; bare file IDs, inline Base64, arbitrary URLs and raw local paths at the connector boundary are forbidden. All required local artifacts must exist and be frozen before the first Drive mutation;
10. use exactly one staging surface: the connected Google Drive `upload_file` action to the exact bound `pending/` folder ID. Upload PNG page(s) first in order and the prebuilt manifest last. Verify each successful response/readback against the requested filename, MIME type and parent folder. Connector success proves staging only;
11. run the trusted RPi5 Drive verify/import operator once. That ingest operator remains Drive-to-RPi5 pull-only and performs the contract-required catalogue, derivative and public-HTTP proof internally;
12. when the ingest operator returns `COLORING_PAGES_DRIVE_INGEST=PASS`, treat it as terminal publication success, immediately report `PASS`, and stop.

Do not invoke arbitrary host `rclone`, the legacy RPi5 stage sender, a second staging surface, or Base64-over-RDC as an alternate production path. After the first Google Drive upload attempt, any staging/file-handoff/operator error is a fail-closed STOP without retry, rollback, overwrite, cleanup or surface switching. Do not run discretionary post-success diagnostics, repeated health checks, external/public HTTP rechecks, extra catalogue scans, Drive archive/delete, cleanup or unrelated runtime verification after trusted ingest-operator PASS.

The category is selected from the canonical registry in `metadata/categories.json`. Current category IDs are:

- `tiere` — Tiere;
- `fahrzeuge` — Fahrzeuge;
- `alphabet` — Alphabet;
- `lernen` — Lernen;
- `figuren` — Figuren & Helden;
- `jahreszeiten` — Jahreszeiten & Feste.

### New-publication ID allocation

New Chat publications use an opaque technical ID that deliberately carries no type/topic/category semantics:

```text
NNNNNNN
```

The canonical machine-readable policy is `metadata/id-policy.json`. During `PUBLISH`, generate exactly seven decimal digits independently for each activity, for example `0427183`. There is no shared sequence, no "next number", and no highest-ID scan. Read fresh LIVE `catalog.json` and require the candidate to be absent before any Drive/content mutation. When several independent publication candidates are being prepared in the same local batch, their IDs must also be distinct from each other.

A collision found before the first mutation is handled simply by generating another random seven-digit candidate and checking again. Existing descriptive, sequential or otherwise legacy IDs remain immutable and do not participate in allocation. Human-facing meaning stays in `title`, `category` and other metadata, not in the ID. Any collision or identity drift discovered after mutation begins remains a fail-closed STOP.

When exactly one category clearly fits the approved page, choose it automatically and include it in the frozen manifest metadata. If more than one category is plausible, or none of the current categories fits, STOP before Drive upload and ask the owner to choose an existing category or create a new category through a reviewed source change. Never use a silent default category.

After those values are frozen, the complete JSON manifest must be materialized and validated locally before any Drive write. Do not upload any PNG first and then attempt to construct the manifest. Single-page v1 stages its PNG then manifest. Multi-page v2 stages all 2–12 ordered PNG pages in ascending index order and the single manifest last; only manifest **preparation** moves before the first mutation.

Only after the frozen identity, metadata, and prebuilt manifest all pass preflight does the approval bind to the reviewed content-ingest operation.

`PUBLISH` itself must produce a current successful validation for every page before the first content mutation. A prior manual `UPSCALE-PRINT` or `VALIDATE-PRINT` is not required and is not publication authority. The importer contract remains authoritative for ingestion, while the Chat authoring layer binds only the freshly validated A4 print-master bytes rather than the lower-resolution generation draft.

The authorized path is only:

```text
exact approved page or ordered page set
→ exact PNG page(s) + prebuilt manifest in approved Drive pending/
→ trusted RPi5 verification of every page
→ one coloring-pages importer invocation for the activity
→ public catalogue/media verification
```

For multi-page v2, page filenames are `<id>-1.png`, `<id>-2.png`, … and every manifest page entry binds its exact index, filename, SHA-256 and byte size. Historical `RPi5_main` activation revisions prove that v2 was activated, but they do not prove current runtime eligibility. Before the first Drive mutation, freshly verify that the installed `/usr/local/bin/coloring-pages-drive-ingest` Git blob matches the current `RPi5_main` operator source and that the importer blob at the operator contract’s pinned consumer source revision matches current `coloring-pages/main` `tools/coloring-pages-import`; any mismatch is a STOP requiring a separately reviewed host repin/install.

`PUBLISH` does **not** authorize:

- a different generated image;
- overwrite of an existing page ID;
- Drive archive/delete;
- application deploy;
- Cloudflare/DNS/tunnel changes;
- secrets, credentials, permissions or repository settings;
- cleanup, rollback or an alternate mutation path.

If there is ambiguity about which page/page set is approved, if any approved page bytes cannot be bound exactly, if category selection is ambiguous, if the intended activity ID already exists, or if state drifts after mutation begins, STOP rather than guessing or retrying.

## Conversation behavior

The intended human interaction is deliberately terse:

```text
User: `PUBLISH`
ChatGPT:
→ derive fresh exact A4 print master(s) without generating new artwork
→ validate and freeze exact SHA-256 + byte size
→ determine one allowed category
→ prebuild/validate manifest
→ one preselected Drive staging upload surface for PNG(s) + manifest
→ trusted RPi5 pull + SHA verification + immutable import + required public verification
→ operator PASS is terminal: report PASS and stop
```

If the image needs work before publication:

```text
User: REMAKE
```

or:

```text
User: EDIT vienkāršāks fons
```

Because the image-generation surface may return the generated draft without an additional text message, the stable next command for an accepted draft is simply `PUBLISH`. Preparation and validation remain mandatory gates, but they run inside that one command.

The normal publication commands to remember are:

```text
MAKE / REMAKE / EDIT → PUBLISH
```

Optional troubleshooting/inspection remains available as `UPSCALE-PRINT` and `VALIDATE-PRINT`.
## Relationship to existing contracts

This command layer is intentionally thin:

- `docs/MEDIA_STANDARD_V1.md` defines acceptable source media and import geometry;
- `docs/CHAT_TO_DRIVE_INGESTION_V1.md` defines single-page staging, integrity and publication;
- `docs/CHAT_TO_DRIVE_INGESTION_V2.md` defines production-activated ordered multi-page staging, integrity and publication;
- `AGENTS.md` defines repository authority and STOP/owner gates.

Where this convenience command layer conflicts with any stricter canonical contract, the stricter contract wins.

## Simpler independent-activity batch flow (source-only preflight)

When the owner requests multiple **separate coloring pages**, they are independent v1
activities, not an ordered v2 multi-page activity. Preserve the exact generation order
and the owner's separate-page intent until publication. One unambiguous `PUBLISH`
approves the entire explicitly selected set; do **not** demand one approval or
`PUBLISH RESUME ...` command per page. Each page still gets its own random
seven-digit ID, frozen SHA-256, byte size, category and v1 manifest.

First check generated images visually against the `MAKE` contract: they MUST
actually be black-outlines-on-white coloring-page drafts (unless intentional
worksheet color was requested), not photos, painted illustrations, or completed
colored art. Reject an unsuitable result and regenerate it **before** requesting
`PUBLISH`; never silently publish an unsuitable image.

To reduce repetitive local preparation, use
`tools/coloring-pages-publish-preflight` with a complete owner-approved plan
and freshly retrieved read-only LIVE catalog snapshot. Example plan:

```json
{
  "schema": "rozkalns.coloring-pages.publish-preflight-plan.v1",
  "activities": [
    {"draft": "reading.png", "title": "Junge liest ein Buch", "category": "figuren"},
    {"draft": "football.png", "title": "Junge spielt Fußball", "category": "figuren"}
  ]
}
```

```bash
python3 tools/coloring-pages-publish-preflight \
  --plan /tmp/approved-pages/plan.json \
  --fresh-live-catalog /tmp/approved-pages/live-catalog.json \
  --output-dir /tmp/approved-pages/prepared
```

This **offline, source-only helper** creates all `<id>.png` and
`<id>.json` v1 pairs and a local `preflight-index.json` summary in one
invocation, using the reviewed print-master helper for preparation and validation.
It does **not** connect to Drive or RPi5, and its output alone is **not**
publication eligibility or a LIVE-state proof. The caller remains responsible
for fresh ingest-operator/importer alignment, current LIVE-catalog ID
non-collision, manifest/media integrity, and runtime materialization of every
local artifact into a connector `file_uri` before the first Drive mutation.

After preparation, use one connected Google Drive upload surface for the whole
publication. For each independent activity upload its prepared PNG and then its
already-built manifest to the exact bound `pending/` folder; do not mix upload
surfaces. The trusted RPi5 importer is then invoked once per activity, observing
each terminal ingest PASS. This does not grant retry, alternate staging,
overwrite or rollback; after any mutation failure, STOP and report the exact
succeeded subset, with no automatic continuation of the rest.

Normal user-facing outcome is **one compact status** for the whole set: PASS
with number published, or a precise STOP with whether any mutation happened,
which items succeeded, and the one actual blocked capability/gate. Never
invent new magic `PUBLISH ... RESUME ...` syntax as a workaround for missing
tool capabilities. A repeated command alone cannot create missing file refs.

