"""Regressions for the direct Google Drive PUBLISH staging contract."""

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


class DirectDriveConnectorContractTest(unittest.TestCase):
    def setUp(self):
        self.legacy_sender = json.loads(
            (
                ROOT / "deploy/publish-trusted-rpi5-stage-sender-v1.json"
            ).read_text(encoding="utf-8")
        )

    def assert_common_prewrite_guards(self, data):
        staging = data["drive_staging"]
        self.assertEqual(staging["staging_surface"], "google-drive-connector-upload-file")
        self.assertEqual(
            staging["upload_surface_must_accept"],
            ["runtime-materialized-file-uri"],
        )
        self.assertTrue(staging["runtime_materialized_file_uri_required"])
        self.assertTrue(staging["raw_local_path_at_connector_boundary_forbidden"])
        self.assertTrue(staging["bare_file_id_forbidden"])
        self.assertTrue(staging["inline_base64_forbidden"])
        self.assertTrue(staging["arbitrary_url_file_handoff_forbidden"])
        self.assertTrue(staging["exact_local_artifacts_required_before_first_mutation"])
        self.assertFalse(staging["envelope_materialization_required_before_first_mutation"])
        self.assertFalse(staging["envelope_validation_required_before_first_mutation"])
        self.assertFalse(staging["trusted_host_stage_sender_upload_allowed"])
        self.assertTrue(staging["direct_google_drive_connector_upload_allowed"])
        self.assertTrue(staging["arbitrary_host_rclone_upload_forbidden"])
        self.assertEqual(staging["connector_upload_action"], "Google_Drive.upload_file")
        self.assertEqual(staging["connector_expected_input"], "file_uri")
        self.assertTrue(staging["connector_response_readback_required"])
        self.assertTrue(staging["single_upload_surface_per_publication"])
        self.assertTrue(staging["upload_surface_selection_required_before_first_mutation"])
        self.assertEqual(
            staging["connector_after_first_mutation_error"],
            "stop-without-retry-rollback-cleanup-or-alternate-mutation",
        )

        connector = data["direct_drive_connector"]
        self.assertEqual(connector["action"], "Google_Drive.upload_file")
        self.assertEqual(connector["destination_namespace"], "pending")
        self.assertTrue(connector["exact_folder_id_required"])
        self.assertEqual(connector["top_level_file_parameter"], "file_uri")
        self.assertTrue(connector["runtime_materialization_required"])
        self.assertTrue(connector["raw_local_path_at_connector_boundary_forbidden"])
        self.assertTrue(connector["bare_file_id_forbidden"])
        self.assertTrue(connector["inline_base64_forbidden"])
        self.assertTrue(connector["arbitrary_url_forbidden"])
        self.assertEqual(connector["accepted_input_expected"], "file_uri")
        self.assertTrue(connector["read_only_readback_required"])
        self.assertEqual(
            connector["mutating_dispatch_mode"],
            "one-explicit-upload-call-per-artifact",
        )
        self.assertTrue(connector["mutating_connector_loop_or_batch_dispatch_forbidden"])
        self.assertEqual(connector["upload_response_parent_field"], "parent_id")
        self.assertEqual(connector["metadata_readback_parent_field"], "parent_ids")
        self.assertEqual(
            connector["parent_identity_acceptance"],
            "exact-pending-folder-id-only",
        )

        authority = data["authority"]
        self.assertFalse(
            authority["stage_sender_runtime_alignment_required_before_first_mutation"]
        )
        self.assertTrue(
            authority["drive_connector_file_materialization_required_before_first_mutation"]
        )
        self.assertTrue(
            authority["publish_request_bridge_runtime_alignment_required_before_first_mutation"]
        )

        bridge = data["host_ingestion"]["request_bridge"]
        self.assertEqual(
            bridge["runtime_owner_repository"],
            "rozkalnsandris/RPi5_main",
        )
        self.assertEqual(
            bridge["contract_path"],
            "ops/contracts/coloring-pages-publish-request-bridge-v1.json",
        )
        self.assertEqual(
            bridge["installed_dispatcher_path"],
            "/usr/local/bin/coloring-pages-publish-request-dispatcher",
        )
        self.assertEqual(
            bridge["incoming_request"],
            "/srv/coloring-pages-content/state/publish-request-bridge/incoming/batch-<batch_id>.json",
        )
        self.assertEqual(
            bridge["incoming_ready"],
            "/srv/coloring-pages-content/state/publish-request-bridge/incoming/batch-<batch_id>.ready",
        )
        self.assertEqual(
            bridge["result_path"],
            "/srv/coloring-pages-content/state/publish-request-bridge/results/batch-<batch_id>.result.json",
        )
        self.assertEqual(
            bridge["request_schema"],
            "rozkalns.rpi5-main.coloring-pages-publish-request.v1",
        )
        self.assertEqual(
            bridge["result_schema"],
            "rozkalns.rpi5-main.coloring-pages-publish-request-result.v1",
        )
        self.assertEqual(bridge["batch_id_pattern"], "^[0-9a-f]{32}$")
        self.assertEqual(bridge["maximum_activities"], 20)
        self.assertEqual(
            bridge["request_write_action"],
            "Remote_Desktop_Commander.write_file",
        )
        self.assertEqual(
            bridge["ready_write_action"],
            "Remote_Desktop_Commander.write_file",
        )
        self.assertEqual(
            bridge["result_read_action"],
            "Remote_Desktop_Commander.read_file",
        )
        self.assertTrue(bridge["request_before_ready"])
        self.assertTrue(bridge["generic_start_process_ingest_forbidden"])
        self.assertFalse(bridge["request_contains_media_bytes"])
        self.assertTrue(bridge["base64_media_transfer_forbidden"])
        self.assertTrue(bridge["runtime_alignment_required_before_first_drive_mutation"])
        self.assertTrue(bridge["request_contains_manifest_metadata"])
        self.assertEqual(bridge["manifest_transport"], "inline-json-object")
        self.assertTrue(bridge["manifest_must_match_activity_identity"])
        self.assertFalse(bridge["normal_publish_drive_manifest_upload"])
        self.assertEqual(bridge["operator_manifest_argument"], "--manifest-json")
        self.assertEqual(
            bridge["terminal_success"],
            "every-requested-activity-status-is-PASS-or-ALREADY_PROCESSED",
        )

    def test_v1_uses_direct_connector_for_png_only_and_inline_manifest(self):
        data = contract(1)
        self.assert_common_prewrite_guards(data)
        staging = data["drive_staging"]
        self.assertEqual(staging["publish_order"], ["image"])
        self.assertFalse(staging["manifest_is_readiness_signal"])
        self.assertTrue(staging["bridge_ready_marker_is_readiness_signal"])
        self.assertFalse(staging["normal_publish_manifest_upload"])
        self.assertEqual(
            staging["manifest_transport"],
            "publish-request-bridge-inline",
        )
        self.assertIn(
            "materialize-runtime-file-reference-for-image",
            staging["preflight_order"],
        )
        self.assertIn("verify-ingest-operator-runtime", staging["preflight_order"])
        self.assertIn("verify-publish-request-bridge-runtime", staging["preflight_order"])
        self.assertIn("write-request-with-inline-manifest", staging["preflight_order"])
        self.assertIn("write-ready-marker", staging["preflight_order"])
        self.assertNotIn("invoke-google-drive-connector-image-then-manifest", staging["preflight_order"])
        self.assertEqual(
            data["host_ingestion"]["operator_invocation"],
            "/usr/local/bin/coloring-pages-drive-ingest --id <id> --expected-sha256 <sha256> --expected-size <bytes> --manifest-json <validated-v1-manifest-json>",
        )
        connector = data["direct_drive_connector"]
        self.assertEqual(connector["order"], ["png-page-only"])
        self.assertFalse(connector["manifest_upload_allowed_in_normal_publish"])
        self.assertEqual(
            connector["manifest_transport"],
            "publish-request-bridge-inline",
        )

    def test_v2_uses_direct_connector_and_preserves_page_order(self):
        data = contract(2)
        self.assert_common_prewrite_guards(data)
        staging = data["drive_staging"]
        self.assertEqual(data["activity"]["min_pages"], 2)
        self.assertEqual(data["activity"]["max_pages"], 12)
        self.assertEqual(
            staging["upload_order"],
            "all-pages-in-ascending-index",
        )
        self.assertFalse(staging["manifest_is_readiness_signal"])
        self.assertTrue(staging["bridge_ready_marker_is_readiness_signal"])
        self.assertFalse(staging["normal_publish_manifest_upload"])
        self.assertEqual(
            data["direct_drive_connector"]["order"],
            "all-pages-in-ascending-index",
        )
        self.assertFalse(
            data["direct_drive_connector"]["manifest_upload_allowed_in_normal_publish"]
        )
        self.assertTrue(
            staging["all_page_bytes_and_manifest_must_exist_before_first_mutation"]
        )
        self.assertTrue(staging["manifest_validation_required_before_first_mutation"])
        self.assertEqual(
            data["host_ingestion"]["operator_invocation"],
            "/usr/local/bin/coloring-pages-drive-ingest --id <id> --expected-page <index>:<sha256>:<bytes> [repeat --expected-page per page] --manifest-json <validated-v2-manifest-json>",
        )

    def test_pull_only_ingest_remains_separate(self):
        for version in (1, 2):
            data = contract(version)
            self.assertFalse(data["host_ingestion"]["host_rclone_upload_allowed"])
            self.assertEqual(
                data["host_ingestion"]["transport_direction"],
                "drive-to-rpi5-pull-only",
            )
            legacy = data["staging_sender"]
            self.assertEqual(
                legacy["contract_ref"],
                "deploy/publish-trusted-rpi5-stage-sender-v1.json",
            )
            self.assertFalse(legacy["production_upload_allowed"])
            self.assertTrue(legacy["arbitrary_rclone_forbidden"])
            self.assertFalse(legacy["publish_uses_canary_mode"])

    def test_legacy_sender_contract_is_not_production_default(self):
        self.assertEqual(
            self.legacy_sender["status"],
            "legacy-reviewed-fallback-not-production-default",
        )
        self.assertFalse(self.legacy_sender["authority"]["production_publish_default"])
        self.assertFalse(
            self.legacy_sender["runtime_preflight"]["required_before_first_drive_mutation"]
        )
        self.assertTrue(
            self.legacy_sender["handoff"][
                "legacy_sender_must_not_be_used_as_alternate_after_connector_attempt"
            ]
        )
        evidence = self.legacy_sender["canary_evidence"]
        self.assertTrue(evidence["historical_only"])
        self.assertFalse(evidence["publish_executed"])


if __name__ == "__main__":
    unittest.main()
