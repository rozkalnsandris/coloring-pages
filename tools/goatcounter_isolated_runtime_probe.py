"""Opt-in isolated GoatCounter v2.7.0 runtime proof with synthetic data only.

No downloads, Docker, real users, public traffic, production access, RPi5
operations, or GitHub workflow mutations. Requires a separately obtained and
independently reviewed local binary plus its exact expected SHA-256. Starts one
loopback listener in a fresh private temporary directory, writes ONLY
synthetic test data, shuts down, and invokes the read-only SQLite probe.

The result is NOT a legal clearance, identity proof for downloaded binaries,
Cloudflare/proxy-log assessment, or LIVE authorization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import secrets
import signal
import socket
import sqlite3
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from goatcounter_offline_privacy_probe import (
    DB_NAME, MARKER, MARKER_BYTES, PREFIX, ProbeStop, inspect_fixture,
)

HOST = "stats.example.test"
EMAIL = "goatcounter-probe@example.com"
PAGE_ID = "0427183"
PAGE_PATH = "/coloring-page/" + PAGE_ID
VIEWS = 2


class RuntimeStop(Exception):
    """Stable failure code: never include tokens, paths or raw DB records."""


def _stop(code: str) -> None:
    raise RuntimeStop(code)


def _host_guard() -> None:
    if (platform.node().split(".", 1)[0].casefold() == "rpi5"
            or (hasattr(os, "geteuid") and os.geteuid() == 0)):
        _stop("UNSAFE_HOST_OR_ROOT")


def _verified_binary(path_arg: str, expected_digest: str) -> Path:
    path = Path(path_arg)
    if (not path.is_absolute() or path.is_symlink() or not path.is_file()
            or re.fullmatch(r"[0-9a-f]{64}", expected_digest) is None):
        _stop("BINARY_INPUT_INVALID")
    if not os.access(path, os.X_OK):
        _stop("BINARY_NOT_EXECUTABLE")
    if path.stat().st_size > 128 * 1024 * 1024:
        _stop("BINARY_TOO_LARGE")
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(1024 * 1024)
            if not block:
                break
            hasher.update(block)
    if hasher.hexdigest() != expected_digest:
        _stop("BINARY_DIGEST_MISMATCH")
    return path


def _isolated_env(root: Path) -> dict[str, str]:
    # No proxy, inherited auth token, production HOME or GOATCOUNTER_ flags.
    return {
        "HOME": str(root), "TMPDIR": str(root), "TZ": "UTC",
        "PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C",
    }


def _run(binary: Path, root: Path, env: dict[str, str], *argv: str) -> None:
    try:
        result = subprocess.run(
            [str(binary), *argv], cwd=root, env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=20, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        _stop("BINARY_COMMAND_ERROR")
    if result.returncode != 0:
        _stop("BINARY_COMMAND_REJECTED")


def _version(binary: Path, root: Path, env: dict[str, str]) -> None:
    try:
        p = subprocess.run(
            [str(binary), "version", "-json"], cwd=root, env=env,
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, timeout=10, check=False,
        )
        data = json.loads(p.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        _stop("VERSION_READ_FAILED")
    if (p.returncode != 0 or not isinstance(data, dict)
            or data.get("version") not in ("2.7.0", "v2.7.0")):
        _stop("WRONG_GOATCOUNTER_VERSION")


def _make_site(binary: Path, root: Path, env: dict[str, str], db: Path) -> str:
    db_arg = "sqlite+" + str(db)
    _run(binary, root, env, "db", "newdb", "-db=" + db_arg)
    # Test credentials exist only inside this temporary synthetic database.
    password = secrets.token_hex(20)
    _run(binary, root, env, "db", "create", "site",
         "-vhost=" + HOST, "-user.email=" + EMAIL,
         "-user.password=" + password, "-db=" + db_arg)
    password = ""
    _run(binary, root, env, "db", "create", "apitoken",
         "-user=" + EMAIL, "-name=synthetic-count-only",
         "-perm=count", "-db=" + db_arg)
    try:
        with sqlite3.connect(db, timeout=2) as con:
            con.row_factory = sqlite3.Row
            sites = con.execute(
                "SELECT site_id, settings FROM sites"
            ).fetchall()
            tokens = con.execute(
                "SELECT token FROM api_tokens"
            ).fetchall()
            if len(sites) != 1 or len(tokens) != 1:
                _stop("SYNTHETIC_SITE_OR_TOKEN_COUNT")
            settings = json.loads(sites[0]["settings"])
            if not isinstance(settings, dict):
                _stop("SYNTHETIC_SETTINGS_INVALID")
            settings["collect"] = 1  # CollectNothing, not zero/defaults.
            settings["ignore_ips"] = []
            con.execute(
                "UPDATE sites SET settings=? WHERE site_id=?",
                (json.dumps(settings, separators=(",", ":")), sites[0]["site_id"]),
            )
            token = tokens[0]["token"]
            if not isinstance(token, str) or len(token) < 16:
                _stop("SYNTHETIC_TOKEN_INVALID")
            return token
    except (sqlite3.DatabaseError, ValueError, TypeError):
        _stop("SYNTHETIC_DATABASE_SETUP")


def _free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _tcp_ready(port: int, proc: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            _stop("SERVER_EARLY_EXIT")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.1)
    _stop("LOOPBACK_NOT_READY")


def _count_once(port: int, token: str) -> None:
    # Never forward caller-supplied JSON, UA, IP, referrer or UTM.
    body = json.dumps(
        {"no_sessions": True, "hits": [{"path": PAGE_PATH}]},
        separators=(",", ":"),
    ).encode("ascii")
    request = urllib.request.Request(
        "http://127.0.0.1:" + str(port) + "/api/v0/count",
        data=body, method="POST",
        headers={
            "Host": HOST,
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )
    try:
        # Exactly one HTTP transmission. Never resend after ambiguity.
        with urllib.request.urlopen(request, timeout=5) as response:
            if response.status != 202:
                _stop("BACKEND_NOT_ACCEPTED")
            response.read(1024)
    except (OSError, urllib.error.HTTPError, ValueError):
        _stop("BACKEND_RESPONSE_UNCERTAIN")


def _stop_server(proc: subprocess.Popen[bytes]) -> None:
    if proc.poll() is None:
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=12)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
            _stop("SERVER_SHUTDOWN_TIMEOUT")


def run_isolated(binary_arg: str, digest_arg: str) -> str:
    _host_guard()
    binary = _verified_binary(binary_arg, digest_arg)
    with tempfile.TemporaryDirectory(prefix=PREFIX) as temp:
        root = Path(temp)
        os.chmod(root, 0o700)
        env = _isolated_env(root)
        _version(binary, root, env)
        db = root / DB_NAME
        token = _make_site(binary, root, env, db)
        (root / MARKER).write_bytes(MARKER_BYTES)
        port = _free_loopback_port()
        proc = None
        try:
            proc = subprocess.Popen(
                [str(binary), "serve", "-db=sqlite+" + str(db),
                 "-listen=127.0.0.1:" + str(port), "-tls=http",
                 "-store-every=1"],
                cwd=root, env=env, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            _tcp_ready(port, proc)
            for _ in range(VIEWS):
                _count_once(port, token)
            token = ""  # Never output or retain credential after submission.
            # v2.7 count endpoint returns 202 before SQLite persistence.
            time.sleep(3)
        except OSError:
            _stop("LOOPBACK_PROCESS_ERROR")
        finally:
            if proc is not None:
                _stop_server(proc)
        try:
            inspect_fixture(root, page_id=PAGE_ID, expected_views=VIEWS)
        except ProbeStop:
            _stop("ISOLATED_SQLITE_PRIVACY_GATE")
    return "PASS_SYNTHETIC_GOATCOUNTER_RUNTIME_ONLY_NOT_LIVE_OR_LEGAL_PROOF"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True)
    parser.add_argument("--expected-binary-sha256", required=True)
    args = parser.parse_args()
    try:
        result = run_isolated(args.binary, args.expected_binary_sha256)
    except (RuntimeStop, OSError) as exc:
        code = str(exc) if isinstance(exc, RuntimeStop) else "ISOLATION_IO_ERROR"
        print("GOATCOUNTER_ISOLATED=STOP CODE=" + code)
        return 2
    print("GOATCOUNTER_ISOLATED=" + result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
