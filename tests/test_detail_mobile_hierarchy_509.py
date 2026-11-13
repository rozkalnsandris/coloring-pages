"""Regression coverage for mobile detail hierarchy (#509)."""
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DetailMobileHierarchy509Tests(unittest.TestCase):
    def test_detail_has_one_h1_and_mobile_semantic_order(self):
        html = (ROOT / "detail.html").read_text(encoding="utf-8")
        self.assertEqual(html.count('id="detail-title"'), 1)
        summary = html.index('class="detail-copy detail-summary"')
        media = html.index('class="detail-media"')
        controls = html.index('class="detail-controls"')
        self.assertLess(summary, media)
        self.assertLess(media, controls)
        self.assertEqual(
            len(re.findall(r'<a class="action-primary[^"]*"[^>]*data-action-print(?:\s|>)', html)),
            1,
        )
        self.assertLess(html.index("data-action-print"), html.index("data-action-png"))
        self.assertLess(html.index("data-action-png"), html.index("data-action-like"))
        self.assertIn("data-detail-page-switcher", html)
        self.assertIn("data-report-open", html)

    def test_desktop_and_mobile_grid_areas_preserve_required_hierarchy(self):
        css = (ROOT / "css/detail-hierarchy.css").read_text(encoding="utf-8")
        self.assertIn('"media summary"', css)
        self.assertIn('"media controls"', css)
        mobile = css[css.index("@media (max-width: 720px)"):]
        summary = mobile.index('"summary"')
        media = mobile.index('"media"')
        controls = mobile.index('"controls"')
        self.assertLess(summary, media)
        self.assertLess(media, controls)
        self.assertIn("min-height: min(72vh, 520px)", mobile)
        self.assertIn(".detail-controls .detail-actions { margin-top: 0; }", mobile)

    def test_primary_action_is_not_duplicated_and_help_is_compact(self):
        html = (ROOT / "detail.html").read_text(encoding="utf-8")
        self.assertIn("Einfach auf A4 drucken", html)
        self.assertIn(
            "Alternativ kannst du die hochauflösende PNG-Druckdatei herunterladen.",
            html,
        )
        css = (ROOT / "css/detail-hierarchy.css").read_text(encoding="utf-8")
        self.assertIn("padding: 14px 16px", css)

    def test_related_titles_are_visually_clamped_without_cropping_art(self):
        css = (ROOT / "css/detail-related.css").read_text(encoding="utf-8")
        self.assertIn("-webkit-line-clamp: 3", css)
        self.assertIn("-webkit-box-orient: vertical", css)
        self.assertIn("max-height: 3.6em", css)
        self.assertIn("object-fit: contain", css)

    def test_detail_only_assets_use_content_hash_versions(self):
        html = (ROOT / "detail.html").read_text(encoding="utf-8")
        for filename in ("css/detail-hierarchy.css", "css/detail-related.css"):
            version = hashlib.sha256((ROOT / filename).read_bytes()).hexdigest()[:16]
            self.assertIn(f"{filename}?v={version}", html)


if __name__ == "__main__":
    unittest.main()
