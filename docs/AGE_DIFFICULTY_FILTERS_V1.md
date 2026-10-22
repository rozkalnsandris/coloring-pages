# Age and difficulty filters — source contract (#201)

## Metadata
Only explicitly reviewed catalogue metadata is used. Existing importer `ALLOWED_AGES = {"3-6", "4-8"}` and `ALLOWED_DIFFICULTIES = {"easy", "normal", "detailed"}` remain unchanged. The homepage offers these **exact** age ranges (`3–6 Jahre`, `4–8 Jahre`), never inferring `3–4` or `5–6` from `3–6`. Difficulty labels are `Einfach`, `Mittel`, `Detailliert`.

An absent/unrecognized age or difficulty is **unknown**, never automatically assigned to either filter. Unknown records appear when the relevant filter is empty; when a value is selected they do not match it. Unknown badges are omitted instead of showing `undefined Jahre`. Multi-page activities are one record, so only activity-level metadata is filtered, not independently inferred page values.

## Behavior
The controls are optional, keyboard-accessible labelled native `select` elements above the homepage gallery. Search, category, topic, age and difficulty combine by **intersection**. Newest-first original catalogue order, pagination, Popular/Trending lists, and print/PNG remain unchanged. Reset clears both facets and existing search/topic/category selections.

Only allowlisted age/difficulty values are restored from `?age=` and `?difficulty=`; controls write those two parameters with `history.pushState` without removing campaign/other parameters or fragment, and `popstate` restores facets for Back/Forward. Unknown parameters are safely ignored. No database, visitor ID, cookie, backend, content import or deployment in this source work.

Source-only PR and exact-head CI/review. Merge and any bounded automatic app LIVE release require separate owner authorization.
