import base64
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/coloring-pages-drive-stage-envelope"
API = runpy.run_path(str(SCRIPT))
EnvelopeError = API["EnvelopeError"]
build_v1 = API["build_v1"]
build_v2 = API["build_v2"]
envelope_raw = API["envelope_raw"]

PNG1 = b"\x89PNG\r\n\x1a\n" + b"prepared-page-one"
PNG2 = b"\x89PNG\r\n\x1a\n" + b"prepared-page-two"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def common(source_kind):
    return {
        "title": "Ausmalbild",
        "character": "",
        "category": "lernen",
        "age": "3-6",
        "difficulty": "easy",
        "language": "de",
        "source_kind": source_kind,
        "approval_class": "explicit-owner-chat-approval",
    }


class TrustedStageEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def write_v1(self, ident, data=PNG1, category="lernen"):
        png = self.dir / f"{ident}.png"
        png.write_bytes(data)
        manifest = {
            "schema": "rozkalns.coloring-pages.drive-staging-manifest.v1",
            "id": ident,
            "sha256": digest(data),
            "size_bytes": len(data),
            **common("chatgpt-generated-png"),
        }
        manifest["category"] = category
        (self.dir / f"{ident}.json").write_text(
            json.dumps(manifest, separators=(",", ":")), encoding="utf-8"
        )
        return {
            "id": ident,
            "png": f"{ident}.png",
            "manifest": f"{ident}.json",
            "sha256": digest(data),
            "size_bytes": len(data),
        }

    def save_index(self, rows):
        (self.dir / "preflight-index.json").write_text(
            json.dumps(
                {
                    "schema": "rozkalns.coloring-pages.publish-preflight-result.v1",
                    "activities": rows,
                },
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )

    def write_v2(self, ident="7654321"):
        pages = []
        for index, data in enumerate((PNG1, PNG2), start=1):
            name = f"{ident}-{index}.png"
            (self.dir / name).write_bytes(data)
            pages.append(
                {
                    "index": index,
                    "file": name,
                    "sha256": digest(data),
                    "size_bytes": len(data),
                }
            )
        manifest = {
            "schema": "rozkalns.coloring-pages.drive-staging-manifest.v2",
            "id": ident,
            "pages": pages,
            **common("chatgpt-generated-png-set"),
        }
        path = self.dir / f"{ident}.json"
        path.write_text(json.dumps(manifest, separators=(",", ":")), encoding="utf-8")
        return path

    def test_v1_independent_activities_emit_png_then_manifest(self):
        rows = [self.write_v1("1234567", PNG1), self.write_v1("2345678", PNG2)]
        self.save_index(rows)
        envelope = build_v1(self.dir)
        self.assertEqual(
            envelope["schema"],
            "rozkalns.rpi5-main.coloring-pages-drive-stage-envelope.v1",
        )
        self.assertEqual(
            [activity["id"] for activity in envelope["activities"]],
            ["1234567", "2345678"],
        )
        for activity in envelope["activities"]:
            ident = activity["id"]
            self.assertEqual(
                [item["name"] for item in activity["artifacts"]],
                [f"{ident}.png", f"{ident}.json"],
            )
            self.assertEqual(
                [item["mime"] for item in activity["artifacts"]],
                ["image/png", "application/json"],
            )
            for item in activity["artifacts"]:
                raw = base64.b64decode(item["data_b64"], validate=True)
                self.assertEqual(digest(raw), item["sha256"])
                self.assertEqual(len(raw), item["size_bytes"])

    def test_v2_emits_ordered_pages_then_manifest(self):
        path = self.write_v2()
        envelope = build_v2(path)
        activity = envelope["activities"][0]
        self.assertEqual(activity["id"], "7654321")
        self.assertEqual(
            [item["name"] for item in activity["artifacts"]],
            ["7654321-1.png", "7654321-2.png", "7654321.json"],
        )
        self.assertEqual(activity["artifacts"][-1]["mime"], "application/json")

    def test_v1_sha_mismatch_fails_before_envelope(self):
        row = self.write_v1("1234567")
        row["sha256"] = "0" * 64
        self.save_index([row])
        with self.assertRaisesRegex(EnvelopeError, "png-sha-or-size-mismatch"):
            build_v1(self.dir)

    def test_v1_invalid_category_fails(self):
        row = self.write_v1("1234567", category="other")
        self.save_index([row])
        with self.assertRaisesRegex(EnvelopeError, "manifest-category-invalid"):
            build_v1(self.dir)

    def test_duplicate_v1_activity_id_fails(self):
        row = self.write_v1("1234567")
        self.save_index([row, dict(row)])
        with self.assertRaisesRegex(EnvelopeError, "duplicate-activity-id"):
            build_v1(self.dir)

    def test_v2_manifest_filename_must_match_id(self):
        path = self.write_v2()
        wrong = self.dir / "other.json"
        path.rename(wrong)
        with self.assertRaisesRegex(EnvelopeError, "v2-manifest-filename-invalid"):
            build_v2(wrong)

    def test_v2_page_order_or_name_mismatch_fails(self):
        path = self.write_v2()
        manifest = json.loads(path.read_text())
        manifest["pages"][1]["index"] = 3
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(EnvelopeError, "v2-page-order-or-name-invalid"):
            build_v2(path)

    def test_v2_page_sha_mismatch_fails(self):
        path = self.write_v2()
        manifest = json.loads(path.read_text())
        manifest["pages"][0]["sha256"] = "0" * 64
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(EnvelopeError, "png-sha-or-size-mismatch"):
            build_v2(path)

    def test_v2_manifest_is_last_even_after_serialization(self):
        path = self.write_v2()
        envelope = build_v2(path)
        raw = json.loads(envelope_raw(envelope))
        names = [item["name"] for item in raw["activities"][0]["artifacts"]]
        self.assertEqual(names[-1], "7654321.json")
        self.assertTrue(all(name.endswith(".png") for name in names[:-1]))

    def test_duplicate_json_key_is_rejected(self):
        row = self.write_v1("1234567")
        self.save_index([row])
        manifest_path = self.dir / "1234567.json"
        manifest_path.write_text(
            '{"schema":"rozkalns.coloring-pages.drive-staging-manifest.v1",'
            '"id":"1234567","id":"1234567"}',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(EnvelopeError, "duplicate-json-key"):
            build_v1(self.dir)

    def test_adapter_has_no_network_rclone_or_credential_implementation(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in (
            "import requests",
            "urllib.request",
            "import socket",
            "subprocess",
            "rclone ",
            "access_token",
            "client_secret",
            "Bearer ",
            "os.environ",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
