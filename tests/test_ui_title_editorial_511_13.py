"""Guard issue #511 finding 13's read-only editorial snapshot against accidental removal."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "UI_UX_TITLE_EDITORIAL_511_13.md"
SNAPSHOT_SHA = "3c13653f15c89fa4a620758c15566f4587eb48dfd526312ce60f9db306edd3c7"


class UITitleEditorial51113Tests(unittest.TestCase):
    def test_editorial_plan_exists_with_original_snapshot_and_owner_gate(self):
        text = PLAN.read_text(encoding="utf-8")
        self.assertIn(f"LIVE catalogue snapshot SHA-256: `{SNAPSHOT_SHA}`", text)
        self.assertIn("This is a **source-only editorial plan**.", text)
        self.assertIn("## Future apply gate", text)
        self.assertIn("A future catalogue-title mutation is a separate operation", text)

    def test_evidence_inventory_has_unique_ids_and_expected_snapshot_scope(self):
        text = PLAN.read_text(encoding="utf-8")
        duplicated = text.split("## Duplicate-title editorial candidates", 1)[1].split(
            "## High-confidence orthography and casing candidates", 1
        )[0]
        orthography = text.split("## High-confidence orthography and casing candidates", 1)[1].split(
            "## Future apply gate", 1
        )[0]

        def ids(section):
            return [
                line.split("`", 2)[1]
                for line in section.splitlines()
                if line.startswith("| `")
            ]

        duplicated_ids, orthography_ids = ids(duplicated), ids(orthography)
        self.assertEqual(len(duplicated_ids), 40)
        self.assertEqual(len(set(duplicated_ids)), 40)
        self.assertGreaterEqual(len(orthography_ids), 30)
        self.assertEqual(len(set(orthography_ids)), len(orthography_ids))


if __name__ == "__main__":
    unittest.main()
