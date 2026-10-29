import importlib.machinery
import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "print-basket-real-media-qa-server.py"


def load_tool():
    loader = importlib.machinery.SourceFileLoader("real_media_qa_server", str(TOOL))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


qa = load_tool()


class HeaderBag:
    def __init__(self, content_type="application/json", content_length=None):
        self._content_type = content_type
        self._content_length = content_length

    def get(self, name):
        if name == "Content-Length":
            return self._content_length
        return None

    def get_content_type(self):
        return self._content_type


class FakeResponse:
    def __init__(self, *, data=b"{}", url="https://ausmalwiese.de/catalog.json",
                 status=200, content_type="application/json", content_length=None):
        self._data = data
        self._url = url
        self.status = status
        self.headers = HeaderBag(content_type, content_length)

    def geturl(self):
        return self._url

    def read(self, limit):
        return self._data[:limit]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeOpener:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        return self.response


class RealMediaQaServerTests(unittest.TestCase):
    def test_origin_is_exact_https_origin_only(self):
        self.assertEqual(
            qa.canonical_origin("https://ausmalwiese.de"),
            "https://ausmalwiese.de",
        )
        self.assertEqual(
            qa.canonical_origin("https://ausmalwiese.de/"),
            "https://ausmalwiese.de",
        )
        for bad in (
            "http://ausmalwiese.de",
            "https://user@example.com",
            "https://ausmalwiese.de/path",
            "https://ausmalwiese.de?x=1",
            "https://ausmalwiese.de/#x",
            "not-a-url",
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    qa.canonical_origin(bad)

    def test_catalog_allowlist_matches_public_print_contract_and_excludes_ambiguity(self):
        catalog = [
            {"id": "1234567", "title": "A", "print": "media/1234567/print.png"},
            {
                "id": "cut-1",
                "title": "Cut",
                "pages": [
                    {"print": "/media/cut-1/print-1.png"},
                    {"print": "media/cut-1/print-2.png"},
                ],
            },
            {"id": "bad", "title": "Bad", "print": "/media/other/print.png"},
            {"id": "dup", "title": "One", "print": "/media/dup/print.png"},
            {"id": "dup", "title": "Two", "print": "/media/dup/print.png"},
            {"id": "empty", "title": "Empty", "pages": []},
        ]
        self.assertEqual(
            qa.allowed_public_print_paths(catalog),
            frozenset({
                "/media/1234567/print.png",
                "/media/cut-1/print-1.png",
                "/media/cut-1/print-2.png",
            }),
        )

    def test_fetch_exact_rejects_redirect_shape_and_oversize(self):
        good = FakeOpener(FakeResponse(data=b"[]"))
        data, mime = qa.fetch_exact(
            good,
            "https://ausmalwiese.de/catalog.json",
            32,
            "application/json",
        )
        self.assertEqual(data, b"[]")
        self.assertEqual(mime, "application/json")
        self.assertEqual(good.requests[0][0].headers["Accept"], "application/json")

        redirected = FakeOpener(FakeResponse(url="https://www.ausmalwiese.de/catalog.json"))
        with self.assertRaises(RuntimeError):
            qa.fetch_exact(
                redirected,
                "https://ausmalwiese.de/catalog.json",
                32,
                "application/json",
            )

        oversized = FakeOpener(FakeResponse(data=b"x" * 33))
        with self.assertRaises(RuntimeError):
            qa.fetch_exact(
                oversized,
                "https://ausmalwiese.de/catalog.json",
                32,
                "application/json",
            )

    def test_static_file_resolution_is_repo_bounded(self):
        js = qa.safe_repo_file(ROOT, "/js/book-output-session.mjs")
        self.assertEqual(js, (ROOT / "js" / "book-output-session.mjs").resolve())
        self.assertIsNone(qa.safe_repo_file(ROOT, "/tools/print-basket-real-media-qa.html"))
        self.assertIsNone(qa.safe_repo_file(ROOT, "/js/../../AGENTS.md"))
        self.assertIsNone(qa.safe_repo_file(ROOT, "/metadata/categories.json"))

    def test_git_head_sha_supports_loose_and_packed_refs_without_shell(self):
        sha = "a" * 40
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            metadata = root / ".git"
            (metadata / "refs" / "heads").mkdir(parents=True)
            (metadata / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
            (metadata / "refs" / "heads" / "main").write_text(sha + "\n", encoding="utf-8")
            self.assertEqual(qa.git_head_sha(root), sha)

            (metadata / "refs" / "heads" / "main").unlink()
            (metadata / "packed-refs").write_text(
                "# pack-refs with: peeled fully-peeled\n"
                + sha + " refs/heads/main\n",
                encoding="utf-8",
            )
            self.assertEqual(qa.git_head_sha(root), sha)

    def test_context_contains_only_public_origin_source_sha_and_staging_status(self):
        sha = "b" * 40
        payload = json.loads(
            qa.qa_context_bytes(sha, "https://ausmalwiese.de").decode("utf-8")
        )
        self.assertEqual(payload, {
            "schema": "ausmalwiese.book-real-media-qa-context.v1",
            "publicOrigin": "https://ausmalwiese.de",
            "sourceSha": sha,
            "status": "STAGING ONLY",
        })

    def test_tool_is_loopback_only_non_persistent_and_not_in_production_image(self):
        source = TOOL.read_text(encoding="utf-8")
        docker = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn('ThreadingHTTPServer(("127.0.0.1", args.port), handler)', source)
        self.assertNotIn("0.0.0.0", source)
        self.assertNotIn("write_bytes(", source)
        self.assertNotIn("subprocess", source)
        self.assertNotIn("os.system", source)
        self.assertNotIn("print-basket-real-media-qa", docker)
        self.assertIn('QA_CONTEXT = "/qa/context.json"', source)
        self.assertIn('QA_RECEIPT_MODULE = "/qa/print-basket-real-media-qa-receipt.mjs"', source)
        self.assertIn('QA_VISITOR_HTML = "/qa/visitor/"', source)
        self.assertIn('QA_VISITOR_BOOTSTRAP = "/qa/visitor-bootstrap.mjs"', source)

        visitor_html = (ROOT / "tools" / "print-basket-visitor-qa.html").read_text(encoding="utf-8")
        visitor_bootstrap = (ROOT / "tools" / "print-basket-visitor-qa-bootstrap.mjs").read_text(encoding="utf-8")
        production_html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("STAGING ONLY", visitor_html)
        self.assertIn("__AUSMALWIESE_BOOK_OUTPUT_QA_RELEASE__", visitor_bootstrap)
        self.assertIn("combinedPrint: true", visitor_bootstrap)
        self.assertIn("coveredZip: true", visitor_bootstrap)
        self.assertIn('import("/js/print-basket-ui.mjs")', visitor_bootstrap)
        self.assertNotIn("__AUSMALWIESE_BOOK_OUTPUT_QA_RELEASE__", production_html)


if __name__ == "__main__":
    unittest.main()
