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
8. run the fresh host-runtime alignment preflight from `deploy/chat-to-drive-ingestion.json` / `deploy/chat-to-drive-ingestion-v2.json`: installed operator blob must match current `RPi5_main` source, the operator contract’s pinned consumer source revision must resolve, and its `tools/coloring-pages-import` blob must match current `coloring-pages/main`; mismatch means STOP before the first Drive write and requires a separately reviewed `RPi5_main` repin/install;
9. before the first Drive write, select one Drive upload surface that can accept every locally prepared PNG plus the already-built manifest, then stage the exact prepared PNG(s) followed by the manifest through that same surface;
10. run the trusted RPi5 verify/import operator once; RPi5-side `rclone` is Drive-to-RPi5 pull-only and is not a Chat staging upload path;
11. let that trusted operator perform the contract-required post-import catalogue, derivative and public-HTTP proof internally;
12. when the operator returns `COLORING_PAGES_DRIVE_INGEST=PASS`, treat it as terminal publication success, immediately report `PASS`, and stop.

Do not switch Drive upload surfaces after the first mutation. A staging/file-handoff/tool error after mutation begins is a fail-closed STOP, not permission to try host-side `rclone`, a second uploader, overwrite, retry, rollback or cleanup. Do not run discretionary post-success diagnostics, repeated health checks, external/public HTTP rechecks, extra catalogue scans, Drive archive/delete, cleanup or unrelated runtime verification after trusted operator PASS.

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
