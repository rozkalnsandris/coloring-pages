"""Regression guard for UI/UX audit #511 narrow-header unavailable state."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BasketSummaryReflow511Tests(unittest.TestCase):
    def test_unavailable_summary_keeps_full_accessible_label_but_compact_visual_count(self):
        source = (ROOT / "js/print-basket-ui.mjs").read_text(encoding="utf-8")
        self.assertIn('summary.setAttribute("aria-label", "Drucksammlung nicht verfügbar");', source)
        self.assertIn('if (count) count.textContent = "–";', source)
        self.assertNotIn('if (count) count.textContent = "nicht verfügbar";', source)


if __name__ == "__main__":
    unittest.main()
