"""A passing source geometry test must not imply that owner approved the art (#221)."""
import importlib.machinery
import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
loader=importlib.machinery.SourceFileLoader("cutpaste_art_221",str(ROOT/"tools/coloring-pages-cut-paste"))
spec=importlib.util.spec_from_loader("cutpaste_art_221",loader)
module=importlib.util.module_from_spec(spec)
loader.exec_module(module)

class CutPasteArtApprovalBoundaryTests(unittest.TestCase):
    def test_geometric_sample_requires_human_art_review(self):
        sample=json.loads((ROOT/"tests/fixtures/cut_paste/v1_bat_valid.json").read_text(encoding="utf-8"))
        _,meta=module.render(sample)
        self.assertEqual(meta["art_review"]["status"],"PENDING")
        self.assertFalse(meta["art_review"]["human_visual_approval"])
        self.assertIn("DRAFT_ONLY",meta["review_status"])
        self.assertNotIn("APPROVED",json.dumps(meta))

    def test_review_document_preserves_editorial_gate(self):
        p=(ROOT/"docs/CUT_PASTE_ART_DIRECTION_V1.md").read_text(encoding="utf-8")
        for term in ("VISUAL_FAIL","Bézier","art-first","Physical print","Owner acceptance"):
            self.assertIn(term.lower(),p.lower())

if __name__=="__main__":
    unittest.main()
