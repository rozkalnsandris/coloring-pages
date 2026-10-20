"""Regressions for the trusted RPi5 PUBLISH staging contract."""

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


class TrustedRpi5StageSenderContractTest(unittest.TestCase):
    def setUp(self):
        self.sender = json.loads(
            (
                ROOT / "deploy/publish-trusted-rpi5-stage-sender-v1.json"
            ).read_text(encoding="utf-8")
        )

    def assert_common_prewrite_guards(self, staging):
        self.assertEqual(
            staging["staging_surface"],
            "trusted-rpi5-drive-stage-sender",
        )
        self.assertEqual(
            staging["staging_sender_contract_ref"],
            "deploy/publish-trusted-rpi5-stage-sender-v1.json",
        )
        self.assertEqual(
            staging["sender_envelope_schema"],
            "rozkalns.rpi5-main.coloring-pages-drive-stage-envelope.v1",
        )
        self.assertEqual(staging["sender_production_namespace"], "pending")
        self.assertFalse(staging["provider_owned_source_file_ref_required"])
        self.assertFalse(staging["ephemeral_local_path_is_remote_upload_ref"])
        self.assertTrue(staging["exact_local_artifacts_required_before_first_mutation"])
        self.assertTrue(staging["envelope_materialization_required_before_first_mutation"])
        self.assertTrue(staging["envelope_validation_required_before_first_mutation"])
        self.assertTrue(staging["trusted_host_stage_sender_upload_allowed"])
        self.assertTrue(staging["arbitrary_host_rclone_upload_forbidden"])
        self.assertEqual(
            staging["sender_success_signal"],
            "COLORING_PAGES_DRIVE_STAGE=PASS",
        )
        self.assertTrue(staging["sender_pass_is_staging_only"])
        self.assertTrue(staging["single_upload_surface_per_publication"])
        self.assertTrue(staging["upload_surface_selection_required_before_first_mutation"])
        self.assertEqual(
            staging["upload_surface_must_accept"],
            ["validated-rpi5-stage-envelope"],
        )
        for obsolete in (
            "stable_upload_source_refs_required_before_first_mutation",
            "stable_upload_source_ref_semantics",
            "stable_upload_source_ref_required_for",
            "stable_upload_source_ref_required_for_every_page",
            "current_files_surface_source_field",
            "stable_upload_source_ref_failure_before_first_mutation",
        ):
            self.assertNotIn(obsolete, staging)

    def test_v1_uses_sender_envelope_and_preserves_manifest_last(self):
        data = contract(1)
        staging = data["drive_staging"]
        self.assert_common_prewrite_guards(staging)
        self.assertEqual(staging["publish_order"], ["image", "manifest"])
        self.assertTrue(staging["manifest_is_readiness_signal"])
        self.assertIn(
            "materialize-and-validate-rpi5-stage-envelope",
            staging["preflight_order"],
        )
        self.assertIn(
            "verify-stage-sender-runtime",
            staging["preflight_order"],
        )
        self.assertTrue(
            data["authority"]["stage_sender_runtime_alignment_required_before_first_mutation"]
        )

    def test_v2_uses_sender_envelope_and_preserves_page_order(self):
        data = contract(2)
        staging = data["drive_staging"]
        self.assert_common_prewrite_guards(staging)
        self.assertEqual(data["activity"]["min_pages"], 2)
        self.assertEqual(data["activity"]["max_pages"], 12)
        self.assertEqual(
            staging["upload_order"],
            "all-pages-in-ascending-index-then-manifest",
        )
        self.assertTrue(staging["all_page_bytes_and_manifest_must_exist_before_first_mutation"])
        self.assertTrue(staging["manifest_validation_required_before_first_mutation"])
        self.assertTrue(
            data["authority"]["stage_sender_runtime_alignment_required_before_first_mutation"]
        )

    def test_stage_sender_is_separate_from_pull_only_ingest_operator(self):
        for version in (1, 2):
            data = contract(version)
            self.assertFalse(data["host_ingestion"]["host_rclone_upload_allowed"])
            self.assertEqual(
                data["host_ingestion"]["transport_direction"],
                "drive-to-rpi5-pull-only",
            )
            self.assertEqual(
                data["staging_sender"]["contract_ref"],
                "deploy/publish-trusted-rpi5-stage-sender-v1.json",
            )
            self.assertTrue(data["staging_sender"]["arbitrary_rclone_forbidden"])
            self.assertTrue(data["staging_sender"]["staging_pass_is_not_publication_success"])
            self.assertFalse(data["staging_sender"]["publish_uses_canary_mode"])

    def test_sender_contract_is_owner_gated_and_fail_closed(self):
        authority = self.sender["authority"]
        for key in (
            "source_merge_authorizes_live",
            "source_merge_authorizes_drive_write",
            "source_merge_authorizes_ingest",
            "source_merge_authorizes_publish",
            "source_merge_authorizes_credentials",
        ):
            self.assertFalse(authority[key])
        self.assertTrue(authority["explicit_owner_publish_required"])

        runtime = self.sender["runtime_preflight"]
        self.assertTrue(runtime["required_before_first_drive_mutation"])
        self.assertTrue(runtime["fresh_rpi5_main_required"])
        self.assertTrue(runtime["installed_sender_blob_must_match_fresh_source"])
        self.assertTrue(runtime["installed_wrapper_blob_must_match_fresh_source"])
        self.assertTrue(runtime["credential_content_read_forbidden"])

        sender = self.sender["staging_sender"]
        self.assertEqual(sender["production_namespace"], "pending")
        self.assertEqual(sender["canary_namespace"], "canary")
        self.assertTrue(sender["canary_mode_forbidden_for_publish"])
        self.assertTrue(sender["arbitrary_namespace_forbidden"])
        self.assertTrue(sender["arbitrary_rclone_forbidden"])
        self.assertEqual(
            sender["after_first_mutation_error"],
            "stop-without-retry-rollback-cleanup-or-alternate-mutation",
        )

    def test_canary_evidence_is_historical_not_runtime_authority(self):
        evidence = self.sender["canary_evidence"]
        self.assertEqual(
            evidence["rpi5_main_revision"],
            "b7dce379d48c7214ccabe14f28ce5dbdc998d781",
        )
        self.assertEqual(evidence["activity_id"], "1132001")
        self.assertEqual(evidence["namespace"], "canary")
        self.assertTrue(evidence["pending_same_id_absent"])
        self.assertTrue(evidence["drive_readback_verified"])
        self.assertFalse(evidence["ingest_executed"])
        self.assertFalse(evidence["publish_executed"])
        self.assertTrue(evidence["historical_only"])


if __name__ == "__main__":
    unittest.main()
