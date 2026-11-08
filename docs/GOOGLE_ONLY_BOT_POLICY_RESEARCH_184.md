# Google-only bot access research (#184)

Status: source-only research/design, 2026-11-08. This document does not authorize or claim any Cloudflare, DNS, Worker, WAF, tunnel, runtime, or LIVE change.

## Decision

Use a layered policy:

1. Keep **Google Search crawling** available: verified Googlebot traffic (including Googlebot Smartphone/Desktop and Googlebot-Image) plus Google-InspectionTool for Search Console testing.
2. Block known AI crawlers through **Cloudflare AI Crawl Control / AI Crawler and Agent access policies** rather than Free Bot Fight Mode.
3. Use a narrowly scoped **WAF custom rule only after a read-only zone inventory** proves the available fields, current rules/order, required monitoring traffic, and hostname set.
4. Treat `robots.txt` as an advisory preference layer, not as enforcement.
5. Do not use Free **Bot Fight Mode** for this Google-only policy: it is domain-wide, cannot be customized, and cannot be skipped by WAF rules.

The current repository `robots.txt` is intentionally permissive:

```text
User-agent: *
Allow: /

Sitemap: https://ausmalwiese.de/sitemap.xml
```

Do not change it in this research PR. Cloudflare can prepend managed directives when Bot Preference Sync is enabled, so future source changes must be reconciled with the real zone configuration first.

## Allowed crawler set

The proposed allow set is deliberately smaller than "all verified bots":

- Googlebot Smartphone/Desktop: allow.
- Googlebot-Image: allow.
- Googlebot-Video / Googlebot-News when presented as Googlebot: allow as Google Search-family crawling.
- Google-InspectionTool: allow for Search Console / Rich Results testing.
- GoogleOther, GoogleOther-Image, GoogleOther-Video: do not specially allow; they are not tied to a specific Google Search product.
- Google-CloudVertexBot / Google-Agent / other user-triggered or AI/agent fetchers: do not specially allow.
- Bingbot, Yandexbot, Baidubot and other search crawlers: block under the owner-selected Google-only policy.
- Claude, GPT, Bytespider and other AI search/training/assistant crawlers: block through AI Crawl Control where identified.
- Uptime/security/webhook bots: do not classify as unwanted until the read-only zone/monitoring inventory proves they are unnecessary.

A bare Google-looking User-Agent is not enough to grant an exception. Google documents that User-Agent strings can be spoofed. The WAF exception must require Cloudflare's known-bot signal (`cf.client.bot`) together with the Google Search-family User-Agent.

## Proposed WAF order

This is a **candidate ruleset for later validation**, not a LIVE instruction.

### Rule 1 — Google Search-family exception

Place before any crawler block rule.

Candidate expression:

```text
(http.host in {"ausmalwiese.de" "www.ausmalwiese.de"} and
 cf.client.bot and
 (lower(http.user_agent) contains "googlebot" or
  lower(http.user_agent) contains "google-inspectiontool"))
```

Candidate action: **Skip only the later custom crawler-block rule(s)**. Do not use a broad skip that disables unrelated managed security controls.

If `www.ausmalwiese.de` is not actually routed to this site in the fresh zone inventory, remove it before activation. Never add hostnames by assumption.

### Rule 2 — non-Google search crawlers

Preferred expression only if the fresh zone proves `cf.verified_bot_category` is usable in the current plan/ruleset:

```text
(http.host in {"ausmalwiese.de" "www.ausmalwiese.de"} and
 cf.client.bot and
 cf.verified_bot_category eq "Search Engine Crawler")
```

Candidate action: **Block**.

Rule 1 must precede Rule 2 so verified Google Search-family traffic is not blocked.

If the category field is unavailable or its behavior cannot be proven on the actual plan, **STOP**. Do not replace it with an unreviewed "block all `cf.client.bot`" rule, because Cloudflare's known-bot set also includes monitoring, security, webhooks, page previews and other legitimate automation.

