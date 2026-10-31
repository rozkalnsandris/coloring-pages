"""Offline managed Topics v2 public and importer regressions (#438)."""
import copy
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LOADER = importlib.machinery.SourceFileLoader("cp_topics_438",
                                              str(ROOT / "tools/coloring_pages_topics.py"))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
topics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(topics)
LOADER = importlib.machinery.SourceFileLoader("cp_import_438",
                                              str(ROOT / "tools/coloring-pages-import"))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
importer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(importer)


class ManagedTopicsTests(unittest.TestCase):
    def setUp(self):
        self.seed = topics.seed_from_source(ROOT / "metadata/topics.json")

    def test_seed_preserves_all_v1_entries_and_digest(self):
        original = json.loads((ROOT / "metadata/topics.json").read_text())
        self.assertEqual(self.seed["topics"], original["topics"])
        self.assertEqual(self.seed["revision"], 1)
        encoded = topics.serialize_registry(self.seed)
        self.assertEqual(encoded, topics.serialize_registry(self.seed))
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "topics.json"
            path.write_bytes(encoded)
            self.assertEqual(topics.read_registry(path),
                             (self.seed, hashlib.sha256(encoded).hexdigest()))

    def test_add_rename_remove_change_revision_and_digest(self):
        doc = copy.deepcopy(self.seed)
        original = topics.serialize_registry(doc)
        doc["revision"] = 2
        doc["topics"].append({"id": "berufe", "label": "Berufe", "icon": "🧑‍🌾",
                              "kind": "evergreen", "legacy_terms": ["beruf"]})
        added = topics.serialize_registry(doc)
        self.assertNotEqual(original, added)
        doc["revision"] = 3
        doc["topics"][-1]["label"] = "Traumberufe"
        self.assertNotEqual(added, topics.serialize_registry(doc))
        doc["revision"] = 4
        doc["topics"].pop()
        self.assertNotEqual(original, topics.serialize_registry(doc))

    def test_schema_kind_calendar_terms_labels_and_duplicates_fail_closed(self):
        invalid = [
            lambda d: d.update(schema="wrong"),
            lambda d: d.update(revision=True),
            lambda d: d.update(revision=0),
            lambda d: d.update(topics=[]),
            lambda d: d.update(topics=d["topics"] * 7),
            lambda d: d["topics"].append(copy.deepcopy(d["topics"][0])),
            lambda d: d["topics"][0].update(id="../bad"),
            lambda d: d["topics"][0].update(label=" E\u0301 "),
            lambda d: d["topics"][0].update(icon="<script>"),
            lambda d: d["topics"][0].update(kind="other"),
            lambda d: d["topics"][0].update(extra=True),
            lambda d: d["topics"][0].update(active_from="02-30"),
            lambda d: d["topics"][0].update(active_to="13-01"),
            lambda d: d["topics"][0].update(legacy_terms=["repeat", "repeat"]),
            lambda d: d["topics"][0].update(legacy_terms=["\x00bad"]),
            lambda d: d["topics"][-1].update(active_from="01-01"),
            lambda d: d["topics"][-1].pop("legacy_terms"),
        ]
        for edit in invalid:
            doc = copy.deepcopy(self.seed)
            edit(doc)
            with self.subTest(edit=edit), self.assertRaises(topics.RegistryError):
                topics.serialize_registry(doc)

    def test_cross_year_and_leap_day(self):
        winter = next(t for t in self.seed["topics"] if t["id"] == "winter")
        self.assertEqual((winter["active_from"], winter["active_to"]), ("12-01", "02-29"))
        topics.serialize_registry(self.seed)

    def test_missing_symlink_permission_and_noncanonical_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "topics.json"
            with self.assertRaises(topics.RegistryError):
                topics.read_registry(path)
            path.write_bytes(topics.serialize_registry(self.seed))
            os.chmod(path, 0o666)
            with self.assertRaises(topics.RegistryError):
                topics.read_registry(path)
            os.chmod(path, 0o644)
            path.write_text(json.dumps(self.seed))
            with self.assertRaises(topics.RegistryError):
                topics.read_registry(path)
            path.unlink()
            path.symlink_to(ROOT / "metadata/topics.json")
            with self.assertRaises(topics.RegistryError):
                topics.read_registry(path)

    def test_importer_rejects_missing_or_stale_topics_without_catalog_writes(self):
        from coloring_pages_categories import seed_from_source, serialize_registry
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            for directory in ("inbox", "originals", "public/media", "state"):
                (root / directory).mkdir(parents=True, exist_ok=True)
            catalog = root / "public/catalog.json"
            catalog.write_text("[]\n")
            (root / "public/categories.json").write_bytes(
                serialize_registry(seed_from_source(ROOT / "metadata/categories.json")))
            source = root / "inbox/page.png"
            source.write_bytes(b"invalid-png")
            meta = {"id": "page", "title": "Page", "character": "",
                    "category": "tiere", "age": "3-6", "difficulty": "easy", "language": "de"}
            with self.assertRaisesRegex(importer.ImportError, "topic registry"):
                importer.import_page(source, root, meta)
            (root / "public/topics.json").write_bytes(topics.serialize_registry(self.seed))
            with self.assertRaisesRegex(importer.ImportError, "SHA-256"):
                importer.import_page(source, root, dict(meta, topic_registry_sha256="0"*64))
            self.assertEqual(catalog.read_text(), "[]\n")
            self.assertEqual(list((root / "public/media").iterdir()), [])

    def test_contract_exact_runtime_endpoint_and_no_seed_fallback(self):
        nginx = (ROOT / "deploy/nginx.conf").read_text()
        block = nginx.split("location = /topics.json {")[1].split("}", 1)[0]
        self.assertIn("root /var/lib/coloring-pages/public", block)
        self.assertIn("try_files /topics.json =503", block)
        self.assertIn('Cache-Control "no-store"', block)
        docker = (ROOT / "Dockerfile").read_text()
        self.assertNotIn("COPY metadata/topics.json /usr/share/nginx/html/topics.json", docker)
        self.assertIn("COPY tools/coloring_pages_topics.py", docker)
        contract = json.loads((ROOT / "deploy/importer-runtime.json").read_text())
        self.assertEqual(contract["topic_registry"], "/srv/coloring-pages-content/public/topics.json")
        self.assertEqual(contract["topic_registry_version_argument"], "--topics-sha256")
        self.assertIn("rozkalns.coloring-pages.topics.v2", (ROOT / "js/app.js").read_text())


if __name__ == "__main__":
    unittest.main()
