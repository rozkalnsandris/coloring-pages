"""Issue #219 fixture contract tests; not production geometry/print QA."""
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/cut_paste"

def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

def world_anchor(part, point):
    x, y = point
    angle = math.radians(part["assembly"]["rotate_deg"])
    scale = part["assembly"]["scale"]
    dx, dy = part["assembly"]["translate_mm"]
    return (dx + scale * (x * math.cos(angle) - y * math.sin(angle)),
            dy + scale * (x * math.sin(angle) + y * math.cos(angle)))

def check_basic_semantics(record):
    """Only cross-record fixtures, NOT physical cutting or SVG validation."""
    errors = []
    parts = record["parts"]
    ids = [p["id"] for p in parts]
    features = [p["feature"] for p in parts]
    if len(ids) != len(set(ids)):
        errors.append("duplicate id")
    if len(features) != len(set(features)):
        errors.append("duplicate feature")
    if record.get("preview_source") != "recompose-exact-parts":
        errors.append("independent preview")
    bases = [p for p in parts if p["role"] == "base"]
    if len(bases) != 1:
        errors.append("base count")
    integrated = {f for b in bases for f in b["built_in_features"]}
    if integrated.intersection(features):
        errors.append("duplicate integrated feature")
    by_id = {p["id"]: p for p in parts}
    for p in parts:
        if p["cut"]["method"] != "offset-of-outer-path":
            errors.append("independent cutting contour")
        if p["role"] == "base":
            if p["glue"] is not None:
                errors.append("base with glue")
            continue
        glue = p.get("glue")
        if not isinstance(glue, dict) or glue.get("side") != "front":
            errors.append("not front glue")
            continue
        target = by_id.get(glue["target_id"])
        if target is None or target is p:
            errors.append("bad glue target")
            continue
        ax, ay = world_anchor(p, glue["piece_anchor_mm"])
        bx, by = world_anchor(target, glue["target_anchor_mm"])
        if math.hypot(ax - bx, ay - by) > 0.1:
            errors.append("glue anchor mismatch")
        if p["assembly"]["z_index"] <= target["assembly"]["z_index"]:
            errors.append("bad glue z order")
    return errors

class CutPasteAuthoringTests(unittest.TestCase):
    def test_version_and_paper_constants(self):
        schema = json.loads((ROOT / "metadata/cut-paste-character-v1.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["preview_source"]["const"], "recompose-exact-parts")
        self.assertEqual(schema["properties"]["print_target"]["properties"]["raster_px"]["const"], [2480, 3508])
        self.assertEqual(schema["properties"]["page_layout"]["properties"]["ink_box_mm"]["const"], [17, 17, 193, 256])

    def test_valid_bat_inventory(self):
        source = fixture("v1_bat_valid.json")
        self.assertEqual(len(source["parts"]), 9)
        self.assertEqual(sum(p["role"] == "cutout" for p in source["parts"]), 8)
        self.assertEqual(check_basic_semantics(source), [])

    def test_duplicate_eye_fails(self):
        errors = check_basic_semantics(fixture("v1_bat_invalid_duplicate.json"))
        self.assertIn("duplicate id", errors)
        self.assertIn("duplicate feature", errors)

    def test_integrated_wing_fails(self):
        self.assertIn("duplicate integrated feature",
                      check_basic_semantics(fixture("v1_bat_invalid_integrated_wing.json")))

if __name__ == "__main__":
    unittest.main()
