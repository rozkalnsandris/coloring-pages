import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "build_catalog.py"
SPEC = importlib.util.spec_from_file_location("build_catalog", MODULE_PATH)
build_catalog = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(build_catalog)


class BuildCatalogTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.metadata = self.root / "metadata"
        self.originals = self.root / "originals" / "rettungshunde"
        self.metadata.mkdir(parents=True)
        self.originals.mkdir(parents=True)

    def tearDown(self):
        self.tempdir.cleanup()

    def write_record(self, name="ben-001.json", **overrides):
        record = {
            "id": "ben-001",
            "title": "Ben hilft bei der Feuerwehr",
            "character": "Ben",
            "category": "rettungshunde",
            "age": "3-6",
            "difficulty": "easy",
            "language": "de",
            "original": "originals/rettungshunde/ben-001.png",
        }
        record.update(overrides)
        path = self.metadata / name
        path.write_text(json.dumps(record), encoding="utf-8")
        return path

    def touch_original(self, relative="rettungshunde/ben-001.png"):
        path = self.root / "originals" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fixture")
        return path

    def test_empty_metadata_builds_empty_catalog(self):
        entries = build_catalog.load_catalog(self.metadata, self.root)
        self.assertEqual(entries, [])

    def test_valid_record_generates_deterministic_media_paths(self):
        self.touch_original()
        self.write_record()

        entries = build_catalog.load_catalog(self.metadata, self.root)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["id"], "ben-001")
        self.assertEqual(entries[0]["thumb"], "/media/ben-001/ben-001-thumb.webp")
        self.assertEqual(entries[0]["preview"], "/media/ben-001/ben-001-preview.webp")
        self.assertEqual(entries[0]["print"], "/media/ben-001/ben-001.png")
        self.assertEqual(entries[0]["pdf"], "/media/ben-001/ben-001.pdf")

    def test_duplicate_id_fails_closed(self):
        self.touch_original()
        self.write_record("a.json")
        self.write_record("b.json")

        with self.assertRaisesRegex(build_catalog.CatalogError, "duplicate id"):
            build_catalog.load_catalog(self.metadata, self.root)

    def test_missing_original_fails_closed(self):
        self.write_record()

        with self.assertRaisesRegex(build_catalog.CatalogError, "original does not exist"):
            build_catalog.load_catalog(self.metadata, self.root)

    def test_path_traversal_fails_closed(self):
        self.write_record(original="../secret.png")

        with self.assertRaisesRegex(build_catalog.CatalogError, "safe repository-relative"):
            build_catalog.load_catalog(self.metadata, self.root)

    def test_unknown_field_fails_closed(self):
        self.touch_original()
        self.write_record(extra="not-allowed")

        with self.assertRaisesRegex(build_catalog.CatalogError, "unexpected fields"):
            build_catalog.load_catalog(self.metadata, self.root)

    def test_invalid_enum_fails_closed(self):
        self.touch_original()
        self.write_record(difficulty="hard")

        with self.assertRaisesRegex(build_catalog.CatalogError, "difficulty must be one of"):
            build_catalog.load_catalog(self.metadata, self.root)

    def test_catalog_is_sorted_by_id(self):
        self.touch_original("rettungshunde/ben-002.png")
        self.touch_original("rettungshunde/ben-001.png")
        self.write_record(
            "z.json",
            id="ben-002",
            title="Ben zwei",
            original="originals/rettungshunde/ben-002.png",
        )
        self.write_record("a.json")

        entries = build_catalog.load_catalog(self.metadata, self.root)

        self.assertEqual([entry["id"] for entry in entries], ["ben-001", "ben-002"])

    def test_write_catalog_is_stable_json(self):
        output = self.root / "dist" / "catalog.json"
        entries = [{"id": "ben-001", "title": "Ä"}]

        build_catalog.write_catalog(entries, output)

        self.assertEqual(
            output.read_text(encoding="utf-8"),
            '[\n  {\n    "id": "ben-001",\n    "title": "Ä"\n  }\n]\n',
        )


if __name__ == "__main__":
    unittest.main()
