# Opt-in application image and private socket wiring (#376)

This is the application integration following #424 and RPi5_main #1275. It is
source-only. The default Dockerfile, Compose, SIMPLE-DEPLOY metadata, production
pointer and publication workflow do not select this variant. Merging these
files does not publish the derivative, mount a socket or activate public counts.

## Image and Compose contract

`deploy/Dockerfile.origin-counting` takes an explicitly selected application
image through `APPLICATION_IMAGE`. For a real rollout it must be a reviewed
`ghcr.io/rozkalnsandris/coloring-pages@sha256:<64 lowercase hex>` digest with
verified linux/arm64 provenance. Do not use a mutable tag. The Dockerfile argument
is not a provenance validator: freeze and verify that base identity before build.
The renderer must match the application source/configuration selected for that
build. It refuses a pre-integrated or unexpected Nginx insertion layout.

The derivative preserves the application files/importer and creates the additional
`/etc/nginx/nginx-origin.conf`. Nginx runs as UID 101 with that exact baked config,
without an environment-templating entrypoint. The inherited image's original
Nginx config stays present but is not the derivative's active config. The default
application image still runs its original configuration.

Build the derivative only in the later explicitly approved publication operation;
record both base digest and resulting arm64 derivative digest. Use the separate
`ghcr.io/rozkalnsandris/coloring-pages-origin` image name, never retag it as the
default application's `:production`. This source change supplies no registry
push workflow or production command.

`tools/goatcounter_origin_compose.py` generates a new JSON Compose override from
two mandatory arguments: `--image` (that derivative repository and immutable
SHA-256 digest) and `--socket-group` (positive decimal container-visible group).
It accepts no tag, other registry/repository, root/named/interpolated group,
leading-zero group or existing output file. `--output` is mandatory. Generation
does not invoke Docker, read credentials or inspect/change host state.

The override targets only the existing `coloring-pages` service. It selects
linux/arm64, adds that supplementary group, and adds exactly the read-only bind
of `/run/ausmalwiese-pageview` at the same path, with `create_host_path: false`.
The socket directory must already exist; do not let Compose create a replacement.
The directory bind follows socket inode replacement and still permits intended
IPC writes. It does not expose the database, credential or other host directories.
The existing content volume, ports, health checks and container hardening remain
in the base Compose configuration.

The supplemental group grants filesystem access; it does not replace the
collector's primary host UID/GID `SO_PEERCRED` check. Revalidate user namespace
mapping, actual peer identity and the container-visible group mapping to the
socket's host group under the final authorized rollout. Do not reuse an earlier
numeric observation as evergreen authority or guess the socket group from UID 101.

RPi5_main must separately integrate this opt-in image/override into its trusted
deployment source. The generic SIMPLE-DEPLOY reconciler still selects the default
application; this PR does not configure it to preserve an origin variant. Public
activation must wait for reviewed reconciler ownership, so a later ordinary app
update cannot silently remove or replace the selected variant. Do not manually
apply an overlay behind an unaware reconciler.

## Request and logging behavior

The reviewed #424 query grammar, fixed four-header/21-byte message, catalog check,
private Unix destination, timeouts and no-retry semantics remain in effect. There
is no new browser event or public collector route. Like/Print/QR/campaign source
and historical data are unchanged. See [transport semantics](GOATCOUNTER_ORIGIN_TRANSPORT_376.md).

The counting variant now also disables **ordinary detail-route access logging**.
Both detail-route and mirror error logging were already suppressed to prevent
original metadata leakage on upstream failures. This removes raw detail-request
diagnostics; collector failures can lose counts without a per-request log.
Other origin routes and edge logs retain their prior behavior and must still be
covered by the actual-flow privacy assessment. This is not end-to-end anonymity.
Only eligible origin requests count; cache hits, dropped attempts and pre-mirror
failures do not. Repeats, bots, conditional responses and later HTML failures can
count. Do not label the result successful page renders or unique visitors.

## Validation and limitations

The isolated workflow builds the current full application Dockerfile using the
already pinned amd64 Nginx manifest, then builds the real derivative recipe. The
local CI base tag refers only to that newly built fixture; it is not a production
image policy exception. The proof compares hashes of all public files/importer
tools between base and derivative and compares the baked Nginx config to the exact
renderer output. The network-isolated derivative then serves synthetic HTML with
the existing wire/failure/permission/socket-replacement test suite. It mounts no
configuration override, so it exercises the derivative's actual CMD/config.

Docker Compose itself normalizes the generated override merged with the default
source: only image/platform/group and one narrow bind may differ. Pure tests
cover malformed identities, overwrite/symlink rejection and default isolation.
The job has read-only GitHub permissions, no push, deployment, RPi5 or secrets.
It does not prove arm64 runtime behavior, production user mappings, real stored
events, retention cleanup, protected reporting or legal readiness.

## Activation prerequisites remain open

1. Fresh exact application and private collector baseline; the dated private
   readiness [receipt](https://github.com/rozkalnsandris/RPi5_main/pull/1275#issuecomment-6556300753)
   establishes successful private installation only.
2. Protected aggregate reader/reporting for `/origin-detail-request/` with its own
   read-only credential boundary; the current count-only token is not broadened.
3. Actual-flow privacy/notice/logging assessment coordinated with legal PR #158.
4. Reviewed RPi5 deployment/reconciler integration and explicit source merges,
   derivative publication and bounded runtime/public-activation authorization.
   Existing authorizations are consumed; source continuation is NO-LIVE.
5. Final arm64 image, group/peer, socket and health verification plus explicitly
   authorized event/storage observation. A live detail GET after activation can
   write a count and is not read-only. Capture activation time and verification
   limits; no unapproved retry, cleanup, rollback or old-browser fallback.

Official references: [Docker Compose services](https://docs.docker.com/reference/compose-file/services/)
(`group_add`, read-only bind and `create_host_path`),
[Nginx mirror](https://nginx.org/en/docs/http/ngx_http_mirror_module.html).
