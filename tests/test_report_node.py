"""Run the optional source-only Worker contract suite in the normal CI unittest job."""
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReportWorkerNodeTests(unittest.TestCase):
    def test_worker_and_report_ui(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js is required for the report Worker tests")
        loader = ROOT / "tests" / "cloudflare_email_loader.mjs"
        result = subprocess.run(
            [
                node,
                "--experimental-loader",
                str(loader),
                "--test",
                "tests/test_report_worker.mjs",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=40,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            "Worker tests failed:\n" + result.stdout + "\n" + result.stderr,
        )


if __name__ == "__main__":
    unittest.main()
