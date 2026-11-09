# Instagram content research (#198)

Status: source-only research/design, checked 2026-11-08. This document does not create/configure an Instagram account, publish content, connect services, buy ads, change the website, or authorize LIVE.

## Decision

**GO for a small manual Instagram pilot.**

**OUT OF SCOPE:** TikTok.

The simplest MVP is:
- Instagram only;
- original Ausmalwiese illustrations;
- manual owner review before every public post;
- no real children;
- no synthetic people;
- no paid ads;
- no scheduler/API integration;
- no website code changes;
- no changes to printable A4 masters.

## Audience

Primary audience:
- Familien in Deutschland;
- Kitas;
- Vorschulen;
- adults searching for free printable coloring pages and activities for children roughly 3–6.

Core message:
- **Kostenlose Ausmalbilder und Aktivitäten zum Ausdrucken.**
- Destination: **ausmalwiese.de**.

Tone:
- clear;
- warm;
- useful;
- no exaggerated claims;
- no fake certifications or guaranteed learning outcomes.

## Four-week MVP

Recommended cadence:
- 2 feed/carousel posts per week;
- 1 Reel per week;
- Stories only when there is a real reason to post.

Working effort estimate:
- static/carousel draft: 30–60 minutes;
- simple Reel: 45–90 minutes;
- weekly review/metrics note: about 30 minutes.

These are planning estimates, not measured production timings.

MVP cost target:
- €0 paid media;
- no required paid scheduler;
- no new paid SaaS assumed.

Any external AI/video/audio tool must be checked for current commercial-use rights and price before adoption.

## First five post concepts

### 1. Neue Ausmalbilder

Format:
- Instagram carousel;
- 3–5 slides;
- one clean branded cover;
- 2–4 original Ausmalwiese previews;
- final CTA slide.

German draft copy:

> Neue Ausmalbilder auf Ausmalwiese. Kostenlos ausdrucken für Zuhause, Kita und Vorschule. Mehr auf ausmalwiese.de

### 2. Vom Ausmalbild zur Farbe

Format:
- short Reel;
- original black-and-white Ausmalwiese line art;
- gentle transition to a colored illustrative version;
- no real/synthetic person;
- end card: **Kostenlos ausdrucken auf ausmalwiese.de**.

If AI generation/significant AI editing is used, preserve provenance and check Meta's current disclosure/label controls before publishing.

### 3. Kita-Idee der Woche

Format:
- carousel or Reel;
- one simple seasonal or learning activity;
- one sentence explaining the use case;
- CTA to the exact existing page/category.

German draft copy:

> Kita-Idee der Woche: eine einfache Mal- und Lernaktivität zum kostenlosen Ausdrucken.

Do not claim pedagogical certification unless independently supported.

### 4. Ausmal-Kalender — Monatsthema

Format:
- one monthly/seasonal visual;
- 2–4 matching published themes;
- feed post + optional Story.

German draft copy:

> Was passt zu diesem Monat? Entdecke passende Ausmalbilder und Aktivitäten auf ausmalwiese.de.

Do not imply nationwide German school-holiday dates where dates differ by Bundesland.

### 5. So druckst du dein Ausmalbild

Format:
- short screen-demo Reel;
- show find → preview → Drucken;
- no admin/private UI;
- no user data;
- no private URLs.

German draft copy:

> Ausmalbild auswählen, öffnen und auf „Drucken“ tippen. Fertig für A4.

## Working media formats

These are production targets for consistency, not claims about every Instagram platform maximum.

### Feed / carousel
- preferred portrait working canvas: 1080 × 1350 px (4:5);
- alternate square: 1080 × 1080 px;
- PNG/JPEG;
- sparse, large text;
- consistent ratio within one carousel.

### Reels / Stories
- working canvas: 1080 × 1920 px (9:16);
- MP4;
- keep important text/logo away from UI-covered edges;
- ensure the visual still works muted.

Always preview the exact media in the current Instagram composer before publishing.

## Creation workflow

