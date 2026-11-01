#!/usr/bin/env python3
"""Synthetic Nginx/Unix IPC proof on an ephemeral GitHub runner only.

No GoatCounter binary, production catalog, host service, credential or database.
Only a pinned network-isolated test container and newly created /tmp files.
"""
from __future__ import annotations

import concurrent.futures
import argparse
from email.utils import formatdate
from http.server import BaseHTTPRequestHandler
import json
import os
from pathlib import Path
import socket
import socketserver
import struct
import subprocess
import tempfile
import threading
import time

from goatcounter_origin_contract import backend_message
from goatcounter_origin_nginx import render

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ("nginxinc/nginx-unprivileged@sha256:"
         "6742337773a7ca839e7a76f489cc684cc410e3de46c0c83be8bb2bb9944360ef")
CATALOG = [{"id": "0123456", "preview": "synthetic.webp", "print": "synthetic.png"},
           {"id": "1234567", "hidden": True, "preview": "x", "print": "x"}]


def run(*args: str, data: bytes | None = None, check: bool = True):
    return subprocess.run(args, input=data, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=30, check=check)


class MockServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        pass


class Receiver:
    def __init__(self, path: Path):
        self.path = path
        self.records = []
        self.backend = []
        self.mode = "ok"
        self.lock = threading.Lock()
        self.server = None

    def start(self):
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                self.connection.settimeout(1)
                peer = struct.unpack("3i", self.connection.getsockopt(
                    socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i")))
                headers = list(self.headers.items())
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(min(length, 129))
                with owner.lock:
                    owner.records.append((self.command, self.path, headers, body, peer[1]))
                    mode = owner.mode
                status = 202
                try:
                    assert peer[1] == 101, "fixture requires rootful Docker without UID remapping"
                    result = backend_message(self.command, self.path, headers, body, CATALOG)
                    with owner.lock:
                        owner.backend.append(result)
                except (ValueError, AssertionError):
                    status = 400
                if mode == "slow":
                    time.sleep(1)
                if mode == "malformed":
                    self.wfile.write(b"invalid upstream response\r\n")
                    return
                self.send_response(status)
                self.send_header("Content-Length", "0")
                self.end_headers()

        self.server = MockServer(str(self.path), Handler)
        os.chmod(self.path, 0o660)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(timeout=2)
            self.server = None
            self.path.unlink()

    def counts(self):
        with self.lock:
            return len(self.records), len(self.backend)


def probe(application_image=False):
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("RUNNER_ENVIRONMENT") != "github-hosted":
        raise RuntimeError("EPHEMERAL_GITHUB_RUNNER_REQUIRED")
    with tempfile.TemporaryDirectory(prefix="origin-probe-") as temp:
        root = Path(temp)
        ipc = root / "ipc"
        ipc.mkdir(mode=0o750)
        html = root / "html"
        html.mkdir(mode=0o755)
        for name in ("detail.html", "print.html", "index.html"):
            (html / name).write_text("synthetic page\n")
        config = root / "nginx.conf"
        # Disable ordinary access logging only in the fixture. Production logging
        # is a separate release assessment; renderer preserves its configuration.
        candidate = render((ROOT / "deploy/nginx.conf").read_text())
        config.write_text(candidate.replace("access_log /dev/stdout;", "access_log off;"))
        receiver = Receiver(ipc / "origin.sock")
        receiver.start()
        container = None
        try:
            selected_image = "coloring-pages-origin-app:ci" if application_image else IMAGE
            config_args = [] if application_image else [
                "--mount", f"type=bind,src={config},dst=/etc/nginx/nginx.conf,readonly"]
            command_args = [] if application_image else ["-g", "daemon off;"]
            container = run("docker", "run", "-d",
                            "--pull=never" if application_image else "--pull=always",
                            "--platform=linux/amd64",
                            "--network=none", "--read-only", "--user=101:101",
                            "--group-add=" + str(os.getgid()), "--cap-drop=ALL",
                            "--security-opt=no-new-privileges", "--pids-limit=32",
                            "--memory=64m", "--cpus=1", "--tmpfs=/tmp:rw,nosuid,nodev,size=16m",
                            *config_args,
                            "--mount", f"type=bind,src={ipc},dst=/run/ausmalwiese-pageview,readonly",
                            "--mount", f"type=bind,src={html},dst=/usr/share/nginx/html,readonly",
                            "--entrypoint=nginx", selected_image, *command_args).stdout.decode().strip()
            version = run("docker", "exec", container, "nginx", "-v")
            assert b"nginx/1.29.1" in version.stderr
            active_config = "/etc/nginx/nginx-origin.conf" if application_image else "/etc/nginx/nginx.conf"
            run("docker", "exec", container, "nginx", "-t", "-c", active_config)
            if application_image:
                baked = run("docker", "exec", container, "cat", active_config).stdout.decode()
                assert baked == candidate, "derivative must use exact rendered source configuration"

            def request(target, method="GET", body=b"", status=200, conditional=""):
                raw = (f"{method} {target} HTTP/1.1\r\nHost: example.invalid\r\n"
                       "Connection: close\r\nCookie: PRIVATE_COOKIE\r\n"
                       "Authorization: Bearer PRIVATE_AUTH\r\nUser-Agent: PRIVATE_UA\r\n"
                       "Referer: https://example.invalid/PRIVATE_REF\r\n"
                       "X-Forwarded-For: 192.0.2.99\r\nOrigin: https://example.invalid\r\n"
                       f"Content-Length: {len(body)}\r\n{conditional}\r\n").encode() + body
                start = time.monotonic()
                response = run("docker", "exec", "-i", container, "nc", "-w", "3",
                               "127.0.0.1", "8080", data=raw).stdout
                elapsed = time.monotonic() - start
                assert response.startswith(f"HTTP/1.1 {status} ".encode()), response[:100]
                if status == 200 and method == "GET" and target.split("?")[0] in (
                        "/detail.html", "/print.html", "/index.html"):
                    assert b"synthetic page" in response
                    assert b"Cache-Control: no-cache" in response
                return elapsed

            request("/ready")
            before = receiver.counts()
            valid = ["id=0123456", "campaign=PRIVATE_QUERY&id=0123456&x=a%20b", "x=&id=0123456"]
            for query in valid:
                request("/detail.html?" + query)
            assert receiver.counts() == (before[0] + 3, before[1] + 3), receiver.records
            rejected = ["id=123456", "id=12345678", "ID=0123456", "%69d=0123456",
                        "id=0123456&id=1234567", "id=0123456&Id=1234567",
                        "id=0123456&%69d=1234567", "id=0123456&x=%GG",
                        "id=0123456&", "&id=0123456", "id=0123456&bare",
                        "id=%30%31%32%33%34%35%36", "id=0123456&x=" + "a" * 2048]
            before = receiver.counts()
            for query in rejected:
                request("/detail.html?" + query)
            request("/detail.html")
            request("/detail.html?id=0123456", method="HEAD")
            request("/detail.html?id=0123456", method="POST", body=b"PRIVATE_BODY", status=405)
            request("/print.html?id=0123456")
            request("/__origin_count?id=0123456", status=404)
            assert receiver.counts() == before

            # Eligibility is checked again at the collector, not trusted from Nginx.
            request("/detail.html?id=1234567")
            request("/detail.html?id=9999999")
            assert receiver.counts() == (before[0] + 2, before[1])
            # Body/header minimization, even when an ordinary GET carries a body.
            request("/detail.html?id=0123456", body=b"PRIVATE_BODY")
            assert receiver.counts() == (before[0] + 3, before[1] + 1)
            before = receiver.counts()
            modified = formatdate((html / "detail.html").stat().st_mtime, usegmt=True)
            request("/detail.html?id=0123456", status=304,
                    conditional="If-Modified-Since: " + modified + "\r\n")
            assert receiver.counts() == (before[0] + 1, before[1] + 1)
            # Repeated and parallel requests count independently; no identifier dedup.
            before = receiver.counts()
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(request, ["/detail.html?id=0123456"] * 8))
            assert receiver.counts() == (before[0] + 8, before[1] + 8)
            # try_files runs before mirror: a missing file does not reach it.
            (html / "detail.html").unlink()
            before = receiver.counts()
            request("/detail.html?id=0123456", status=404)
            assert receiver.counts() == before
            (html / "detail.html").write_text("synthetic page\n")
            # A later static-handler permission failure occurs after mirror.
            os.chmod(html / "detail.html", 0o000)
            request("/detail.html?id=0123456", status=403)
            assert receiver.counts() == (before[0] + 1, before[1] + 1)
            os.chmod(html / "detail.html", 0o644)

            for mode in ("slow", "malformed"):
                receiver.mode = mode
                before = receiver.counts()
                assert request("/detail.html?id=0123456&secret=PRIVATE_QUERY") < 1.5
                assert receiver.counts() == (before[0] + 1, before[1] + 1)
            receiver.mode = "ok"
            # Read-only directory bind still supports IPC, but cannot create files.
            denied = run("docker", "exec", container, "touch",
                         "/run/ausmalwiese-pageview/forbidden", check=False)
            assert denied.returncode != 0 and not (ipc / "forbidden").exists()
            before = receiver.counts()
            os.chmod(receiver.path, 0o600)
            request("/detail.html?id=0123456&secret=PRIVATE_QUERY")
            assert receiver.counts() == before
            os.chmod(receiver.path, 0o660)
            receiver.stop()
            assert request("/detail.html?id=0123456&secret=PRIVATE_QUERY") < 1.5
            assert receiver.counts() == before
            receiver.start()  # same directory mount, new socket inode
            request("/detail.html?id=0123456")
            assert receiver.counts() == (before[0] + 1, before[1] + 1)
            for method, target, headers, body, uid in receiver.records:
                assert method == "POST" and target == "/internal/origin-count"
                assert uid == 101
                assert len(headers) == 4
                assert b"PRIVATE_" not in body
                assert "PRIVATE_" not in str(headers)
            logs = run("docker", "logs", container)
            if application_image:
                # Other routes keep ordinary access logs. Detail requests and
                # mirror failure diagnostics must not disclose their sentinels.
                assert b"PRIVATE_QUERY" not in logs.stdout + logs.stderr
                assert b"PRIVATE_" not in logs.stderr
                assert b" /detail.html" not in logs.stdout
            else:
                assert b"PRIVATE_" not in logs.stdout + logs.stderr
            print(json.dumps({"result": "PASS", "image": selected_image,
                              "baked_application_config": application_image,
                              "synthetic_wire_requests": receiver.counts()[0],
                              "synthetic_backend_payloads": receiver.counts()[1],
                              "live_data": False, "production_activation": False}))
        except Exception:
            if container:
                logs = run("docker", "logs", container, check=False)
                print((logs.stdout + logs.stderr).decode(errors="replace")[-4000:])
            raise
        finally:
            if container:
                run("docker", "rm", "-f", container, check=False)
            receiver.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--application-image", action="store_true")
    probe(parser.parse_args().application_image)
