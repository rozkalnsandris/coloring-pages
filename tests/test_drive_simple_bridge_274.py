"""One-helper PUBLISH Drive bridge offline regression tests (#274)."""
import dataclasses
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools/coloring-pages-drive-upload"
API = runpy.run_path(str(SCRIPT))
freeze, send_once = API["freeze"], API["send_once"]
Blocked, UncertainUpload = API["Blocked"], API["UncertainUpload"]
FOLDER = "pinnedFolder0987654321"
PNG = b"\x89PNG\r\n\x1a\n" + b"fixture-only-not-a-real-a4-png"


def make_hash(data):
    return hashlib.sha256(data).hexdigest()


class SimpleBridgeTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.dir = Path(self.folder.name)
        self.rows = []
        for number in ("0427183", "0427184"):
            self.rows.append(self.make_activity(number))
        self.save_index()

    def make_activity(self, ident):
        data = PNG + ident.encode()
        name = ident + ".png"
        (self.dir / name).write_bytes(data)
        manifest = {
            "schema": "rozkalns.coloring-pages.drive-staging-manifest.v1",
            "id": ident, "sha256": make_hash(data),
            "size_bytes": len(data), "title": "Frosch", "character": "",
            "category": "tiere", "age": "3-6", "difficulty": "easy",
            "language": "de", "source_kind": "chatgpt-generated-png",
            "approval_class": "explicit-owner-chat-approval",
        }
        (self.dir / (ident + ".json")).write_text(json.dumps(manifest))
        return {
            "id": ident, "png": name, "manifest": ident + ".json",
            "sha256": make_hash(data), "size_bytes": len(data),
        }

    def save_index(self):
        (self.dir / "preflight-index.json").write_text(json.dumps({
            "schema": API["INDEX_SCHEMA"], "activities": self.rows,
        }))

    def cli(self, folder=FOLDER):
        return subprocess.run([
            sys.executable, str(SCRIPT), "--prepared-dir", str(self.dir),
            "--folder-id", folder,
        ], capture_output=True, text=True, check=False)

    def blocked(self, reason):
        with self.assertRaisesRegex(Blocked, reason):
            freeze(self.dir, FOLDER)

    def sender(self, calls, failure_at=0, invalid_at=0):
        def handler(url, content_type, body):
            calls.append((url, content_type, body))
            pos = len(calls)
            if pos == failure_at:
                raise TimeoutError("unknown remote mutation")
            req = self.plan[pos - 1]
            return {
                "id": "drivefile_" + str(pos).zfill(12),
                "name": req.filename, "mimeType": req.mime,
                "parents": [FOLDER], "size": str(req.media_size),
                "md5Checksum": req.media_md5 if pos != invalid_at else "0" * 32,
            }
        return handler

    @property
    def plan(self):
        return freeze(self.dir, FOLDER)

    def test_two_prepared_activities_exact_order(self):
        items = self.plan
        self.assertEqual([x.filename for x in items], [
            "0427183.png", "0427183.json", "0427184.png", "0427184.json",
        ])
        self.assertEqual([x.mime for x in items], [
            "image/png", "application/json", "image/png", "application/json",
        ])
        for item in items:
            self.assertEqual(item.folder_id, FOLDER)
            self.assertEqual(item.request_sha256, make_hash(item.body))
            self.assertIn(b'"parents":["' + FOLDER.encode() + b'"]', item.body)
            self.assertEqual(item.body.count(b"Content-Type:"), 2)
            self.assertTrue(item.content_type.startswith("multipart/related; boundary="))

    def test_cli_is_strictly_check_only_nonzero(self):
        proc = self.cli()
        self.assertEqual(proc.returncode, 3)
        self.assertIn("BRIDGE=OFFLINE_ONLY", proc.stdout)
        self.assertIn("UPLOAD_PERFORMED=NO", proc.stdout)
        self.assertIn("PUBLISH=NOT_PERFORMED", proc.stdout)
        self.assertNotIn("PASS", proc.stdout)

    def test_cli_rejects_folder_path_not_id(self):
        self.assertEqual(self.cli("pending/").returncode, 2)

    def test_no_oauth_or_http_implementation(self):
        code = SCRIPT.read_text()
        for forbidden in ("urllib.request", "import requests", "from requests",
                          "access_token", "Bearer ", "os.environ", "urlopen(",
                          "client_secret", "import socket"):
            self.assertNotIn(forbidden, code)

    def test_tampered_png_sha_blocks_whole_batch(self):
        (self.dir / "0427184.png").write_bytes(PNG + b"modified")
        self.blocked("png-hash-or-signature")

    def test_missing_last_manifest_blocks_whole_batch(self):
        (self.dir / "0427184.json").unlink()
        self.blocked("file-open-failed")

    def test_manifest_identity_mismatch(self):
        path = self.dir / "0427184.json"
        man = json.loads(path.read_text())
        man["sha256"] = "0" * 64
        path.write_text(json.dumps(man))
        self.blocked("manifest-binding")

    def test_duplicate_id_fails(self):
        self.rows.append(self.rows[0].copy())
        self.save_index()
        self.blocked("invalid-or-duplicate-id")

    def test_duplicate_json_key_fails(self):
        p = self.dir / "0427183.json"
        p.write_bytes(p.read_bytes().replace(b'"id":', b'"id":"0000000","id":', 1))
        self.blocked("duplicate-json-key")

    def test_category_cannot_be_object(self):
        p = self.dir / "0427183.json"
        m = json.loads(p.read_text())
        m["category"] = ["tiere"]
        p.write_text(json.dumps(m))
        self.blocked("manifest-binding")

    def test_prepared_symlink_is_blocked(self):
        p = self.dir / "0427183.png"
        p.unlink()
        target = self.dir / "some-file"
        target.write_bytes(PNG)
        p.symlink_to(target)
        self.blocked("file-open-failed")

    def test_index_path_escape_is_blocked(self):
        self.rows[0]["png"] = "../foo.png"
        self.save_index()
        self.blocked("filename-mismatch")

    def test_oversized_png_precheck_bounded_read(self):
        p = self.dir / "0427183.png"
        with p.open("r+b") as stream:
            stream.truncate(100_000_000)
        self.blocked("file-size-limit")

    def test_oversized_json_bounded_read(self):
        p = self.dir / "0427183.json"
        with p.open("ab") as stream:
            stream.write(b" " * API["JSON_LIMIT"])
        self.blocked("file-size-limit")

    def test_multipart_over_limit_includes_frame(self):
        item = self.rows[0]
        raw = PNG + b"x" * (API["LIMIT"] - len(PNG) - 10)
        p = self.dir / item["png"]
        p.write_bytes(raw)
        item["sha256"], item["size_bytes"] = make_hash(raw), len(raw)
        path = self.dir / item["manifest"]
        m = json.loads(path.read_text())
        m["sha256"], m["size_bytes"] = item["sha256"], item["size_bytes"]
        path.write_text(json.dumps(m))
        self.save_index()
        self.blocked("multipart-over-5mb")

    def test_mock_sender_returns_ids_not_publish_status(self):
        calls = []
        result = send_once(self.plan, self.sender(calls))
        self.assertEqual(len(result), 4)
        self.assertEqual(len(calls), 4)
        self.assertTrue(all(item[0] == API["URL"] for item in calls))

    def test_sender_failure_first_has_no_retry(self):
        calls = []
        with self.assertRaises(UncertainUpload) as ctx:
            send_once(self.plan, self.sender(calls, failure_at=1))
        self.assertEqual(ctx.exception.attempt, 1)
        self.assertEqual(len(calls), 1)

    def test_sender_failure_later_has_no_retry(self):
        calls = []
        with self.assertRaises(UncertainUpload) as ctx:
            send_once(self.plan, self.sender(calls, failure_at=3))
        self.assertEqual(ctx.exception.attempt, 3)
        self.assertEqual(len(calls), 3)

    def test_response_md5_mismatch_stops_without_manifest(self):
        calls = []
        with self.assertRaisesRegex(UncertainUpload, "response-identity-uncertain"):
            send_once(self.plan, self.sender(calls, invalid_at=1))
        self.assertEqual(len(calls), 1)

    def test_fake_response_size_must_be_decimal_string(self):
        requests = self.plan
        def response(url, content_type, body):
            req = requests[0]
            return {"id": "someid_123456789", "name": req.filename, "mimeType": req.mime,
                    "parents": [FOLDER], "size": req.media_size,
                    "md5Checksum": req.media_md5}
        with self.assertRaisesRegex(UncertainUpload, "response-identity-uncertain"):
            send_once(requests, response)

    def test_wrong_mime_order_preflight(self):
        items = self.plan
        with self.assertRaisesRegex(Blocked, "frozen-identity-or-order"):
            send_once((items[1], items[0]), lambda *args: self.fail("called sender"))

    def test_mutated_body_blocked_before_first_call(self):
        items = self.plan
        first = dataclasses.replace(items[0], body=items[0].body + b"bad")
        with self.assertRaisesRegex(Blocked, "frozen-identity-or-order"):
            send_once((first,) + items[1:], lambda *args: self.fail("called sender"))

    def test_forged_media_sha256_and_fingerprint_fail_before_sender(self):
        items = self.plan
        altered = dataclasses.replace(items[0], media_sha256="0" * 64)
        altered = dataclasses.replace(altered, identity_sha256=API["identity_digest"](
            altered.filename, altered.mime, altered.folder_id,
            altered.content_type, altered.media_sha256, altered.media_md5,
            altered.media_size, altered.request_sha256,
        ))
        with self.assertRaisesRegex(Blocked, "frozen-identity-or-order"):
            send_once((altered,) + items[1:], lambda *args: self.fail("called sender"))

    def test_forged_media_md5_and_fingerprint_fail_before_sender(self):
        items = self.plan
        altered = dataclasses.replace(items[0], media_md5="0" * 32)
        altered = dataclasses.replace(altered, identity_sha256=API["identity_digest"](
            altered.filename, altered.mime, altered.folder_id,
            altered.content_type, altered.media_sha256, altered.media_md5,
            altered.media_size, altered.request_sha256,
        ))
        with self.assertRaisesRegex(Blocked, "frozen-identity-or-order"):
            send_once((altered,) + items[1:], lambda *args: self.fail("called sender"))

    def test_forged_media_size_and_fingerprint_fail_before_sender(self):
        items = self.plan
        altered = dataclasses.replace(items[0], media_size=items[0].media_size + 1)
        altered = dataclasses.replace(altered, identity_sha256=API["identity_digest"](
            altered.filename, altered.mime, altered.folder_id,
            altered.content_type, altered.media_sha256, altered.media_md5,
            altered.media_size, altered.request_sha256,
        ))
        with self.assertRaisesRegex(Blocked, "frozen-identity-or-order"):
            send_once((altered,) + items[1:], lambda *args: self.fail("called sender"))

    def test_valid_bodies_in_two_folders_block_entire_batch(self):
        items = self.plan
        other_folder = "differentPendingFolder123"
        second_id = items[2].filename[:-4]
        png = (self.dir / (second_id + ".png")).read_bytes()
        manifest = (self.dir / (second_id + ".json")).read_bytes()
        altered_pair = (
            API["multipart"](second_id + ".png", "image/png", png, other_folder),
            API["multipart"](second_id + ".json", "application/json", manifest, other_folder),
        )
        calls = []
        with self.assertRaisesRegex(Blocked, "batch-folder-or-id-mismatch"):
            send_once(items[:2] + altered_pair, lambda *args: calls.append(args))
        self.assertEqual(calls, [])

    def test_duplicate_ids_in_distinct_valid_pairs_block_entire_batch(self):
        items = self.plan
        calls = []
        with self.assertRaisesRegex(Blocked, "batch-folder-or-id-mismatch"):
            send_once(items[:2] + items[:2], lambda *args: calls.append(args))
        self.assertEqual(calls, [])

    def test_request_body_metadata_mismatch_blocks_before_sender(self):
        items = self.plan
        altered = dataclasses.replace(items[0], body=items[0].body.replace(
            b'"parents":["' + FOLDER.encode() + b'"]',
            b'"parents":["otherPendingFolder123"]',
        ))
        altered = dataclasses.replace(
            altered, request_sha256=make_hash(altered.body),
            identity_sha256=API["identity_digest"](
                altered.filename, altered.mime, altered.folder_id,
                altered.content_type, altered.media_sha256, altered.media_md5,
                altered.media_size, altered.request_sha256,
            ),
        )
        with self.assertRaisesRegex(Blocked, "frozen-identity-or-order"):
            send_once((altered,) + items[1:], lambda *args: self.fail("called sender"))

    def with_forged_manifest(self, index, **replacement_fields):
        items = list(self.plan)
        request = items[index]
        raw = json.loads((self.dir / request.filename).read_text())
        raw.update(replacement_fields)
        items[index] = API["multipart"](
            request.filename, "application/json",
            json.dumps(raw).encode("utf-8"), FOLDER,
        )
        return tuple(items)

    def test_manifest_sha_mismatch_blocks_before_any_callback(self):
        calls = []
        forged = self.with_forged_manifest(1, sha256="0" * 64)
        with self.assertRaisesRegex(Blocked, "manifest-binding"):
            send_once(forged, lambda *args: calls.append(args))
        self.assertEqual(calls, [])

    def test_manifest_size_mismatch_blocks_before_any_callback(self):
        calls = []
        forged = self.with_forged_manifest(1, size_bytes=1)
        with self.assertRaisesRegex(Blocked, "manifest-binding"):
            send_once(forged, lambda *args: calls.append(args))
        self.assertEqual(calls, [])

    def test_manifest_wrong_id_blocks_before_any_callback(self):
        calls = []
        forged = self.with_forged_manifest(1, id="7654321")
        with self.assertRaisesRegex(Blocked, "manifest-binding"):
            send_once(forged, lambda *args: calls.append(args))
        self.assertEqual(calls, [])

    def test_manifest_wrong_category_blocks_before_any_callback(self):
        calls = []
        forged = self.with_forged_manifest(1, category="not-a-category")
        with self.assertRaisesRegex(Blocked, "manifest-binding"):
            send_once(forged, lambda *args: calls.append(args))
        self.assertEqual(calls, [])

    def test_invalid_second_activity_manifest_stops_entire_batch(self):
        calls = []
        forged = self.with_forged_manifest(3, sha256="f" * 64)
        with self.assertRaisesRegex(Blocked, "manifest-binding"):
            send_once(forged, lambda *args: calls.append(args))
        self.assertEqual(calls, [])

    def test_duplicate_json_manifest_key_blocks_before_sender(self):
        calls = []
        items = list(self.plan)
        request = items[1]
        raw = (self.dir / request.filename).read_bytes().replace(
            b'"id":', b'"id":"7654321","id":', 1,
        )
        items[1] = API["multipart"](request.filename, request.mime, raw, FOLDER)
        with self.assertRaisesRegex(Blocked, "duplicate-json-key"):
            send_once(tuple(items), lambda *args: calls.append(args))
        self.assertEqual(calls, [])

    def test_missing_manifest_field_blocks_before_any_callback(self):
        calls = []
        items = list(self.plan)
        request = items[1]
        obj = json.loads((self.dir / request.filename).read_text())
        obj.pop("size_bytes")
        items[1] = API["multipart"](
            request.filename, request.mime, json.dumps(obj).encode(), FOLDER,
        )
        with self.assertRaisesRegex(Blocked, "invalid-manifest"):
            send_once(tuple(items), lambda *args: calls.append(args))
        self.assertEqual(calls, [])

    def test_missing_sender_does_not_attempt_upload(self):
        with self.assertRaisesRegex(Blocked, "invalid-frozen-or-sender"):
            send_once(self.plan, None)


if __name__ == "__main__":
    unittest.main()
