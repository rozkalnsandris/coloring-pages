"""Offline, source-only guard for one Ausmalwiese Stats Worker deployment.

No credentials, Cloudflare requests, Wrangler invocation, or LIVE write path.
Sanitized inventories are data supplied by a *separately trusted* operator;
these pure checks do not authenticate them or authorize deployment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = "deploy/stats-worker-exact-source-v1.json"
SOURCE_PATH = "cloudflare/stats-worker.js"
WORKER = "coloring-pages-stats-v1"
BLOB = "dd5a2859d55b9ef2d9fb9a9d8bf0a535d25a5ba4"
QR_HOST = "ausmalwiese.de"
QR_DEST = "https://ausmalwiese.de/"
ROUTES = frozenset({
    "coloring.rozkalns.net/api/stats/*",
    "ausmalwiese.de/api/stats/*",
    "www.ausmalwiese.de/api/stats/*",
    "ausmalwiese.de/q",
})
BINDINGS = {
    "DB": "d1_database",
    "RATE_LIMITER": "rate_limiter",
    "PUBLIC_ORIGIN": "plain_text",
    "CF_ANALYTICS_HOST": "plain_text",
    "CF_ZONE_TAG": "plain_text",
    "VISITOR_HMAC_KEY": "secret_text",
    "CF_ANALYTICS_API_TOKEN": "secret_text",
}
EXCLUDED = frozenset({
    "worker-name", "worker-routes", "worker-custom-domains",
    "worker-bindings", "worker-secrets", "worker-vars", "d1-schema-data",
    "cloudflare-zone-dns", "access-waf", "other-workers",
})
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
VERSION = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z")


class GuardFailure(ValueError):
    """Stable source or sanitized-inventory mismatch (no secret details)."""


def _fixed_file(root: Path, rel: str, *, limit: int) -> bytes:
    path = root / rel
    try:
        if path.is_symlink():
            raise GuardFailure("FILE_SYMLINK")
        mode = path.stat().st_mode
        if not stat.S_ISREG(mode) or path.stat().st_size > limit:
            raise GuardFailure("FILE_IDENTITY")
        return path.read_bytes()
    except (OSError, UnicodeError) as exc:
        raise GuardFailure("FILE_UNREADABLE") from exc


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def check_source_contract(root: Path = ROOT) -> dict[str, str]:
    """Validate an immutable Worker byte identity and the fixed review contract."""
    try:
        c = json.loads(_fixed_file(root, CONTRACT_PATH, limit=12000))
    except (ValueError, UnicodeError) as exc:
        raise GuardFailure("CONTRACT_INVALID") from exc
    required = {
        "schema", "repository", "worker", "environment", "source_path",
        "source_blob_sha1", "qr_host", "qr_destination", "routes",
        "bindings", "excluded_changes", "deployment_mode",
    }
    if not isinstance(c, dict) or set(c) != required:
        raise GuardFailure("CONTRACT_KEYS")
    fixed = {
        "schema": "ausmalwiese.stats-worker-exact-source-deploy.v1",
        "repository": "rozkalnsandris/coloring-pages",
        "worker": WORKER,
        "environment": "production",
        "source_path": SOURCE_PATH,
        "source_blob_sha1": BLOB,
        "qr_host": QR_HOST,
        "qr_destination": QR_DEST,
        "deployment_mode": "separate-owner-authorized-trusted-operator-only",
    }
    if any(c.get(k) != v for k, v in fixed.items()):
        raise GuardFailure("CONTRACT_IDENTITY")
    if not isinstance(c["routes"], list) or len(c["routes"]) != 4 or set(c["routes"]) != ROUTES:
        raise GuardFailure("CONTRACT_ROUTES")
    if type(c["bindings"]) is not dict or c["bindings"] != BINDINGS:
        raise GuardFailure("CONTRACT_BINDINGS")
    if not isinstance(c["excluded_changes"], list) or len(c["excluded_changes"]) != len(EXCLUDED) or set(c["excluded_changes"]) != EXCLUDED:
        raise GuardFailure("CONTRACT_EXCLUSIONS")
    data = _fixed_file(root, SOURCE_PATH, limit=150000)
    if git_blob_sha1(data) != BLOB:
        raise GuardFailure("WORKER_BLOB_DRIFT")
    try:
        source = data.decode("utf-8")
    except UnicodeError as exc:
        raise GuardFailure("WORKER_ENCODING") from exc
    if (f'const PRINT_QR_HOST = "{QR_HOST}";' not in source
            or f'const PRINT_QR_DESTINATION = "{QR_DEST}";' not in source
            or 'const DEFAULT_ORIGIN = "https://coloring.rozkalns.net";' not in source):
        raise GuardFailure("WORKER_QR_OR_ORIGIN_DRIFT")
    return {"worker": WORKER, "blob": BLOB, "result": "SOURCE_CONTRACT_OK_NOT_LIVE_PROOF"}


def check_sanitized_inventory(payload: Any) -> dict[str, Any]:
    """Pure structural check; the caller must independently authenticate LIVE evidence.

    Hashes for nonsecret identities/values are produced inside a trusted
    reader and are never written to this repository. Secrets expose only
    binding name and kind, never a value or digest.
    """
    if type(payload) is not dict or set(payload) != {
        "schema", "worker", "environment", "version", "traffic_percent",
        "routes", "bindings",
    }:
        raise GuardFailure("INVENTORY_KEYS")
    if (payload["schema"] != "ausmalwiese.stats-worker-sanitized-inventory.v1"
            or payload["worker"] != WORKER
            or payload["environment"] != "production"
            or type(payload["version"]) is not str
            or not VERSION.fullmatch(payload["version"])
            or type(payload["traffic_percent"]) is not int
            or payload["traffic_percent"] != 100):
        raise GuardFailure("INVENTORY_TARGET_OR_VERSION")
    routes = payload["routes"]
    if (type(routes) is not list or len(routes) != len(ROUTES)
            or any(type(x) is not str for x in routes)
            or set(routes) != ROUTES):
        raise GuardFailure("INVENTORY_ROUTES")
    bindings = payload["bindings"]
    if type(bindings) is not list or len(bindings) != len(BINDINGS):
        raise GuardFailure("INVENTORY_BINDING_COUNT")
    fingerprints: dict[str, str | None] = {}
    for binding in bindings:
        if type(binding) is not dict or set(binding) != {"name", "type", "fingerprint"}:
            raise GuardFailure("INVENTORY_BINDING_FIELDS")
        name = binding["name"]
        if type(name) is not str or name in fingerprints or BINDINGS.get(name) != binding["type"]:
            raise GuardFailure("INVENTORY_BINDING_IDENTITY")
        fingerprint = binding["fingerprint"]
        if binding["type"] == "secret_text":
            if fingerprint is not None:
                raise GuardFailure("INVENTORY_SECRET_EXPOSURE")
        elif type(fingerprint) is not str or not SHA256.fullmatch(fingerprint):
            raise GuardFailure("INVENTORY_FINGERPRINT")
        fingerprints[name] = fingerprint
    if set(fingerprints) != set(BINDINGS):
        raise GuardFailure("INVENTORY_BINDING_SET")
    return {"version": payload["version"], "fingerprints": fingerprints}


def compare_sanitized_inventories(before: Any, after: Any) -> None:
    """Reject any route, binding, or nonsecret target drift after a future deploy.

    Does not verify source bytes at Cloudflare or independently attest either
    snapshot. Trusted live pre/post collection remains a separate owner gate.
    """
    old = check_sanitized_inventory(before)
    new = check_sanitized_inventory(after)
    if old["version"] == new["version"]:
        raise GuardFailure("VERSION_NOT_CHANGED")
    if old["fingerprints"] != new["fingerprints"]:
        raise GuardFailure("BINDING_VALUE_OR_TARGET_DRIFT")


def main() -> int:
    parser = argparse.ArgumentParser(description="Stats Worker SOURCE-ONLY deployment contract check")
    parser.add_argument("--check-contract", required=True, action="store_true")
    args = parser.parse_args()
    try:
        outcome = check_source_contract()
    except GuardFailure as exc:
        print("STOP_SOURCE_CONTRACT_" + str(exc))
        return 2
    if args.check_contract:
        print(outcome["result"] + " worker=" + outcome["worker"] + " blob=" + outcome["blob"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
