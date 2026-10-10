"""Dependency-free Worker/browser API contract tests; runs actual Worker code with fake D1."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WorkerContractTests(unittest.TestCase):
    def test_offline_api_compatibility(self):
        result = subprocess.run(
            ["node", "--test", "tests/worker_api_contract.mjs"],
            cwd=ROOT, capture_output=True, text=True, timeout=30, check=False,
        )
        self.assertEqual(
            result.returncode, 0,
            "Worker contract tests failed:\n" + result.stdout + "\n" + result.stderr,
        )


if __name__ == "__main__":
    unittest.main()
