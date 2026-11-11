"""Offline regressions for the read-only SEO duplicate-title inventory."""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "tools" / "coloring-pages-seo-title-audit"


def activity(activity_id, title, topic="herbst"):
    return {
        "id": activity_id,
        "title": title,
        "categories": ["jahreszeiten"],
        "topics": [topic],
        "preview": f"/media/{activity_id}/preview.webp",
        "print": f"/media/{activity_id}/print.png",
    }


class SEOTitleAuditTests(unittest.TestCase):
    def run_audit(self, source, extra=()):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "catalog.json"
            raw = source if isinstance(source, bytes) else json.dumps(source, ensure_ascii=False).encode("utf-8")
            path.write_bytes(raw)
            result = subprocess.run(
                [sys.executable, str(HELPER), "--catalog", str(path), *extra],
                capture_output=True, text=True, check=False,
            )
            return result, hashlib.sha256(raw).hexdigest()

    def test_same_title_distinct_art_is_review_only(self):
        records = [
            activity("9115775", "Vogelscheuche im Kürbisfeld"),
            activity("5831978", "  VOGELSCHEUCHE   im Kürbisfeld ", "halloween"),
            activity("1234567", "Eichhörnchen"),
        ]
        outcome, digest = self.run_audit(records)
        self.assertEqual(outcome.returncode, 0, outcome.stderr)
        report = json.loads(outcome.stdout)
        self.assertEqual(report["catalog_sha256"], digest)
        self.assertEqual(report["activity_count"], 3)
        self.assertEqual(report["title_collision_group_count"], 1)
        self.assertEqual(report["title_collision_activity_count"], 2)
        group, = report["groups"]
        self.assertEqual([entry["id"] for entry in group["entries"]], ["5831978", "9115775"])
        self.assertEqual(group["artwork_identity"], "unverified")
        self.assertNotEqual(group["entries"][0]["print"], group["entries"][1]["print"])
        self.assertNotIn("canonical", group)
        self.assertNotIn("redirect", group)

    def test_byte_bound_report_is_deterministic(self):
        records = [activity("2", "Karotte"), activity("1", "Karotte")]
        first, digest = self.run_audit(records, extra=("--expected-catalog-sha256", hashlib.sha256(json.dumps(records, ensure_ascii=False).encode("utf-8")).hexdigest()))
        second, _ = self.run_audit(records)
        self.assertEqual(first.returncode, 0)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(json.loads(first.stdout)["catalog_sha256"], digest)

    def test_failure_emits_no_partial_report(self):
        invalid = [
            ([activity("1", "A"), activity("1", "B")], "duplicate activity id"),
            ({"items": []}, "catalogue must be an array"),
            ([{"id": "1", "title": " "}], "invalid title"),
            (b"{broken", "SEO_AUDIT_ERROR"),
        ]
        for source, error in invalid:
            with self.subTest(error=error):
                result, _ = self.run_audit(source)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn(error, result.stderr)
        mismatch, _ = self.run_audit([activity("1", "Dino")], extra=("--expected-catalog-sha256", "0" * 64,))
        self.assertNotEqual(mismatch.returncode, 0)
        self.assertEqual(mismatch.stdout, "")
        self.assertIn("SHA-256 mismatch", mismatch.stderr)


if __name__ == "__main__":
    unittest.main()