### AI crawlers

Use AI Crawl Control / AI Crawler and Agent access policies as the primary control for known AI crawlers. On Free, detection is primarily based on self-identifying User-Agent strings; therefore this is useful enforcement for identified crawlers, not proof that all hostile automation is blocked.

Recommended policy target:
- Search behavior: Block for AI search crawlers not explicitly approved.
- Agent behavior: Block.
- Training behavior: Disallow/Block according to the current Cloudflare control exposed by the zone.
- Do not configure Pay Per Crawl.
- Do not configure custom block bodies; they require a paid plan and are unnecessary here.

Direct edits to the AI Crawl Control-generated WAF rule should be avoided unless the dashboard cannot express the required hostname/path exception. Cloudflare recommends using the Crawlers interface as the primary control surface.

## Plan/cost matrix

| Control | Free-plan status | Fit for #184 | Decision |
| --- | --- | --- | --- |
| AI Crawl Control / AI crawler policies | Available; Free detection is mainly User-Agent based | Good for named/self-identifying AI crawlers | Use |
| Managed robots.txt / Bot Preference Sync | Available on all plans | Preference/signaling only; not enforcement | Use only after reconciliation |
| WAF custom rules | Available; Free limit 5 rules; all actions except Log; no regex | Good for host-scoped rule order and verified-bot + UA composition | Use only after inventory |
| Bot Fight Mode | Free | Domain-wide, cannot be customized or skipped; may challenge API/mobile traffic | Do not use |
| Super Bot Fight Mode | Paid tiers | More control, but not required for the minimal policy | No upgrade requirement |
| Bot Management score/tags | Higher-tier/Enterprise-dependent fields | Stronger detection but unnecessary for a Free-first design | Do not assume |
| Custom AI block response | Paid plans | Cosmetic, not needed | Do not use |

The minimal design therefore has **no required paid upgrade**. A future upgrade is a separate business decision, not a prerequisite for this policy.

## robots.txt target

Cloudflare states that robots directives are voluntary and do not technically prevent access. If Bot Preference Sync is later enabled, Cloudflare may prepend managed directives to the existing origin file.

Before any source edit:
1. Fetch the public `/robots.txt` and the zone's Bot Preference Sync state.
2. Confirm Cloudflare's prepended groups and avoid contradictory equal-specificity groups.
3. Preserve Google Search access and the sitemap.
4. Prefer Cloudflare's managed AI directives for AI crawler preferences.
5. Do not use `robots.txt` as the only block for hostile crawlers.

## Required read-only preflight before any LIVE change

A separate explicit read-only authorization must collect only sanitized configuration evidence for the exact Ausmalwiese zone:

- exact zone/hostname set;
- current plan;
- AI Crawl Control policies;
- Bot Preference Sync / managed robots state;
- Bot Fight Mode / Super Bot Fight Mode state;
- existing WAF custom rules, order and available rule slots;
- whether `cf.verified_bot_category` is accepted in the actual zone rule editor/API;
- required uptime/health/security monitoring and its request identity;
- current `/robots.txt`, `/sitemap.xml`, `/health`, `/ready`, `/q`, Stats Worker/API paths;
- any other property sharing a rule scope.

No secret values, raw credentials or unrelated account configuration are required.

## Verification matrix and fail-closed thresholds

A future activation must be staged and must STOP on any threshold breach. These are acceptance thresholds, not rollback authority.

