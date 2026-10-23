# Simple privacy rules for Ausmalwiese

Status: owner-selected product direction, 2026-10-18 (Europe/Berlin).
Tracking: #256. Legal pages: #158.

## Three product rules

1. Browse, download PNG and print A4 without an account, age gate or Like permission.
2. Keep the heart and public reaction total. New reactions must not create or use a persistent visitor identifier, Like cookie, fingerprint or personal voting history. Do not promise one person / one vote or remember a person's Like on their next visit.
3. Keep Impressum and Datenschutz short, readable and accurate. Describe actual processing and mandatory information; keep engineering checklists and historical design debates out of public pages.

This replaces the proposed 18+ gate, 180-day Like-cookie flow and cross-visit Like recognition as the target product. It does not say those mechanisms have been removed from code or production. Older design records describe the existing implementation/history only.

## Minimal implementation

- Reuse the existing Worker/D1 and page-level totals; no account service, consent-management platform, age-verification service or new database.
- Add a narrowly scoped aggregate reaction endpoint, then switch the frontend to it and the existing aggregate Print endpoint. Submit the page ID, not a browser identifier. Do not silently fall back to personalized endpoints.
- A confirmed reaction increments the public total. Disable repeated submission during the current page view; after reload another reaction can occur. Cross-visit unlike/history is deliberately no longer promised. Do not manufacture durable identity to enforce uniqueness.
- Show success only after confirmation. An ambiguous submission must not trigger an automatic resend. Printing remains independent of telemetry failures.
- Apply proportionate existing abuse controls and strict request validation. Do not persist IP-derived voting identities or individual reaction logs. Cloudflare still processes request metadata; do not call the whole service anonymous.
- Preserve historical totals and data while planning the transition. Retire old personalized write paths at the coordinated cutover. Existing identifiable records, cookie sessions and backups need a bounded transition decision based on actual deployed state; do not silently delete them or claim they disappeared.

## Legal text and release

GDPR Article 8 is not a universal ban on children clicking a heart or a universal 18+ requirement. It concerns consent-based processing for an online service offered directly to a child. Removing persistent recognition reduces the problem but does not automatically exempt HTTP/IP processing from GDPR or all device operations from TDDDG.

Assess the actual minimal request/security processing and document its legal basis; legitimate interests are a candidate requiring necessity and balancing with children's rights, not an automatic exemption. Retain the required controller/contact, purposes/bases, recipients/transfers, retention criteria and rights in the notice. Do not invent retention periods or publish unresolved placeholders.

Only three release questions are needed: does the implemented data flow match this design; are the applicable legal disclosures/basis supported by facts; and is the exact deployment separately authorized? Add another blocker only for a concrete issue in that implementation, with its reason and smallest necessary remedy. Draft guidance and speculative future features are not additional legal obligations.

PR #158 currently describes the older cookie target and must be reconciled before publication. Legacy retention/erasure duties remain relevant only where those records actually exist. A new aggregate reaction does not itself require a 180-day cookie-expiry Cron.

Source work may proceed through review. Merge, Worker/D1/Cron changes, production cleanup and deployment retain the existing explicit owner authorization boundaries. This document does not change repository governance or certify compliance.

## Official basis checked 2026-10-18

- [GDPR Articles 6, 8, 13 and Recital 26](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng).
- [TDDDG §25](https://www.gesetze-im-internet.de/ttdsg/__25.html).
- [EDPB: lawful processing](https://www.edpb.europa.eu/sme/be-compliant/process-personal-data-lawfully_en).
