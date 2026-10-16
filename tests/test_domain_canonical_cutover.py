"""Guard Ausmalwiese canonical source, sitemap handoff and QR cutover."""
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEW = "https://ausmalwiese.de"
OLD = "https://coloring.rozkalns.net"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class CanonicalDomainSourceTests(unittest.TestCase):
    def test_exact_home_kita_canonicals_and_generic_detail_shell(self):
        index = read("index.html")
        kita = read("kita.html")
        self.assertIn(f'<link rel="canonical" href="{NEW}/">', index)
        self.assertIn(f'<link rel="canonical" href="{NEW}/kita">', kita)
        self.assertNotIn(OLD, index)
        self.assertNotIn(OLD, kita)
        self.assertNotIn('rel="canonical"', read("detail.html"))
        self.assertIn('name="robots" content="noindex"', read("print.html"))

    def test_verified_detail_canonical_with_encoded_catalogue_id(self):
        detail = read("js/detail.js")
        self.assertIn('function addVerifiedDetailCanonical(id)', detail)
        self.assertIn(f'{NEW}/detail.html?id=', detail)
        self.assertIn("encodeURIComponent(id)", detail)
        self.assertNotIn(OLD, detail)
        self.assertIn('robots.setAttribute("content", "noindex")', detail)

    def test_robots_static_sitemap_and_read_only_generator_agree(self):
        self.assertIn(f"Sitemap: {NEW}/sitemap.xml", read("robots.txt"))
        root = ET.fromstring(read("sitemap.xml"))
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [loc.text for loc in root.findall("sm:url/sm:loc", ns)]
        self.assertEqual(urls, [f"{NEW}/", f"{NEW}/kita"])
        generator = read("tools/coloring-pages-sitemap")
        self.assertIn(f'ORIGIN = "{NEW}"', generator)
        self.assertNotIn(OLD, generator)

    def test_q_direct_destination_and_legacy_stats_allowlist_unchanged(self):
        worker = read("cloudflare/stats-worker.js")
        self.assertIn('const PRINT_QR_HOST = "ausmalwiese.de";', worker)
        self.assertIn('const PRINT_QR_DESTINATION = "https://ausmalwiese.de/";', worker)
        self.assertIn('url.hostname === PRINT_QR_HOST', worker)
        self.assertIn('const DEFAULT_ORIGIN = "https://coloring.rozkalns.net";', worker)
        self.assertIn('"https://www.ausmalwiese.de"', worker)

    def test_merge_and_runtime_gates_are_explicit(self):
        instructions = read("docs/DOMAIN_CANONICAL_CUTOVER_V1.md")
        for phrase in ("Hold application MERGE", "RPi5 operator upgrade",
                       "Stats Worker separately deploys", "owner LIVE",
                       "RPi5_main#996"):
            self.assertIn(phrase, instructions)
        # The operator must be coordinated before app MERGE; the running
        # Worker and dynamic sitemap each require a later independent LIVE
        # gate, with the legacy hostname redirect strictly last.
        gates = (
            "Prepare the RPi5 operator upgrade first",
            "Deploy and verify the application",
            "Stats Worker separately deploys",
            "Publish and verify the dynamic sitemap",
            "Redirect the legacy host last",
        )
        positions = [instructions.index(gate) for gate in gates]
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()
