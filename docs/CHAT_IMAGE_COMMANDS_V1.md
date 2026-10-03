# Chat image commands v1

## Goal

Make the normal owner workflow for creating and publishing one coloring page as short as possible while preserving the existing media and content-ingest trust boundaries.

Normal happy path:

```text
MAKE lapsa
→ ChatGPT generates one coloring-page PNG candidate
→ owner visually approves the exact latest generated image
PUBLISH
→ freeze page ID + SHA-256 + byte size
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
- PNG-oriented source artwork;
- portrait composition, approximately A4 ratio;
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

Generate a new composition for the same subject using the same project art standard.

`REMAKE` does not approve or publish either the old or new image.

### `EDIT <instruction>`

Edit the exact latest generated coloring-page candidate according to the instruction while preserving unrelated parts of the image where practical.

Examples:

```text
EDIT mazāk detaļu fonā
EDIT resnākas kontūras
EDIT noņem mākoni labajā augšējā stūrī
```

The edited result becomes the latest candidate. `EDIT` is not publication approval.

### `PUBLISH`

`PUBLISH` is explicit owner approval of the exact latest generated image in the current conversation.

Before the first content mutation, the operator must freeze:

- one stable page ID;
- SHA-256 of the exact approved PNG bytes;
- exact byte size;
- required catalogue metadata.

Only after those values are frozen does the approval bind to the reviewed content-ingest operation.

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

If there is ambiguity about which image is the latest approved candidate, if the image bytes cannot be bound exactly, if the intended page ID already exists, or if state drifts after mutation begins, STOP rather than guessing or retrying.

## Conversation behavior

The intended human interaction is deliberately terse:

```text
User: MAKE lapsa
Assistant: [generated image]

User: PUBLISH
Assistant: [freeze exact identity, execute bounded ingest, report PASS or STOP]
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

## Relationship to existing contracts

This command layer is intentionally thin:

- `docs/MEDIA_STANDARD_V1.md` defines acceptable source media and import geometry;
- `docs/CHAT_TO_DRIVE_INGESTION_V1.md` defines exact-image staging, integrity and publication;
- `AGENTS.md` defines repository authority and STOP/owner gates.

Where this convenience command layer conflicts with any stricter canonical contract, the stricter contract wins.
