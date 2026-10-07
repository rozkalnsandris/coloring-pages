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

    def test_v1_and_v2_are_production_activated_after_repin(self):
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
        self.assertEqual(host["installed_path"], "/usr/local/bin/coloring-pages-drive-ingest")
        self.assertNotIn("operator_repository_revision", host)
        self.assertNotIn("installed_blob_sha", host)
        self.assertNotIn("installed_identity", host)
        self.assertNotIn("importer_image_digest", host)
        self.assertNotIn("host_operator_activation_satisfied", self.v2["authority"])
        self.assertTrue(
            self.v2["authority"]["host_operator_activation_must_be_verified_fresh_before_publish"]
        )
        self.assertTrue(
            self.v2["authority"]["host_importer_alignment_must_be_verified_fresh_before_publish"]
        )
        self.assertTrue(
            self.v2["authority"]["historical_activation_evidence_is_not_current_runtime_authority"]
        )
        preflight = host["current_runtime_preflight"]
        self.assertTrue(preflight["required_before_first_drive_mutation"])
        self.assertEqual(preflight["runtime_owner_repository"], "rozkalnsandris/RPi5_main")
        self.assertEqual(preflight["operator_source_path"], "ops/bin/coloring-pages-drive-ingest")
        self.assertEqual(
            preflight["operator_contract_path"],
            "ops/contracts/coloring-pages-drive-ingest-operator-v1.json",
        )
        self.assertEqual(preflight["consumer_importer_path"], "tools/coloring-pages-import")
        self.assertTrue(preflight["installed_operator_blob_must_match_fresh_operator_source"])
        self.assertTrue(
            preflight["operator_contract_pinned_consumer_source_revision_must_resolve"]
        )
        self.assertTrue(
            preflight["operator_pinned_importer_blob_must_match_current_consumer_importer_blob"]
        )
        self.assertEqual(
            preflight["mismatch_disposition"],
            "stop-before-first-drive-mutation-requires-rpi5-main-repin",
        )
        repin = host["repin_activation_evidence"]
        self.assertEqual(repin["activated_at"], "2026-10-05")
        self.assertEqual(repin["source_revision"], "7e3e6b6d6574c1dc5199618dbb974b1fae83eaf5")
        self.assertEqual(repin["installed_blob_sha"], "399df72159479c405166d011f140a967bdb749a5")
        self.assertEqual(repin["installed_identity"], "root:root:755")
        self.assertEqual(repin["importer_image_digest"], "sha256:53801684e0ce5a30d195d3436220a71b350112fc6e6fdc6fe107779d13c857ba")
        self.assertEqual(repin["reason"], "newest-first-catalog-importer")
        self.assertFalse(repin["state_created"])
        self.assertFalse(repin["lock_created"])
        self.assertFalse(repin["rclone_config_changed"])
        self.assertFalse(repin["sudoers_changed"])
        self.assertFalse(repin["rclone_executed"])
        self.assertFalse(repin["content_imported"])
        self.assertFalse(repin["systemd_changed"])
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
        self.assertIsNotNone(re.fullmatch(manifest["id_pattern"], "8152047"))

    def test_manifest_is_last_and_all_page_identities_are_frozen_first(self):
        staging = self.v2["drive_staging"]
        self.assertEqual(
            staging["upload_order"],
            "all-pages-in-ascending-index-then-manifest",
        )
        self.assertTrue(staging["manifest_is_readiness_signal"])
        self.assertTrue(staging["upload_surface_selection_required_before_first_mutation"])
        self.assertTrue(staging["single_upload_surface_per_publication"])
        self.assertEqual(staging["upload_surface_must_accept"], ["prepared-png-pages", "prebuilt-manifest"])
        self.assertTrue(staging["host_rclone_upload_forbidden"])
        self.assertTrue(staging["all_page_bytes_and_manifest_must_exist_before_first_mutation"])
        self.assertTrue(staging["all_page_sha256_and_size_must_be_frozen_before_first_mutation"])
        self.assertTrue(staging["manifest_validation_required_before_first_mutation"])

    def test_host_contract_verifies_every_page_before_inbox_publish(self):
        host = self.v2["host_ingestion"]
        self.assertEqual(host["runtime_owner"], "rozkalnsandris/RPi5_main")
        self.assertEqual(host["transport_direction"], "drive-to-rpi5-pull-only")
        self.assertFalse(host["host_rclone_upload_allowed"])
        self.assertIn("sha256", host["verify_all_pages_before_first_inbox_publish"])
        self.assertIn("size-bytes", host["verify_all_pages_before_first_inbox_publish"])
        self.assertIn("contiguous-page-indexes", host["verify_all_pages_before_first_inbox_publish"])
        self.assertEqual(host["importer_invocation_order"], "ascending-page-index")
        self.assertTrue(host["importer_requires_id_argument"])
        self.assertFalse(host["application_redeploy_required"])

    def test_operator_pass_is_terminal_publication_proof(self):
        proof = self.v2["post_import_verification"]
        self.assertTrue(proof["performed_by_trusted_host_operator"])
        self.assertEqual(proof["operator_success_signal"], "COLORING_PAGES_DRIVE_INGEST=PASS")
        self.assertTrue(proof["operator_pass_is_terminal_publication_success"])
        self.assertFalse(proof["external_repeat_after_operator_pass"])

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
