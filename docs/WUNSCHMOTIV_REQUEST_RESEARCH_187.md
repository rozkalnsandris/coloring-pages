# Wunschmotiv vorschlagen — minimal request-flow decision (#187)

Status: **research and UI specification only** (2026-10-22). No form, user-text intake, Worker, D1 database, Cloudflare rule, route, legal policy or LIVE service is installed by this PR. Source baseline: `rozkalnsandris/coloring-pages@1ad4b70e41390f06d8920a44319b50fd557d53be`.

## Actual frontend evidence and goal

The static, mobile-first catalogue uses `index.html` with `[data-empty-state]`, and `js/app.js` sets its current fallback to **“Keine passenden Malvorlagen gefunden.”** when filters yield zero results. The homepage already provides an ordinary public contact `mailto:` link in its about section. Do not infer that a request form or submission processor exists today.

**Product goal:** an adult visitor who cannot find a motive can privately suggest **one short topic**, without supplying a name, email, account, image, address or child's identity. Suggestions are for **human editorial review only**; no automatic content publication, tracking, confirmation email, moderation feed or public display of submitted text.

## Alternatives and decision

| Route | No name/email required? | Maintenance / pricing | Spam, privacy and UX implications | Decision |
| --- | --- | --- | --- | --- |
| Existing `mailto:` contact | **No**: sender necessarily uses an email account/address | No new technical infrastructure | Opens a local email app, exposes sender email, sends message to inbox; unsuitable as a claim of anonymous suggestion | Keep as **clearly optional existing alternative**, with an explicit email-address warning |
| Hosted external form | Potentially | Vendor terms/fees and vendor lifecycle | Third-party handling of free text, different origin/branding, retention/legal review and abuse controls; unsuitable without a verified contract | Not MVP |
| **Same-origin Cloudflare Worker + D1**, one private text field | **Yes** | Small edge function, D1 schema/storage, actual quotas and deletion operator | Needs strict validation, Turnstile Siteverify, spam defense, operational moderation and legally reviewed retention | **Preferred conditional MVP**, *not authorized or deployed* |
| Static page with only a notice | Yes, collects no data | Zero runtime | No actual suggestion channel | Safe interim state until the full MVP is approved |

**Decision:** keep the existing site unchanged until a separately owner-reviewed source implementation and privacy/security gates make the same-origin Worker/D1 intake safe. Then offer the one-field same-origin option; do not silently replace it with a `mailto:` that demands personal contact details. The optional preexisting footer email link may remain, clearly identified as email contact. No RPi5 database or full CMS.

As of Cloudflare documentation reviewed **2026-10-22**, Workers Free advertises **100,000 requests/day**, **10 ms CPU/request** and **50 subrequests/request**; D1 Free lists **5 million rows read/day**, **100,000 rows written/day**, and **5 GB total storage**. These are *service-level reference limits*, **not evidence of this site's plan, quotas, usage or free eligibility**. Free limits can change and excess D1 daily usage can fail requests; refresh official terms before any deployment and budget for normal traffic, abuse and moderation. References:
- https://developers.cloudflare.com/workers/platform/limits/
- https://developers.cloudflare.com/d1/platform/pricing/
- https://developers.cloudflare.com/turnstile/get-started/server-side-validation/

## Proposed microcopy and interaction (German, unpublished)

```text
[Search field: "Was möchtest du ausmalen?"]

Keine passenden Malvorlagen gefunden.

Nicht gefunden? Wunschmotiv vorschlagen
Du kannst uns ein Motiv für zukünftige Ausmalbilder vorschlagen.
Bitte keine Namen, Kontaktdaten oder persönlichen Informationen eingeben.

Wunschmotiv (max. 80 Zeichen)
[ z. B. Ein Bagger im Schnee                              ]

[ Schutzprüfung ]           [ Vorschlag senden ]

Hinweis: Dein Vorschlag wird intern geprüft. Es gibt keine
Veröffentlichungsgarantie und keine persönliche Antwort.
```

