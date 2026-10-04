# Chat image commands v1

## Goal

Make the normal owner workflow for creating and publishing one coloring activity as short as possible while preserving the existing media and content-ingest trust boundaries.

Normal happy path:

```text
MAKE lapsa
→ ChatGPT generates one coloring-page PNG draft
UPSCALE-PRINT
→ deterministic CPU/Pillow white cleanup + A4 print-master preparation
VALIDATE-PRINT
→ read-only PASS with exact print-master SHA-256 + byte size
PUBLISH
→ owner approves the exact validated print master
→ determine one valid category
→ freeze page ID + validated print-master SHA-256 + byte size + category
→ Drive staging
→ trusted RPi5 verify/import
→ public verification
```

The commands below are a project conversation convention. They do not replace GitHub policy, the media standard, or the Chat-to-Drive ingestion contract.

## Commands

### `MAKE <subject>`

Immediately generate one new coloring-page candidate using everything after `MAKE` as the subject or scene.

Examples:

```text
MAKE lapsa
MAKE lapsa mežā pie sēnēm
MAKE ugunsdzēsēju mašīna pie stacijas
```

Default generation contract:

- original illustration suitable for public project use;
- output as PNG on an exact `1024×1536` pixel portrait (2:3) canvas;
- `1024×1536` describes the whole page/canvas, not the subject dimensions;
- when the image-generation surface exposes output-size/aspect-ratio controls, set the output size directly to `1024×1536` rather than relying only on prompt wording;
- wide subjects such as cars, trains, buses or aircraft may be composed horizontally inside the portrait page; keep the complete subject visible, centered naturally, with comfortable white space and no cropping;
- white/light page background;
- preserve intentional color when the requested worksheet uses color; ordinary coloring pages default to black/high-contrast line art;
- thick, clean contours where line art is used;
- large coloring regions;
- few small details;
- primary age target 3–6;
- no watermark;
- no unnecessary text;
- for ordinary coloring pages, avoid unnecessary grayscale shading or filled dark backgrounds; learning worksheets may use intentional color when the task requires it;
- keep important artwork inside comfortable page margins;
- prefer one clear focal subject and a simple supporting scene.

The canonical import gates remain in `docs/MEDIA_STANDARD_V1.md`. A generated candidate is not published merely because it was generated.

If the requested subject would require directly copying a protected branded character, preserve the theme or role but create an original character instead for the public catalogue.

### `REMAKE`

Generate a new composition for the same subject using the same project art standard and the same exact `1024×1536` PNG portrait canvas.

The subject itself does not need to be vertical. A wide vehicle or other horizontal subject should remain horizontally composed inside the portrait page rather than forcing the subject into a vertical pose.

`REMAKE` does not approve or publish either the old or new image.

### `EDIT <instruction>`

Edit the exact latest generated coloring-page candidate according to the instruction while preserving unrelated parts of the image where practical.

Examples:

```text
EDIT mazāk detaļu fonā
EDIT resnākas kontūras
EDIT noņem mākoni labajā augšējā stūrī
```

The edited result becomes the latest draft candidate. Request the edited output on the same exact `1024×1536` PNG portrait canvas; do not use automatic output sizing. `EDIT` is not publication approval and invalidates any earlier print-master validation.

`REMAKE` likewise invalidates any earlier print-master validation for the affected page/set.

### `UPSCALE-PRINT`

Transform the exact latest generated draft/page set without asking the image model to generate or redraw anything.

Use `tools/coloring-pages-print-master prepare <draft.png> <print-master.png>` or an exact equivalent execution of that reviewed helper. The helper:

- accepts PNG only;
- composites transparency onto white;
- normalizes near-neutral bright AI whites to exact `#FFFFFF`;
- preserves source aspect ratio;
- centers the resized artwork on an exact `2480×3508` white A4 canvas;
- uses Pillow `Resampling.LANCZOS`;
- applies the reviewed conservative `UnsharpMask(radius=0.45, percent=35, threshold=3)`;
- performs a final near-white normalization after resampling;
- writes PNG with 300×300 DPI metadata;
- never overwrites the source draft.

This is deterministic interpolation/print preparation, not AI detail recovery. It grants no content publication authority.

For an ordered multi-page activity, every page must receive its own print master and the page order must remain unchanged.

### `VALIDATE-PRINT`

Read-only validate the latest print master(s) with `tools/coloring-pages-print-master validate <print-master.png>`.

