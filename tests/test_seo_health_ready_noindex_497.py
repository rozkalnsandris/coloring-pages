"""SEO contract for technical health endpoints (#497)."""

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def location_body(nginx: str, spec: str) -> str:
    pattern = re.compile(
        r"(?m)^[ \t]*location[ \t]+" + re.escape(spec) + r"[ \t]*\{([^{}]*)\}"
    )
    matches = pattern.findall(nginx)
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one nginx location: {spec}")
    return matches[0]


class HealthReadyNoindexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nginx = (ROOT / "deploy/nginx.conf").read_text(encoding="utf-8")

    def test_health_endpoint_stays_200_plain_text_and_is_noindex(self):
        body = location_body(self.nginx, "= /health")
        self.assertIn("default_type text/plain;", body)
        self.assertIn('add_header X-Robots-Tag "noindex" always;', body)
        self.assertIn('return 200 "ok\\n";', body)

    def test_ready_endpoint_stays_200_plain_text_and_is_noindex(self):
        body = location_body(self.nginx, "= /ready")
        self.assertIn("default_type text/plain;", body)
        self.assertIn('add_header X-Robots-Tag "noindex" always;', body)
        self.assertIn('return 200 "ready\\n";', body)

    def test_health_endpoints_are_not_in_sitemap(self):
        root = ET.parse(ROOT / "sitemap.xml").getroot()
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [x.text for x in root.findall("s:url/s:loc", ns)]
        self.assertNotIn("https://ausmalwiese.de/health", urls)
        self.assertNotIn("https://ausmalwiese.de/ready", urls)


if __name__ == "__main__":
    unittest.main()
