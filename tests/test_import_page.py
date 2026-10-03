import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "coloring-pages-import"
LOADER = importlib.machinery.SourceFileLoader("coloring_pages_import", str(MODULE_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
importer = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(importer)


class ImportPageTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.content = self.root / "content"
        for relative in ("inbox", "originals", "public/media", "state"):
            (self.content / relative).mkdir(parents=True, exist_ok=True)
        (self.content / "public/catalog.json").write_text("[]\n", encoding="utf-8")
        self.source = self.content / "inbox/fire-pup-001.png"
        self.write_source()

    def tearDown(self):
        self.tempdir.cleanup()

    def write_source(self, size=(1055, 1491), fmt="PNG", path=None):
        target = path or self.source
        image = Image.new("L", size, color=255)
        for x in range(150, min(size[0] - 150, 700)):
            image.putpixel((x, min(300, size[1] - 1)), 0)
        image.save(target, format=fmt)

    def metadata(self, **overrides):
        value = {
            "id": "fire-pup-001",
            "title": "Fire Pup 001",
            "character": "",
            "category": "rettungshunde",
            "age": "3-6",
            "difficulty": "easy",
            "language": "de",
        }
        value.update(overrides)
        return value

    def test_success_preserves_source_and_generates_derivatives(self):
        original_bytes = self.source.read_bytes()
        entry = importer.import_page(self.source, self.content, self.metadata())

        self.assertEqual(entry["id"], "fire-pup-001")
        original = self.content / "originals/fire-pup-001/source.png"
        media = self.content / "public/media/fire-pup-001"
        self.assertEqual(original.read_bytes(), original_bytes)
        self.assertEqual((media / "source.png").read_bytes(), original_bytes)
        self.assertTrue((media / "thumb.webp").is_file())
        self.assertTrue((media / "preview.webp").is_file())
        self.assertTrue((media / "print.pdf").read_bytes().startswith(b"%PDF"))

        catalog = json.loads(
            (self.content / "public/catalog.json").read_text(encoding="utf-8")
        )
        self.assertEqual(catalog, [entry])
        self.assertEqual(entry["thumb"], "/media/fire-pup-001/thumb.webp")
        self.assertEqual(entry["preview"], "/media/fire-pup-001/preview.webp")
        self.assertEqual(entry["print"], "/media/fire-pup-001/source.png")
        self.assertEqual(entry["pdf"], "/media/fire-pup-001/print.pdf")
        self.assertEqual(
            (self.content / "public/catalog.json").stat().st_mode & 0o777,
            0o644,
        )

    def test_unknown_category_rejected_before_publication(self):
        with self.assertRaisesRegex(importer.ImportError, "category must be one of"):
            importer.import_page(
                self.source,
                self.content,
                self.metadata(category="berufe"),
            )

    def test_category_registry_contains_current_public_filters(self):
        self.assertEqual(
            importer.load_allowed_categories(),
            frozenset(
                {
                    "rettungshunde",
                    "tiere",
                    "fahrzeuge",
                    "alphabet",
                    "lernen",
                    "jahreszeiten",
                }
            ),
        )

    def test_non_png_rejected(self):
        Image.new("RGB", (1055, 1491), "white").save(self.source, format="JPEG")
        with self.assertRaisesRegex(importer.ImportError, "source must be PNG"):
            importer.import_page(self.source, self.content, self.metadata())

    def test_two_by_three_source_is_accepted_and_preserved(self):
        self.write_source(size=(1024, 1536))
        original_bytes = self.source.read_bytes()

        importer.import_page(self.source, self.content, self.metadata())

        self.assertEqual(
            (self.content / "originals/fire-pup-001/source.png").read_bytes(),
            original_bytes,
        )
        self.assertEqual(
            (self.content / "public/media/fire-pup-001/source.png").read_bytes(),
            original_bytes,
        )
        self.assertTrue(
            (self.content / "public/media/fire-pup-001/print.pdf")
            .read_bytes()
            .startswith(b"%PDF")
        )

    def test_invalid_aspect_rejected(self):
        Image.new("L", (1200, 1200), 255).save(self.source, format="PNG")
        with self.assertRaisesRegex(importer.ImportError, "portrait orientation"):
            importer.import_page(self.source, self.content, self.metadata())

    def test_too_narrow_portrait_ratio_rejected(self):
        Image.new("L", (900, 1500), 255).save(self.source, format="PNG")
        with self.assertRaisesRegex(importer.ImportError, "approximately A4/2:3"):
            importer.import_page(self.source, self.content, self.metadata())

    def test_duplicate_id_rejected(self):
        importer.import_page(self.source, self.content, self.metadata())
        with self.assertRaisesRegex(importer.ImportError, "duplicate page id"):
            importer.import_page(self.source, self.content, self.metadata())

    def test_failure_keeps_published_catalog_unchanged(self):
        sentinel = [{"id": "existing-001"}]
        catalog = self.content / "public/catalog.json"
        catalog.write_text(json.dumps(sentinel) + "\n", encoding="utf-8")

        Image.new("L", (1200, 1200), 255).save(self.source, format="PNG")
        before = catalog.read_bytes()
        with self.assertRaises(importer.ImportError):
            importer.import_page(self.source, self.content, self.metadata())

        self.assertEqual(catalog.read_bytes(), before)

    def test_source_outside_inbox_is_rejected(self):
        outside = self.root / "outside.png"
        self.write_source(path=outside)
        with self.assertRaisesRegex(importer.ImportError, "inside the content inbox"):
            importer.import_page(outside, self.content, self.metadata())

    def test_nested_inbox_source_is_rejected(self):
        nested_dir = self.content / "inbox/nested"
        nested_dir.mkdir()
        nested = nested_dir / "fire-pup-001.png"
        self.write_source(path=nested)
        with self.assertRaisesRegex(importer.ImportError, "direct child"):
            importer.import_page(nested, self.content, self.metadata())

    def test_missing_bootstrap_layout_is_rejected(self):
        (self.content / "state").rmdir()
        with self.assertRaisesRegex(importer.ImportError, "required content directory"):
            importer.import_page(self.source, self.content, self.metadata())

    def test_filename_defaults_are_stable(self):
        path = self.root / "Water Rescue Pup 001.png"
        Image.new("L", (1055, 1491), 255).save(path, format="PNG")
        self.assertEqual(importer.slug_from_path(path), "water-rescue-pup-001")
        self.assertEqual(
            importer.default_title("water-rescue-pup-001"),
            "Water Rescue Pup 001",
        )


if __name__ == "__main__":
    unittest.main()
