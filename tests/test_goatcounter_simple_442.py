"""Consent-gated GoatCounter SIMPLE source tests; no public events."""
import pathlib
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class GoatCounterSimple442(unittest.TestCase):
    def test_html_is_consent_gated_and_notice_is_shipped(self):
        for name in ("index.html", "detail.html"):
            html = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn('data-goatcounter-simple="consent"', html)
            self.assertIn('data-analytics-consent', html)
            self.assertIn('data-analytics-settings', html)
            self.assertIn('href="/datenschutz.html"', html)
            self.assertIn('<meta name="referrer" content="origin">', html)
            self.assertIn('src="js/goatcounter-simple.js?v=20261106consent1"', html)
        notice = (ROOT / "datenschutz.html").read_text(encoding="utf-8")
        self.assertIn("Analyse erlauben", notice)
        self.assertIn("Art. 6 Abs. 1 lit. a DSGVO", notice)
        self.assertIn("ausmalwiese.analytics-consent.v1", notice)
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("datenschutz.html", dockerfile)
        detail = (ROOT / "js/detail.js").read_text(encoding="utf-8")
        self.assertIn('window.GoatCounterSimple?.detail?.(entry.id, entry.title)', detail)
        self.assertIn('window.ColoringStats?.trackView?.(entry.id)', detail)

    @unittest.skipUnless(shutil.which("node"), "Node.js not installed")
    def test_browser_contract(self):
        p = subprocess.run(
            ["node", str(ROOT / "tests/test_goatcounter_simple_442.cjs")],
            cwd=ROOT, capture_output=True, text=True, timeout=15, check=False,
        )
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("PASS", p.stdout)


if __name__ == "__main__":
    unittest.main()
