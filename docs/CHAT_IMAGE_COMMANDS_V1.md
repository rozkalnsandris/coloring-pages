# Chat image commands v1

## Goal

Make the normal owner workflow for creating and publishing one coloring page as short as possible while preserving the existing media and content-ingest trust boundaries.

Normal happy path:

```text
MAKE lapsa
→ ChatGPT generates one coloring-page PNG candidate
→ owner visually approves the exact latest generated image
PUBLISH
→ determine one valid category
→ freeze page ID + SHA-256 + byte size + category
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
- white background;
- black/high-contrast line art;
- thick, clean contours;
- large coloring regions;
- few small details;
- primary age target 3–6;
- no watermark;
- no unnecessary text;
- no grayscale shading or filled dark background unless the subject genuinely requires a small solid detail;
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

The edited result becomes the latest candidate. Request the edited output on the same exact `1024×1536` PNG portrait canvas; do not use automatic output sizing. `EDIT` is not publication approval.

`OK` is intentionally not a publication command. It is treated only as a normal conversational acknowledgement so it cannot accidentally authorize content ingestion.

### `PUBLISH`

`PUBLISH` is explicit owner approval of the exact latest generated image in the current conversation.

Before the first content mutation, the operator must freeze:

- one stable page ID;
- SHA-256 of the exact approved PNG bytes;
- exact byte size;
- exactly one valid category;
- required catalogue metadata.

The category is selected from the canonical registry in `metadata/categories.json`. Current category IDs are:

- `rettungshunde` — Rettungshunde;
- `tiere` — Tiere;
- `fahrzeuge` — Fahrzeuge;
- `alphabet` — Alphabet;
- `lernen` — Lernen;
- `jahreszeiten` — Jahreszeiten.

When exactly one category clearly fits the approved page, choose it automatically and include it in the frozen manifest metadata. If more than one category is plausible, or none of the current categories fits, STOP before Drive upload and ask the owner to choose an existing category or create a new category through a reviewed source change. Never use a silent default category.

After those values are frozen, the complete JSON manifest must be materialized and validated locally before any Drive write. Do not upload the PNG first and then attempt to construct the manifest. The Drive write order remains PNG first, manifest last; only manifest **preparation** moves before the first mutation.

Only after the frozen identity, metadata, and prebuilt manifest all pass preflight does the approval bind to the reviewed content-ingest operation.

This generation-size rule does not add a new `PUBLISH`-only geometry preflight. The existing media/importer contract remains authoritative for ingestion; the workflow change is to request the correct `1024×1536` canvas at `MAKE` / `REMAKE` / `EDIT` time.

The authorized path is only:

```text
exact approved PNG
→ exact PNG + manifest in approved Drive pending/
→ trusted RPi5 verification
→ coloring-pages importer
→ public catalogue/media verification
```

`PUBLISH` does **not** authorize:

- a different generated image;
- overwrite of an existing page ID;
- Drive archive/delete;
- application deploy;
- Cloudflare/DNS/tunnel changes;
- secrets, credentials, permissions or repository settings;
- cleanup, rollback or an alternate mutation path.

If there is ambiguity about which image is the latest approved candidate, if the image bytes cannot be bound exactly, if category selection is ambiguous, if the intended page ID already exists, or if state drifts after mutation begins, STOP rather than guessing or retrying.

## Conversation behavior

The intended human interaction is deliberately terse:

```text
User: MAKE lapsa
Assistant: [generated image]

User: PUBLISH
Assistant: [determine category, freeze exact identity + category, execute bounded ingest, report PASS or STOP]
```

If the image needs work:

```text
User: REMAKE
```

or:

```text
User: EDIT vienkāršāks fons
```

Because the image-generation surface may return the generated image without an additional text message, the owner should treat `PUBLISH` as the stable next command whenever the displayed result is accepted.

The four commands to remember are:

```text
MAKE / REMAKE / EDIT / PUBLISH
```

## Relationship to existing contracts

This command layer is intentionally thin:

- `docs/MEDIA_STANDARD_V1.md` defines acceptable source media and import geometry;
- `docs/CHAT_TO_DRIVE_INGESTION_V1.md` defines exact-image staging, integrity and publication;
- `AGENTS.md` defines repository authority and STOP/owner gates.

Where this convenience command layer conflicts with any stricter canonical contract, the stricter contract wins.
