# Community Galerie research (#200)

Status: source-only research/design, checked 2026-11-09. This document does not collect real submissions, create an upload endpoint, configure storage, create accounts, publish photos, or authorize LIVE.

## Decision

**Do not build browser uploads for the first version.**

If the owner later wants to test demand, use only a **small manually moderated guardian-submission pilot**, and only after a separate legal/privacy review and explicit owner setup approval.

The pilot should accept **artwork-only photos**:
- no child face or body;
- no first/last name;
- no age;
- no school/Kita;
- no location;
- no social handle;
- no visible address, badge, certificate or other identifying background detail;
- no signatures or handwritten personal information on the artwork.

Public gallery cards should identify only the artwork/template, not the child.

This keeps the current V1 browser-upload exclusion intact and avoids creating a new public upload trust boundary before the concept is proven useful.

## Why this is the preferred first step

### Manual moderated pilot — preferred

Advantages:
- smallest technical surface;
- no public upload endpoint;
- no new public database/API;
- every item receives human review before publication;
- demand and moderator workload can be measured before building infrastructure;
- easy to stop without leaving a permanent upload service.

Trade-offs:
- manual work;
- an adult contact channel still processes personal data;
- consent evidence and deletion requests must be handled correctly;
- email/provider/storage setup still needs a reviewed processor/privacy decision.

### Browser upload endpoint — NO-GO for phase 1

A browser upload feature would introduce:
- a new internet-facing file-ingestion boundary;
- malware/malformed-file handling;
- abuse/rate-limit/CAPTCHA decisions;
- private pending storage;
- moderation tooling;
- consent records;
- deletion/backups workflow;
- processor/security review;
- a new LIVE service or managed storage integration.

That is disproportionate before a manual pilot proves demand.

## Legal/privacy position

This is a product/research recommendation, not legal advice.

Before any real submission is accepted, the owner must approve a reviewed legal/privacy basis for:
- receiving the adult submitter's contact data;
- storing the submitted image;
- moderating it;
- publishing a public derivative;
- retaining consent/licence evidence;
- handling withdrawal/deletion requests.

Key principles:
- GDPR Article 5 requires purpose limitation, data minimisation, storage limitation and appropriate security.
- GDPR Article 6 requires a lawful basis.
- If relying on consent, GDPR Article 7 requires demonstrable, clear consent and withdrawal that is as easy as giving consent.
- Children receive special protection under GDPR. If a service is offered directly to a child and consent is the legal basis, Article 8 adds parental-responsibility requirements.
- German KunstUrhG §22 generally requires consent before a person's image is distributed or publicly displayed. The pilot therefore excludes people from submitted images rather than relying on exceptions.
- A child's drawing can itself be a protected work if it meets copyright requirements. Under German UrhG §7 the creator is the author; §31 governs grants of usage rights. The submission process therefore needs an explicit, narrow publication licence rather than assuming the parent owns all rights.

Primary sources:
- GDPR Articles 5–8: https://eur-lex.europa.eu/eli/reg/2016/679/oj
- EDPB children guidance: https://www.edpb.europa.eu/topics/key-gdpr-concepts/children_en
- EDPB consent summary: https://www.edpb.europa.eu/system/files/2026-04/edpb-summary-consent_en.pdf
- KunstUrhG §22: https://www.gesetze-im-internet.de/kunsturhg/__22.html
- UrhG §7: https://www.gesetze-im-internet.de/urhg/__7.html
- UrhG §31: https://www.gesetze-im-internet.de/urhg/__31.html

## Minimal pilot UX

Public page title:
- **Community Galerie**

Intro:
- **Bunte Kunstwerke aus unserer Community**
- **Hier zeigen wir ausgewählte, von Familien eingesendete Ausmalbilder. Jedes Bild wird vor der Veröffentlichung geprüft.**

Gallery card:
- artwork image;
- optional original Ausmalwiese template title;
- button/link: **Zur Ausmalvorlage**;
- no child name, age or location.

Submission entry point:
- **Bild einsenden**

Phase-1 behavior:
- do not open an upload form;
- explain that submissions are currently accepted only through the separately approved guardian contact channel;
- show a short checklist before the adult sends anything.

