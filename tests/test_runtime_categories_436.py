"""#436 managed taxonomy source safety tests (no production side effects)."""
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tools" / "coloring_pages_categories.py"
loader = importlib.machinery.SourceFileLoader("coloring_pages_categories_436", str(PATH))
spec = importlib.util.spec_from_loader(loader.name, loader)
registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(registry)


class ManagedCategoryTests(unittest.TestCase):
    def setUp(self):
        self.seed = registry.seed_from_source(ROOT / "metadata/categories.json")

    def test_seed_is_deterministic_and_core_is_stable(self):
        self.assertEqual(self.seed["revision"], 1)
        self.assertEqual([x["id"] for x in self.seed["categories"]], list(registry.CORE_IDS))
        self.assertEqual(registry.serialize_registry(self.seed), registry.serialize_registry(self.seed))

    def test_strict_registry_roundtrip_and_digest(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "categories.json"
            data = registry.serialize_registry(self.seed)
            path.write_bytes(data)
            doc, digest = registry.read_registry(path)
            self.assertEqual(doc, self.seed)
            self.assertEqual(digest, hashlib.sha256(data).hexdigest())

    def test_managed_add_rename_and_revision_change(self):
        doc = json.loads(json.dumps(self.seed))
        doc["revision"] = 2
        doc["categories"].append({"id": "berufe", "label": "Berufe"})
        newer = registry.serialize_registry(doc)
        doc["revision"] = 3
        doc["categories"][-1]["label"] = "Traumberufe"
        self.assertNotEqual(newer, registry.serialize_registry(doc))

    def test_bad_schemas_ids_labels_duplicates_and_core_removal(self):
        for value in [
            dict(self.seed, schema="wrong"),
            dict(self.seed, revision=0),
            dict(self.seed, revision=True),
            dict(self.seed, categories=self.seed["categories"][:-1]),
            dict(self.seed, categories=[*self.seed["categories"], self.seed["categories"][0]]),
            dict(self.seed, categories=[*self.seed["categories"], {"id": "../unsafe", "label": "X"}]),
            dict(self.seed, categories=[*self.seed["categories"], {"id": "essen-natur", "label": "Wrong"}]),
            dict(self.seed, categories=[*self.seed["categories"], {"id": "seasonal", "label": "Wrong"}]),
            dict(self.seed, categories=[*self.seed["categories"], {"id": "valid", "label": "\x00no"}]),
            dict(self.seed, categories=[*self.seed["categories"], {"id": "valid", "label": " é "}]),
            dict(self.seed, unexpected="x"),
        ]:
            with self.subTest(value=value), self.assertRaises(registry.RegistryError):
                registry.serialize_registry(value)

    def test_missing_symlink_and_malformed_registry_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "categories.json"
            with self.assertRaises(registry.RegistryError):
                registry.read_registry(path)
            path.write_text("{}", encoding="utf-8")
            with self.assertRaises(registry.RegistryError):
                registry.read_registry(path)
            path.unlink()
            path.symlink_to(ROOT / "metadata/categories.json")
            with self.assertRaises(registry.RegistryError):
                registry.read_registry(path)

    def test_unsafe_mode_and_noncanonical_json_refused(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "categories.json"
            path.write_bytes(registry.serialize_registry(self.seed))
            os.chmod(path, 0o666)
            with self.assertRaises(registry.RegistryError):
                registry.read_registry(path)
            os.chmod(path, 0o644)
            path.write_text(json.dumps(self.seed), encoding="utf-8")
            with self.assertRaises(registry.RegistryError):
                registry.read_registry(path)

    def test_importer_exact_digest_and_missing_registry_fail_closed(self):
        p = ROOT / "tools" / "coloring-pages-import"
        loader = importlib.machinery.SourceFileLoader("cp_import_436", str(p))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        importer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(importer)
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            for name in ["inbox", "originals", "public/media", "state"]:
                (root / name).mkdir(parents=True, exist_ok=True)
            (root / "public/catalog.json").write_text("[]\n")
            source = root / "inbox" / "page.png"
            source.write_bytes(b"invalid-image-is-safe-before-validation")
            metadata = {"id":"page", "title":"Page", "character":"", "category":"tiere", "age":"3-6", "difficulty":"easy", "language":"de"}
            with self.assertRaisesRegex(importer.ImportError, "registry"):
                importer.import_page(source, root, metadata)
            data = registry.serialize_registry(self.seed)
            (root / "public/categories.json").write_bytes(data)
            with self.assertRaisesRegex(importer.ImportError, "SHA-256"):
                importer.import_page(source, root, dict(metadata, category_registry_sha256="0"*64))
            self.assertEqual(list((root / "public/media").iterdir()), [])
            self.assertEqual((root / "public/catalog.json").read_text(), "[]\n")

    def test_nginx_read_only_runtime_without_seed_fallback(self):
        nginx = (ROOT / "deploy/nginx.conf").read_text()
        self.assertIn("location = /categories.json", nginx)
        self.assertIn("try_files /categories.json =503", nginx)
        self.assertNotIn("try_files /categories.json =404", nginx)
        self.assertIn("root /var/lib/coloring-pages/public", nginx)
        docker = (ROOT / "Dockerfile").read_text()
        self.assertNotIn("COPY metadata/categories.json /usr/share/nginx/html/categories.json", docker)

    def test_public_custom_facets_use_dom_text_and_valid_ids(self):
        js = (ROOT / "js/app.js").read_text()
        self.assertIn('fetch("/categories.json"', js)
        self.assertIn("runtimeCategoryIds.has(id)", js)
        self.assertIn('url.searchParams.set("category", activeCategory)', js)
        self.assertIn("link.dataset.runtimeCategory = item.id;", js)
        self.assertIn("title.textContent = item.label;", js)
        self.assertNotIn("innerHTML = item.label", js)
        self.assertIn('href="/tiere"', (ROOT / "index.html").read_text())


if __name__ == "__main__":
    unittest.main()
