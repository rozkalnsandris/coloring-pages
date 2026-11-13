"""Regression coverage for UI/UX audit #08 public taxonomy labels."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PublicTaxonomyLabels511Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = (ROOT / "index.html").read_text(encoding="utf-8")

    def test_canonical_category_labels_match_managed_public_vocabulary(self):
        expected = {
            "tiere": "Tiere",
            "fahrzeuge": "Fahrzeuge",
            "figuren": "Figuren &amp; Helden",
            "jahreszeiten": "Jahreszeiten &amp; Feste",
        }
        for category_id, label in expected.items():
            match = re.search(
                rf'<details[^>]+data-category-ids="{category_id}"[^>]*>(.*?)</details>',
                self.home,
                re.S,
            )
            self.assertIsNotNone(match, category_id)
            self.assertIn(f'<span class="category-group-name">{label}</span>', match.group(1))

    def test_curated_groups_are_explicitly_presented_as_topic_worlds(self):
        groups = re.findall(
            r'<details[^>]+data-curated-topic-group[^>]*>(.*?)</details>',
            self.home,
            re.S,
        )
        self.assertEqual(len(groups), 2)
        for group in groups:
            self.assertRegex(group, r'<span class="category-group-name">Themenwelt [^<]+</span>')
        self.assertIn("Themenwelt Obst &amp; Gemüse", self.home)
        self.assertIn("Themenwelt Natur &amp; Weltraum", self.home)

    def test_stale_overlapping_headings_do_not_return(self):
        self.assertNotIn('<span class="category-group-name">Figuren &amp; Fantasie</span>', self.home)
        self.assertNotIn('<span class="category-group-name">Feste &amp; Jahreszeiten</span>', self.home)
        self.assertIn("Wähle eine Kategorie oder Themenwelt", self.home)


if __name__ == "__main__":
    unittest.main()