Draft German checklist:
- **Nur das ausgemalte Blatt fotografieren.**
- **Keine Kinder oder andere Personen auf dem Foto.**
- **Keine Namen, Adressen, Schulen, Kitas oder andere persönlichen Angaben im Bild.**
- **Nur eigene Fotos und Inhalte einsenden, die veröffentlicht werden dürfen.**

Accessibility:
- semantic headings;
- keyboard-accessible links/buttons;
- descriptive alt text about the artwork, not the child;
- no autoplay;
- no interaction that requires hover;
- clear confirmation/error wording if a later submission form is built.

## Proposed submission lifecycle

No real submission may enter this lifecycle until the separate legal/privacy and operational gates are passed.

### 1. Submit

Adult guardian uses the approved private contact channel.

Collect only:
- one adult contact address if needed for consent/takedown communication;
- submitted image;
- optional Ausmalwiese activity/template ID;
- consent/licence confirmation;
- internal timestamp and moderation state.

Do not collect child name, age, school, Kita, location or social account.

### 2. Private quarantine

Before moderation:
- image is private;
- no public URL;
- no indexing;
- no automatic gallery publication;
- access limited to authorized moderator(s).

### 3. Technical sanitation

Accept only reviewed raster formats, initially JPEG/PNG.

Required processing before publication:
- validate actual file signature, not only extension/MIME;
- reject malformed or unsupported files;
- decode and re-encode through a trusted image library;
- strip EXIF, GPS and all metadata;
- remove embedded ICC/comment/application metadata unless explicitly needed;
- constrain pixel dimensions and byte size;
- generate a safe public derivative;
- never serve the raw submitted file from the public gallery.

Suggested initial bounds:
- maximum upload/contact attachment: 10 MB;
- maximum decoded dimensions: 6000 × 6000 px;
- reject files that exceed resource limits.

These are design defaults and require implementation tests before use.

### 4. Human moderation

Moderator verifies:
- no person/face/body;
- no names/signatures;
- no address/location/school/Kita clues;
- no sexual, violent, hateful or otherwise inappropriate material;
- no third-party franchise/character infringement;
- artwork plausibly relates to an Ausmalwiese template if a link is claimed;
- consent/licence record is complete;
- image is visually suitable for a child-friendly gallery.

No AI-only automatic approval.

### 5a. Reject

If rejected:
- do not publish;
- record only a minimal internal rejection reason;
- delete the submitted media according to the retention schedule;
- do not create a public record.

### 5b. Approve and publish

Publish only:
- sanitized public derivative;
- neutral artwork description;
- optional link to the matching Ausmalwiese template.

Do not publish:
- raw attachment;
- adult email;
- consent record;
- moderation notes;
- internal IDs that reveal contact data;
- child identity.

### 6. Report / withdrawal / takedown

Provide a visible **Bild melden / Veröffentlichung widerrufen** route.

For phase 1 this may be a reviewed contact method rather than a new web form.

On a credible withdrawal/takedown request:
1. unpublish the public derivative promptly;
2. stop further promotional reuse;
3. validate the request against the consent/contact record without requesting unnecessary new child data;
4. delete source/media and associated personal data according to the approved retention/deletion schedule;
5. propagate deletion to backups where technically possible within the documented backup window.

### 7. Deletion

No public item should be retained indefinitely by default.

Proposed pilot retention, subject to legal review:
- pending/unreviewed submission: maximum 30 days;
- rejected media: delete within 7 days after moderation;
- rejected contact/administrative record: maximum 30 days unless needed for an active dispute;
- published public derivative: only while consent/licence remains active and the gallery remains useful;
- adult contact + consent/licence evidence: retain only as long as necessary to prove and administer the active publication, then delete on the approved post-removal schedule;
- backups: document a bounded deletion propagation period, target maximum 30 days.

Do not freeze these durations into code until the legal/privacy gate approves them.

## Media/storage design

### Private source area

Requirements:
- not under a public web root;
- random non-identifying object IDs;
- least-privilege moderator access;
- encryption in transit;
- storage-provider access controls;
- auditability sufficient for moderation/deletion;
- no public listing;
- no predictable filenames based on email/name.

