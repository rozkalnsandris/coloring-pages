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
        self.source = self.root / "fire-pup-001.png"
        self.write_source()

    def tearDown(self):
        self.tempdir.cleanup()

    def write_source(self, size=(1055, 1491), fmt="PNG"):
        image = Image.new("L", size, color=255)
        for x in range(150, min(size[0] - 150, 700)):
            image.putpixel((x, min(300, size[1] - 1)), 0)
        image.save(self.source, format=fmt)

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

    def test_non_png_rejected(self):
        Image.new("RGB", (1055, 1491), "white").save(self.source, format="JPEG")
        with self.assertRaisesRegex(importer.ImportError, "source must be PNG"):
            importer.import_page(self.source, self.content, self.metadata())

    def test_invalid_aspect_rejected(self):
        Image.new("L", (1200, 1200), 255).save(self.source, format="PNG")
        with self.assertRaisesRegex(importer.ImportError, "portrait orientation"):
            importer.import_page(self.source, self.content, self.metadata())

    def test_duplicate_id_rejected(self):
        importer.import_page(self.source, self.content, self.metadata())
        with self.assertRaisesRegex(importer.ImportError, "duplicate page id"):
            importer.import_page(self.source, self.content, self.metadata())

    def test_failure_keeps_published_catalog_unchanged(self):
        public = self.content / "public"
        public.mkdir(parents=True)
        sentinel = [{"id": "existing-001"}]
        catalog = public / "catalog.json"
        catalog.write_text(json.dumps(sentinel) + "\n", encoding="utf-8")

        Image.new("L", (1200, 1200), 255).save(self.source, format="PNG")
        before = catalog.read_bytes()
        with self.assertRaises(importer.ImportError):
            importer.import_page(self.source, self.content, self.metadata())

        self.assertEqual(catalog.read_bytes(), before)

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
