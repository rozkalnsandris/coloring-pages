# Origin-request transport implementation and isolated proof (#376)

Implements the first transport boundary from the accepted
[origin-request plan](GOATCOUNTER_ORIGIN_REQUEST_PLAN_376.md), merged in #419.
This source produces and tests a candidate Nginx configuration; it does not
modify the application's current `deploy/nginx.conf`, Dockerfile or Compose.
The separate [opt-in application image](GOATCOUNTER_ORIGIN_APP_376.md) now bakes
this generator's output. Default deployment still does not select it, and merging
its source does not activate collection. Public collection remains held.

## Source components

- `tools/goatcounter_origin_nginx.py` renders the existing Nginx configuration
  plus a private Unix mirror into a **new** explicitly named output file. It
  rejects an unexpected insertion layout or an already-integrated config.
- `tools/goatcounter_origin_contract.py` independently validates the exact
  minimized message and published catalog ID, producing the distinct
  `/origin-detail-request/<id>` GoatCounter payload with `no_sessions: true`.
  It is a pure protocol specification for the forthcoming RPi5 listener, not a
  network listener or a credential-bearing backend sender.
- `tools/goatcounter_origin_isolated_probe.py` exercises the generated config
  using actual pinned Nginx and a synthetic Unix receiver on GitHub-hosted CI.
- `.github/workflows/goatcounter-origin-isolated.yml` runs the proof on relevant
  PRs and main changes with read-only repository permissions. It has no deploy,
  credential, public traffic or RPi5 step.

The renderer preserves ordinary page/cache/Like/Print/QR/campaign behavior. Only
the exact normalized `/detail.html` route gains an internal mirror. The original
method and validated ID are frozen before the subrequest changes URI context.
The upstream target, method, headers, length and body are constructed afresh;
inherited query arguments are discarded. No retry, raw event spool or public
collector route is added. Main detail and mirror access logging and **both mirror and main detail
route error logging** are disabled. The real failure probe showed that suppressing
only the mirror location's error log still exposed the original URL/referrer
through the main connection's error log. This deliberately removes ordinary
detail-route error diagnostics too; the eventual collector must use bounded,
sanitized health/error classes, not raw requests. Origin access logging
and error logs for other routes are unchanged and remain a separate processing/
release assessment. This is not a claim that all origin logs are anonymous.

The real-Nginx probe caught that a trailing `?` on a static `proxy_pass` URI does
not discard inherited query arguments. The candidate explicitly clears `$args`
inside the internal subrequest after freezing the eligible ID. Exact-target and
sentinel assertions guard against forwarding any original query.

## Deliberately conservative query grammar

Only GET, 1–2048 query characters, one literal case-sensitive `id` and seven
ASCII digits qualify. Preserve leading zeroes. All keys must be nonempty literal
ASCII letters/digits or `_ . ~ -`; all fields must have `=`. Values may contain
ASCII URL characters or valid `%HH` escapes. Additional values are discarded.
Duplicate `id`, any `ID`/`Id`/`iD` alias, **any encoded query key**, malformed
escapes, empty fields, bare keys or encoded id digits drop measurement while HTML
still follows its normal delivery path. This conservative subset can undercount
otherwise valid application requests; it is explicit, not silent normalization.

The receiver accepts exactly four headers (Host, Content-Type, Content-Length,
Connection), exact POST `/internal/origin-count`, and the fixed 21-byte JSON body.
It rejects hidden, unknown or malformed/duplicate catalog data independently.
The Host value is not authentication. The real listener must enforce Unix socket
permissions and the expected Linux peer identity before accepting this shape.

## Isolation and coverage

The probe is restricted to ephemeral GitHub-hosted runners. It creates temporary
synthetic HTML/catalog/socket files and one container with `--network none`,
read-only root, no capabilities, CPU/memory/PID bounds and a bounded /tmp tmpfs.
It mounts only its three fixture paths, with no production files or Docker socket
inside the container. The container has no external network path. The host mock
constructs backend payloads in memory; it never calls GoatCounter.

Pinned Linux amd64 Nginx 1.29.1 image manifest (resolved from the official
`nginxinc/nginx-unprivileged:1.29.1-alpine` tag on 2026-10-29):
`sha256:6742337773a7ca839e7a76f489cc684cc410e3de46c0c83be8bb2bb9944360ef`.
The matching published arm64 manifest is
`sha256:a16464a6a6fb8251820e5335aaf57e7947482e44a5d48d5272d40068d2557bcf`;
this PR does not claim to have executed that architecture or the deployed image.

Assertions cover valid leading-zero IDs, discarded campaign/other values,
malformed/duplicate/encoded/case-alias IDs, HEAD/POST/other paths, direct internal
route denial, private-header/body stripping, catalog rejection, repeated and
parallel requests, conditional 304 requests, final HTML failure, slow/malformed/
absent receiver, no retries, socket permission denial and socket replacement.
The read-only directory mount permits IPC but refuses file creation. The fixture
asserts observed peer UID 101 and supplies only the runner's resolved group ID;
it does not infer production UID mappings or invent production group numbers.

Slow receiver checks bound the complete response time to 1.5 seconds in the
ephemeral fixture, with 100 ms connect/send and 200 ms read timeouts. This is not
a production latency SLO or a proof against arbitrary traffic floods. Cache hits
that never contact this origin cannot count. There is no lossless/dedup/2xx-only
claim: repeated/conditional requests and later HTML failures can count.

The pinned integration also distinguishes two failure phases: `try_files` rejects
a missing HTML file before mirroring (no attempt), while a static-handler read
permission failure after mirroring can count despite a final 403. The probe
checks both. This is not a count of successful responses or all origin arrivals.

## Remaining activation prerequisites

1. RPi5_main must implement the bounded Unix listener/peer checks, socket lifecycle
   and service integration using the existing count-only credential. Freeze a
   reviewed source/install envelope and a fresh allowed host baseline; the
   completed private-install/retention authorizations cannot be reused.
2. The app must explicitly adopt the generated config plus a dedicated directory
   bind and verified supplementary group. Capture the exact application image
   and architecture, preserve existing delivery behavior, and run the same proof
   against that final configuration. Source candidate success is not deployment.
3. Implement the separately protected aggregate reader and truthful reporting
   labels, and resolve the actual-flow privacy/notice/logging assessment in #158.
4. Obtain exact source merge and separate runtime/public-activation authority.
   A live detail GET after cutover can write analytics; it is not read-only.

The existing browser PR #391 and public pageview tunnel path remain superseded.
Do not use them as a fallback when the Unix transport is unavailable.

Official references: [Nginx mirror](https://nginx.org/en/docs/http/ngx_http_mirror_module.html),
[Nginx proxy](https://nginx.org/en/docs/http/ngx_http_proxy_module.html),
[GoatCounter backend API](https://www.goatcounter.com/help/backend).
