"""Freeze the Cut & Paste MAKE A4/no-downscale documentation contract (#221)."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A4_WIDTH, A4_HEIGHT = 2480, 3508
PORTRAIT_MM = (210, 297)


def browser_print_scale(left, top, right, bottom):
    """Mirror js/print.js pixel-bbox-inclusive computation, no browser APIs."""
    ink_width = (right - left + 1) * PORTRAIT_MM[0] / A4_WIDTH
    ink_height = (bottom - top + 1) * PORTRAIT_MM[1] / A4_HEIGHT
    return min(1.0, 176.0 / ink_width, 239.0 / ink_height)


class CutPasteMakeA4LayoutDocsTests(unittest.TestCase):
    def test_top_at_15_mm_plus_footer_bottom_shrinks(self):
        # The PDF-style 15 mm border alone is not enough for print.js guard.
        self.assertLess(browser_print_scale(630, 177, 1847, 3023), 1.0)

    def test_actual_17_mm_ink_guard_preserves_100_percent(self):
        # Same graphics dimensions moved independently on sheet one.
        self.assertEqual(browser_print_scale(630, 202, 1847, 3023), 1.0)

    def test_make_only_applies_to_requested_cut_paste(self):
        policy=(ROOT / "AGENTS.md").read_text(encoding="utf-8")
        commands=(ROOT / "docs/CHAT_IMAGE_COMMANDS_V1.md").read_text(encoding="utf-8")
        placement=(ROOT / "docs/CUT_PASTE_A4_PLACEMENT_V1.md").read_text(encoding="utf-8")
        for s in (policy,commands,placement):
            self.assertIn("MAKE Cut & Paste",s)
        for s in (policy,commands):
            self.assertIn("17..256 mm",s)
        self.assertIn("17 mm",placement)
        self.assertIn("ordinary",commands.lower())
        for term in ("15 mm", "2 mm", "41 mm", "256 mm", "scale=1", "physical"):
            self.assertIn(term.lower(),placement.lower())

if __name__=="__main__":
    unittest.main()
