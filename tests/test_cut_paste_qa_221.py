"""Vector offset, collision and A4 ink regression gates for issue #221.

No automated test can certify the physical cut-and-glue session.
"""
import copy
import importlib.machinery
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
import cut_paste_geometry as geometry

loader=importlib.machinery.SourceFileLoader("cutpaste_221",str(ROOT/"tools/coloring-pages-cut-paste"))
spec=importlib.util.spec_from_loader("cutpaste_221",loader)
app=importlib.util.module_from_spec(spec)
loader.exec_module(app)

def fixture():
    return json.loads((ROOT/"tests/fixtures/cut_paste/v1_bat_valid.json").read_text(encoding="utf-8"))


class CutPasteGeometryTests(unittest.TestCase):
    def test_outward_contour_is_real_closed_geometry(self):
        part=fixture()["parts"][1]  # large triangle ear
        original=geometry.polygon_of(part["art"]["outer_path_d"])
        guide=geometry.polygon_of(geometry.outline_d(part))
        self.assertTrue(guide.covers(original))
        self.assertGreater(guide.area,original.area)
        self.assertGreater(original.exterior.distance(guide.exterior),1.7)

    def test_invalid_paths_block(self):
        for path in ("M 0 0 A 3 3 0 0 1 2 2 Z",
                     "M 0 0 L 10 10 L 0 10 L 10 0 Z",
                     "M 0 0 L 10 0 L 10 10",
                     "M 0 0 L 3 0 M 0 0 L 0 3 Z"):
            with self.subTest(path=path),self.assertRaises(ValueError):
                geometry.polygon_of(path)

    def test_conflicting_cutouts_block(self):
        part=fixture()["parts"][1]
        style=fixture()["cut_style"]
        with self.assertRaisesRegex(ValueError,"too close"):
            geometry.validate_cuts([(part,60,40),(part,61,41)],style)

    def test_oversized_and_wrong_layer_pieces_block(self):
        record=fixture()
        record["parts"][-1]["assembly"]["scale"]=3
        with self.assertRaises(ValueError):
            app.render(record)
        record=fixture()
        record["parts"][1]["assembly"]["z_index"]=-1
        with self.assertRaisesRegex(ValueError,"Glue order"):
            app.render(record)

    def test_duplicate_parts_and_front_glue_mismatch_block(self):
        record=fixture()
        record["parts"][0]["built_in_features"].append("wing-left")
        with self.assertRaisesRegex(ValueError,"Integrated feature"):
            app.render(record)
        record=fixture()
        record["parts"][1]["glue"]["piece_anchor_mm"][0]+=15
        with self.assertRaisesRegex(ValueError,"glue anchors"):
            app.render(record)

    def test_header_preview_collision_blocks(self):
        record=fixture()
        record["page_layout"]["preview_box_mm"]=[70,120,40,30]
        with self.assertRaisesRegex(ValueError,"Preview overlaps"):
            app.render(record)

    def test_physical_png_shape_and_footer_ink_bounds(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/"sheet.png"
            image=Image.new("RGB",(2480,3508),"white")
            ImageDraw.Draw(image).rectangle((430,700,1600,2900),outline="#000000",width=8)
            image.save(target,dpi=(300,300))
            self.assertEqual(len(geometry.validate_png(target)),4)
            ImageDraw.Draw(image).rectangle((0,0,80,80),fill="black")
            image.save(target,dpi=(300,300))
            with self.assertRaisesRegex(ValueError,"ink region"):
                geometry.validate_png(target)


if __name__=="__main__":
    unittest.main()
