import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import goatcounter_origin_contract as contract
import goatcounter_origin_nginx as nginx

CATALOG = [{"id": "0123456", "preview": "synthetic.webp", "print": "synthetic.png"},
           {"id": "1234567", "hidden": True, "preview": "x", "print": "x"}]
HEADERS = [("Host", contract.HOST), ("Content-Type", "application/json"),
           ("Content-Length", "21"), ("Connection", "close")]
BODY = b'{"page_id":"0123456"}'

class OriginContractTests(unittest.TestCase):
    def test_literal_id_and_discarded_values(self):
        for query in ["id=0123456", "campaign=SECRET&id=0123456&x=a%20b", "x=&id=0123456"]:
            self.assertEqual(contract.eligible_id("GET", "/detail.html", query), "0123456")
    def test_ambiguous_and_malformed_queries_are_not_counted(self):
        for query in ["", "id=123456", "id=12345678", "id=%30%31%32%33%34%35%36",
                      "id=0123456&id=0123456", "ID=0123456", "id=0123456&Id=1234567",
                      "%69d=0123456", "id=0123456&%69d=1234567", "id=0123456&x=%GG",
                      "id=0123456&", "&id=0123456", "id=0123456&bare", "id=１２３４５６７",
                      "id=0123456&x=" + "a" * 2048]:
            with self.subTest(query=query[:80]):
                self.assertIsNone(contract.eligible_id("GET", "/detail.html", query))
    def test_only_get_detail_counts(self):
        for method, path in [("HEAD", "/detail.html"), ("POST", "/detail.html"),
                             ("GET", "/print.html"), ("GET", "/DETAIL.html")]:
            self.assertIsNone(contract.eligible_id(method, path, "id=0123456"))
    def test_backend_payload_has_distinct_prefix_and_no_metadata(self):
        result = contract.backend_message("POST", contract.ROUTE, HEADERS, BODY, CATALOG)
        self.assertEqual(json.loads(result), {"no_sessions": True,
                         "hits": [{"path": "/origin-detail-request/0123456"}]})
    def test_extra_duplicate_or_missing_headers_rejected(self):
        for headers in [HEADERS + [("Cookie", "secret")], HEADERS + [HEADERS[0]],
                        HEADERS[1:], HEADERS + [("Origin", "https://ausmalwiese.de")]]:
            with self.assertRaises(ValueError):
                contract.backend_message("POST", contract.ROUTE, headers, BODY, CATALOG)
    def test_catalog_and_wire_independently_validated(self):
        for body, catalog in [(b'{"page_id":"1234567"}', CATALOG),
                              (b'{"page_id":"9999999"}', CATALOG), (BODY, CATALOG * 2),
                              (b'{"page_id":"abcdefg"}', CATALOG)]:
            with self.assertRaises(ValueError):
                contract.backend_message("POST", contract.ROUTE, HEADERS, body, catalog)
        for method, target in [("GET", contract.ROUTE), ("POST", contract.ROUTE + "?id=0123456")]:
            with self.assertRaises(ValueError):
                contract.backend_message(method, target, HEADERS, BODY, CATALOG)
    def test_renderer_supports_current_and_pre_detail_location_bases(self):
        base = (ROOT / "deploy/nginx.conf").read_text()
        result = nginx.render(base)
        restored = result.replace(nginx.MAP + "\n", "", 1).replace(
            nginx.DETAIL_DIRECTIVES, "", 1).replace(nginx.LOCATIONS + "\n", "", 1)
        self.assertEqual(restored, base)
        self.assertEqual(result.count("location = /detail.html"), 1)
        self.assertIn("mirror /__origin_count;", result)

        legacy = """http {
    server {
        location ~* \\.html$ {
            add_header Cache-Control "no-cache" always;
            try_files $uri =404;
        }
        location = /health {
            return 200 "ok";
        }
    }
}
"""
        legacy_result = nginx.render(legacy)
        self.assertEqual(legacy_result.count("location = /detail.html"), 1)
        self.assertIn(nginx.LEGACY_DETAIL_LOCATION.strip(), legacy_result)
        self.assertIn("mirror /__origin_count;", legacy_result)

        for rendered in (result, legacy_result):
            with self.assertRaises(ValueError):
                nginx.render(rendered)

if __name__ == "__main__":
    unittest.main()
