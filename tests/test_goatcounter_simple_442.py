"""Source-only GoatCounter SIMPLE smoke tests, no collector or public events."""
import pathlib
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class GoatCounterSimple442(unittest.TestCase):
    def test_html_is_opt_in_off_until_ingress_approved(self):
        for name in ("index.html", "detail.html"):
            html = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn('data-goatcounter-simple="off"', html)
            self.assertIn('src="js/goatcounter-simple.js?v=442"', html)
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