PASS requires:

- PNG;
- exact `2480×3508` geometry;
- RGB/no alpha;
- approximately 300×300 DPI metadata;
- exact `#FFFFFF` across the complete outer page border.

The validator prints exact byte size and SHA-256. Any failure blocks `PUBLISH`. A later `EDIT` or `REMAKE` invalidates the PASS and requires a new `UPSCALE-PRINT → VALIDATE-PRINT` cycle.

`OK` is intentionally not a publication command. It is treated only as a normal conversational acknowledgement so it cannot accidentally authorize content ingestion.

### `PUBLISH`

`PUBLISH` is explicit owner approval of the exact latest **validated print-master** page or exact ordered validated print-master set in the current conversation. The lower-resolution generation draft is not the published byte identity.

Before the first content mutation, the operator must freeze:

- one stable activity/page ID;
- the ordered page count;
- SHA-256 of every exact approved PNG;
- exact byte size of every approved PNG;
- exactly one valid category;
- required catalogue metadata.

The category is selected from the canonical registry in `metadata/categories.json`. Current category IDs are:

- `tiere` — Tiere;
- `fahrzeuge` — Fahrzeuge;
- `alphabet` — Alphabet;
- `lernen` — Lernen;
- `figuren` — Figuren & Helden;
- `jahreszeiten` — Jahreszeiten & Feste.

When exactly one category clearly fits the approved page, choose it automatically and include it in the frozen manifest metadata. If more than one category is plausible, or none of the current categories fits, STOP before Drive upload and ask the owner to choose an existing category or create a new category through a reviewed source change. Never use a silent default category.

After those values are frozen, the complete JSON manifest must be materialized and validated locally before any Drive write. Do not upload any PNG first and then attempt to construct the manifest. Single-page v1 stages its PNG then manifest. Multi-page v2 stages all 2–12 ordered PNG pages in ascending index order and the single manifest last; only manifest **preparation** moves before the first mutation.

Only after the frozen identity, metadata, and prebuilt manifest all pass preflight does the approval bind to the reviewed content-ingest operation.

`PUBLISH` requires a current successful `VALIDATE-PRINT` for every page in the approved set. The importer contract remains authoritative for ingestion, but the Chat authoring layer now binds the validated A4 print-master bytes rather than the lower-resolution generation draft.

The authorized path is only:

```text
exact approved page or ordered page set
→ exact PNG page(s) + prebuilt manifest in approved Drive pending/
→ trusted RPi5 verification of every page
→ one coloring-pages importer invocation for the activity
→ public catalogue/media verification
```

For multi-page v2, page filenames are `<id>-1.png`, `<id>-2.png`, … and every manifest page entry binds its exact index, filename, SHA-256 and byte size. The trusted host operator at `RPi5_main@dc6b784bba471731ff060ece207e06d67cda16d3` supports this v2 path through the same installed `/usr/local/bin/coloring-pages-drive-ingest` command.

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
User: MAKE lapsa
Assistant: [generated draft]

User: UPSCALE-PRINT
Assistant: [derived A4 print master; no new artwork]

User: VALIDATE-PRINT
Assistant: [PASS/FAIL + exact print-master identity]

User: PUBLISH
Assistant: [determine category, freeze exact validated identity + category, execute bounded ingest, report PASS or STOP]
```

If the image needs work:

```text
User: REMAKE
```

or:

```text
User: EDIT vienkāršāks fons
```

Because the image-generation surface may return the generated draft without an additional text message, the stable next command for an accepted draft is `UPSCALE-PRINT`; `PUBLISH` is valid only after the derived print master passes `VALIDATE-PRINT`.

The publication commands to remember are:

```text
MAKE / REMAKE / EDIT → UPSCALE-PRINT → VALIDATE-PRINT → PUBLISH
```

## Relationship to existing contracts

This command layer is intentionally thin:

- `docs/MEDIA_STANDARD_V1.md` defines acceptable source media and import geometry;
- `docs/CHAT_TO_DRIVE_INGESTION_V1.md` defines single-page staging, integrity and publication;
- `docs/CHAT_TO_DRIVE_INGESTION_V2.md` defines production-activated ordered multi-page staging, integrity and publication;
- `AGENTS.md` defines repository authority and STOP/owner gates.

Where this convenience command layer conflicts with any stricter canonical contract, the stricter contract wins.
