"""Page-one placement follows the SVG-only Cut & Paste contract, issue #220.

Tests preserve assembly identity and keep physical art approval out of automation.
"""
import importlib.machinery
import importlib.util
import json
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
    def test_body_close_to_footer_without_printed_preview(self):
        svg, meta = app.render(sample())
        self.assertGreater(meta["base_page_offset_y_mm"], 0)
        self.assertGreater(meta["base_page_cut_bottom_mm"], 255)
        self.assertLess(meta["base_page_cut_bottom_mm"], 256)
        self.assertNotIn('id="assembled-preview"', svg["01-base.svg"])
        self.assertEqual(svg["01-base.svg"].count('data-part-id="body"'), 1)
        for part in meta["parts"]:
            if part != "body":
                self.assertNotIn('data-part-id="'+part+'"', svg["01-base.svg"])
        self.assertFalse(meta["printed_preview"])
        self.assertNotIn("preview_bounds_mm", meta)
        self.assertNotIn("preview_scale", meta)
        self.assertEqual(meta["geometry_qa"]["physical_assembly"], "PENDING")

    def test_legacy_preview_box_does_not_change_outputs(self):
        one = sample()
        two = sample()
        two["page_layout"]["preview_box_mm"] = [70, 120, 40, 30]
        self.assertEqual(app.render(one), app.render(two))

    def test_page_two_and_proof_keep_identical_exact_part_geometry(self):
        a, ma = app.render(sample())
        self.assertIn('id="assembled-proof"', a["03-assembly-proof.svg"])
        self.assertIn('id="cutout-sheet"', a["02-cutouts.svg"])
        self.assertEqual(len(ma["cutouts"]), len(ma["parts"]) - 1)

    def test_too_tall_assembly_refuses_silent_downscale(self):
        record = sample()
        record["parts"][0]["cut"]["offset_mm"] = 60
        with self.assertRaisesRegex(ValueError, "footer|resizing|A4"):
            app.render(record)


if __name__ == "__main__":
    unittest.main()
