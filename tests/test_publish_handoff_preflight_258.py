"""Offline-only regressions for #258 local-to-Drive file handoff.

Synthetic snapshot references are never interpreted as real provider exports.
"""
import base64
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/coloring-pages-publish-handoff-preflight"
PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jfL8AAAAASUVORK5CYII="
)


class HandoffProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.prepared = self.dir / "prepared"
        self.prepared.mkdir()
        self.rows = []
        self.refs = []
        for i in range(5):
            page_id = str(5100000 + i)
            png_name, json_name = page_id + ".png", page_id + ".json"
            png = PNG_1PX
            png_sha = hashlib.sha256(png).hexdigest()
            (self.prepared / png_name).write_bytes(png)
            manifest = {
                "schema": "rozkalns.coloring-pages.drive-staging-manifest.v1",
                "id": page_id,
                "sha256": png_sha,
                "size_bytes": len(png),
                "title": "Sankt Martin " + str(i + 1),
                "character": "", "category": "jahreszeiten", "age": "3-6",
                "difficulty": "easy", "language": "de",
                "source_kind": "chatgpt-generated-png",
                "approval_class": "explicit-owner-chat-approval",
            }
            json_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
            (self.prepared / json_name).write_bytes(json_bytes)
            self.rows.append({
                "id": page_id, "png": png_name, "manifest": json_name,
                "sha256": png_sha, "size_bytes": len(png),
            })
            for name, data, mime in (
                (png_name, png, "image/png"), (json_name, json_bytes, "application/json")
            ):
                self.refs.append({
                    "file": name,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "size_bytes": len(data), "mime_type": mime,
                    "file_uri": {
                        "file_id": "sediment://file_synthetic_" + name,
                        "download_url": "https://example.invalid/synthetic/" + name,
                        "file_name": name, "mime_type": mime,
                    },
                })
        self.write("prepared/preflight-index.json", {
            "schema": "rozkalns.coloring-pages.publish-preflight-result.v1",
            "activities": self.rows,
        })
        self.capabilities = {
            "schema": "rozkalns.coloring-pages.publish-handoff-capabilities.v1",
            "upload": {
                "surface": "google-drive.upload_file",
                "source_field": "file_uri",
                "accepts": ["image/png", "application/json"],
            },
            "snapshot_materializer": {
                "available": True, "source_field": "file_uri",
                "supports_local_png_and_json": True,
            },
        }
        self.bindings = {
            "schema": "rozkalns.coloring-pages.publish-handoff-bindings.v1",
            "surface": "google-drive.upload_file",
            "source_field": "file_uri",
            "references": self.refs,
        }
        self.write("capabilities.json", self.capabilities)
        self.write("bindings.json", self.bindings)

    def write(self, path, payload):
        (self.dir / path).write_text(json.dumps(payload), encoding="utf-8")

    def run_probe(self, capabilities=True, bindings=True):
        cmd = [sys.executable, str(SCRIPT), "--prepared-dir", str(self.prepared)]
        if capabilities:
            cmd += ["--capabilities", str(self.dir / "capabilities.json")]
        if bindings:
            cmd += ["--bindings", str(self.dir / "bindings.json")]
        return subprocess.run(cmd, capture_output=True, text=True, check=False)

    def assert_blocked(self, reason):
        result = self.run_probe()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("HANDOFF_PREFLIGHT=BLOCKED", result.stderr)
        self.assertIn("REASON=" + reason, result.stderr)
        self.assertIn("DRIVE_MUTATION=NO", result.stderr)

    def test_five_pages_ten_synthetic_snapshots_are_only_offline_candidates(self):
        result = self.run_probe()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("REFERENCES_CHECKED=10", result.stdout)
        self.assertIn("HANDOFF_PREFLIGHT=OFFLINE_CANDIDATE_ONLY", result.stdout)
        self.assertIn("REMOTE_SNAPSHOT_BYTES_VERIFIED=NO", result.stdout)
        self.assertIn("PUBLISH_AUTHORIZATION=NOT_GRANTED", result.stdout)
        self.assertNotIn("=PASS", result.stdout)

    def test_no_capabilities_is_fail_closed(self):
        result = self.run_probe(capabilities=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("REASON=capabilities-not-provided", result.stderr)

    def test_materializer_absent(self):
        self.capabilities["snapshot_materializer"]["available"] = False
        self.write("capabilities.json", self.capabilities)
        self.assert_blocked("snapshot-materializer-unavailable")

    def test_source_file_ref_not_file_uri(self):
        self.capabilities["upload"]["source_field"] = "source_file_ref"
        self.write("capabilities.json", self.capabilities)
        self.assert_blocked("unsupported-upload-surface")

    def test_missing_bindings_is_fail_closed(self):
        result = self.run_probe(bindings=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("REASON=snapshot-references-not-provided", result.stderr)

    def test_missing_one_of_ten_references(self):
        self.bindings["references"].pop()
        self.write("bindings.json", self.bindings)
        self.assert_blocked("missing-or-extra-snapshots")

    def test_mismatched_sha256_fails(self):
        self.bindings["references"][0]["sha256"] = "0" * 64
        self.write("bindings.json", self.bindings)
        self.assert_blocked("binding-identity-mismatch")

    def test_mismatched_size_fails(self):
        self.bindings["references"][1]["size_bytes"] += 1
        self.write("bindings.json", self.bindings)
        self.assert_blocked("binding-identity-mismatch")

    def test_legacy_container_path_is_rejected(self):
        self.bindings["references"][0]["file_uri"] = {"container_path": "/mnt/data/a.png"}
        self.write("bindings.json", self.bindings)
        self.assert_blocked("unsupported-reference")

    def test_arbitrary_url_or_expired_ephemeral_string_is_rejected(self):
        self.bindings["references"][0]["file_uri"] = "https://example.invalid/expired"
        self.write("bindings.json", self.bindings)
        self.assert_blocked("unsupported-reference")

    def test_wrong_file_name_is_rejected(self):
        self.bindings["references"][0]["file_uri"]["file_name"] = "someone-else.png"
        self.write("bindings.json", self.bindings)
        self.assert_blocked("unsupported-reference")

    def test_mixed_surface_is_rejected(self):
        self.bindings["surface"] = "legacy-files"
        self.write("bindings.json", self.bindings)
        self.assert_blocked("unsupported-bindings-surface")

    def test_modified_local_png_is_detected(self):
        (self.prepared / self.rows[0]["png"]).write_bytes(PNG_1PX + b"altered")
        self.assert_blocked("png-identity-mismatch")

    def test_modified_manifest_is_detected(self):
        p = self.prepared / self.rows[0]["manifest"]
        d = json.loads(p.read_text())
        d["id"] = "9999999"
        p.write_text(json.dumps(d), encoding="utf-8")
        self.assert_blocked("manifest-identity-mismatch")

    def test_duplicate_id_fails(self):
        index = json.loads((self.prepared / "preflight-index.json").read_text())
        index["activities"][1]["id"] = index["activities"][0]["id"]
        self.write("prepared/preflight-index.json", index)
        self.assert_blocked("invalid-or-duplicate-id")

    def test_prepared_path_escape_is_rejected(self):
        index = json.loads((self.prepared / "preflight-index.json").read_text())
        index["activities"][0]["png"] = "../elsewhere.png"
        self.write("prepared/preflight-index.json", index)
        self.assert_blocked("filename-mismatch")


if __name__ == "__main__":
    unittest.main()
