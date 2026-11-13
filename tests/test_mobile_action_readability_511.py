"""Regression coverage for UI/UX audit #511 final mobile action readability QA."""

import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_HTML = (
    "alphabet.html", "datenschutz.html", "detail.html", "essen-natur.html",
    "fahrzeuge.html", "figuren.html", "herbst.html", "impressum.html",
    "index.html", "jahreszeiten.html", "kalender.html", "kita-herbst.html",
    "kita.html", "lernen.html", "name.html", "print.html", "stats.html",
    "tiere.html", "traffic.html",
)


class MobileActionReadability511Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = (ROOT / "css/app.css").read_text(encoding="utf-8")

    def test_mobile_outline_actions_do_not_drop_below_twelve_px(self):
        self.assertIn(
            ".outline-link { font-size: 12px; padding: 7px 9px; white-space: normal; }",
            self.css,
        )
        self.assertIn(
            ".outline-link { gap: 5px; padding-inline: 8px; font-size: 12px; }",
            self.css,
        )
        self.assertNotIn(".outline-link { font-size: 11px;", self.css)
        self.assertNotIn(".outline-link { gap: 5px; padding-inline: 8px; font-size: 10px;", self.css)

    def test_mobile_action_text_can_wrap_in_narrow_layouts(self):
        self.assertIn("white-space: normal;", self.css)

    def test_all_public_consumers_use_exact_app_css_content_hash(self):
        version = hashlib.sha256((ROOT / "css/app.css").read_bytes()).hexdigest()[:16]
        for filename in PUBLIC_HTML:
            html = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn(f"css/app.css?v={version}", html, filename)


if __name__ == "__main__":
    unittest.main()