### Public derivative

Requirements:
- sanitized re-encoded image only;
- no EXIF/GPS;
- no child identifier in filename/path;
- fixed display-size derivative;
- immutable/versioned URL if the existing public media model requires it;
- separate from canonical A4 print originals.

Community images must never replace or mutate Ausmalwiese printable masters.

## Abuse protections

For the preferred manual pilot:
- no anonymous browser endpoint;
- submission frequency controlled manually;
- dedicated moderator review;
- no public comments/messages;
- no likes/hearts in MVP;
- no competitions/prizes;
- no ranking children/artworks.

If a browser upload is proposed later, it must separately design:
- strict request-size limits;
- server-side byte validation;
- rate limiting;
- Turnstile/CAPTCHA only if justified, with server-side verification;
- duplicate/replay handling;
- safe error messages;
- malware/decompression-bomb protections;
- private object storage;
- CSRF/origin policy where applicable;
- operational alerting and incident response.

## Moderation rules

Immediate reject:
- visible person/face/body;
- personal name/signature;
- school/Kita/address/location details;
- sexual/nude content;
- violence or abuse;
- hate/extremist content;
- third-party copyrighted/franchise characters not authorized for publication;
- advertising/spam;
- unsafe QR codes/URLs/text;
- content unrelated to the gallery purpose.

Manual review should be deliberately conservative because the audience includes children.

## Rights/licence proposal

A future guardian submission flow should request a **narrow, non-exclusive licence** only for:
- displaying the sanitized artwork in the Ausmalwiese Community Galerie;
- generating technical display derivatives necessary for that publication;
- optional separately selected promotional reuse only if the guardian explicitly opts into that distinct purpose.

Do not bundle Instagram/social reuse into gallery consent by default.

Do not request ownership transfer or an exclusive licence.

Exact legal wording requires legal review before real use.

## Withdrawal and social reuse

Gallery publication consent must not automatically authorize:
- Instagram reposting;
- ads;
- newsletters;
- partner websites;
- merchandise;
- training AI models.

Any such use is a separate purpose and requires a separately reviewed legal/owner gate.

## Operations

Pilot capacity target:
- maximum 5–10 newly reviewed submissions per week;
- one authorized moderator;
- no SLA promise to users;
- pause intake if moderation backlog exceeds the operator's capacity.

A moderator checklist should be stored with operational documentation, not displayed publicly.

No automated publication.

## Phased implementation plan

### Phase 0 — research (this issue)

Deliver:
- privacy-first concept;
- manual-pilot decision;
- lifecycle;
- German UX proposal;
- media/moderation controls;
- retention proposal;
- explicit later gates.

No real child/user image collection.

### Phase 1 — legal/privacy + operator design

Separate owner approval required for:
- lawful basis and transparency text;
- consent/licence wording;
- guardian verification proportionality;
- retention/deletion schedule;
- processor/provider choice and DPA where required;
- takedown/withdrawal process;
- moderator responsibility.

No intake before this gate passes.

### Phase 2 — manual pilot setup

Separate owner approval required for:
- exact contact channel;
- private storage;
- moderator access;
- sanitation tooling/process;
- deletion process;
- initial gallery UI/source PR.

Still no public browser upload.

### Phase 3 — limited public gallery

Only sanitized, individually approved derivatives are published.

Verify:
- no raw attachment publicly reachable;
- no personal metadata;
- correct template links;
- accessible gallery;
- report/takedown route;
- deletion process works end to end.

### Phase 4 — browser upload reconsideration

Only after the manual pilot has evidence of:
- sustained demand;
- manageable moderation;
- accepted legal/privacy process;
- safe media pipeline;
- bounded storage/operational cost.

A browser endpoint requires a new source/security/LIVE issue and explicit change to the current V1 upload exclusion.

## Go / no-go

**GO:** research plus a future, separately approved, manual moderated artwork-only pilot.

**NO-GO now:** browser uploads, real-child photos, public pending files, automatic moderation/publication, comments, direct messaging, likes/rankings, contests, social reposting by default, or any new RPi5 upload backend.

This satisfies the research/design ticket without collecting or publishing any real child's photo.
