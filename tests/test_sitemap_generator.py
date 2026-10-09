"""Source-only contract tests for a catalogue-backed SEO sitemap candidate."""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "tools" / "coloring-pages-sitemap"
ORIGIN = "https://coloring.rozkalns.net"


def entry(activity_id):
    root = f"/media/{activity_id}"
    return {
        "id": activity_id,
        "title": "Malvorlage",
        "thumb": f"{root}/thumb.webp",
        "preview": f"{root}/preview.webp",
        "print": f"{root}/print.png",
    }


def sitemap_urls(xml):
    tree = ET.fromstring(xml)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [loc.text for loc in tree.findall("sm:url/sm:loc", ns)]


class SitemapGeneratorTests(unittest.TestCase):
    def invoke(self, data=None, *, raw=None, extra_args=()):
        with tempfile.TemporaryDirectory() as temp:
            catalogue = Path(temp) / "catalog.json"
            catalogue.write_text(
                json.dumps(data) if raw is None else raw, encoding="utf-8"
            )
            return subprocess.run(
                [sys.executable, str(HELPER), "--catalog", str(catalogue), *extra_args],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_only_published_ids_plus_verified_static_urls(self):
        result = self.invoke([entry("9912254"), entry("abc-123")])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            sitemap_urls(result.stdout),
            [
                f"{ORIGIN}/",
                f"{ORIGIN}/kita",
                f"{ORIGIN}/detail.html?id=9912254",
                f"{ORIGIN}/detail.html?id=abc-123",
            ],
        )
        self.assertNotIn("<lastmod>", result.stdout)

    def test_exact_catalogue_snapshot_hash_accepts_current_bytes(self):
        catalog = [entry("9912254"), entry("1234567")]
        raw = json.dumps(catalog)
        expected = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        result = self.invoke(
            catalog, extra_args=("--expected-catalog-sha256", expected)
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(sitemap_urls(result.stdout)), 4)

    def test_catalogue_snapshot_mismatch_fails_without_output(self):
        catalog = [entry("9912254")]
        result = self.invoke(
            catalog, extra_args=("--expected-catalog-sha256", "0" * 64)
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("SITEMAP_ERROR: catalogue SHA-256 does not match", result.stderr)

    def test_malformed_expected_hash_fails_closed(self):
        result = self.invoke(
            [entry("9912254")],
            extra_args=("--expected-catalog-sha256", "NOT-A-DIGEST"),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("SITEMAP_ERROR: expected catalogue SHA-256", result.stderr)

    def test_optional_hash_keeps_original_read_only_usage_compatible(self):
        result = self.invoke([entry("9912254")])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(sitemap_urls(result.stdout)), 3)

    def test_multi_page_activity_is_one_url(self):
        activity = entry("1234567")
        activity["pages"] = [
            {"preview": "/media/1234567/preview-1.webp", "print": "/media/1234567/print-1.png"},
            {"preview": "/media/1234567/preview-2.webp", "print": "/media/1234567/print-2.png"},
        ]
        result = self.invoke([activity])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            sitemap_urls(result.stdout),
            [f"{ORIGIN}/", f"{ORIGIN}/kita", f"{ORIGIN}/detail.html?id=1234567"],
        )

    def test_invalid_catalogue_never_emits_partial_sitemap(self):
        cases = [
            [entry("1234567"), entry("1234567")],
            [entry("1234567"), entry("bad&item")],
            [entry("1234567"), {"id": "7654321", "title": "Not renderable"}],
            {"items": [entry("1234567")]},
        ]
        for case in cases:
            with self.subTest(case=case):
                result = self.invoke(case)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn("SITEMAP_ERROR", result.stderr)

    def test_bad_json_never_emits_partial_sitemap(self):
        result = self.invoke(raw="[broken")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_empty_catalogue_keeps_only_home_and_kita(self):
        result = self.invoke([])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sitemap_urls(result.stdout), [f"{ORIGIN}/", f"{ORIGIN}/kita"])


if __name__ == "__main__":
    unittest.main()
