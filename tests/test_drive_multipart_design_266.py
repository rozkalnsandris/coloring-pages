"""Independent, network-free multipart Drive request design regression tests (#266)."""
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/coloring-pages-drive-multipart-design"
API = runpy.run_path(str(SCRIPT))
DesignBlocked = API["DesignBlocked"]
design = API["design"]
multipart_request = API["multipart_request"]
PNG = b"\x89PNG\r\n\x1a\n"
FOLDER = "pinnedPendingFolder12345"


class OfflineDriveDesignTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.rows = []
        for i in range(5):
            self.rows.append(self.create_activity(5000110 + i, b"page-data-" + bytes([i])))
        self.write_index()

    def create_activity(self, ident, extra):
        ident = str(ident)
        png = PNG + extra
        sha = hashlib.sha256(png).hexdigest()
        (self.directory / (ident + ".png")).write_bytes(png)
        manifest = {
            "schema": "rozkalns.coloring-pages.drive-staging-manifest.v1",
            "id": ident, "sha256": sha, "size_bytes": len(png),
            "title": "Sankt Martin " + ident, "character": "",
            "category": "jahreszeiten", "age": "3-6",
            "difficulty": "easy", "language": "de",
            "source_kind": "chatgpt-generated-png",
            "approval_class": "explicit-owner-chat-approval",
        }
        (self.directory / (ident + ".json")).write_text(json.dumps(manifest) + "\n")
        return {
            "id": ident, "png": ident + ".png", "manifest": ident + ".json",
            "sha256": sha, "size_bytes": len(png),
        }

    def write_index(self):
        (self.directory / "preflight-index.json").write_text(json.dumps({
            "schema": "rozkalns.coloring-pages.publish-preflight-result.v1",
            "activities": self.rows,
        }))

    def cli(self, folder=FOLDER):
        return subprocess.run([
            sys.executable, str(SCRIPT), "--prepared-dir", str(self.directory),
            "--folder-id", folder,
        ], text=True, capture_output=True, check=False)

    def assert_blocked(self, reason):
        result = self.cli()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("DIRECT_DRIVE_DESIGN=BLOCKED", result.stderr)
        self.assertIn("REASON=" + reason, result.stderr)
        self.assertIn("DRIVE_WRITE=NO", result.stderr)

    def test_five_v1_activities_plan_ten_requests_ordered(self):
        requests = design(self.directory, FOLDER)
        self.assertEqual(len(requests), 10)
        for i in range(5):
            ident = self.rows[i]["id"]
            self.assertEqual(requests[2*i]["metadata"]["name"], ident + ".png")
            self.assertEqual(requests[2*i+1]["metadata"]["name"], ident + ".json")
            self.assertEqual(requests[2*i]["metadata"]["mimeType"], "image/png")
            self.assertEqual(requests[2*i+1]["metadata"]["mimeType"], "application/json")
            self.assertEqual(requests[2*i]["metadata"]["parents"], [FOLDER])
        self.assertEqual({r["url"] for r in requests}, {API["UPLOAD_URL"]})
        self.assertEqual({r["method"] for r in requests}, {"POST"})

    def test_multipart_request_exact_byte_identity(self):
        data = (self.directory / self.rows[0]["png"]).read_bytes()
        r = multipart_request(self.rows[0]["png"], "image/png", data, FOLDER)
        boundary = r["boundary"].encode()
        meta = json.dumps(r["metadata"], ensure_ascii=True, separators=(",", ":")).encode()
        expected = (
            b"--" + boundary + b"\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
            + meta + b"\r\n--" + boundary
            + b"\r\nContent-Type: image/png\r\n\r\n"
            + data + b"\r\n--" + boundary + b"--"
        )
        self.assertEqual(r["body"], expected)
        self.assertEqual(r["media_sha256"], hashlib.sha256(data).hexdigest())
        self.assertEqual(r["content_length"], len(expected))
        self.assertEqual(r["body_sha256"], hashlib.sha256(expected).hexdigest())
        self.assertEqual(r["content_type"], "multipart/related; boundary=" + r["boundary"])

    def test_manifest_media_is_exact_original_json_bytes(self):
        name = self.rows[0]["manifest"]
        data = (self.directory / name).read_bytes()
        r = design(self.directory, FOLDER)[1]
        self.assertIn(data, r["body"])
        self.assertEqual(r["media_sha256"], hashlib.sha256(data).hexdigest())

    def test_cli_is_nonzero_offline_not_publish_success(self):
        result = self.cli()
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertIn("DIRECT_DRIVE_DESIGN=OFFLINE_ONLY", result.stdout)
        self.assertIn("DRIVE_WRITE=NO", result.stdout)
        self.assertIn("AUTHORIZATION=NOT_AVAILABLE", result.stdout)
        self.assertIn("LIVE_IMPORT=NO", result.stdout)
        self.assertNotIn("=PASS", result.stdout)
        payload = json.loads(result.stdout[result.stdout.index("{"):])
        self.assertEqual(payload["request_count"], 10)
        self.assertNotIn("body", payload["requests"][0])

    def test_no_network_or_token_inputs(self):
        source = SCRIPT.read_text()
        self.assertNotIn("urllib.request", source)
        self.assertNotIn("import requests", source)
        self.assertNotIn("Authorization: Bearer", source)
        self.assertNotIn("subprocess", source)
        self.assertNotIn("os.environ", source)

    def test_no_files_changed_by_design(self):
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in self.directory.iterdir()}
        result = self.cli()
        self.assertEqual(result.returncode, 3)
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in self.directory.iterdir()}
        self.assertEqual(before, after)

    def test_invalid_folder_id_fails_closed(self):
        self.assertEqual(self.cli("pending/").returncode, 2)
        self.assertEqual(self.cli("root").returncode, 2)
        self.assertEqual(self.cli("https://drive.google.com/").returncode, 2)

    def test_wrong_png_hash_is_blocked(self):
        (self.directory / self.rows[0]["png"]).write_bytes(PNG + b"tampered")
        self.assert_blocked("png-identity-mismatch")

    def test_wrong_png_size_is_blocked(self):
        self.rows[0]["size_bytes"] += 1
        self.write_index()
        self.assert_blocked("png-identity-mismatch")

    def test_manifest_mismatched_sha_is_blocked(self):
        p = self.directory / self.rows[0]["manifest"]
        j = json.loads(p.read_text())
        j["sha256"] = "0" * 64
        p.write_text(json.dumps(j))
        self.assert_blocked("manifest-identity-mismatch")

    def test_manifest_category_mismatch_is_blocked(self):
        p = self.directory / self.rows[0]["manifest"]
        j = json.loads(p.read_text())
        j["category"] = "unknown"
        p.write_text(json.dumps(j))
        self.assert_blocked("manifest-identity-mismatch")

    def test_invalid_manifest_json_is_blocked(self):
        (self.directory / self.rows[0]["manifest"]).write_text("{invalid json")
        self.assert_blocked("invalid-manifest-json")

    def test_filename_traversal_is_blocked(self):
        self.rows[0]["png"] = "../hijack.png"
        self.write_index()
        self.assert_blocked("filename-mismatch")

    def test_symlink_is_blocked(self):
        p = self.directory / self.rows[0]["png"]
        p.unlink()
        outside = self.directory / "alternative"
        outside.write_bytes(PNG + b"abc")
        p.symlink_to(outside)
        self.assert_blocked("file-unavailable")

    def test_duplicate_activity_id_is_blocked(self):
        self.rows.append(self.rows[0].copy())
        self.write_index()
        self.assert_blocked("invalid-or-duplicate-id")

    def test_more_than_twenty_activities_fails(self):
        self.rows = self.rows * 5
        self.write_index()
        self.assert_blocked("invalid-activity-count")

    def test_multipart_over_five_mb_is_blocked(self):
        r = self.rows[4]
        data = PNG + b"x" * 5_000_000
        p = self.directory / r["png"]
        p.write_bytes(data)
        r["sha256"] = hashlib.sha256(data).hexdigest()
        r["size_bytes"] = len(data)
        j = self.directory / r["manifest"]
        m = json.loads(j.read_text())
        m["sha256"], m["size_bytes"] = r["sha256"], len(data)
        j.write_text(json.dumps(m))
        self.write_index()
        self.assert_blocked("multipart-over-5mb")

    def test_boundary_collision_fails_before_send(self):
        with self.assertRaisesRegex(DesignBlocked, "boundary-collision"):
            multipart_request("1234567.png", "image/png",
                              PNG + b"\r\n--collisionABC\r\ndata",
                              FOLDER, boundary="collisionABC")

    def test_no_arbitrary_media_types(self):
        with self.assertRaisesRegex(DesignBlocked, "unsupported-mime"):
            multipart_request("1234567.png", "text/html", PNG, FOLDER)

    def test_png_name_must_have_png_mime(self):
        with self.assertRaisesRegex(DesignBlocked, "mime-filename-mismatch"):
            multipart_request("1234567.png", "application/json", PNG, FOLDER)

    def test_json_name_must_have_json_mime(self):
        with self.assertRaisesRegex(DesignBlocked, "mime-filename-mismatch"):
            multipart_request("1234567.json", "image/png", PNG, FOLDER)

    def test_unhashable_manifest_category_is_rejected(self):
        p = self.directory / self.rows[0]["manifest"]
        j = json.loads(p.read_text())
        j["category"] = ["jahreszeiten"]
        p.write_text(json.dumps(j))
        self.assert_blocked("manifest-identity-mismatch")

    def test_bad_name_with_slash_rejected(self):
        with self.assertRaisesRegex(DesignBlocked, "invalid-filename"):
            multipart_request("../1234567.png", "image/png", PNG, FOLDER)

    def test_unrecognized_index_schema_is_blocked(self):
        p = self.directory / "preflight-index.json"
        j = json.loads(p.read_text())
        j["schema"] = "untrusted-v2"
        p.write_text(json.dumps(j))
        self.assert_blocked("invalid-index")

    def test_missing_last_manifest_blocks_entire_plan(self):
        (self.directory / self.rows[-1]["manifest"]).unlink()
        result = self.cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("DIRECT_DRIVE_DESIGN=BLOCKED", result.stderr)
        self.assertNotIn('"requests"', result.stdout)


if __name__ == "__main__":
    unittest.main()
