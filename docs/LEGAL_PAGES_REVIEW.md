# Legal pages reconciliation for #256

Status: **SOURCE REVIEW ONLY / NO LEGAL CERTIFICATION**

Baseline: `coloring-pages/main@27b44cd27ad7f1a6b9f5b15d07bd6dcbf5370b0c`  
AUTO-RUN: `3cea3eaf-0322-4a0b-9a94-88d69c5a8444`  
Supersedes direct integration of stale Draft PR #158.

## Current verified model

- Current frontend source and the 2026-11-09 read-only RPi5 check use `/api/stats/like-aggregate` and no persistent `visitor_id` or `localStorage` identifier for Like/Print.
- The deployed legacy page-stats request containing `visitor_id` returns HTTP 410.
- `datenschutz.html` was publicly available, while `impressum.html` returned HTTP 404 before this source change.
- This change does not mutate D1, delete legacy records, change GoatCounter behavior, or certify a legal basis.

## Reconciliation decision

- Add a concise German `impressum.html` with the operator name, postal address and email already present in the privacy notice.
- Package the page in the application image and link it from the existing legal footers on `index.html`, `detail.html` and `datenschutz.html`.
- Update the Like/Print section of `datenschutz.html` to match the aggregate implementation: no persistent browser identifier, Like cookie or fingerprint for new reactions; IP may be used transiently for abuse limiting and is not stored as the reaction/print identifier in D1.
- Keep historical pseudonymous records explicit as a separate transition concern; this source change does not delete or reclassify them.
- Leave the separate optional GoatCounter consent flow unchanged.

## Legal-source guardrails

The official DDG §5 text requires specified provider/contact information where its scope applies, and GDPR Art. 13 requires purposes and legal basis when personal data are collected. GDPR Art. 21 provides the objection right for processing based on Art. 6(1)(f). These references support the engineering checklist; they are not legal certification.

Official references:
- https://www.gesetze-im-internet.de/ddg/__5.html
- https://eur-lex.europa.eu/eli/reg/2016/679/oj

## Remaining gates

1. Exact-head CI/review for this focused PR.
2. Explicit owner `MERGE` authorization if accepted.
3. Any deployment/LIVE behavior follows the repository's separate bounded merge/LIVE rules.
4. Historical D1 cleanup/deletion, retention decisions and any broader legal sign-off remain outside this source PR.
