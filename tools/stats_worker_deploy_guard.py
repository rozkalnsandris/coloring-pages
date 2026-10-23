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
CONTRACT_PATH = "deploy/stats-worker-exact-source-v2.json"
SOURCE_PATH = "cloudflare/stats-worker.js"
CONFIG_PATH = "cloudflare/wrangler.stats-worker.jsonc"
ADDITIVE_MIGRATION_PATH = "cloudflare/stats-cookie-like-migration.sql"
CLEANUP_MIGRATION_PATH = "cloudflare/stats-remove-daily-visitor-hmac.sql"

WORKER = "coloring-pages-stats-v1"
BLOB = "ccb68d7bbf12474f32e0f94d574ead1b02cd9c7e"
CONFIG_BLOB = "3733263a391274f2b6b0f2023c8656565bde8e1a"
ADDITIVE_MIGRATION_BLOB = "b5346c05cb27de1010dab2027b0b923e999af775"
CLEANUP_MIGRATION_BLOB = "a7cffb110adfceb5c1ff4dcd17a7009c549976a5"

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
LIVE_SEQUENCE = [
    "additive-migration-before-worker",
    "worker-version-upload",
    "worker-version-deploy-100-percent",
    "read-only-runtime-verification",
    "cron-trigger-separate-owner-gate",
    "legacy-daily-visitors-cleanup-separate-owner-gate",
]
EXCLUDED = frozenset({
    "worker-name", "worker-routes", "worker-custom-domains",
    "worker-bindings", "worker-secrets", "worker-vars",
    "cloudflare-zone-dns", "access-waf", "other-workers",
    "unlisted-d1-schema-data", "automatic-retry", "automatic-rollback",
    "automatic-cleanup",
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
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


def _check_blob(root: Path, path: str, expected: str, *, limit: int, error: str) -> None:
    if git_blob_sha1(_fixed_file(root, path, limit=limit)) != expected:
        raise GuardFailure(error)


def check_source_contract(root: Path = ROOT) -> dict[str, str]:
    """Validate immutable Worker/config/migration identities and review contract."""
    try:
        c = json.loads(_fixed_file(root, CONTRACT_PATH, limit=16000))
    except (ValueError, UnicodeError) as exc:
        raise GuardFailure("CONTRACT_INVALID") from exc

    required = {
        "schema", "repository", "worker", "environment", "source_path",
        "source_blob_sha1", "wrangler_config_path", "wrangler_config_blob_sha1",
        "additive_migration_path", "additive_migration_blob_sha1",
        "cleanup_migration_path", "cleanup_migration_blob_sha1",
        "qr_host", "qr_destination", "routes", "bindings", "live_sequence",
        "excluded_changes", "deployment_mode",
    }
    if not isinstance(c, dict) or set(c) != required:
        raise GuardFailure("CONTRACT_KEYS")

    fixed = {
        "schema": "ausmalwiese.stats-worker-exact-source-deploy.v2",
        "repository": "rozkalnsandris/coloring-pages",
        "worker": WORKER,
        "environment": "production",
        "source_path": SOURCE_PATH,
        "source_blob_sha1": BLOB,
        "wrangler_config_path": CONFIG_PATH,
        "wrangler_config_blob_sha1": CONFIG_BLOB,
        "additive_migration_path": ADDITIVE_MIGRATION_PATH,
        "additive_migration_blob_sha1": ADDITIVE_MIGRATION_BLOB,
        "cleanup_migration_path": CLEANUP_MIGRATION_PATH,
        "cleanup_migration_blob_sha1": CLEANUP_MIGRATION_BLOB,
        "qr_host": QR_HOST,
        "qr_destination": QR_DEST,
        "deployment_mode": "separate-owner-authorized-trusted-operator-only",
    }
    if any(c.get(k) != v for k, v in fixed.items()):
        raise GuardFailure("CONTRACT_IDENTITY")
    if (not isinstance(c["routes"], list)
            or len(c["routes"]) != len(ROUTES)
            or set(c["routes"]) != ROUTES):
        raise GuardFailure("CONTRACT_ROUTES")
    if type(c["bindings"]) is not dict or c["bindings"] != BINDINGS:
        raise GuardFailure("CONTRACT_BINDINGS")
    if c["live_sequence"] != LIVE_SEQUENCE:
        raise GuardFailure("CONTRACT_LIVE_SEQUENCE")
    if (not isinstance(c["excluded_changes"], list)
            or len(c["excluded_changes"]) != len(EXCLUDED)
            or set(c["excluded_changes"]) != EXCLUDED):
        raise GuardFailure("CONTRACT_EXCLUSIONS")

    _check_blob(
        root, CONFIG_PATH, CONFIG_BLOB, limit=20000,
        error="CONFIG_BLOB_DRIFT",
    )
    _check_blob(
        root, ADDITIVE_MIGRATION_PATH, ADDITIVE_MIGRATION_BLOB, limit=30000,
        error="ADDITIVE_MIGRATION_BLOB_DRIFT",
    )
    _check_blob(
        root, CLEANUP_MIGRATION_PATH, CLEANUP_MIGRATION_BLOB, limit=10000,
        error="CLEANUP_MIGRATION_BLOB_DRIFT",
    )

    data = _fixed_file(root, SOURCE_PATH, limit=150000)
    if git_blob_sha1(data) != BLOB:
        raise GuardFailure("WORKER_BLOB_DRIFT")
    try:
        source = data.decode("utf-8")
    except UnicodeError as exc:
        raise GuardFailure("WORKER_ENCODING") from exc
    if (f'const PRINT_QR_HOST = "{QR_HOST}";' not in source
            or f'const PRINT_QR_DESTINATION = "{QR_DEST}";' not in source
            or 'const DEFAULT_ORIGIN = "https://coloring.rozkalns.net";' not in source
            or "LIKE_COOKIE_TTL_SECONDS" not in source
            or "/api/stats/print-aggregate" not in source):
        raise GuardFailure("WORKER_PRIVACY_OR_ORIGIN_DRIFT")

    return {
        "worker": WORKER,
        "blob": BLOB,
        "result": "SOURCE_CONTRACT_OK_NOT_LIVE_PROOF",
    }


def check_sanitized_inventory(payload: Any) -> dict[str, Any]:
    """Pure structural check; caller must independently authenticate LIVE evidence."""
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
        if type(binding) is not dict or set(binding) != {
            "name", "type", "fingerprint"
        }:
            raise GuardFailure("INVENTORY_BINDING_FIELDS")
        name = binding["name"]
        if (type(name) is not str or name in fingerprints
                or BINDINGS.get(name) != binding["type"]):
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
    """Reject route, binding, or nonsecret target drift after a future deploy."""
    old = check_sanitized_inventory(before)
    new = check_sanitized_inventory(after)
    if old["version"] == new["version"]:
        raise GuardFailure("VERSION_NOT_CHANGED")
    if old["fingerprints"] != new["fingerprints"]:
        raise GuardFailure("BINDING_VALUE_OR_TARGET_DRIFT")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stats Worker SOURCE-ONLY deployment contract check"
    )
    parser.add_argument("--check-contract", required=True, action="store_true")
    args = parser.parse_args()
    try:
        outcome = check_source_contract()
    except GuardFailure as exc:
        print("STOP_SOURCE_CONTRACT_" + str(exc))
        return 2
    if args.check_contract:
        print(
            outcome["result"]
            + " worker=" + outcome["worker"]
            + " blob=" + outcome["blob"]
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
