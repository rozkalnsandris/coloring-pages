"""Regressions for fail-closed PUBLISH upload-source contracts (v1 and v2)."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def contract(version):
    path = ROOT / "deploy" / (
        "chat-to-drive-ingestion.json"
        if version == 1
        else "chat-to-drive-ingestion-v2.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


class StableUploadSourceRefsTest(unittest.TestCase):
    def assert_common_prewrite_guards(self, staging):
        self.assertTrue(staging["stable_upload_source_refs_required_before_first_mutation"])
        self.assertEqual(
            staging["stable_upload_source_ref_semantics"],
            "immutable-exported-file-snapshot",
        )
        self.assertEqual(staging["current_files_surface_source_field"], "source_file_ref")
        self.assertTrue(staging["legacy_ephemeral_container_path_upload_forbidden"])
        self.assertEqual(staging["stable_upload_source_ref_failure_before_first_mutation"], "stop")
        self.assertTrue(staging["single_upload_surface_per_publication"])
        self.assertTrue(staging["upload_surface_selection_required_before_first_mutation"])
        self.assertTrue(staging["host_rclone_upload_forbidden"])
        self.assertTrue(staging["manifest_is_readiness_signal"])
        self.assertIn("prebuilt-manifest", staging["stable_upload_source_ref_required_for"])
        self.assertIn("prebuilt-manifest", staging["upload_surface_must_accept"])

    def test_v1_single_page_and_manifest_both_have_stable_refs(self):
        staging = contract(1)["drive_staging"]
        self.assert_common_prewrite_guards(staging)
        self.assertIn("prepared-png", staging["stable_upload_source_ref_required_for"])
        self.assertIn("prepared-png", staging["upload_surface_must_accept"])
        self.assertEqual(staging["publish_order"], ["image", "manifest"])

    def test_v2_every_page_and_manifest_have_stable_refs(self):
        data = contract(2)
        staging = data["drive_staging"]
        self.assert_common_prewrite_guards(staging)
        self.assertEqual(data["activity"]["min_pages"], 2)
        self.assertEqual(data["activity"]["max_pages"], 12)
        self.assertTrue(staging["stable_upload_source_ref_required_for_every_page"])
        self.assertIn("prepared-png-pages", staging["stable_upload_source_ref_required_for"])
        self.assertIn("prepared-png-pages", staging["upload_surface_must_accept"])
        self.assertTrue(staging["all_page_bytes_and_manifest_must_exist_before_first_mutation"])
        self.assertTrue(staging["manifest_validation_required_before_first_mutation"])
        self.assertEqual(staging["upload_order"], "all-pages-in-ascending-index-then-manifest")
        self.assertEqual(
            data["fail_closed"]["after_first_mutation"],
            "stop-without-retry-rollback-cleanup-or-alternate-mutation",
        )


if __name__ == "__main__":
    unittest.main()
