"""Source-side sitemap host-handoff pin and non-authority contract."""

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "deploy/sitemap-publication-handoff-v1.json"
HELPER = ROOT / "tools/coloring-pages-sitemap"
DOC = ROOT / "docs/SITEMAP_PUBLISHER_HANDOFF_V1.md"


class SitemapPublisherHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_handoff_source_is_pinned_to_exact_git_blob(self):
        cfg = self.contract
        self.assertEqual(cfg["schema"], "rozkalns.coloring-pages.sitemap-publisher-handoff.v1")
        self.assertEqual(cfg["status"], "source-only-advisory-not-host-authority")
        self.assertEqual(cfg["consumer_repository"], "rozkalnsandris/coloring-pages")
        self.assertEqual(cfg["host_owner_repository"], "rozkalnsandris/RPi5_main")
        self.assertEqual(cfg["generator"]["source_path"], "tools/coloring-pages-sitemap")
        data = HELPER.read_bytes()
        git_blob = hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\x00" + data
        ).hexdigest()
        self.assertEqual(cfg["generator"]["git_blob_sha1"], git_blob)
        self.assertFalse(cfg["generator"]["writes_files"])

    def test_generator_invocation_is_read_only_and_snapshot_bound(self):
        generator = self.contract["generator"]
        self.assertEqual(
            (generator["input_argument"], generator["snapshot_argument"],
             generator["candidate_verify_argument"]),
            ("--catalog", "--expected-catalog-sha256", "--verify-sitemap"),
        )
        source = HELPER.read_text(encoding="utf-8")
        self.assertIn("hashlib.sha256(catalog_bytes).hexdigest()", source)
        self.assertIn("candidate.read(len(expected_xml) + 1)", source)
        self.assertEqual(
            self.contract["static_urls"],
            [
                "https://coloring.rozkalns.net/",
                "https://coloring.rozkalns.net/kita",
            ],
        )

    def test_handoff_grants_no_production_authority(self):
        self.assertEqual(
            set(self.contract["authority"]),
            {
                "allows_host_operator_install",
                "allows_content_publication",
                "allows_application_deploy",
                "allows_scheduling",
                "allows_host_permission_changes",
                "allows_cloudflare_or_search_console_changes",
            },
        )
        self.assertTrue(all(value is False for value in self.contract["authority"].values()))
        self.assertNotIn("command", self.contract)
        self.assertNotIn("host_command", self.contract)

    def test_requires_shared_lock_and_production_reverification(self):
        requirements = self.contract["publisher_requirements"]
        self.assertEqual(len(requirements), len(set(requirements)))
        for required in (
            "pin-and-verify-exact-generator-Git-blob",
            "reuse-existing-Drive-ingest-advisory-lock-with-same-inode",
            "exclude-any-other-catalogue-writer-before-publication",
            "verify-candidate-XML-byte-for-byte-under-held-lock",
            "atomic-same-directory-replace-and-fsync",
            "fail-closed-no-retry-no-rollback-after-mutation",
        ):
            self.assertIn(required, requirements)
        docs = DOC.read_text(encoding="utf-8")
        self.assertIn("advisory", docs)
        self.assertIn("owner LIVE gate", docs)
        self.assertIn("SITEMAP_PUBLISHER_HANDOFF_V1", (ROOT / "docs/SEO_PREFLIGHT_V1.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
