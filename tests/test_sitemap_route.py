"""Contract for optional runtime sitemap routing without changing publication."""

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def location_body(nginx: str, spec: str) -> str:
    pattern = re.compile(
        r"(?m)^[ \t]*location[ \t]+" + re.escape(spec)
        + r"[ \t]*\{([^{}]*)\}"
    )
    matches = pattern.findall(nginx)
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one nginx location: {spec}")
    return matches[0]


class SitemapRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nginx = (ROOT / "deploy/nginx.conf").read_text(encoding="utf-8")

    def test_exact_sitemap_location_checks_read_only_public_store_first(self):
        body = location_body(self.nginx, "= /sitemap.xml")
        self.assertIn("root /var/lib/coloring-pages/public;", body)
        self.assertIn("try_files /sitemap.xml @static_sitemap;", body)
        self.assertIn('add_header Cache-Control "no-cache" always;', body)
        self.assertNotIn("proxy_pass", body)
        self.assertNotIn("rewrite", body)

    def test_missing_dynamic_sitemap_falls_back_to_static_file_only(self):
        body = location_body(self.nginx, "@static_sitemap")
        self.assertIn("root /usr/share/nginx/html;", body)
        self.assertIn("try_files /sitemap.xml =404;", body)
        self.assertIn('add_header Cache-Control "no-cache" always;', body)
        self.assertNotIn("alias", body)
        self.assertNotIn("proxy_pass", body)

    def test_existing_static_sitemap_is_preserved_in_image(self):
        docker = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("COPY robots.txt sitemap.xml /usr/share/nginx/html/", docker)
        static = ROOT / "sitemap.xml"
        root = ET.parse(static).getroot()
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [x.text for x in root.findall("s:url/s:loc", ns)]
        self.assertEqual(
            urls,
            ["https://coloring.rozkalns.net/", "https://coloring.rozkalns.net/kita"],
        )

    def test_runtime_content_mount_stays_read_only(self):
        compose = (ROOT / "deploy/docker-compose.simple.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "coloring_pages_content:/var/lib/coloring-pages/public:ro", compose
        )
        self.assertNotIn("/srv/coloring-pages-content/inbox", self.nginx)


if __name__ == "__main__":
    unittest.main()
