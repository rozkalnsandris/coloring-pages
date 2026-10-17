"""Focused source-only tests for #220; physical/shape QA is #221."""
import importlib.machinery
import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"tools/coloring-pages-cut-paste"
loader=importlib.machinery.SourceFileLoader("cutpaste",str(PATH))
spec=importlib.util.spec_from_loader("cutpaste",loader)
app=importlib.util.module_from_spec(spec)
loader.exec_module(app)

def fixture(name="v1_bat_valid.json"):
    return json.loads((ROOT/"tests/fixtures/cut_paste"/name).read_text("utf-8"))

class CutPasteExporterTests(unittest.TestCase):
    def test_derived_views_share_the_same_parts(self):
        svg,meta=app.render(fixture())
        self.assertEqual(len(meta["parts"]),9)
        self.assertEqual(len(meta["cutouts"]),8)
        for part in meta["parts"]:
            marker='data-part-id="'+part+'"'
            self.assertIn(marker,svg["03-assembly-proof.svg"])
            self.assertIn(marker,svg["01-base.svg"])
            self.assertEqual(svg["02-cutouts.svg"].count(marker),0 if part=="body" else 1)
        self.assertIn('id="assembled-preview"',svg["01-base.svg"])
        self.assertNotIn("stroke-dasharray",svg["03-assembly-proof.svg"])

    def test_idempotent_svg_and_layout(self):
        self.assertEqual(app.render(fixture()),app.render(fixture()))

    def test_duplicate_and_already_integrated_piece_fail(self):
        for name in ("v1_bat_invalid_duplicate.json","v1_bat_invalid_integrated_wing.json"):
            with self.subTest(name=name),self.assertRaises(ValueError):
                app.render(fixture(name))

    def test_finished_preview_collision_fails(self):
        data=fixture()
        data["page_layout"]["preview_box_mm"]=[70,120,30,20]
        with self.assertRaisesRegex(ValueError,"Preview overlaps"): app.render(data)

    def test_oversized_piece_fails(self):
        data=fixture()
        data["parts"][-1]["art"]["size_mm"]=[190,49]
        with self.assertRaisesRegex(ValueError,"Cutout exceeds|Assembled subject exceeds"): app.render(data)

if __name__=="__main__":
    unittest.main()
