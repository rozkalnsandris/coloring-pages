"""Run pure JavaScript basket model cases in ordinary Python unittest CI.

Node is available on the GitHub-hosted Ubuntu runner; use no npm install,
browser, network access or external test library.
"""

from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BasketSelectionJavaScriptTests(unittest.TestCase):
    def test_pure_model_node_cases(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js required to exercise the basket model")
        completed = subprocess.run(
            [node, "--test", "tests/test_print_basket_selection.mjs"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=40,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            f"Node basket-model tests failed:\n{completed.stdout}\n{completed.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
