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

    def test_new_publication_ids_are_opaque_and_fixed_width(self):
        self.assertEqual(
            self.policy["schema"],
            "rozkalns.coloring-pages.id-policy.v1",
        )
        new = self.policy["new_publication"]
        self.assertEqual(new["format"], "cp-NNNNNN")
        self.assertEqual(new["prefix"], "cp")
        self.assertEqual(new["digits"], 6)
        self.assertEqual(new["sequence_start"], 1)
        self.assertEqual(
            new["allocation"],
            "next-after-highest-existing-sequence",
        )
        self.assertFalse(new["reuse_gaps"])
        self.assertFalse(new["semantic_components"])
        self.assertIsNotNone(re.fullmatch(new["pattern"], new["example"]))

    def test_live_catalog_is_allocation_source_and_legacy_ids_do_not_advance_sequence(self):
        source = self.policy["allocation_source"]
        self.assertEqual(source["canonical_state"], "live-catalog")
        self.assertEqual(
            source["catalog_path"],
            "/srv/coloring-pages-content/public/catalog.json",
        )
        self.assertTrue(source["ignore_nonmatching_legacy_ids"])
        self.assertTrue(source["candidate_must_be_absent_before_first_mutation"])
        self.assertEqual(source["exhaustion_behavior"], "stop")

        legacy = self.policy["legacy_ids"]
        self.assertTrue(legacy["accepted"])
        self.assertTrue(legacy["immutable"])
        self.assertFalse(legacy["rename_existing"])
        self.assertFalse(legacy["count_toward_sequence"])


if __name__ == "__main__":
    unittest.main()
