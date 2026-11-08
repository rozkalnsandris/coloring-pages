# ARM64 origin image release

This implements the application source portion of
[RPi5_main #1348](https://github.com/rozkalnsandris/RPi5_main/issues/1348).
The default application Dockerfile, SIMPLE-DEPLOY workflow and production pointer
are unchanged. A source merge runs validation only. No RPi5 connection, profile
installation, public counting or legal clearance is part of this workflow.

## Selected candidate

`deploy/goatcounter-origin-release.json` is a reviewed build selection, not a
publication receipt. It distinguishes the ordinary application source, the base
OCI index, its ARM64 image manifest, the immutable origin recipe, shared publisher
and the accepted RPi5 evidence validator. The ordinary source can precede the
recipe revision. The selected base was verified against public registry metadata
and its successful ordinary publication run in #1348; it is refreshed during proof
and immediately before/after publication. Pointer drift refuses the operation.

Baseline refresh #459 binds the ordinary application to the latest GitHub-proven
SIMPLE-DEPLOY publication from source `3231e678b0214d52a0db4aafeb5647bf5d07dae0`:
index `sha256:128cfaf14542e7811f5d2c2d4cf5e29b3b9b61d55849844f536d27af0398609d`
and its `linux/arm64` manifest
`sha256:b6bfc551ab39239ce500328c8a9ec018b1913790d5180b464df63ea4034766cb`.
The evidence is SIMPLE-DEPLOY run `42305541900`; later merges #453 and #456 do
not touch application-image inputs and therefore do not supersede this base.

The recipe remains at `bca36e1ef516e370e880c44b3c27785e82f0d9e0`; this PR extends
the proof tooling, not the recipe or Nginx renderer. The RPi5 parser is checked out
at `ccd468de5ae6ea76cdc3dd009bd06812c20e6874`. Its original validation functions
check the real unmodified in-toto statement and derivative configuration. A changed
recipe/parser requires coordinated source review, not relaxed validation.

## Build once, prove and preserve

The `GoatCounter ARM64 origin release` workflow uses an ephemeral native
`ubuntu-24.04-arm` runner. PRs, pushes and manual runs with `publish=false` have
read-only GitHub permissions. Skopeo is installed only on that runner; there is no
host package installation. Existing AMD64 origin tests remain in their own job.

The proof builds from the immutable remote Git recipe, the exact base digest and
`--provenance=mode=max,version=v0.2` into an OCI tar archive. It checks every blob
hash and bounded metadata, rejects links/path traversal/duplicate archive entries,
selects one ARM64 image plus its bound attestation, and validates both through the
accepted RPi5 source. It does not invent an attestation or rewrite one to fit the
parser. Format mismatch is a refusal requiring review of real emitted evidence.

Skopeo loads the ARM64 image from that archive into the ephemeral Docker daemon.
Its image config digest must equal the archive's config digest. The proof compares
all built application/public asset/importer fingerprints with the base, normalizes
the Compose delta, then runs the existing synthetic Unix receiver cases against
the actual derivative CMD/config. These cover eligible/rejected requests, minimized
headers/body/query data, collector failure, socket permissions/replacement, and
fail-open serving. Like/Print/QR/campaign source remains byte-identical; this is not
a new live engagement/browser test. No real catalog, GoatCounter DB or public
event is used. Runtime RPi5 user mappings still need their separate verification.

`origin-release-candidate` retains the exact OCI archive and available public
evidence for seven days, including partial evidence on a failed proof. A successful
proof adds `proof.json` with source/run, candidate, archive and image identities.
Partial artifacts are not release-ready. Neither the archive hash nor supplied
JSON alone authenticates a builder; review the GitHub run and exact workflow source.

## Separate publication decision

Publication is unavailable on PR/push events. After source review and explicit
merge, a separately authorized owner dispatch on `main` must supply:

- `publish=true`;
- `expected_source_sha` = the exact reviewed merged workflow SHA;
- `authorization` = the following string, substituting that same full SHA and the
  reviewed base digest from the candidate contract:

```text
PUBLISH GOATCOUNTER-ORIGIN WORKFLOW=<40-character-merged-workflow-sha> BASE=<sha256:reviewed-base-index> RECIPE=bca36e1ef516e370e880c44b3c27785e82f0d9e0
```

Both actor and triggering actor must be the repository owner; a rerun attempt is
refused. Inputs pass through environment variables, not executable interpolation.
This source PR/merge is not authorization to dispatch publication. A run with the
publication input enabled first rechecks authority, builds/proves a fresh candidate
with read-only permissions, then gives only the subsequent publication job
`packages:write`. The job obtains only this run's artifact, repeats provenance and
archive/receipt validation, and refuses stale source/run or base identities.

The registry credential is the job token, passed through stdin into an ephemeral
auth file outside artifacts. It is never a repository file, CLI argument or report.
The destination is fixed to `ghcr.io/rozkalnsandris/coloring-pages-origin` with a
unique `candidate-<run-id>` tag. An existing tag or ambiguous absence check refuses
publication. `skopeo copy --all --preserve-digests --retry-times=0` copies the exact
tested archive, including provenance, without rebuilding or promoting ordinary
`:production`. Immutable remote index and ARM64 manifest hashes are verified after
copy; those identities bind the same config/layers already exercised by the proof.
The immutable ARM64 manifest is the later deployment identity, not the candidate
tag or attestation index. `publication.json` is retained separately for 30 days.

GitHub package permission/visibility is not changed by this workflow. If first
publication cannot prove destination absence or cannot write the package, stop;
do not broaden credentials/settings or silently use another image repository.
A failed/ambiguous copy may leave a partial or complete unpublished-for-deployment
candidate in GHCR. There is no automatic repeat, overwrite, rollback or cleanup.
The workflow concurrency group only serializes publication; it grants no authority.
A new manual dispatch is a new publication decision, not an automatic retry.

## After publication

Successful publication still needs fresh RPi5 primary-peer/group/socket evidence,
the actual-flow notice/assessment in legal draft #158, a reviewed request/bundle and
separate exact runtime/public-activation authorization. Private GoatCounter and
ADMIN reporting are not reinstalled. Follow the accepted
[RPi5 deployment procedure](https://github.com/rozkalnsandris/RPi5_main/blob/ccd468de5ae6ea76cdc3dd009bd06812c20e6874/docs/GOATCOUNTER_ORIGIN_DEPLOY_V1.md).

Later ordinary application updates require a newly reviewed candidate contract
and artifact pair. The opted-in reconciler deliberately holds rather than falling
back to the ordinary image. The fixed candidate must not be silently advanced in
this workflow. The metric remains eligible origin detail HTTP requests, not unique
people or all browser-rendered pages; retained reporting periods remain UTC.

## Validation

`python3 -m unittest discover -s tests -p 'test_goatcounter_origin_*.py' -v`
runs the focused offline suite. OCI/RPi integration cases require the pinned
`.rpi-release` checkout supplied by the release workflow; ordinary CI explicitly
skips those cases when it is absent. Real ARM64 proof is performed by the release
job. Publication itself requires the separate decision above and is not a PR test.

References checked during implementation:
[OCI exporter](https://docs.docker.com/build/exporters/oci-docker/),
[Docker provenance](https://docs.docker.com/build/metadata/attestations/slsa-provenance/),
[Skopeo copy](https://github.com/podman-container-tools/skopeo/blob/main/docs/skopeo-copy.1.md),
[GitHub hosted runner platforms](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
