"""Offline auth/folder/Drive mock adapter regression coverage, issue #270."""
import dataclasses
import hashlib
import json
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools/coloring-pages-drive-trusted-upload-adapter"
API = runpy.run_path(str(MODULE))
Blob = API["Blob"]
Gate = API["SyntheticGate"]
Receipt = API["MockReceipt"]
StopBefore = API["StopBeforeWrite"]
StopAfter = API["StopAfterWrite"]
plan_v1 = API["plan_v1"]
simulate = API["simulate_v1"]
FOLDER = "frozen-pending-folder123"
ACTIVITY = "0427183"
PNG = b"\x89PNG\r\n\x1a\nfixture-bytes"


def blob(name, mime, data):
    return Blob(name, mime, data, hashlib.sha256(data).hexdigest(), len(data))


class TrustedAdapterSourceTests(unittest.TestCase):
    def setUp(self):
        self.gate = Gate(
            proof_class="synthetic-offline-only",
            owner_command="PUBLISH-fixture-only",
            surface=API["SURFACE"],
            intended_folder_id=FOLDER,
            observed_folder_id=FOLDER,
            auth_state="SIMULATED_CAPABILITY_ONLY",
            oauth_client_identity="offline-identity",
            observed_client_identity="offline-identity",
            folder_access="SIMULATED_WRITER_ONLY",
            catalog_state="SIMULATED_FRESH_NONCOLLIDING",
            importer_state="SIMULATED_PINNED",
            duplicate_names="SIMULATED_ABSENT",
            issued_at=1000,
            expires_at=1100,
            observed_at=1050,
        )
        self.png = blob(ACTIVITY + ".png", "image/png", PNG)
        self.manifest_bytes = json.dumps({
            "schema": "rozkalns.coloring-pages.drive-staging-manifest.v1",
            "id": ACTIVITY,
            "sha256": self.png.sha256,
            "size_bytes": self.png.size_bytes,
            "title": "Sankt Martin",
            "character": "",
            "category": "jahreszeiten",
            "age": "3-6",
            "difficulty": "easy",
            "language": "de",
            "source_kind": "chatgpt-generated-png",
            "approval_class": "explicit-owner-chat-approval",
        }).encode()
        self.manifest = blob(ACTIVITY + ".json", "application/json", self.manifest_bytes)

    def plan(self, **gate_changes):
        gate = dataclasses.replace(self.gate, **gate_changes)
        return plan_v1(ACTIVITY, self.png, self.manifest, FOLDER, gate)

    def receipts(self):
        return (
            Receipt("pngDriveFile_123456789", ACTIVITY + ".png", "image/png", FOLDER, len(PNG)),
            Receipt("jsonDriveFile_123456789", ACTIVITY + ".json", "application/json", FOLDER, len(self.manifest_bytes)),
        )

    def assert_blocked(self, pattern, **changes):
        with self.assertRaisesRegex(StopBefore, pattern):
            self.plan(**changes)

    def test_plan_is_frozen_two_part_v1_and_exact_folder(self):
        plan = self.plan()
        self.assertEqual(plan.folder_id, FOLDER)
        self.assertEqual([r.filename for r in plan.requests], [ACTIVITY + ".png", ACTIVITY + ".json"])
        self.assertEqual([r.mime_type for r in plan.requests], ["image/png", "application/json"])
        self.assertTrue(all(r.folder_id == FOLDER for r in plan.requests))
        self.assertEqual(len(plan.requests), 2)
        self.assertIn(self.png.data, plan.requests[0].body)
        self.assertIn(self.manifest_bytes, plan.requests[1].body)
        self.assertTrue(plan.requests[1].body.index(self.manifest_bytes) > 0)
        self.assertEqual(plan.requests[0].media_sha256, self.png.sha256)
        for r in plan.requests:
            self.assertEqual(r.request_sha256, hashlib.sha256(r.body).hexdigest())
            self.assertIn(b'"parents":["' + FOLDER.encode() + b'"]', r.body)
            self.assertTrue(r.content_type.startswith("multipart/related; boundary="))

    def test_synthetic_success_explicitly_not_live(self):
        receipt = simulate(self.plan(), self.receipts())
        self.assertEqual(receipt.state, "SIMULATED_ONLY_NOT_PUBLISH")
        self.assertEqual(receipt.accepted_count, 2)
        self.assertEqual(receipt.drive_writes, 0)
        self.assertEqual(receipt.live_imports, 0)

    def test_no_oauth_or_network_capability_in_module(self):
        text = MODULE.read_text()
        for forbidden in ("import requests", "urllib.request", "http.client", "access_token", "Bearer ", "os.environ", "subprocess", "from socket", "import socket", "requests.post"):
            self.assertNotIn(forbidden, text)
        self.assertNotIn("PUBLISH=PASS", text)

    def test_missing_gate_is_refused(self):
        with self.assertRaisesRegex(StopBefore, "missing-gate"):
            plan_v1(ACTIVITY, self.png, self.manifest, FOLDER, None)

    def test_real_proof_class_is_not_accepted(self):
        self.assert_blocked("no-production-permit", proof_class="owner-signed")

    def test_real_publish_phrase_does_not_grant_access(self):
        self.assert_blocked("owner-authority-unverified", owner_command="PUBLISH")

    def test_upload_surface_is_single_and_exact(self):
        self.assert_blocked("upload-surface-mismatch", surface="google-drive.upload_file")

    def test_frozen_folder_mismatch_fails(self):
        self.assert_blocked("intended-folder-mismatch", intended_folder_id="different-folder-123")

    def test_actual_folder_observation_mismatch_fails(self):
        self.assert_blocked("effective-folder-mismatch", observed_folder_id="different-folder-123")

    def test_invalid_pending_folder_fails(self):
        with self.assertRaisesRegex(StopBefore, "invalid-folder-id"):
            plan_v1(ACTIVITY, self.png, self.manifest, "pending/", self.gate)

    def test_unverified_auth_state_fails(self):
        self.assert_blocked("auth-unverified", auth_state="UNKNOWN")

    def test_client_identity_mismatch_fails(self):
        self.assert_blocked("oauth-client-mismatch", observed_client_identity="other-client")

    def test_folder_access_is_not_assumed(self):
        self.assert_blocked("folder-access-unverified", folder_access="UNKNOWN")

    def test_catalog_evidence_is_required(self):
        self.assert_blocked("catalog-unverified", catalog_state="NOT_CHECKED")

    def test_importer_evidence_is_required(self):
        self.assert_blocked("importer-unverified", importer_state="NOT_CHECKED")

    def test_ambiguous_duplicate_name_blocks_before_simulation(self):
        self.assert_blocked("duplicate-name-uncertain", duplicate_names="SAME_NAME_FOUND")

    def test_stale_auth_evidence_fails(self):
        self.assert_blocked("stale-evidence", observed_at=1100)

    def test_evidence_future_clock_fails(self):
        self.assert_blocked("stale-evidence", observed_at=999)

    def test_evidence_window_is_bounded(self):
        self.assert_blocked("stale-evidence", expires_at=1450)

    def test_bad_activity_id_fails(self):
        with self.assertRaisesRegex(StopBefore, "invalid-id"):
            plan_v1("123", self.png, self.manifest, FOLDER, self.gate)

    def test_wrong_png_sha_rejected_before_a_request(self):
        self.png = dataclasses.replace(self.png, sha256="0" * 64)
        with self.assertRaisesRegex(StopBefore, "blob-hash-size-mismatch"):
            self.plan()

    def test_wrong_manifest_size_rejected(self):
        self.manifest = dataclasses.replace(self.manifest, size_bytes=self.manifest.size_bytes + 1)
        with self.assertRaisesRegex(StopBefore, "blob-hash-size-mismatch"):
            self.plan()

    def test_manifest_id_mismatch_rejected(self):
        j = json.loads(self.manifest_bytes)
        j["id"] = "5555555"
        self.manifest = blob(ACTIVITY + ".json", "application/json", json.dumps(j).encode())
        with self.assertRaisesRegex(StopBefore, "manifest-binding"):
            self.plan()

    def test_manifest_category_mismatch_rejected(self):
        j = json.loads(self.manifest_bytes)
        j["category"] = ["jahreszeiten"]
        self.manifest = blob(ACTIVITY + ".json", "application/json", json.dumps(j).encode())
        with self.assertRaisesRegex(StopBefore, "manifest-binding"):
            self.plan()

    def test_png_signature_is_only_a_mock_check(self):
        self.png = blob(ACTIVITY + ".png", "image/png", b"invalid-not-png")
        with self.assertRaisesRegex(StopBefore, "png-signature-only-mismatch"):
            self.plan()

    def test_oversized_png_rejected_before_request(self):
        raw = API["PNG_SIGNATURE"] + b"x" * (API["MAX_MULTIPART_BYTES"] + 2)
        self.png = blob(ACTIVITY + ".png", "image/png", raw)
        j = json.loads(self.manifest_bytes)
        j["sha256"], j["size_bytes"] = self.png.sha256, self.png.size_bytes
        self.manifest = blob(ACTIVITY + ".json", "application/json", json.dumps(j).encode())
        with self.assertRaisesRegex(StopBefore, "multipart-over-5mb"):
            self.plan()

    def test_oversized_manifest_rejected_before_request(self):
        raw = self.manifest_bytes + b" " * API["MANIFEST_MAX_BYTES"]
        self.manifest = blob(ACTIVITY + ".json", "application/json", raw)
        with self.assertRaisesRegex(StopBefore, "manifest-too-large"):
            self.plan()

    def test_multipart_boundary_collision_rejected(self):
        # Force a deterministic boundary to exercise the defensive branch.
        builder = API["make_request"]
        namespace = builder.__globals__
        original = namespace["digest"]
        namespace["digest"] = lambda data: "b" * 64
        try:
            malicious = PNG + b"\\r\\n--ausmalwiese-" + b"b" * 32
            with self.assertRaisesRegex(StopBefore, "mime-boundary-collision"):
                builder(blob(ACTIVITY + ".png", "image/png", malicious), FOLDER)
        finally:
            namespace["digest"] = original

    def test_missing_mock_reply_prewrite_stop(self):
        with self.assertRaisesRegex(StopBefore, "missing-scripted-replies"):
            simulate(self.plan(), tuple())

    def test_first_mock_receipt_mismatch_stops_without_second(self):
        first, second = self.receipts()
        first = dataclasses.replace(first, parent_id="wrongFolder12345")
        with self.assertRaises(StopAfter) as e:
            simulate(self.plan(), (first, second))
        self.assertEqual((e.exception.attempted, e.exception.accepted), (1, 0))
        self.assertEqual(e.exception.reason, "simulated-receipt-mismatch")

    def test_missing_file_id_does_not_imply_success(self):
        first, second = self.receipts()
        first = dataclasses.replace(first, file_id="")
        with self.assertRaises(StopAfter) as e:
            simulate(self.plan(), (first, second))
        self.assertEqual(e.exception.attempted, 1)

    def test_wrong_response_size_is_terminal(self):
        first, second = self.receipts()
        second = dataclasses.replace(second, size_bytes=9)
        with self.assertRaises(StopAfter) as e:
            simulate(self.plan(), (first, second))
        self.assertEqual((e.exception.attempted, e.exception.accepted), (2, 1))

    def test_first_mock_transport_error_is_terminal(self):
        _, second = self.receipts()
        with self.assertRaises(StopAfter) as e:
            simulate(self.plan(), (TimeoutError("unknown"), second))
        self.assertEqual((e.exception.attempted, e.exception.accepted), (1, 0))
        self.assertEqual(e.exception.reason, "simulated-transport-unknown")

    def test_second_mock_transport_error_is_terminal(self):
        first, _ = self.receipts()
        with self.assertRaises(StopAfter) as e:
            simulate(self.plan(), (first, TimeoutError("unknown")))
        self.assertEqual((e.exception.attempted, e.exception.accepted), (2, 1))

    def test_mock_receipts_cannot_be_out_of_order(self):
        receipts = self.receipts()
        with self.assertRaises(StopAfter) as e:
            simulate(self.plan(), tuple(reversed(receipts)))
        self.assertEqual(e.exception.attempted, 1)

    def test_frozen_request_tamper_blocks_before_mock_send(self):
        plan = self.plan()
        first = dataclasses.replace(plan.requests[0], body=plan.requests[0].body + b"x")
        altered = dataclasses.replace(plan, requests=(first, plan.requests[1]))
        with self.assertRaisesRegex(StopBefore, "request-identity-drift"):
            simulate(altered, self.receipts())

    def test_wrong_request_order_refused_before_mock(self):
        plan = self.plan()
        altered = dataclasses.replace(plan, requests=tuple(reversed(plan.requests)))
        with self.assertRaisesRegex(StopBefore, "invalid-request-order"):
            simulate(altered, self.receipts())


if __name__ == "__main__":
    unittest.main()
