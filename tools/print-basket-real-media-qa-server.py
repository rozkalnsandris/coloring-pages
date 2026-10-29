#!/usr/bin/env python3
"""Loopback-only real-media staging server for #199/#206 print QA.

This helper is intentionally not part of the production image. It serves the
current repository JS/CSS/assets plus a fresh public catalogue and only those
public print PNG paths that the catalogue itself currently authorizes.

It never writes media to disk, never exposes a LAN listener, never changes LIVE,
and never treats a staging result as visitor/physical-print approval.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_CATALOG_BYTES = 8 * 1024 * 1024
MAX_PRINT_BYTES = 32 * 1024 * 1024
SHA40 = re.compile(r"^[a-f0-9]{40}$")
ACTIVITY_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PRINT_PATH = re.compile(
    r"^/media/([a-z0-9]+(?:-[a-z0-9]+)*)/"
    r"print(?:-[a-z0-9]+|\.[a-f0-9]{64})?\.png$"
)
STATIC_PREFIXES = ("/js/", "/css/", "/assets/")
QA_HTML = "/qa/"
QA_MODULE = "/qa/harness.mjs"
QA_RECEIPT_MODULE = "/qa/print-basket-real-media-qa-receipt.mjs"
QA_CONTEXT = "/qa/context.json"
QA_VISITOR_HTML = "/qa/visitor/"
QA_VISITOR_BOOTSTRAP = "/qa/visitor-bootstrap.mjs"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def canonical_origin(raw: str) -> str:
    if not isinstance(raw, str):
        raise TypeError("origin must be text")
    parsed = urllib.parse.urlsplit(raw)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
    ):
        raise ValueError("origin must be an exact HTTPS origin")
    return f"https://{parsed.netloc}"


def build_opener():
    return urllib.request.build_opener(NoRedirect())


def fetch_exact(opener, url: str, limit: int, accept: str) -> tuple[bytes, str]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": accept,
            "User-Agent": "Ausmalwiese-QA/1.0",
        },
        method="GET",
    )
    try:
        response = opener.open(request, timeout=30)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"upstream HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("upstream unavailable") from exc

    with response:
        status = getattr(response, "status", None)
        final_url = response.geturl()
        if status != 200 or final_url != url:
            raise RuntimeError("upstream response was not exact HTTP 200")
        length = response.headers.get("Content-Length")
        if length is not None:
            try:
                if int(length) < 1 or int(length) > limit:
                    raise RuntimeError("upstream content length outside QA bound")
            except ValueError as exc:
                raise RuntimeError("invalid upstream content length") from exc
        data = response.read(limit + 1)
        if not data or len(data) > limit:
            raise RuntimeError("upstream response outside QA bound")
        content_type = response.headers.get_content_type()
        return data, content_type


def parse_catalog(data: bytes) -> list[dict]:
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("public catalogue is not valid UTF-8 JSON") from exc
    if not isinstance(payload, list):
        raise RuntimeError("public catalogue must be a JSON array")
    return payload


def canonical_print_path(value: object, activity_id: str) -> str | None:
    if not isinstance(value, str):
        return None
    path = value if value.startswith("/") else f"/{value}"
    match = PRINT_PATH.fullmatch(path)
    if not match or match.group(1) != activity_id:
        return None
    return path


def allowed_public_print_paths(catalog: list[dict]) -> frozenset[str]:
    counts: dict[str, int] = {}
    for entry in catalog:
        if isinstance(entry, dict):
            activity_id = entry.get("id")
            if isinstance(activity_id, str) and ACTIVITY_ID.fullmatch(activity_id):
                counts[activity_id] = counts.get(activity_id, 0) + 1

    allowed: set[str] = set()
    for entry in catalog:
        if not isinstance(entry, dict):
            continue
        activity_id = entry.get("id")
        if (
            not isinstance(activity_id, str)
            or counts.get(activity_id) != 1
            or not isinstance(entry.get("title"), str)
            or not entry["title"].strip()
        ):
            continue

        if "pages" in entry:
            pages = entry.get("pages")
            if not isinstance(pages, list) or not 1 <= len(pages) <= 12:
                continue
            values = [
                page.get("print") if isinstance(page, dict) else None
                for page in pages
            ]
        else:
            values = [entry.get("print")]

        canonical = [
            canonical_print_path(value, activity_id)
            for value in values
        ]
        if any(path is None for path in canonical):
            continue
        if len(set(canonical)) != len(canonical):
            continue
        allowed.update(canonical)

    return frozenset(allowed)


def safe_repo_file(repo_root: pathlib.Path, request_path: str) -> pathlib.Path | None:
    if not request_path.startswith(STATIC_PREFIXES):
        return None
    relative = urllib.parse.unquote(request_path).lstrip("/")
    candidate = (repo_root / relative).resolve()
    root = repo_root.resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    return candidate


def git_dir(repo_root: pathlib.Path) -> pathlib.Path:
    dotgit = repo_root / ".git"
    if dotgit.is_dir():
        return dotgit.resolve()
    if dotgit.is_file():
        text = dotgit.read_text(encoding="utf-8").strip()
        if not text.startswith("gitdir: "):
            raise RuntimeError("unsupported .git file")
        target = pathlib.Path(text[8:].strip())
        if not target.is_absolute():
            target = (repo_root / target).resolve()
        return target
    raise RuntimeError("repository git metadata unavailable")


def git_head_sha(repo_root: pathlib.Path) -> str:
    metadata = git_dir(repo_root)
    head = (metadata / "HEAD").read_text(encoding="utf-8").strip()
    if SHA40.fullmatch(head):
        return head
    if not head.startswith("ref: "):
        raise RuntimeError("git HEAD is not a SHA or ref")
    ref = head[5:].strip()
    loose = metadata / ref
    if loose.is_file():
        value = loose.read_text(encoding="utf-8").strip()
        if SHA40.fullmatch(value):
            return value
    packed = metadata / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith(("#", "^")):
                continue
            try:
                value, name = line.split(" ", 1)
            except ValueError:
                continue
            if name == ref and SHA40.fullmatch(value):
                return value
    raise RuntimeError("git HEAD ref could not be resolved")


def qa_context_bytes(source_sha: str, public_origin: str) -> bytes:
    if not SHA40.fullmatch(source_sha):
        raise RuntimeError("invalid source SHA")
    return (
        json.dumps(
            {
                "schema": "ausmalwiese.book-real-media-qa-context.v1",
                "sourceSha": source_sha,
                "publicOrigin": public_origin,
                "status": "STAGING ONLY",
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def make_handler(
    *,
    repo_root: pathlib.Path,
    origin: str,
    opener,
    catalog_bytes: bytes,
    allowed_paths: frozenset[str],
    context_bytes: bytes,
):
    qa_html = repo_root / "tools" / "print-basket-real-media-qa.html"
    qa_module = repo_root / "tools" / "print-basket-real-media-qa.mjs"
    qa_receipt_module = repo_root / "tools" / "print-basket-real-media-qa-receipt.mjs"
    qa_visitor_html = repo_root / "tools" / "print-basket-visitor-qa.html"
    qa_visitor_bootstrap = repo_root / "tools" / "print-basket-visitor-qa-bootstrap.mjs"

    class Handler(BaseHTTPRequestHandler):
        server_version = "AusmalwieseQAServer/1.1"

        def log_message(self, format, *args):
            return

        def _headers(self, status: int, content_type: str, length: int):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(length))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; img-src 'self' blob:; "
                "font-src 'self'; style-src 'self'; script-src 'self'; "
                "object-src 'none'; base-uri 'none'; form-action 'none'",
            )
            self.end_headers()

        def _bytes(self, status: int, content_type: str, data: bytes):
            self._headers(status, content_type, len(data))
            self.wfile.write(data)

        def _file(self, path: pathlib.Path, content_type: str | None = None):
            try:
                data = path.read_bytes()
            except OSError:
                self._bytes(404, "text/plain; charset=utf-8", b"not found\n")
                return
            guessed = content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            if guessed.startswith("text/") or guessed in ("application/javascript", "application/json"):
                guessed += "; charset=utf-8"
            self._bytes(200, guessed, data)

        def do_GET(self):
            parsed = urllib.parse.urlsplit(self.path)
            if parsed.query or parsed.fragment:
                self._bytes(404, "text/plain; charset=utf-8", b"not found\n")
                return
            path = parsed.path

            if path == QA_HTML:
                self._file(qa_html, "text/html; charset=utf-8")
                return
            if path == QA_MODULE:
                self._file(qa_module, "application/javascript; charset=utf-8")
                return
            if path == QA_RECEIPT_MODULE:
                self._file(qa_receipt_module, "application/javascript; charset=utf-8")
                return
            if path == QA_CONTEXT:
                self._bytes(200, "application/json; charset=utf-8", context_bytes)
                return
            if path == QA_VISITOR_HTML:
                self._file(qa_visitor_html, "text/html; charset=utf-8")
                return
            if path == QA_VISITOR_BOOTSTRAP:
                self._file(qa_visitor_bootstrap, "application/javascript; charset=utf-8")
                return
            if path == "/catalog.json":
                self._bytes(200, "application/json; charset=utf-8", catalog_bytes)
                return
            if path.startswith("/media/"):
                if path not in allowed_paths:
                    self._bytes(404, "text/plain; charset=utf-8", b"not allowlisted\n")
                    return
                try:
                    data, content_type = fetch_exact(
                        opener,
                        origin + path,
                        MAX_PRINT_BYTES,
                        "image/png",
                    )
                    if content_type != "image/png":
                        raise RuntimeError("upstream print media is not image/png")
                except RuntimeError:
                    self._bytes(502, "text/plain; charset=utf-8", b"upstream media unavailable\n")
                    return
                self._bytes(200, "image/png", data)
                return

            static = safe_repo_file(repo_root, path)
            if static is not None:
                self._file(static)
                return

            self._bytes(404, "text/plain; charset=utf-8", b"not found\n")

    return Handler


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Serve the #199 real-media staging QA harness on loopback only."
    )
    parser.add_argument(
        "--origin",
        default="https://ausmalwiese.de",
        help="Exact public HTTPS origin (default: https://ausmalwiese.de)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Loopback port 1024-65535 (default: 8765)",
    )
    parser.add_argument(
        "--repo-root",
        default=str(pathlib.Path(__file__).resolve().parents[1]),
        help=argparse.SUPPRESS,
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if not 1024 <= args.port <= 65535:
        print("STOP: port must be between 1024 and 65535", file=sys.stderr)
        return 2

    try:
        origin = canonical_origin(args.origin)
        repo_root = pathlib.Path(args.repo_root).resolve()
        if not (repo_root / "js" / "book-output-session.mjs").is_file():
            raise RuntimeError("repo root does not contain expected #199 source")
        source_sha = git_head_sha(repo_root)
        context = qa_context_bytes(source_sha, origin)
        opener = build_opener()
        catalog_url = origin + "/catalog.json"
        catalog_bytes, content_type = fetch_exact(
            opener,
            catalog_url,
            MAX_CATALOG_BYTES,
            "application/json",
        )
        if content_type not in ("application/json", "text/json", "text/plain"):
            raise RuntimeError("public catalogue has unexpected MIME type")
        catalog = parse_catalog(catalog_bytes)
        allowed = allowed_public_print_paths(catalog)
        if not allowed:
            raise RuntimeError("public catalogue contains no allowlisted print PNGs")
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2

    handler = make_handler(
        repo_root=repo_root,
        origin=origin,
        opener=opener,
        catalog_bytes=catalog_bytes,
        allowed_paths=allowed,
        context_bytes=context,
    )
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)

    print(
        f"QA_STAGING_SERVER=READY source_sha={source_sha} origin={origin} "
        f"allowlisted_print_paths={len(allowed)} "
        f"url=http://127.0.0.1:{args.port}/qa/"
    )
    print("STAGING_ONLY=true production_release_flags_unchanged=true")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
