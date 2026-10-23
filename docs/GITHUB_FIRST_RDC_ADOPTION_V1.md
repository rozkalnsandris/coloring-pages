# GitHub-first / bounded RDC fallback — Coloring Pages

Status: **source-only consumer adoption**; active only after the separate exact-head owner merge. Issue: #292.
Upstream accepted policy: `rozkalnsandris/ops-workflows@4e89b75d7f496dfb43fd9c1eb10a995fad53fdd8`. Local adapter: `.github/github-first-rdc-v1.json`; test: `tests/test_github_first_rdc_v1.py`.

## Tool selection, one step at a time

Connected GitHub is the mandatory default for source/files, branches/commits, issues, PRs, reviews, CI and canonical source continuity, and GitHub Actions is preferred for equivalent safe tests.

RDC is the **host-local exception**, not a second GitHub client. An exception requires a precise missing GitHub operation and GitHub Actions alternative, an actual RPi5-local task, applicable separate current authority, a minimal bounded step, and a public-safe record of `STEP`, `REPOSITORY_AND_TARGET`, `GITHUB_CAPABILITY_CHECKED`, `PRECISE_CAPABILITY_GAP`, `GITHUB_CI_NOT_EQUIVALENT_REASON`, `MINIMAL_RDC_OPERATION`, `EXISTING_AUTHORIZATION` and `GITHUB_RETURN_EVIDENCE`. Sequence: **GitHub -> minimal RDC -> GitHub**. Do not expose runtime secrets or artwork/private content in public evidence.

GitHub 403/429, denied permissions, timeout, failure, rate limit or uncertain dispatched mutation => **STOP**, never switch to RDC as retry or bypass.

## Coloring Pages stricter safety

- Repository source and RPi5 production PNG/media/catalogue have separate owners. No production PNG binaries are committed.
- Only a fresh exact owner `MERGE coloring-pages #N` approves that merge; its existing bounded application-input auto-LIVE semantics are **unchanged**, not expanded.
- Only a fresh explicit `PUBLISH` of the exact approved draft/set authorizes bounded media preparation and content publication. Neither this adoption nor CI authorizes it.
- FAST v2.3 remains lightweight, `AUTO-RUN FULL` stays owner-command-only and source-only, Queue and GITHUB-ONLY are not adopted, and no `.github/agent-bootstrap.json` is added.
- Secrets, runtime, RPi5 content store, Cloudflare, deployment and any other LIVE actions retain their exact existing trust gates.

## No deploy from governance merge

The existing `.github/workflows/simple-deploy.yml` on-main trigger lists only `Dockerfile`, `tools/coloring-pages-import`, `deploy/nginx.conf`, `index.html`, `detail.html`, `print.html`, `css/**`, `js/**`, `assets/**`. This adoption changes `AGENTS.md`, `.github/github-first-rdc-v1.json`, `.github/workflows/github-first-rdc-policy.yml`, `docs/GITHUB_FIRST_RDC_ADOPTION_V1.md`, and `tests/test_github_first_rdc_v1.py`, none of which match this deploy allowlist. Source CI runs but no application-image publishing is triggered by these paths.
