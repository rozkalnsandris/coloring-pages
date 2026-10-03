import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ChatToDriveIngestionContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(
            (ROOT / "deploy/chat-to-drive-ingestion.json").read_text(encoding="utf-8")
        )

    def test_contract_is_transport_only_and_owner_gated(self):
        self.assertEqual(
            self.contract["schema"],
            "rozkalns.coloring-pages.chat-to-drive-ingestion.v1",
        )
        self.assertEqual(self.contract["status"], "production-activated")
        self.assertEqual(self.contract["canonical_domains"]["drive_role"], "transport-only")
        authority = self.contract["authority"]
        self.assertFalse(authority["source_merge_authorizes_drive_upload"])
        self.assertFalse(authority["source_merge_authorizes_drive_download"])
        self.assertFalse(authority["source_merge_authorizes_host_execution"])
        self.assertFalse(authority["source_merge_authorizes_production_import"])
        self.assertFalse(authority["source_merge_authorizes_drive_archive_or_delete"])
        self.assertTrue(authority["live_content_import_requires_fresh_owner_authorization"])
        self.assertTrue(authority["category_binding_required_before_first_mutation"])
        self.assertEqual(authority["publication_command"], "PUBLISH")
        self.assertFalse(authority["ok_is_publication_authority"])

    def test_activation_evidence_records_first_production_pass(self):
        evidence = self.contract["activation_evidence"]
        self.assertEqual(evidence["activated_at"], "2026-10-03")
        self.assertEqual(
            evidence["proof_class"],
            "first-owner-authorized-production-import",
        )
        self.assertEqual(evidence["id"], "bauarbeiter-hund-001")
        self.assertEqual(
            evidence["sha256"],
            "d3162381a26ba47d847d28f6dc6349efa003f69807f4e902f8d116634130e8df",
        )
        self.assertEqual(evidence["size_bytes"], 1258789)
        self.assertEqual(evidence["runtime_owner"], "rozkalnsandris/RPi5_main")
        self.assertEqual(
            evidence["runtime_revision"],
            "d663073e4a0b7e33bba3b73b84643b4035839640",
        )
        self.assertTrue(evidence["receipt_present"])
        self.assertEqual(evidence["catalog_match_count"], 1)
        self.assertEqual(evidence["required_public_url_count"], 5)
        self.assertEqual(evidence["required_public_http_status"], 200)

    def test_drive_staging_requires_exact_blob_bytes_and_manifest_last(self):
        staging = self.contract["drive_staging"]
        self.assertEqual(staging["provider"], "google-drive")
        self.assertEqual(staging["object_class"], "blob-file")
        self.assertTrue(staging["google_workspace_conversion_forbidden"])
        self.assertTrue(staging["exact_folder_id_binding_required_at_live"])
        self.assertTrue(staging["folder_name_is_not_authority"])
        self.assertEqual(staging["publish_order"], ["image", "manifest"])
        self.assertTrue(staging["manifest_is_readiness_signal"])
        self.assertTrue(staging["exact_source_bytes_required"])
        self.assertTrue(staging["preupload_sha256_required"])
        self.assertTrue(staging["category_binding_required_before_upload"])

    def test_manifest_contract_binds_integrity_and_importer_metadata(self):
        manifest = self.contract["manifest"]
        self.assertEqual(
            manifest["schema"],
            "rozkalns.coloring-pages.drive-staging-manifest.v1",
        )
        for required in (
            "id",
            "sha256",
            "size_bytes",
            "title",
            "character",
            "category",
            "age",
            "difficulty",
            "language",
            "source_kind",
            "approval_class",
        ):
            self.assertIn(required, manifest["required_fields"])
        self.assertIsNotNone(re.fullmatch(manifest["sha256_pattern"], "a" * 64))
        self.assertIsNotNone(re.fullmatch(manifest["id_pattern"], "aviator-pup-001"))
        self.assertEqual(manifest["source_kind"], "chatgpt-generated-png")
        self.assertEqual(manifest["approval_class"], "explicit-owner-chat-approval")
        self.assertEqual(
            manifest["allowed_category"],
            [
                "rettungshunde",
                "tiere",
                "fahrzeuge",
                "alphabet",
                "lernen",
                "jahreszeiten",
            ],
        )
        self.assertEqual(manifest["category_registry"], "metadata/categories.json")
        self.assertEqual(manifest["unknown_fields"], "reject")

    def test_activation_requires_end_to_end_integrity_canary(self):
        canary = self.contract["integrity_canary"]
        self.assertTrue(canary["required_before_activation"])
        self.assertEqual(
            canary["pass_condition"],
            "preupload_sha256_equals_downloaded_sha256",
        )
        self.assertFalse(canary["conversion_or_reencode_allowed"])

    def test_host_flow_keeps_drive_outside_importer_and_publishes_atomically(self):
        host = self.contract["host_ingestion"]
        self.assertEqual(host["runtime_owner"], "rozkalnsandris/RPi5_main")
        self.assertEqual(host["transport_client"], "rclone")
        self.assertTrue(host["credential_values_must_not_be_read_or_emitted"])
        self.assertFalse(host["fresh_pending_fast_list_allowed"])
        self.assertEqual(
            host["download_target"],
            "/srv/coloring-pages-content/state/drive-ingest/<id>.png.partial",
        )
        self.assertEqual(
            host["inbox_target"],
            "/srv/coloring-pages-content/inbox/<id>.png",
        )
        self.assertEqual(host["inbox_publish"], "atomic-rename-after-integrity-pass")
        self.assertEqual(host["importer_contract_ref"], "deploy/importer-runtime.json")
        self.assertTrue(host["immutable_importer_image_digest_required_at_live"])
        self.assertIn("category", host["verify_before_inbox_publish"])
        self.assertFalse(host["application_redeploy_required"])

    def test_post_import_proof_preserves_source_and_checks_publication(self):
        required = set(self.contract["post_import_verification"]["required"])
        for proof in (
            "original-source-sha256-matches-manifest",
            "public-source-sha256-matches-manifest",
            "catalog-has-exactly-one-id",
            "catalog-metadata-matches-manifest",
            "thumb-webp-exists",
            "preview-webp-exists",
            "print-pdf-exists",
            "public-catalog-http-200",
            "public-thumb-http-200",
            "public-preview-http-200",
            "public-source-http-200",
            "public-pdf-http-200",
        ):
            self.assertIn(proof, required)
        self.assertEqual(
            self.contract["post_import_verification"]["web_origin"],
            "https://coloring.rozkalns.net",
        )
        self.assertFalse(
            self.contract["post_import_verification"]["application_restart_required"]
        )

    def test_fail_closed_and_no_automatic_overwrite(self):
        self.assertFalse(self.contract["idempotency"]["automatic_overwrite"])
        self.assertFalse(
            self.contract["idempotency"]["automatic_retry_after_mutation_error"]
        )
        self.assertIn(
            "automatic-overwrite-of-existing-page-id",
            self.contract["forbidden"],
        )
        self.assertIn("category-not-allowed", self.contract["fail_closed"]["conditions"])
        self.assertEqual(
            self.contract["fail_closed"]["after_first_mutation"],
            "stop-without-retry-rollback-cleanup-or-alternate-mutation",
        )


if __name__ == "__main__":
    unittest.main()
