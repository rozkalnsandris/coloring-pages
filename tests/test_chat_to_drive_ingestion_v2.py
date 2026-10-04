import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ChatToDriveIngestionV2ContractTests(unittest.TestCase):
    def setUp(self):
        self.v1 = json.loads(
            (ROOT / "deploy/chat-to-drive-ingestion.json").read_text(encoding="utf-8")
        )
        self.v2 = json.loads(
            (ROOT / "deploy/chat-to-drive-ingestion-v2.json").read_text(encoding="utf-8")
        )

    def test_v1_and_v2_are_production_activated(self):
        self.assertEqual(self.v1["status"], "production-activated")
        self.assertEqual(
            self.v2["schema"],
            "rozkalns.coloring-pages.chat-to-drive-ingestion.v2",
        )
        self.assertEqual(self.v2["status"], "production-activated")
        compatibility = self.v2["compatibility"]
        self.assertEqual(
            compatibility["active_single_page_contract"],
            "deploy/chat-to-drive-ingestion.json",
        )
        self.assertTrue(compatibility["v1_remains_production_activated"])
        self.assertTrue(compatibility["v2_does_not_change_v1_publish_semantics"])
        host = self.v2["host_ingestion"]
        self.assertEqual(host["activation_state"], "production-activated")
        self.assertEqual(
            host["operator_repository_revision"],
            "dc6b784bba471731ff060ece207e06d67cda16d3",
        )
        self.assertEqual(
            host["installed_blob_sha"],
            "5d6821ad42c8c9d887a03606279e6c70745a993f",
        )
        self.assertEqual(host["installed_path"], "/usr/local/bin/coloring-pages-drive-ingest")
        self.assertEqual(host["installed_identity"], "root:root:755")
        self.assertEqual(host["importer_image_digest"], "sha256:09822c1ceed359e0365c0e647763c6f1d8b31fb4f4ab564d7959c383709034b2")
        self.assertTrue(self.v2["authority"]["host_operator_activation_satisfied"])
        evidence = host["activation_evidence"]
        self.assertEqual(evidence["non_production_v2_canary"], "pass")
        self.assertTrue(evidence["ordered_page_identity_verified"])
        self.assertTrue(evidence["hash_mismatch_rejected"])
        self.assertFalse(evidence["rclone_executed"])
        self.assertFalse(evidence["docker_executed"])
        self.assertFalse(evidence["production_content_mutated"])

    def test_v2_source_merge_grants_no_live_authority(self):
        authority = self.v2["authority"]
        for key in (
            "source_merge_authorizes_drive_upload",
            "source_merge_authorizes_drive_download",
            "source_merge_authorizes_host_execution",
            "source_merge_authorizes_production_import",
            "source_merge_authorizes_drive_archive_or_delete",
            "source_merge_authorizes_credentials_or_settings_mutation",
        ):
            self.assertFalse(authority[key])
        self.assertTrue(authority["live_content_import_requires_fresh_owner_authorization"])
        self.assertTrue(authority["host_operator_activation_required_before_v2_publish"])
        self.assertFalse(authority["ok_is_publication_authority"])

    def test_manifest_binds_ordered_exact_page_set(self):
        manifest = self.v2["manifest"]
        self.assertEqual(
            manifest["schema"],
            "rozkalns.coloring-pages.drive-staging-manifest.v2",
        )
        self.assertIn("pages", manifest["required_fields"])
        pages = manifest["pages"]
        self.assertEqual(pages["min_items"], 2)
        self.assertEqual(pages["max_items"], 12)
        self.assertEqual(
            pages["order"],
            "ascending-contiguous-index-starting-at-1",
        )
        self.assertEqual(
            pages["required_fields"],
            ["index", "file", "sha256", "size_bytes"],
        )
        self.assertEqual(pages["unknown_fields"], "reject")
        self.assertIsNotNone(re.fullmatch(pages["sha256_pattern"], "a" * 64))

    def test_manifest_is_last_and_all_page_identities_are_frozen_first(self):
        staging = self.v2["drive_staging"]
        self.assertEqual(
            staging["upload_order"],
            "all-pages-in-ascending-index-then-manifest",
        )
        self.assertTrue(staging["manifest_is_readiness_signal"])
        self.assertTrue(staging["all_page_bytes_and_manifest_must_exist_before_first_mutation"])
        self.assertTrue(staging["all_page_sha256_and_size_must_be_frozen_before_first_mutation"])
        self.assertTrue(staging["manifest_validation_required_before_first_mutation"])

    def test_host_contract_verifies_every_page_before_inbox_publish(self):
        host = self.v2["host_ingestion"]
        self.assertEqual(host["runtime_owner"], "rozkalnsandris/RPi5_main")
        self.assertIn("sha256", host["verify_all_pages_before_first_inbox_publish"])
        self.assertIn("size-bytes", host["verify_all_pages_before_first_inbox_publish"])
        self.assertIn("contiguous-page-indexes", host["verify_all_pages_before_first_inbox_publish"])
        self.assertEqual(host["importer_invocation_order"], "ascending-page-index")
        self.assertTrue(host["importer_requires_id_argument"])
        self.assertFalse(host["application_redeploy_required"])

    def test_v2_remains_fail_closed_without_overwrite_or_retry(self):
        self.assertFalse(self.v2["idempotency"]["automatic_overwrite"])
        self.assertFalse(self.v2["idempotency"]["automatic_retry_after_mutation_error"])
        self.assertIn(
            "partial-activity-import-after-page-verification-failure",
            self.v2["forbidden"],
        )
        self.assertEqual(
            self.v2["fail_closed"]["after_first_mutation"],
            "stop-without-retry-rollback-cleanup-or-alternate-mutation",
        )


if __name__ == "__main__":
    unittest.main()
