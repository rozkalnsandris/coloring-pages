import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED_SHA = "94187cc447fc80757db10ac25d49717d00dc8430"


class SimpleDeployPublishTests(unittest.TestCase):
    def test_caller_is_pinned_to_immutable_shared_revision(self):
        workflow = (ROOT / ".github/workflows/simple-deploy.yml").read_text(
            encoding="utf-8"
        )

        expected = (
            "uses: rozkalnsandris/ops-workflows/.github/workflows/"
            f"simple-deploy.yml@{SHARED_SHA}"
        )
        self.assertIn(expected, workflow)
        self.assertRegex(
            workflow,
            r"simple-deploy\.yml@[0-9a-f]{40}",
        )
        self.assertNotRegex(
            workflow,
            r"simple-deploy\.yml@(main|master|v[0-9])\b",
        )

    def test_caller_has_minimum_required_permissions(self):
        workflow = (ROOT / ".github/workflows/simple-deploy.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("permissions:\n  contents: read\n  packages: write", workflow)
        self.assertIn("source_sha: ${{ github.sha }}", workflow)
        self.assertIn("branches: [main]", workflow)
        self.assertNotIn("secrets:", workflow)
        self.assertNotIn("\n    run:", workflow)

    def test_publication_paths_cover_runtime_inputs_and_skip_docs_only_changes(self):
        workflow = (ROOT / ".github/workflows/simple-deploy.yml").read_text(
            encoding="utf-8"
        )

        required_paths = [
            ".github/workflows/simple-deploy.yml",
            ".simple-deploy.json",
            "Dockerfile",
            "requirements-build.txt",
            "index.html",
            "detail.html",
            "print.html",
            "css/**",
            "js/**",
            "assets/**",
            "metadata/**",
            "originals/**",
            "tools/**",
            "deploy/**",
        ]
        self.assertIn("paths:", workflow)
        for path in required_paths:
            self.assertIn(f'      - "{path}"', workflow)

        for docs_only_path in ("README.md", "AGENTS.md", "docs/**", "tests/**"):
            self.assertNotIn(f'      - "{docs_only_path}"', workflow)

    def test_manifest_binds_expected_image_and_target(self):
        manifest = json.loads(
            (ROOT / ".simple-deploy.json").read_text(encoding="utf-8")
        )

        self.assertEqual(
            manifest["image"],
            "ghcr.io/rozkalnsandris/coloring-pages",
        )
        self.assertEqual(
            manifest["target"]["alias"],
            "coloring-pages-public-rpi5",
        )
        self.assertEqual(manifest["build"]["architecture"], "linux/arm64")
        self.assertEqual(manifest["registry"]["pull_profile"], "public-anonymous-pull")

    def test_source_identity_is_deferred_to_merged_main_sha(self):
        workflow = (ROOT / ".github/workflows/simple-deploy.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("push:", workflow)
        self.assertIn("branches: [main]", workflow)
        self.assertIn("source_sha: ${{ github.sha }}", workflow)


if __name__ == "__main__":
    unittest.main()