1. Select an already approved/published Ausmalwiese page or theme.
2. Confirm promotional-use rights.
3. Create a separate social derivative.
4. Add minimal motion/text if making a Reel.
5. Add German copy and Ausmalwiese branding.
6. Check audio/music rights.
7. Check Meta AI disclosure requirements.
8. Owner reviews the exact media + caption.
9. Publish manually in Instagram.
10. Record a minimal weekly metrics note.

No credentials, API tokens, scheduler integration or automatic publishing are part of #198.

## AI disclosure

Meta currently uses an **AI info** label when generated-AI signals are detected or when a creator self-discloses.

Meta currently requires use of its disclosure/label tool for organic content containing photorealistic digitally created/altered video or realistic-sounding audio.

Ausmalwiese policy:
- prefer illustrated/non-photorealistic content;
- do not use synthetic people;
- disclose when Meta requires it;
- preserve C2PA/IPTC provenance where available;
- re-check the current Instagram publishing UI before using a new AI format.

Primary references checked 2026-11-08:
- https://about.fb.com/news/2024/04/metas-approach-to-labeling-ai-generated-content-and-manipulated-media/
- https://about.fb.com/news/2026/02/meta-prepares-for-2026-us-midterms/
- https://about.fb.com/news/2026/07/meta-is-signing-the-eu-ai-act-code-of-practice-on-transparency-of-ai-generated-content/

## Rights and provenance

Every post must have:
- project-owned or explicitly licensed visual source;
- no copied competitor artwork/layout/caption/branding;
- no third-party children's characters or franchise imitation;
- commercial-use rights for any AI-generation/editing tool;
- rights-cleared audio/music;
- source activity/page reference retained internally;
- note whether AI generation/significant AI editing was used.

Do not assume trending audio is cleared for commercial/business use.

## Privacy and child safety

Default policy: **illustration-only**.

Do not publish:
- real child photos;
- children's names;
- schools/Kitas;
- locations;
- contact data;
- social handles;
- Community Galerie submissions;
- synthetic likenesses of real/private minors.

Community Galerie consent, if ever implemented, does not automatically grant Instagram repost rights.

## Visual identity

Use:
- name: **Ausmalwiese**;
- clean white or light background;
- one main illustration;
- restrained brand mark;
- minimal text;
- consistent typography and spacing;
- no fake badges/reviews/scarcity.

Default CTA:
- **Kostenlos ausdrucken auf ausmalwiese.de**
- or **Mehr kostenlose Ausmalbilder auf ausmalwiese.de**

## Metrics

Use existing platform-native and site analytics only.

Instagram:
- reach/views;
- saves;
- shares;
- profile visits;
- follows;
- Reel watch-time/completion indicators when available.

Website:
- aggregate referral/site visits from Instagram where existing analytics already exposes them.

Do not add visitor IDs, cross-site tracking, new pixels/cookies or child identifiers under #198.

## Pilot decision after four weeks

Continue when:
- posts can be produced consistently;
- saves/shares/site visits show repeatable value;
- production effort remains proportionate.

Reduce or stop when:
- content effort is disproportionate;
- there is no useful engagement signal;
- social work distracts from core coloring-page quality.

Do not invent numeric growth targets before a baseline exists.

## Manual publishing checklist

Before every post:
- exact approved media;
- German spelling checked;
- correct page/category/site destination;
- visual rights confirmed;
- audio rights confirmed;
- AI disclosure checked;
- no child/private-person data;
- no admin/private UI;
- no printable A4 master altered;
- owner approval for exact media + caption;
- mobile preview checked in Instagram.

## Separate future gates

After this research, separate owner-gated actions are required for:
1. creating/configuring the official Instagram account;
2. choosing account type and profile settings;
3. setting bio/profile image/site link where available;
4. preparing the first exact five media drafts;
5. approving exact captions and media;
6. publishing;
7. collecting the four-week baseline;
8. deciding whether scheduling automation is justified.

## Final recommendation

**GO:** manual Instagram-only pilot using original illustration-based posts, carousels, Stories and simple Reels.

**NO-GO for now:** TikTok, synthetic people, real-child media, automated publishing, paid ads, third-party scheduler/API integration, or any workflow that changes the website or printable masters.
