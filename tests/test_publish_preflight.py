"""Regression coverage for independent PUBLISH batch preparation."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/coloring-pages-publish-preflight"


class IndependentPublishPreflightTests(unittest.TestCase):
    def inputs(self, folder, categories=("figuren", "figuren")):
        catalog = folder / "catalog.json"
        catalog.write_text(json.dumps([{"id": "0000001"}]))
        items = []
        for n, category in enumerate(categories):
            name = f"draft-{n}.png"
            image = Image.new("RGB", (1024, 1536), "white")
            ImageDraw.Draw(image).rectangle((200, 200, 820, 1250), outline="black", width=12)
            image.save(folder / name)
            items.append({"draft": name, "title": f"Junge {n+1}", "category": category})
        plan = folder / "plan.json"
        plan.write_text(json.dumps({
            "schema": "rozkalns.coloring-pages.publish-preflight-plan.v1",
            "activities": items,
        }))
        return plan, catalog

    def run_script(self, plan, catalog, output):
        return subprocess.run([
            sys.executable, str(SCRIPT), "--plan", str(plan),
            "--fresh-live-catalog", str(catalog), "--output-dir", str(output),
        ], capture_output=True, text=True)

    def test_independent_pages_generate_distinct_v1_pairs(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            plan, catalog = self.inputs(folder)
            output = folder / "prepared"
            result = self.run_script(plan, catalog, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            index = json.loads((output / "preflight-index.json").read_text())
            self.assertEqual(len(index["activities"]), 2)
            ids = {row["id"] for row in index["activities"]}
            self.assertEqual(len(ids), 2)
            self.assertNotIn("0000001", ids)
            for row in index["activities"]:
                self.assertRegex(row["id"], r"^\d{7}$")
                png = output / row["png"]
                manifest = json.loads((output / row["manifest"]).read_text())
                self.assertTrue(png.is_file())
                self.assertEqual(manifest["id"], row["id"])
                self.assertEqual(manifest["sha256"], row["sha256"])
                self.assertEqual(manifest["size_bytes"], png.stat().st_size)
                self.assertEqual(manifest["category"], "figuren")
            self.assertEqual(len(list(output.glob("*.png"))), 2)
            self.assertEqual(len(list(output.glob("*.json"))), 3)

    def test_invalid_category_fails_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            plan, catalog = self.inputs(folder, ("unknown",))
            output = folder / "prepared"
            self.assertNotEqual(self.run_script(plan, catalog, output).returncode, 0)
            self.assertFalse(output.exists())

    def test_existing_output_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            plan, catalog = self.inputs(folder, ("figuren",))
            output = folder / "prepared"
            output.mkdir()
            sentinel = output / "keep.txt"
            sentinel.write_text("keep")
            self.assertNotEqual(self.run_script(plan, catalog, output).returncode, 0)
            self.assertEqual(sentinel.read_text(), "keep")

    def test_duplicate_draft_fails_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            plan, catalog = self.inputs(folder)
            document = json.loads(plan.read_text())
            document["activities"][1]["draft"] = document["activities"][0]["draft"]
            plan.write_text(json.dumps(document))
            output = folder / "prepared"
            self.assertNotEqual(self.run_script(plan, catalog, output).returncode, 0)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
