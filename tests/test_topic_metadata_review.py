"""Offline regression: topic audit reports review candidates without changing content."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "tools/coloring-pages-topic-review"


def registry():
    return {"schema": "rozkalns.coloring-pages.topics.v2", "revision": 2,
            "topics": [
                {"id": "autos", "label": "Autos", "icon": "🚗", "kind": "evergreen",
                 "legacy_terms": ["auto", "cabrio", "wagen"]},
                {"id": "sport", "label": "Sport", "icon": "⚽", "kind": "evergreen",
                 "legacy_terms": ["sport", "fussball"]},
            ]}


def records():
    return [
        {"id": "3798896", "title": "Junge im Cabrio", "category": "figuren", "topics": ["autos"]},
        {"id": "7654321", "title": "Fröhlicher Tänzer", "category": "figuren", "topics": ["autos"]},
        {"id": "7777777", "title": "Altes Cabrio", "category": "fahrzeuge",
         "categories": ["fahrzeuge", "figuren"]},
        {"id": "4444444", "title": "Auto", "category": "figuren", "topics": []},
        {"id": "5555555", "title": "Sportler", "category": "figuren", "topics": ["sport"]},
    ]


class TopicMetadataReviewTests(unittest.TestCase):
    def run_review(self, data=None, topics=None, extra=()):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "catalog.json"
            topics_file = root / "topics.json"
            catalog_bytes = json.dumps(records() if data is None else data, ensure_ascii=False).encode("utf-8")
            topic_bytes = (json.dumps(registry() if topics is None else topics,
                                      ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            source.write_bytes(catalog_bytes)
            topics_file.write_bytes(topic_bytes)
            os.chmod(topics_file, 0o644)
            before = (source.read_bytes(), topics_file.read_bytes())
            result = subprocess.run(
                [sys.executable, str(HELPER), "--catalog", str(source),
                 "--topics", str(topics_file), "--topic", "autos",
                 "--category", "figuren", *extra],
                cwd=ROOT, capture_output=True, text=True, timeout=10, check=False)
            self.assertEqual((source.read_bytes(), topics_file.read_bytes()), before)
            return result, hashlib.sha256(catalog_bytes).hexdigest(), hashlib.sha256(topic_bytes).hexdigest()

    def test_exact_tags_and_legacy_fallback_are_review_only(self):
        response, catalog_sha, topics_sha = self.run_review()
        self.assertEqual(response.returncode, 0, response.stderr)
        report = json.loads(response.stdout)
        self.assertEqual(report["catalog_sha256"], catalog_sha)
        self.assertEqual(report["topics_sha256"], topics_sha)
        self.assertEqual(report["catalogue_activity_count"], 5)
        self.assertEqual(report["matched_count"], 3)
        self.assertEqual(report["title_cue_absent_review_count"], 1)
        self.assertEqual([e["id"] for e in report["entries"]], ["3798896", "7654321", "7777777"])
        self.assertEqual([e["assignment"] for e in report["entries"]],
                         ["explicit", "explicit", "legacy_title_terms"])
        self.assertEqual([e["title_cue_present"] for e in report["entries"]], [True, False, True])
        self.assertIn("not proof", report["notice"])
        self.assertNotIn("corrections", report)

    def test_exact_digest_binding_and_deterministic_report(self):
        first, catalog_sha, topics_sha = self.run_review()
        second, _, _ = self.run_review(extra=("--expected-catalog-sha256", catalog_sha,
                                             "--expected-topics-sha256", topics_sha))
        self.assertEqual(first.returncode, 0)
        self.assertEqual(first.stdout, second.stdout)

    def test_invalid_records_fail_without_partial_report(self):
        bad = [
            (records() + [records()[0]], "duplicate id"),
            ([{"id": "1", "title": "Text", "category": "figuren", "topics": ["unknown"]}],
             "invalid explicit topics"),
            ({"entries": []}, "catalogue must be an array"),
        ]
        for data, message in bad:
            with self.subTest(message=message):
                response, _, _ = self.run_review(data=data)
                self.assertNotEqual(response.returncode, 0)
                self.assertEqual(response.stdout, "")
                self.assertIn(message, response.stderr)

    def test_stale_digest_and_bad_registry_fail_closed(self):
        response, _, _ = self.run_review(extra=("--expected-catalog-sha256", "0" * 64))
        self.assertNotEqual(response.returncode, 0)
        self.assertEqual(response.stdout, "")
        self.assertIn("catalogue SHA-256 mismatch", response.stderr)
        broken = registry()
        broken["schema"] = "wrong"
        response, _, _ = self.run_review(topics=broken)
        self.assertNotEqual(response.returncode, 0)
        self.assertEqual(response.stdout, "")
        self.assertIn("TOPIC_REVIEW_ERROR", response.stderr)


if __name__ == "__main__":
    unittest.main()