| Check | Required result | Failure threshold |
| --- | --- | --- |
| Googlebot Smartphone/Desktop | Allowed on homepage, detail, CSS/JS and canonical content | **1 blocked/failed required request** |
| Googlebot-Image | Can fetch approved public preview/image URLs | **1 blocked/failed required request** |
| Google-InspectionTool | URL Inspection / Rich Results fetch succeeds | **1 failed inspection fetch** |
| Public sitemap and robots | HTTP success and expected content | **1 failure or unexpected managed/source conflict** |
| Human Chrome Android + desktop | Browse → detail → print works | **1 regression** |
| Privacy/low-JS browser | Browse and print remain usable | **1 regression** |
| A4 PNG / print assets | Direct approved download/print remains accessible | **1 regression** |
| `/q` QR landing | Existing redirect path remains functional | **1 regression** |
| Stats/API paths | Existing same-origin behavior remains functional | **1 regression** |
| `/health` + `/ready` / required monitoring | No required monitor is blocked | **1 blocked required monitor** |
| Targeted non-Google crawler samples | Rule matches are blocked as configured | **any matched target allowed unexpectedly** |
| Security Events review | No Google Search-family or required human/monitor request appears in the new block rule sample | **any such false positive** |

Do not use a percentage tolerance for Google or required visitor/monitoring traffic: the acceptable false-positive count is zero in the acceptance sample.

For crawler effectiveness, measure only identified/matched traffic. Do not claim a percentage of **all bots** blocked, because Free AI Crawl Control and UA-based rules cannot identify every crawler.

## Rollout order for a separately authorized future change

1. Read-only inventory and field/rule validation.
2. Prepare exact final expressions and expected rule order from that inventory.
3. Owner reviews one bounded LIVE command naming the exact zone, rule identities, actions and allowed mutations.
4. Apply only the authorized mutation sequence.
5. Run the verification matrix.
6. On any drift, error, blocked Google/visitor/monitor path, or ambiguous outcome: **STOP**. No automatic retry, rollback or cleanup.
7. Any rollback is a new explicit owner authorization.

## Zone-wide risks

- WAF custom rules are zone-scoped; a broad rule may affect unrelated hostnames.
- `cf.client.bot` is not synonymous with Google and includes other legitimate automation.
- `cf.verified_bot_category = "Search Engine Crawler"` includes Googlebot, Bingbot, Yandexbot and Baidubot; it cannot by itself implement Google-only access.
- User-Agent strings alone are spoofable.
- Free AI crawler detection is not comprehensive.
- Bot Fight Mode cannot be bypassed with a WAF Skip rule and may affect API/mobile traffic.
- Managed robots content can be prepended to the origin file and must be checked for conflicts.
- A block that looks correct in source documentation does not prove the actual Cloudflare plan exposes the same fields or that LIVE monitoring is unaffected.

## Owner gates

This research completes the source/design decision only.

Separate gates remain mandatory for:
- read-only Cloudflare baseline inventory;
- any `robots.txt` source change and its PR/CI/merge;
- Cloudflare WAF / AI Crawl Control / Bot Preference Sync mutation;
- any DNS, Tunnel, Worker, route, secret, settings or permission change;
- rollback, retry or cleanup after a consumed mutation.

## Primary sources checked 2026-11-08

- Cloudflare AI Crawl Control — Manage AI crawlers: https://developers.cloudflare.com/ai-crawl-control/features/manage-ai-crawlers/
- Cloudflare AI Crawl Control with WAF: https://developers.cloudflare.com/ai-crawl-control/configuration/ai-crawl-control-with-waf/
- Cloudflare AI Crawler and Agent access policies: https://developers.cloudflare.com/bots/additional-configurations/block-ai-bots/
- Cloudflare managed robots.txt / Bot Preference Sync: https://developers.cloudflare.com/bots/additional-configurations/managed-robots-txt/
- Cloudflare WAF custom rules and plan limits: https://developers.cloudflare.com/waf/custom-rules/
- Cloudflare Bot Fight Mode: https://developers.cloudflare.com/bots/get-started/bot-fight-mode/
- Cloudflare known/verified bots: https://developers.cloudflare.com/bots/concepts/bot/verified-bots/
- Cloudflare Rules language operators: https://developers.cloudflare.com/ruleset-engine/rules-language/operators/
- Cloudflare WAF bot FAQ / `cf.client.bot`: https://developers.cloudflare.com/waf/troubleshooting/faq/
- Google common crawlers: https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers
- Google robots.txt interpretation: https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec
