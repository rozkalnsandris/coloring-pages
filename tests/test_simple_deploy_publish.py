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
            "Dockerfile",
            "tools/coloring-pages-import",
            "deploy/nginx.conf",
            "index.html",
            "detail.html",
            "print.html",
            "css/**",
            "js/**",
            "assets/**",
        ]
        self.assertIn("paths:", workflow)
        for path in required_paths:
            self.assertIn(f'      - "{path}"', workflow)

        for non_image_input in (
            ".github/workflows/simple-deploy.yml",
            ".simple-deploy.json",
            "deploy/**",
            "deploy/chat-to-drive-ingestion.json",
            "deploy/docker-compose.simple.yml",
            "requirements-build.txt",
            "metadata/**",
            "originals/**",
            "tools/**",
            "README.md",
            "AGENTS.md",
            "docs/**",
            "tests/**",
        ):
            self.assertNotIn(f'      - "{non_image_input}"', workflow)

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

    def test_release_authority_documents_bounded_auto_live(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        simple_deploy = (ROOT / "docs/SIMPLE_DEPLOY.md").read_text(
            encoding="utf-8"
        )
        chat_to_drive = (ROOT / "docs/CHAT_TO_DRIVE_INGESTION_V1.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("bounded application auto-LIVE flow", agents)
        self.assertIn("coloring-pages-public-rpi5", simple_deploy)
        self.assertIn("to LIVE automatically", readme)
        self.assertIn(
            "No second generic `AUTHORIZE LIVE` command is required",
            chat_to_drive,
        )

        self.assertNotIn("A merge never authorizes RPi5 deployment", agents)
        self.assertNotIn(
            "No repository source change grants LIVE authority",
            simple_deploy,
        )


if __name__ == "__main__":
    unittest.main()
