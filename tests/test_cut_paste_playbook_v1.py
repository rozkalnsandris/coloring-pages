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
