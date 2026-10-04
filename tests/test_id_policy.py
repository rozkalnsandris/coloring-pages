import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class IdPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads(
            (ROOT / "metadata/id-policy.json").read_text(encoding="utf-8")
        )

    def test_new_publication_ids_are_opaque_random_seven_digit_codes(self):
        self.assertEqual(
            self.policy["schema"],
            "rozkalns.coloring-pages.id-policy.v2",
        )
        new = self.policy["new_publication"]
        self.assertEqual(new["format"], "NNNNNNN")
        self.assertEqual(new["digits"], 7)
        self.assertEqual(new["allocation"], "random-with-collision-check")
        self.assertFalse(new["semantic_components"])
        self.assertIsNotNone(re.fullmatch(new["pattern"], new["example"]))
        self.assertIsNotNone(re.fullmatch(new["pattern"], "0000000"))
        self.assertIsNotNone(re.fullmatch(new["pattern"], "9999999"))
        self.assertIsNone(re.fullmatch(new["pattern"], "123456"))
        self.assertIsNone(re.fullmatch(new["pattern"], "cp-000001"))

    def test_live_catalog_and_current_batch_guard_against_collisions(self):
        source = self.policy["allocation_source"]
        self.assertEqual(source["canonical_state"], "live-catalog")
        self.assertEqual(
            source["catalog_path"],
            "/srv/coloring-pages-content/public/catalog.json",
        )
        self.assertTrue(source["candidate_must_be_absent_before_first_mutation"])
        self.assertEqual(
            source["collision_before_first_mutation"],
            "generate-another-random-candidate",
        )
        self.assertTrue(source["current_batch_candidates_must_be_unique"])
        self.assertEqual(source["exhaustion_behavior"], "stop")

        legacy = self.policy["legacy_ids"]
        self.assertTrue(legacy["accepted"])
        self.assertTrue(legacy["immutable"])
        self.assertFalse(legacy["rename_existing"])
        self.assertFalse(legacy["count_toward_allocation"])


if __name__ == "__main__":
    unittest.main()