**No-results placement:** under the existing `[data-empty-state]` notice, and **only** when the catalogue loaded successfully, there is a nonempty user search query, and matching published results count is zero. Do not show a request invitation for a network/server error, an empty unfiltered catalogue, or a filter-only empty result where clearing filters is the appropriate first action. If no matching results arise after category filters, provide a “Filter zurücksetzen” path before suggesting a topic. Keep the normal result counter, search and gallery intact.

**Successful submission, German:** “Danke! Dein Motivwunsch wurde zur Prüfung aufgenommen. Ob oder wann ein Ausmalbild entsteht, können wir nicht zusagen.”

**Invalid input:** “Bitte gib ein kurzes Motiv mit 3 bis 80 Zeichen ein – ohne Namen, Links oder Kontaktdaten.”

**Rate-limited:** “Zurzeit können wir keinen weiteren Vorschlag annehmen. Bitte versuche es später erneut.”

**Network/server rejection:** “Dein Vorschlag wurde nicht gesendet. Bitte versuche es später erneut.” This must never masquerade as a success.

**Protection issue / expired widget:** “Die Sicherheitsprüfung ist abgelaufen. Bitte starte sie erneut.” Resets a failed/expired Turnstile **before** a fresh visitor-initiated send, not by silently replaying the original submission.

**User interaction states:** initial button only active for a valid, nonempty text field and completed required protection; `aria-describedby` ties the length and privacy warning to the field; status messages use an appropriately polite live region, keyboard focus is preserved, double submission is disabled while sending, input is not cleared until confirmed success, and an explicit visitor action is needed for retry. A `maxlength=80` browser hint is **not** server-side validation. No auto-focus modal or CTA that displaces search results on small screens.

## Data flow, security and lifecycle — design only

Recommended future route: same-origin `POST /api/wunschmotiv`, accepting only a structured JSON body like `{"motif":"Ein Bagger im Schnee","turnstileToken":"..."}`. It is **not a real endpoint** and must not be referenced as a working URL before separate approval and deployment.

1. **Request boundary.** HTTPS only; exact `POST` and `application/json`, small body (e.g. **2 KiB** max before parse), exactly one topic field and protection token, reject other methods and fields; no image/file upload, identifiers, email, address, names, account metadata or arbitrary client-controlled timestamps. Use strict UTF-8 parsing, cap processing time and avoid reflecting raw input into response errors.
2. **Text validation.** Server applies Unicode NFC + whitespace trim and normalizes repeated spacing. Propose **3–80 Unicode code points** (not merely JS UTF-16 units), one line, no control/bidi spoofing characters, URL or obvious email/phone patterns. If a subject appears to contain someone's personal data, reject and ask for a generic motif; regex checks are *not* proof that all personal information was filtered. Render accepted text only with escaped text nodes in the private operator interface, never HTML.
3. **Turnstile.** The **server must POST the visitor token to Siteverify**, using an owner-managed Worker secret, verifying `success`, expected hostname and expected action. Reject failed, missing, expired, replayed and mismatched tokens. Tokens are valid for only **300 seconds** and can be used **once**. Widget-only checks are insufficient. Store no raw Turnstile token in D1 or public logs. The token secret must **never** be included in a GitHub commit or browser bundle.
4. **Abuse control.** Add a honeypot with no visible or accessible false-positive trap, basic server validation, bounded request size and a separately approved server/edge rate-limit policy with minimal transient characteristics. Do **not** rely on `Origin` or `Referer` alone as authentication; enforce the Siteverify and operator access gates. Verify the deployed Cloudflare plan actually supports the proposed rate limiting; do not invent a WAF rule or assume a free-plan rate-limit allotment.
5. **Storage.** A future D1 table should store only a server-generated opaque row ID, normalized short `motif`, `created_at_utc` and private moderation state (`new`, `reviewed`, `rejected`). **Do not store** IP address, user agent, cookies, session ID, geolocation, names, email, tokens, analytics correlation or public profile fields in D1. Edge/security provider may independently process HTTP/IP logs, which must be disclosed/reviewed; “no IP saved in D1” does **not** mean nobody processes an IP.
6. **Retention and operation.** Suggested policy: **30 days maximum** from submission, with no archival of raw free text. A separately reviewed, owner-authorized and **verified deletion mechanism** must actually enforce this deadline (for example a bounded protected cleanup process or authorized scheduled purge). Define who reviews the private queue and who confirms deletion. Without a working deletion procedure, **STOP before accepting live suggestions**. No automatic publication of accepted text; after review use a manually chosen generic topic, if suitable.
7. **Moderation view.** No public `GET /api/wunschmotiv` listing, public form submissions, searchable D1 UI or public read endpoint. Private review access only via separately approved authenticated operator controls and least-privilege service permissions. Reviewers may discard abusive text without any response. Render plain text, never unsanitized HTML.
8. **Failures.** On Siteverify outage, D1 failure, quota exhaustion, malformed input, deletion failure or uncertain write, fail closed and return neutral feedback. The client must not claim acceptance without a confirmed successful server write. Separate internal metrics may count aggregate successes/rejections only after privacy/legal review; never log the submitted topic.

