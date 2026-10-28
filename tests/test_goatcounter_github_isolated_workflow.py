"""Source-only guard for the opt-in GitHub-hosted synthetic GoatCounter proof.

This test never downloads or executes GoatCounter or Docker. It checks
the manually triggered workflow's narrow isolation and privacy boundary.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/goatcounter-isolated-v27.yml"
RUNTIME = ROOT / "tools/goatcounter_isolated_runtime_probe.py"


class GithubIsolatedGoatCounterWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8")

    def test_manual_only_and_read_only_repository_token(self):
        self.assertIn("\non:\n  workflow_dispatch:\n", self.source)
        self.assertNotIn("pull_request:", self.source)
        self.assertNotIn("\n  push:", self.source)
        self.assertIn("permissions:\n  contents: read", self.source)
        self.assertIn("persist-credentials: false", self.source)
        self.assertNotIn("secrets.", self.source)

    def test_release_exact_bytes_and_checksum_before_execution(self):
        self.assertIn("goatcounter-v2.7.0-linux-amd64.gz", self.source)
        self.assertIn("13935060", self.source)
        self.assertIn(
            "98d221cb9c8ef2bf76d8daa9cca647839f8d8b0bb5bc7400ff9337c5da834511",
            self.source,
        )
        self.assertIn("sha256sum --check --status", self.source)
        self.assertIn("--retry 0", self.source)

    def test_real_probe_inside_unprivileged_offline_container(self):
        for required in (
            "docker run --rm",
            "--network none",
            "--read-only",
            "--cap-drop ALL",
            "--security-opt no-new-privileges",
            "--user 65532:65532",
            "--pids-limit 64",
            "--tmpfs /tmp:rw,exec,nosuid,nodev,size=192m,mode=1777",
            "PYTHONDONTWRITEBYTECODE=1",
            "goatcounter_isolated_runtime_probe.py",
            "goatcounter_offline_privacy_probe.py",
            "readonly",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.source)
        self.assertEqual(self.source.count("docker run --rm"), 1)
        self.assertEqual(self.source.count("--tmpfs /tmp:"), 1)
        self.assertNotIn("--tmpfs /tmp:rw,noexec", self.source)
        self.assertNotIn("docker.sock", self.source)
        self.assertNotIn("upload-artifact", self.source)
        self.assertNotIn("docker compose", self.source)
        runtime = RUNTIME.read_text(encoding="utf-8")
        self.assertIn('"-listen=127.0.0.1:"', runtime)
        self.assertIn("inspect_fixture(root, page_id=PAGE_ID", runtime)


if __name__ == "__main__":
    unittest.main()
