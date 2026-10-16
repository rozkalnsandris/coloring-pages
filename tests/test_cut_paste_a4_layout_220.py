"""Page-one placement follows MAKE Cut & Paste ink geometry, issue #220.

Tests preserve assembly identity and keep physical art approval out of automation.
"""
import importlib.machinery
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
tool = ROOT / "tools/coloring-pages-cut-paste"
loader = importlib.machinery.SourceFileLoader("cutpaste_position_220", str(tool))
spec = importlib.util.spec_from_loader("cutpaste_position_220", loader)
app = importlib.util.module_from_spec(spec)
loader.exec_module(app)


def sample():
    return json.loads(
        (ROOT / "tests/fixtures/cut_paste/v1_bat_valid.json").read_text(encoding="utf-8")
    )


class CutPastePlacementTests(unittest.TestCase):
    def test_reference_at_top_body_close_to_footer_without_resizing(self):
        svg, meta = app.render(sample())
        self.assertGreater(meta["base_page_offset_y_mm"], 0)
        self.assertGreater(meta["base_page_cut_bottom_mm"], 255)
        self.assertLess(meta["base_page_cut_bottom_mm"], 256)
        self.assertGreaterEqual(meta["preview_bounds_mm"][1], 17.0)
        self.assertLess(meta["preview_bounds_mm"][1], 17.5)
        top = meta["preview_bounds_mm"][1]
        bottom = meta["base_page_cut_bottom_mm"]
        self.assertLessEqual(bottom - top, 239)
        self.assertIn('id="assembled-preview"', svg["01-base.svg"])
        self.assertIn('id="base" transform="translate(0 ', svg["01-base.svg"])
        self.assertEqual(meta["geometry_qa"]["physical_assembly"], "PENDING")

    def test_page_two_and_proof_keep_identical_exact_part_geometry(self):
        one = sample()
        _, original_meta = app.render(one)
        # Alter the original safe preview slot; optimizing only page 1 must
        # not change the cut-piece sizes, layout, ids or assembled proof.
        two = sample()
        two["page_layout"]["preview_box_mm"] = [160, 20, 30, 28]
        a, ma = app.render(one)
        b, mb = app.render(two)
        self.assertEqual(a["02-cutouts.svg"], b["02-cutouts.svg"])
        self.assertEqual(a["03-assembly-proof.svg"], b["03-assembly-proof.svg"])
        self.assertEqual(ma["cutouts"], mb["cutouts"])
        self.assertEqual(ma["base_page_offset_y_mm"], mb["base_page_offset_y_mm"])
        self.assertEqual(original_meta["parts"], mb["parts"])

    def test_too_tall_assembly_refuses_silent_downscale(self):
        record = sample()
        # All cutouts should stay at their exact author-assigned part scales.
        record["parts"][0]["cut"]["offset_mm"] = 60
        with self.assertRaisesRegex(ValueError, "footer|resizing|A4"):
            app.render(record)


if __name__ == "__main__":
    unittest.main()