### Privacy/usage notice — candidate, legal review required

“**Motivwünsche:** Wenn du freiwillig ein Motiv vorschlägst, verwenden wir den kurzen Text ausschließlich zur internen Prüfung von Themenideen. Bitte gib keine Namen, Kontaktangaben oder andere persönlichen Daten ein. Es gibt keine Antwortpflicht und keine Garantie, dass das Motiv veröffentlicht wird. Vorschläge sollen spätestens nach 30 Tagen gelöscht werden. Details zur Datenverarbeitung stehen in den Datenschutzhinweisen.”

This is **proposed text only**. Do not publish it unchanged as a legal declaration, or claim a deletion guarantee until the actual backend/processor, retention and legal basis have been independently checked. The privacy notice needs the correct responsible entity, processors, lawful basis, purpose, technical logs, deletion/dependency details and contact channel as reviewed by the legal owner. Keep this design issue separate from Like/Print identity changes (#182/#256).

## QA checklist and future authorization gates

- [ ] **UI/mobile:** keyboard/screen reader, text-only (script failure), Android/desktop, focus/live state, 80-character boundary, empty/nonmatching search, category filter-only empty, catalogue-fetch error and navigation continuity; never break normal `Drucken`.
- [ ] **Server validation:** 2/3/80/81-code-point boundaries, whitespace-only, Unicode emoji/umlauts, multiline, injection, SQL injection, invalid JSON/content-type, overlarge payload, unknown keys, invalid `Origin` and XSS payload shown literally in a protected view.
- [ ] **Turnstile:** test Siteverify success, missing/forged/expired/replayed token, wrong action and hostname, fake/dummy testing keys **only in offline CI**, secret absence, timeouts and failed upstream response.
- [ ] **Abuse/operability:** duplicate clicks, concurrent submissions, bot bursts, transient per-source throttling, intentionally broken D1 binding, Worker/free-plan exhaustion, no persistent user identifiers or accidental plaintext logs.
- [ ] **Lifecycle:** 30-day cutoff, idempotent cleanup, deletion verified, operator audit, no public read route and inaccessible moderation page; no live intake until these are done.
- [ ] **Privacy:** owner/legal review of notice, retention, processing roles, external provider logs, child-safety language, optional email alternative and contact address.

**Explicit later gates:** a separately scoped source-only implementation issue and exact HEAD GitHub review for HTML/CSS/vanilla JS and edge Worker/D1 code; separately owner-approved production binding/secrets, D1 schema/migration and purge mechanism; Turnstile widget/key and hostnames; Cloudflare routing/WAF/rate limits; verified private operator access; privacy/legal notices; read-only preflight; then a distinct explicit LIVE authorization and post-deploy correctness checks. No GitHub-only source merge authorizes those Cloudflare/D1/secret or ADMIN changes. Do not use production credentials in ChatGPT or CI. The existing site remains unchanged by this research.

**Decision status:** feasible as a simple, optional feature after the gates, **not delivered** by this research PR. Keep #187 open for implementation and acceptance evidence.
