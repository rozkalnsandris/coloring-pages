"""Documentation-only regression for the owner-reviewed Cut & Paste playbook.

No source images, runtime or publisher are modified.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CutPastePlaybookTests(unittest.TestCase):
    def test_command_alias_and_publish_gate_have_canonical_links(self):
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
        self.assertNotIn("active owner hold", a.lower())
        self.assertNotIn("currently active owner publication hold", (ROOT / "README.md").read_text(encoding="utf-8").lower())
        self.assertIn("fresh owner `PUBLISH`", (ROOT / "docs/CHAT_IMAGE_COMMANDS_V1.md").read_text(encoding="utf-8"))

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
                "ASSEMBLED_FIT=FAIL", "PUBLISH",
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


    def test_svg_handoff_is_default_and_printed_preview_is_removed(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        chat = (ROOT / "docs/CHAT_IMAGE_COMMANDS_V1.md").read_text(encoding="utf-8")
        playbook = (ROOT / "docs/CUT_PASTE_PLAYBOOK_V1.md").read_text(encoding="utf-8")
        placement = (ROOT / "docs/CUT_PASTE_A4_PLACEMENT_V1.md").read_text(encoding="utf-8")

        self.assertIn("ImageGen concept → owner-provided SVG handoff → SVG-only A4 authoring", agents)
        self.assertIn("Page 1 contains only the base/body", agents)
        self.assertIn("No small assembled reference is printed on page 1", chat)
        self.assertIn("Pašreizējais vienkāršotais SVG handoff", playbook)
        self.assertIn("1. lapa:** tikai pamatķermenis", playbook)
        self.assertIn("Page 1 contains only the base/body", placement)
        self.assertIn("never printed on page 1", placement)


    def test_physical_qa_accepts_owner_confirmation_without_photo(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        playbook = (ROOT / "docs/CUT_PASTE_PLAYBOOK_V1.md").read_text(encoding="utf-8")
        qa = (ROOT / "docs/CUT_PASTE_QA_V1.md").read_text(encoding="utf-8")
        art = (ROOT / "docs/CUT_PASTE_ART_DIRECTION_V1.md").read_text(encoding="utf-8")
        for source in (agents, playbook, qa, art):
            self.assertIn("owner", source.lower())
        self.assertIn("photo and ruler measurements are optional", agents.lower())
        self.assertIn("foto un lineāla izmēri ir izvēles", playbook.lower())
        self.assertIn("photo or ruler measurements", qa.lower())
        self.assertIn("photo/measurements are optional", art.lower())
        self.assertIn("ASSEMBLED_FIT", agents)
        self.assertIn("ASSEMBLED_FIT", playbook)


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
            "d79b4a8bb4fae0284d1d777ef7b5238ed7708ef7b2747e3a2c7ad6c1f35837be",
            "f2e19fbb836accd108ef8ec1b49c33049a3baa0acbac2355eef8f6d282fcd240",
        ):
            with self.subTest(token=token):
                self.assertIn(token.lower(), s.lower())

if __name__ == "__main__":
    unittest.main()
