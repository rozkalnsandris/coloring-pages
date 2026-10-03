import importlib.machinery
import importlib.util
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "coloring-pages-import"
LOADER = importlib.machinery.SourceFileLoader("coloring_pages_import_categories", str(MODULE_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
importer = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(importer)


class CategoryContractTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads(
            (ROOT / "metadata/categories.json").read_text(encoding="utf-8")
        )
        self.contract = json.loads(
            (ROOT / "deploy/chat-to-drive-ingestion.json").read_text(encoding="utf-8")
        )

    def test_registry_schema_and_ids_are_stable(self):
        self.assertEqual(
            self.registry["schema"],
            "rozkalns.coloring-pages.categories.v1",
        )
        ids = [item["id"] for item in self.registry["categories"]]
        self.assertEqual(
            ids,
            [
                "rettungshunde",
                "tiere",
                "fahrzeuge",
                "alphabet",
                "lernen",
                "jahreszeiten",
            ],
        )
        self.assertEqual(len(ids), len(set(ids)))

    def test_importer_and_drive_manifest_use_same_category_registry(self):
        registry_ids = {item["id"] for item in self.registry["categories"]}
        self.assertEqual(importer.load_allowed_categories(), frozenset(registry_ids))
        self.assertEqual(
            set(self.contract["manifest"]["allowed_category"]),
            registry_ids,
        )
        self.assertEqual(
            self.contract["manifest"]["category_registry"],
            "metadata/categories.json",
        )
        self.assertTrue(
            self.contract["authority"]["category_binding_required_before_first_mutation"]
        )
        self.assertTrue(
            self.contract["drive_staging"]["category_binding_required_before_upload"]
        )

    def test_public_category_buttons_match_registry(self):
        registry_ids = {item["id"] for item in self.registry["categories"]}
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        filters = set(re.findall(r'data-filter="([^"]+)"', index))
        self.assertEqual(filters, registry_ids)

    def test_runtime_image_contains_category_registry(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn(
            "COPY metadata/categories.json /usr/local/share/coloring-pages/categories.json",
            dockerfile,
        )


if __name__ == "__main__":
    unittest.main()
