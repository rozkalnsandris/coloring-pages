# Like expiry aggregate — anonymisation assessment (#182)

> **2026-10-18 — target superseded:** [Simple privacy rules](SIMPLE_PRIVACY_RULES_V1.md) / #256 replace the adult-only, persistent Like-cookie product direction with aggregate reactions without persistent visitor recognition. The remainder records the earlier design and implemented cookie backend; it does not require the new frontend to adopt that design. Duties for any existing identifiable records remain until a verified, separately authorized transition. No runtime or data change is implied.


**Status:** DRAFT / SOURCE-ONLY / NOT LEGAL SIGN-OFF / NOT LIVE.

## Scope

This assessment covers only the proposed post-expiry table `archived_like_totals` in PR #183. It does not classify the rest of Ausmalwiese analytics, Cloudflare edge/security data, D1 recovery history, legacy v1/v2/v3 records, daily visitor HMACs, Print metadata or provider logs as anonymous.

The source shape is intentionally narrow:

```text
archived_like_totals
- page_id     PRIMARY KEY
- like_count  non-negative integer
```

The expiry transaction first aggregates remaining active Likes by `page_id`, then deletes the expired per-cookie Like rows and the matching `like_cookie_sessions.cookie_hash`. The aggregate table contains no cookie hash, session identifier, consent timestamp, expiry timestamp, event timestamp, IP address, user agent or per-Like row.

## Assessment dimensions

Use the EDPB's current 2026 draft framework as a review aid, not as final law. As of 2026-10-17, Guidelines 02/2026 on Anonymisation are still open for public consultation through 2026-10-30.

### 1. Record isolation / singling out

The archive has one row per public activity/page, not one row per browser/session/person. Individual expired contributions are not stored as separate records. This is strong evidence against record isolation in the archive itself.

### 2. Linkability

The archive contains no key shared with `like_cookie_sessions` or `likes`. Source code does not retain an expiry timestamp or per-session archive mapping. Linkability can still reappear operationally if production keeps another dataset, logs, backups or restore states that preserve the deleted identifiers. Therefore anonymity cannot be concluded from this table alone without runtime/process evidence.

### 3. Inference

A page-level total can reveal that at least one Like existed and, for low counts, can reveal changes in a public metric. The archive does not identify which browser supplied the contribution, but contextual inference must still be considered together with other reasonably available information. Avoid releasing additional fine-grained expiry timestamps, cohort dimensions or small-group metadata that would increase inference risk.

## Current source conclusion

The proposed `page_id + like_count` archive is a **strong candidate for non-linkable aggregate data after the source identifiers are deleted**, but PR #183 must not state as a legal fact that it is anonymous. Public/user-facing wording should describe the technical result: only page-level totals remain in this archive, with no cookie/session identifier.

Before any legal anonymity conclusion or release, verify:
- actual deployed schema matches the two-column design;
- expired cookie/session and per-Like rows are actually deleted by an authorised scheduled process;
- D1 Time Travel/restore procedures do not silently reintroduce linkable rows without reconciliation;
- Worker, edge, Rate Limiter and origin logs cannot reasonably be combined with the archive to recover an individual contribution;
- no extra timestamp/cohort/device dimension is added to the archive;
- the final assessment is revisited when EDPB Guidelines 02/2026 leave draft status.

## Art. 8 interaction

An aggregate becoming non-linkable after expiry does not cure invalid consent during the preceding 180-day pseudonymous period. Because Ausmalwiese visibly serves material for children, the optional Like feature remains behind a separate GDPR Art. 8 audience/parental-authorisation legal gate. The UI is now adult-directed, but wording alone is not age or parental-status verification.

## Official references

- GDPR Art. 8: https://eur-lex.europa.eu/eli/reg/2016/679/oj
- EDPB Guidelines 02/2026 on Anonymisation (draft consultation): https://www.edpb.europa.eu/public-consultations/guidelines-022026-on-anonymisation_en
- TDDDG §25: https://www.gesetze-im-internet.de/ttdsg/__25.html

**No merge, LIVE, D1 migration, Cron activation or legal sign-off is authorized by this assessment.**
