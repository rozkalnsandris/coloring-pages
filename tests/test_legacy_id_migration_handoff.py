"""Issue #455 source-only handoff: no deployment or production mutation authority."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LegacyIdMigrationHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.handoff = json.loads(
            (ROOT / "deploy/legacy-id-migration-handoff-v1.json").read_text(
                encoding="utf-8"
            )
        )
        cls.docs = (ROOT / "docs/LEGACY_ID_MIGRATION_455.md").read_text(
            encoding="utf-8"
        )

    def test_handoff_is_exact_source_only_issue_contract(self):
        h = self.handoff
        self.assertEqual(
            h["schema"],
            "rozkalns.coloring-pages.legacy-id-migration-handoff.v1",
        )
        self.assertEqual(h["issue"], 455)
        self.assertEqual(h["status"], "SOURCE_ONLY_NOT_AUTHORIZED_FOR_LIVE")
        self.assertEqual(h["baseline"]["catalog_count"], 477)
        self.assertEqual(h["baseline"]["legacy_id_count"], 30)
        self.assertRegex(h["baseline"]["catalog_sha256"], r"^[0-9a-f]{64}$")

    def test_normal_importer_policy_is_not_weakened(self):
        policy = json.loads(
            (ROOT / "metadata/id-policy.json").read_text(encoding="utf-8")
        )
        self.assertEqual(policy["new_publication"]["pattern"], "^[0-9]{7}$")
        self.assertEqual(
            policy["new_publication"]["allocation"],
            "random-with-collision-check",
        )
        self.assertTrue(policy["legacy_ids"]["immutable"])
        self.assertFalse(policy["legacy_ids"]["rename_existing"])
        self.assertFalse(self.handoff["normal_id_policy"]["general_rename_tool_allowed"])

    def test_every_required_dependency_has_an_explicit_activation_boundary(self):
        required = self.handoff["required_before_data_cutover"]
        surfaces = {item["surface"] for item in required}
        self.assertEqual(
            surfaces,
            {
                "public_detail_and_print_urls",
                "public_media_urls",
                "print_basket_local_storage",
                "aggregate_like_print_state",
                "error_reports",
                "goatcounter",
                "sitemap_and_internal_links",
                "admin_archive_jobs_and_host_state",
            },
        )
        self.assertTrue(all(item["activation"].strip() for item in required))

    def test_seo_contract_is_permanent_one_to_one_and_chain_free(self):
        seo = self.handoff["seo_contract"]
        self.assertEqual(seo["redirect_status"], 308)
        self.assertTrue(seo["server_side"])
        self.assertTrue(seo["one_to_one"])
        self.assertTrue(seo["redirect_chains_forbidden"])
        self.assertTrue(seo["new_urls_only_in_internal_links_canonical_and_sitemap"])
        self.assertIn("at-least-one-year", seo["old_redirect_retention"])
        self.assertEqual(len(seo["references"]), 3)

    def test_handoff_grants_no_merge_deploy_or_data_write(self):
        self.assertTrue(self.handoff["authority"])
        self.assertTrue(all(value is False for value in self.handoff["authority"].values()))
        self.assertIn("does not change the normal", self.docs)
        self.assertIn("issue #455 forbids", self.docs)
        self.assertIn("separately reviewed", self.docs)


if __name__ == "__main__":
    unittest.main()
