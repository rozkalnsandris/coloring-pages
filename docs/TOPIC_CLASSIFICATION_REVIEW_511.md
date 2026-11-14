# Topic classification review — source-only QA for #511

## Scope and evidence

The public gallery uses the explicit catalogue topics array when present. Only records without that field use the managed Topics v2 legacy title/character terms. The live catalogue and runtime topic registry belong to the RPi5 content store, not GitHub.

A public browser read on 2026-11-14 reported 494 total activities and 109 figure entries. Seven figure entries were displayed under Autos, including a candidate titled Fröhlicher Tänzer. That browser read was NOT bound to a saved catalogue SHA-256 and is NOT evidence of the present catalogue state or proof of an incorrect tag. The original topic metadata must be checked against artwork before any decision.

## Offline audit contract

The new tool at tools/coloring-pages-topic-review accepts a local, owner-authorized, read-only snapshot via --catalog and the matching canonical managed v2 --topics file. --topic is required; --category is optional. For the reported case, choose the canonical topic autos and category figuren. Use both --expected-catalog-sha256 and --expected-topics-sha256 to bind a review to exact bytes.

The report includes the two actual SHA-256 digests, total catalogue count, matched count and the ordered IDs/titles. Each match says whether it came from explicit topics or from legacy title terms. Explicit assignments with no related title/character keyword are marked as manual review candidates; this is NOT proof of a semantic error. A title may legitimately omit a visible element in the artwork.

Only local bytes are read. The tool does not contact the network, inspect images, copy production files, write a report to disk, modify records or propose automatic topic corrections. Registry parsing uses the existing coloring_pages_topics.read_registry fail-closed validation; invalid or stale snapshots yield no partial JSON output. Regression tests use synthetic activities, not production catalogue content.

## Owner-gated next step

Obtain and verify an exact catalogue snapshot through an independently authorized read-only operator path. Confirm ID, current title, full primary/secondary categories, explicit topics and image preview for each candidate. Classify each mapping as correct, wrong or requires more evidence. Any later metadata write needs a separate owner authorization and trusted production operator with lock / immutable identity checks. This PR must not modify LIVE catalogue, topic registry, uploads, media, IDs, titles or deployed code.

The existing title-correction inventory is separately maintained at docs/UI_UX_TITLE_EDITORIAL_511_13.md and is not a current LIVE snapshot.
