"""#584: strict source-generated static Hero art, preserving indexed initial HTML."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from render_landing_hero_static import (  # noqa: E402
    TARGETS, build_pages, image_fragment, marker, render_page,
    ManifestValidationError,
)

# Git blob SHA-1 of each reviewed, pre-marker source HTML at main before #584.
ORIGINAL_BLOBS = {
    "fahrzeuge.html": "ba1e1715abed78dcd150795e95b0dc3404a55a81",
    "herbst.html": "5021dfd92b655122673f29acb6e2e179b6e2e",
}


class GeneratedStaticHero584Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "metadata/landing-hero.v1.json").read_text(encoding="utf-8")
        )

    def test_generated_html_matches_exact_validated_art(self):
        pages = build_pages(ROOT)
        self.assertEqual(set(pages), set(ORIGINAL_BLOBS))
        for namespace, slug, filename, wrapper in TARGETS:
            with self.subTest(filename=filename):
                page = (ROOT / filename).read_text(encoding="utf-8")
                record = self.manifest[namespace][slug]
                self.assertEqual(pages[filename], page)
                self.assertIn(image_fragment(record), page)
                self.assertEqual(page.count(marker(namespace, slug, "start")), 1)
                self.assertEqual(page.count(marker(namespace, slug, "end")), 1)
                self.assertIn(wrapper, page)

    def test_cli_check_is_read_only(self):
        targets = [ROOT / filename for _, _, filename, _ in TARGETS]
        before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in targets]
        result = subprocess.run(
            [sys.executable, "tools/render_landing_hero_static.py", "--check"],
            cwd=ROOT, capture_output=True, text=True, timeout=20, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("matches reviewed manifest", result.stdout)
        after = [hashlib.sha256(path.read_bytes()).hexdigest() for path in targets]
        self.assertEqual(before, after)

    def test_missing_duplicate_moved_and_stale_fragments_fail(self):
        for namespace, slug, filename, wrapper in TARGETS:
            page = (ROOT / filename).read_text(encoding="utf-8")
            record = self.manifest[namespace][slug]
            start = marker(namespace, slug, "start")
            end = marker(namespace, slug, "end")
            for altered in (
                page.replace(start, "", 1),
                page.replace(end, "", 1),
                page.replace(start, start + start, 1),
                page.replace(start, "", 1).replace(wrapper, wrapper + start, 1)
                    .replace(end, end + start, 1),
                page.replace(wrapper, wrapper + wrapper, 1),
            ):
                with self.subTest(filename=filename), self.assertRaises(
                    ManifestValidationError
                ):
                    render_page(altered, namespace, slug, record, wrapper)
            stale = page.replace('fetchpriority="high"', 'fetchpriority="low"', 1)
            self.assertNotEqual(
                render_page(stale, namespace, slug, record, wrapper), stale
            )

    def test_stripping_only_markers_restores_original_html_bytes(self):
        for namespace, slug, filename, _ in TARGETS:
            page = (ROOT / filename).read_text(encoding="utf-8")
            self.assertEqual(page.count("<!-- landing-hero:"), 2)
            stripped = page.replace(marker(namespace, slug, "start"), "", 1)
            stripped = stripped.replace(marker(namespace, slug, "end"), "", 1)
            data = stripped.encode("utf-8")
            git_blob = b"blob " + str(len(data)).encode("ascii") + b"\x00" + data
            self.assertEqual(
                hashlib.sha1(git_blob).hexdigest(), ORIGINAL_BLOBS[filename]
            )
            self.assertEqual(page.count('<h1 id="category-title">'), 1)
            self.assertIn(f'canonical" href="https://ausmalwiese.de/{slug}"', page)
        self.assertEqual(
            (ROOT / "herbst.html").read_text(encoding="utf-8").count(
                '<article class="coloring-card">'
            ), 6
        )

    def test_no_new_routes_topics_or_binary_assets(self):
        self.assertEqual(
            tuple((ns, slug) for ns, slug, _, _ in TARGETS),
            (("categories", "fahrzeuge"), ("topics", "herbst")),
        )
        self.assertEqual(set(self.manifest["categories"]), {"fahrzeuge"})
        self.assertEqual(set(self.manifest["topics"]), {"herbst"})
        self.assertNotIn("tanzen", self.manifest["topics"])


if __name__ == "__main__":
    unittest.main()
