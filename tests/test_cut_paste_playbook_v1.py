"""Documentation-only regression for the owner-reviewed Cut & Paste playbook.

No source images, runtime or publisher are modified.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CutPastePlaybookTests(unittest.TestCase):
    def test_command_alias_and_owner_hold_have_canonical_links(self):
        files = (
            "AGENTS.md",
            "README.md",
            "docs/CHAT_IMAGE_COMMANDS_V1.md",
        )
        for name in files:
            content = (ROOT / name).read_text(encoding="utf-8")
            with self.subTest(file=name):
                self.assertIn("CUT_PASTE_PLAYBOOK_V1.md", content)
        a = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        c = (ROOT / "docs/CHAT_IMAGE_COMMANDS_V1.md").read_text(encoding="utf-8")
        self.assertIn("CUT <subject>", a)
        self.assertIn("CUT <subject>", c)
        self.assertIn("PUBLISH", a)

    def test_assembled_fit_gate_precedes_a4_print_approval(self):
        checks = {
            "AGENTS.md": (
                "ART_CONCEPT_ONLY", "ASSEMBLED_FIT=UNVERIFIED",
                "ASSEMBLED_FIT=FAIL", "176 mm", "STOP",
            ),
            "docs/CUT_PASTE_PLAYBOOK_V1.md": (
                "## 3A.", "assembled_bbox_mm", "assembled_width_mm",
                "assembled_width_mm <= 176 mm", "fitA4InkBounds",
                "2026-10-17", "ASSEMBLED_FIT=PASS",
                "ASSEMBLED_FIT=FAIL", "HOLD",
            ),
            "docs/CUT_PASTE_A4_PLACEMENT_V1.md": (
                "Strict pre-export gate", "x=17..193 mm",
                "y=17..256 mm", "ASSEMBLED_FIT=UNVERIFIED",
                "ASSEMBLED_FIT=FAIL", "Fit to page",
            ),
            "docs/CHAT_IMAGE_COMMANDS_V1.md": (
                "Obligāta secība pirms CUT A4 finalizācijas",
                "176 mm", "ASSEMBLED_FIT=FAIL", "ART_CONCEPT_ONLY",
            ),
        }
        for path, phrases in checks.items():
            source = (ROOT / path).read_text(encoding="utf-8").lower()
            for phrase in phrases:
                with self.subTest(path=path, phrase=phrase):
                    self.assertIn(phrase.lower(), source)

    def test_playbook_separates_machine_from_physical_and_publish(self):
        s = (ROOT / "docs/CUT_PASTE_PLAYBOOK_V1.md").read_text(encoding="utf-8")
        for token in (
            "MAKE Cut & Paste",
            "CUT <subject>",
            "17..193 mm",
            "17..256 mm",
            "2480×3508",
            "300 DPI",
            "4 mm",
            "scale = 1.0",
            "FOOTER",
            "PHYSICAL_QA",
            "PUBLISH",
            "HOLD",
            "d79b4a8bb4fae0284d1d777ef7b5238ed7708ef7b2747e3a2c7ad6c1f35837be",
            "f2e19fbb836accd108ef8ec1b49c33049a3baa0acbac2355eef8f6d282fcd240",
        ):
            with self.subTest(token=token):
                self.assertIn(token.lower(), s.lower())

if __name__ == "__main__":
    unittest.main()
